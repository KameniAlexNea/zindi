# Imports

import os
from getpass import getpass

import requests

from zindi.utils import (
    challenge_idx_selector,
    download,
    get_challenges,
    join_challenge,
    print_challenges,
    print_lb,
    print_submission_board,
    upload,
    user_on_lb,
)


# Class declaration and init
class Zindian:
    """Zindi user-friendly account manager."""

    def __init__(self, username, fixed_password=None):
        """Singin, connect user to the Zindi platform.

        Parameters
        ----------
        username : string
            The challenger's username.
        fixed_password : string, default=None
            The challenger's password, for test.

        """
        self.__headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"
        }
        self.__base_api = "https://api.zindi.africa/v1/competitions"
        self.__auth_data = self.__signin(
            username, fixed_password
        )  # auth & user data from Zindi server after signin
        self.__challenge_selected = False

    # Properties
    @property
    def which_challenge(
        self,
    ):
        """Property: Get the information about the selected challenge."""

        if self.__challenge_selected:
            msg = f"\n[ 🟢 ] You are currently enrolled in : {self.__challenge_data['id']} challenge,\n\t{self.__challenge_data['subtitle']}.\n"
            challenge = self.__challenge_data["id"]
        else:
            msg = "\n[ 🔴 ] You have not yet selected any challenge.\n"
            challenge = None
        print(msg)
        return challenge

    @property
    def my_rank(
        self,
    ):
        """Property: Get the user rank on the leaderboard for the selected challenge."""

        if self.__challenge_selected:
            url = f"{self.__api}/participations/my_participation"
            headers = {
                **self.__headers,
                "auth-token": self.__auth_data["auth_token"],
                "current-url": f"https://zindi.africa/competitions/{self.__challenge_data['id']}/leaderboard",
            }

            response = requests.get(url, headers=headers)
            response_data = response.json()["data"]

            if "errors" in response_data:
                error_msg = f"\n[ 🔴 ] {response_data['errors']}\n"
                raise Exception(error_msg)

            int_rank = response_data.get("public_rank", 0) or 0
            self.__rank = int_rank

            if int_rank == 0:
                rank = "not yet"
            elif str(int_rank)[-1] == "1":
                if len(str(int_rank)) > 1 and str(int_rank)[-2] == "1":
                    rank = f"{int_rank}th"
                else:
                    rank = f"{int_rank}st"
            elif str(int_rank)[-1] == "2":
                if len(str(int_rank)) > 1 and str(int_rank)[-2] == "1":
                    rank = f"{int_rank}th"
                else:
                    rank = f"{int_rank}nd"
            elif str(int_rank)[-1] == "3":
                if len(str(int_rank)) > 1 and str(int_rank)[-2] == "1":
                    rank = f"{int_rank}th"
                else:
                    rank = f"{int_rank}rd"
            else:
                rank = f"{int_rank}th"
            msg = f"\n[ 🟢 ] You are {rank} on the leaderboad of {self.__challenge_data['id']} challenge, Go on...\n"
        else:
            msg = "\n[ 🔴 ] You have not yet selected any challenge.\n"
            int_rank = 0
        print(msg)
        return int_rank

    @property
    def remaining_subimissions(
        self,
    ):
        """Property: Get the number of now remaining submissions for the selected challenge.

        Returns
        -------
        free_submissions : int
            The number of now remaining submissions.
        """
        free_submissions = None
        if self.__challenge_selected:
            url = f"{self.__api}/submissions/limits"
            headers = {**self.__headers, "auth-token": self.__auth_data["auth_token"], "current-url": f"{self.__api}/submit"}

            response = requests.get(url, headers=headers)
            response_data = response.json()["data"]

            if "errors" in response_data:
                error_msg = f"\n[ 🔴 ] {response_data['errors']}\n"
                raise Exception(error_msg)

            free_submissions = response_data["today"]
            msg = f"\n[ 🟢 ] You have {free_submissions} remaining submissions for the challenge {self.__challenge_data['id']}.\n"
            print(msg)
        else:
            msg = "\n[ 🔴 ] You have not yet selected any challenge.\n"
            print(msg)
        return free_submissions

    # Account
    ## Sign In
    def __signin(self, username, fixed_password=None):
        """Singin, connect user to the Zindi platform.

        Parameters
        ----------
        username : string
            The challenger's username.
        fixed_password : string, default=None
            The challenger's password, for test.

        Returns
        -------
        auth_data :  dictionary | json
            The json's response of the sign in request.
        """

        auth_data = None
        url = "https://api.zindi.africa/v1/auth/signin"
        if fixed_password is None:
            password = getpass(prompt="Your password\n>> ")
        else:
            password = fixed_password
        data = {"username": username, "password": password}

        response = requests.post(url, data=data, headers=self.__headers)
        response = response.json()["data"]
        if "errors" in response:
            error_msg = f"[ 🔴 ] {response['errors']}"
            raise Exception(error_msg)
        else:
            print(
                f"\n[ 🟢 ] 👋🏾👋🏾 Welcome {response['user']['username'] } 👋🏾👋🏾\n"
            )
            auth_data = response
        return auth_data

    # Challenge
    ## Select a challenge to participate in
    def select_a_challenge(
        self,
        challenge_id: str = None,
        query: str = None,
        kind: str = "competition",
        reward: str = None,
        active: bool = True,
        fixed_index: int = None,
        per_page: int = 20,
    ):
        """Select a challenge among those available on Zindi, using filter options.

        Parameters
        ----------
        challenge_id : str, default=None
            Direct challenge ID to select (e.g., 'digicow-farmer-training-adoption-challenge').
            If provided, other filter parameters are ignored.
        query : str, default=None
            Text search query to filter challenges by name (e.g., 'Digi', 'Health').
        kind : {'competition', 'hackathon'}, default='competition'
            The kind of the challenges.
        reward : {'prize', 'points', 'knowledge'}, default=None
            The reward type of the challenges. None means all rewards.
        active : bool, default=True
            Whether to show only active challenges.
        fixed_index : int, default=None
            The set index of the selected challenge (for programmatic selection).
        per_page : int, default=20
            The number of challenges to retrieve per page.

        """

        headers = {
            **self.__headers,
            "auth-token": self.__auth_data["auth_token"],
            "current-url": "https://zindi.africa/competitions",
        }

        # Direct selection by challenge_id
        if challenge_id:
            url = f"{self.__base_api}/{challenge_id}"
            response = requests.get(url, headers=headers)
            response_data = response.json()["data"]

            if "errors" in response_data:
                error_msg = f"\n[ 🔴 ] Challenge '{challenge_id}' not found.\n"
                print(error_msg)
                return

            self.__challenge_data = response_data
            self.__api = url
            self.__challenge_selected = True

            # Join the challenge
            join_url = f"{self.__api}/participations"
            print(
                f"\n[ 🟢 ] You choose the challenge : {self.__challenge_data['id']},\n\t{self.__challenge_data.get('subtitle', '')}\n"
            )
            join_challenge(url=join_url, headers=headers)
            return

        # Search-based selection
        url = self.__base_api
        challenges_data = get_challenges(
            query=query,
            kind=kind,
            reward=reward,
            active=active,
            url=url,
            headers=headers,
            per_page=per_page,
        )
        n_challenges = challenges_data.shape[0]

        if n_challenges == 0:
            print("\n[ 🔴 ] No challenges found matching your criteria.\n")
            return

        if fixed_index is None:
            print_challenges(challenges_data=challenges_data)
            challenge_index = challenge_idx_selector(n_challenges)
        else:
            if not isinstance(fixed_index, int) or fixed_index < 0 or fixed_index >= n_challenges:
                error_msg = f"\n[ 🔴 ] The parameter 'fixed_index' must be an integer in range(0, {n_challenges}).\n"
                raise Exception(error_msg)
            challenge_index = fixed_index

        if challenge_index > -1:
            self.__challenge_data = challenges_data.iloc[challenge_index]
            self.__api = f"{self.__base_api}/{self.__challenge_data['id']}"
            self.__challenge_selected = True
            url = f"{self.__api}/participations"
            print(
                f"\n[ 🟢 ] You choose the challenge : {self.__challenge_data['id']},\n\t{self.__challenge_data['subtitle']}.\n"
            )
            join_challenge(
                url=url,
                headers=headers,
            )

    ## Download dataset
    def download_dataset(self, destination=".", make_destination=True):
        """Download the dataset of the selected challenge.

        Parameters
        ----------
        destination : str, default='.'
            The dataset's destination folder .
        make_destination : bool, default=True
            Create destination folder if doesn't exist.

        """

        if not os.path.isdir(destination) and make_destination:
            os.makedirs(destination, exist_ok=True)
        if self.__challenge_selected:
            headers = {**self.__headers, "auth_token": self.__auth_data["auth_token"]}
            data = {"auth_token": self.__auth_data["auth_token"]}
            url = self.__api

            response = requests.get(url, headers=headers, data=data)
            datafiles_ = response.json()["data"]["datafiles"]
            datafiles = []
            [
                datafiles.append(i) for i in datafiles_ if i not in datafiles
            ]  # remove deplicates

            # DOWNLOAD FILES USING ANOTHER METHOD TO SAVE THE ABILITY OF MULTIPROCESSING
            [
                download(
                    url=f"{url}/files/{data['filename']}",
                    filename=os.path.join(destination, data["filename"]),
                    headers=headers,
                )
                for data in datafiles
            ]

        else:
            error_msg = "\n[ 🔴 ] You have to select a challenge before to downoad a dataset,\n\tuse the select_a_challenge method before.\n"
            raise Exception(error_msg)

    ## Push submission file
    def submit(self, filepaths=[], comments=[]):
        """Push submission files for the selected challenge to Zindi platform.

        Parameters
        ----------
        filepaths : list
            The filepaths of submission files to push.
        comments : list
            The comments of submission files to push.

        """

        if self.__challenge_selected:
            headers = {**self.__headers, "auth_token": self.__auth_data["auth_token"]}
            url = f"{self.__api}/submissions"
            # self.submit__ = url
            allowed_extensions = [
                "csv",
            ]
            if len(comments) < len(filepaths):
                n_blank_comment = len(filepaths) - len(comments)
                comments += [""] * n_blank_comment

            for filepath, comment in zip(filepaths, comments):
                extension = filepath.split(".")[-1].strip().lower()
                if extension in allowed_extensions:
                    if os.path.isfile(filepath):
                        # print(f"[INFO] Submiting file : {filepath} , wait ...")
                        response = upload(
                            filepath=filepath,
                            comment=comment,
                            url=url,
                            headers=headers,
                        )
                        response = response.json()["data"]
                        try:
                            print(
                                f"\n[ 🔴 ] Something wrong with file :{filepath} ,\n{response['errors']}\n"
                            )
                        except:
                            print(
                                f"\n[ 🟢 ] Submission ID: {response['id'] } - File submitted : {filepath}\n"
                            )
                    else:
                        print(
                            f"\n[ 🔴 ] File doesn't exists, please verify this filepath : {filepath}\n"
                        )
                else:
                    print(
                        f"\n[ 🔴 ] Submission file must be a CSV file ( .csv ),\n\tplease verify this filepath : {filepath}\n"
                    )
        else:
            error_msg = "\n[ 🔴 ] You have to select a challenge before to push any submission file,\n\tuse the select_a_challenge method before.\n"
            raise Exception(error_msg)

    ## Show leaderboard
    def leaderboard(self, to_print=True, per_page=50):
        """Get the leaderboard and update the user rank for the selected challenge.

        Parameters
        ----------
        to_print : boolean, default=True
            Display the leaderboard or not.

        """

        if self.__challenge_selected:
            headers = {**self.__headers, "auth_token": self.__auth_data["auth_token"]}
            url = f"{self.__api}/participations"
            params_in_url = {
                "page": 0,
                "per_page": per_page,
            }

            response = requests.get(url, headers=headers, params=params_in_url)
            response = response.json()["data"]
            if "errors" in response:
                error_msg = f"\n[ 🔴 ] {response['errors']}\n"
                raise Exception(error_msg)
            else:
                self.__challengers_data = response
                self.__rank = user_on_lb(
                    challengers_data=self.__challengers_data,
                    challenge_id=self.__challenge_data["id"],
                    username=self.__auth_data["user"]["username"],
                    headers=headers,
                )
                if to_print:
                    print_lb(
                        challengers_data=self.__challengers_data, user_rank=self.__rank
                    )
        else:
            error_msg = "\n[ 🔴 ] You have to select a challenge before to get the leaderboard,\n\tuse the select_a_challenge method before.\n"
            raise Exception(error_msg)

    ## Show Submission-board
    def submission_board(self, to_print=True, per_page=50):
        """Get the submission-board for the selected challenge and upadte the private parameters __sb_data for compute remaining submissions.

        Parameters
        ----------
        to_print : boolean, default=True
            Display the submission-board or not.

        """

        # to add : number of submission, available subissions to do
        if self.__challenge_selected:
            url = f"{self.__api}/submissions"
            headers = {**self.__headers, "auth-token": self.__auth_data["auth_token"]}

            params_in_url = {
                "per_page": per_page
            }  # per_page : max number of subimission to retrieve
            response = requests.get(
                url,
                headers=headers,
                data={"auth-token": headers["auth-token"]},
                params=params_in_url,
            )
            print(response)
            response = response.json()["data"]
            if "errors" in response:
                error_msg = f"\n[ 🔴 ] {response['errors']}\n"
                raise Exception(error_msg)
            else:
                self.__sb_data = response
                # self.sb_data = response # for test
                if to_print:
                    print_submission_board(submissions_data=self.__sb_data)
        else:
            error_msg = "\n[ 🔴 ] You have to select a challenge before to get the submission-board,\n\tuse the select_a_challenge method before.\n"
            raise Exception(error_msg)

    # Team
    ## Create
    def create_team(self, team_name, teammates=[]):
        """Create a team for the selected challenge.

        Parameters
        ----------
        team_name : string
            Name of the team to create.
        teammates : list
            List of usernames of Zindians you want to invite to be part of your team.

        """

        if self.__challenge_selected:
            headers = {
                **self.__headers,
            }
            url = f"{self.__api}/my_team"
            data = {"title": team_name, "auth_token": self.__auth_data["auth_token"]}

            response = requests.post(url, headers=headers, data=data)
            response = response.json()["data"]
            if ("errors" in response) and (
                "Leader can only be" not in response["errors"]["base"]
            ):

                error_msg = f"\n[ 🔴 ] {response['errors']['base']}\n"
                raise Exception(error_msg)
            else:
                if ("errors" in response) and (
                    "Leader can only be" in response["errors"]["base"]
                ):
                    print("\n[ 🟢 ] You are already the leader of a team.\n")
                else:
                    print(
                        f"\n[ 🟢 ] Your team is well created as :{response['title']}\n"
                    )
                ##### Invite teammates
                if len(teammates) > 0:
                    self.team_up(zindians=teammates)
                else:
                    print(
                        "You can send invitation to join your team using teamup function"
                    )
        else:
            error_msg = "\n[ 🔴 ] You have to select a challenge before to manage your team,\n\tuse the select_a_challenge method before.\n"
            raise Exception(error_msg)

    ## Team Up
    def team_up(self, zindians=[]):
        """Add challengers to user team for the selected challenge.

        Parameters
        ----------
        zindians : list
            List of challenger's usernames of Zindians to add the team.

        """

        if self.__challenge_selected:
            headers = {
                **self.__headers,
            }
            data = {"auth_token": self.__auth_data["auth_token"]}
            url = f"{self.__api}/my_team/invite"

            for zindian in zindians:
                data = {"username": zindian}
                response = requests.post(url, headers=headers, data=data)
                response = response.json()["data"]
                if "errors" in response:
                    if "is already invited" in response["errors"]["base"]:
                        print(
                            f"\n[ 🟢 ] An invitation has been sent already to join your team to: {zindian}\n"
                        )
                    else:
                        error_msg = f"\n[ 🔴 ] {response['errors']}\n"
                        raise Exception(error_msg)
                else:
                    print(
                        f"\n[ 🟢 ] An invitation has been sent to join your team to: {zindian}\n"
                    )

        else:
            error_msg = "\n[ 🔴 ] You have to select a challenge before to manage your team,\n\tuse the select_a_challenge method before.\n"
            raise Exception(error_msg)

    ## Disband ... think to add kick function to kick-off some selected teammates... think to add team status (invited users, teammates)
    def disband_team(
        self,
    ):
        """Disband user team for the selected challenge."""

        if self.__challenge_selected:
            headers = {
                **self.__headers,
            }
            data = {"auth_token": self.__auth_data["auth_token"]}
            url = f"{self.__api}/my_team"

            response = requests.delete(url, headers=headers, data=data)
            response = response.json()["data"]
            if "errors" in response:
                error_msg = f"\n[ 🔴 ] {response['errors']}\n"
                raise Exception(error_msg)
            else:
                print(f"\n[ 🟢 ] {response}\n")
        else:
            error_msg = "\n[ 🔴 ] You have to select a challenge before to manage your team,\n\tuse the select_a_challenge method before.\n"
            raise Exception(error_msg)
