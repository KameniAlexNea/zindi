# Imports

import os
from getpass import getpass

import pandas as pd

from zindi.platform_api import ZindiPlatformAPI
from zindi.utils import (
    challenge_idx_selector,
    download,
    print_challenges,
    print_lb,
    print_submission_board,
    user_on_lb,
)


class Zindian:
    """High-level user class for Zindi interactions with optional console output."""

    def __init__(self, username, fixed_password=None, to_print=True, api_client=None):
        self.__headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"
        }
        self.__base_api = "https://api.zindi.africa/v1/competitions"
        self.__to_print = to_print
        self.__api_client = api_client or ZindiPlatformAPI(
            base_api=self.__base_api,
            default_headers=self.__headers,
        )
        self.__auth_data = self.__signin(username, fixed_password)
        self.__challenge_selected = False

    def __emit(self, message, to_print=None):
        should_print = self.__to_print if to_print is None else to_print
        if should_print:
            print(message)

    def __require_challenge(self):
        if not self.__challenge_selected:
            error_msg = (
                "\n[ 🔴 ] You have to select a challenge before this action,"
                "\n\tuse the select_a_challenge method before.\n"
            )
            raise Exception(error_msg)
        return self.__challenge_data["id"]

    @property
    def which_challenge(self):
        if self.__challenge_selected:
            return self.__challenge_data["id"]
        return None

    @property
    def my_rank(self):
        if not self.__challenge_selected:
            return 0
        challenge_id = self.__require_challenge()
        response_data = self.__api_client.get_my_participation(
            auth_token=self.__auth_data["auth_token"],
            challenge_id=challenge_id,
        )
        int_rank = response_data.get("public_rank", 0) or 0
        self.__rank = int_rank
        return int_rank

    @property
    def remaining_subimissions(self):
        if not self.__challenge_selected:
            return None
        challenge_id = self.__require_challenge()
        response_data = self.__api_client.get_submission_limits(
            auth_token=self.__auth_data["auth_token"],
            challenge_id=challenge_id,
        )
        return response_data.get("today")

    def __signin(self, username, fixed_password=None):
        password = fixed_password if fixed_password is not None else getpass(prompt="Your password\n>> ")
        response = self.__api_client.signin(username=username, password=password)
        self.__emit(f"\n[ 🟢 ] 👋🏾👋🏾 Welcome {response['user']['username'] } 👋🏾👋🏾\n")
        return response

    def search_competitions(
        self,
        query: str = None,
        kind: str = "competition",
        reward: str = None,
        active: bool = True,
        per_page: int = 20,
    ):
        """Return available competitions as JSON-like list of dictionaries."""

        competitions = self.__api_client.search_competitions(
            auth_token=self.__auth_data["auth_token"],
            query=query,
            kind=kind,
            reward=reward,
            active=active,
            per_page=per_page,
        )
        if isinstance(competitions, dict):
            return competitions.get("results", [])
        return competitions

    def __normalize_challenges(self, competitions):
        """Normalize challenge rows to the schema expected by print helpers."""

        challenges_data = pd.DataFrame(competitions)
        if challenges_data.empty:
            return challenges_data

        alias_map = {
            "id": ["id", "slug"],
            "kind": ["kind", "type"],
            "subtitle": ["subtitle", "title", "name"],
            "reward": ["reward", "prize"],
            "type_of_problem": ["type_of_problem", "problem_type", "problem_types"],
            "data_type": ["data_type", "dataset_type", "data_types"],
            "secret_code_required": ["secret_code_required", "private"],
            "sealed": ["sealed"],
        }

        normalized = pd.DataFrame(index=challenges_data.index)
        for target, candidates in alias_map.items():
            source = next((name for name in candidates if name in challenges_data.columns), None)
            if source is None:
                if target in {"type_of_problem", "data_type"}:
                    normalized[target] = [[] for _ in range(len(challenges_data))]
                elif target in {"secret_code_required", "sealed"}:
                    normalized[target] = False
                else:
                    normalized[target] = ""
            else:
                normalized[target] = challenges_data[source]

        for list_col in ["type_of_problem", "data_type"]:
            normalized[list_col] = normalized[list_col].apply(
                lambda x: x if isinstance(x, list) else ([] if pd.isna(x) else [str(x)])
            )

        normalized["secret_code_required"] = normalized["secret_code_required"].fillna(False).astype(bool)
        normalized["sealed"] = normalized["sealed"].fillna(False).astype(bool)
        return normalized

    def select_a_challenge(
        self,
        challenge_id: str = None,
        query: str = None,
        kind: str = "competition",
        reward: str = None,
        active: bool = True,
        fixed_index: int = None,
        per_page: int = 20,
        to_print=None,
    ):
        competitions = []

        if challenge_id:
            try:
                self.__challenge_data = self.__api_client.get_competition(
                    auth_token=self.__auth_data["auth_token"],
                    challenge_id=challenge_id,
                )
            except Exception:
                return {
                    "challenge": None,
                    "joined": False,
                    "message": f"Challenge '{challenge_id}' not found.",
                }
        else:
            competitions = self.search_competitions(
                query=query,
                kind=kind,
                reward=reward,
                active=active,
                per_page=per_page,
            )
            if len(competitions) == 0:
                return {
                    "challenge": None,
                    "joined": False,
                    "message": "No challenges found matching your criteria.",
                }

            challenges_data = self.__normalize_challenges(competitions)
            n_challenges = challenges_data.shape[0]
            if fixed_index is None:
                if self.__to_print if to_print is None else to_print:
                    print_challenges(challenges_data=challenges_data)
                challenge_index = challenge_idx_selector(n_challenges)
            else:
                if (
                    not isinstance(fixed_index, int)
                    or fixed_index < 0
                    or fixed_index >= n_challenges
                ):
                    raise Exception(
                        f"\n[ 🔴 ] The parameter 'fixed_index' must be an integer in range(0, {n_challenges}).\n"
                    )
                challenge_index = fixed_index

            if challenge_index < 0:
                return {
                    "challenge": None,
                    "joined": False,
                    "message": "No challenge selected.",
                }
            self.__challenge_data = challenges_data.iloc[challenge_index].to_dict()

        challenge_id = self.__challenge_data["id"]
        self.__api = f"{self.__base_api}/{challenge_id}"
        self.__challenge_selected = True

        self.__emit(
            f"\n[ 🟢 ] You choose the challenge : {self.__challenge_data['id']},\n\t{self.__challenge_data.get('subtitle', '')}.\n",
            to_print=to_print,
        )

        join_response = self.__api_client.join_competition(
            auth_token=self.__auth_data["auth_token"],
            challenge_id=challenge_id,
        )
        return {"challenge": self.__challenge_data, "joined": join_response}

    def download_dataset(self, destination=".", make_destination=True):
        challenge_id = self.__require_challenge()
        if not os.path.isdir(destination) and make_destination:
            os.makedirs(destination, exist_ok=True)

        challenge_data = self.__api_client.get_competition(
            auth_token=self.__auth_data["auth_token"],
            challenge_id=challenge_id,
        )
        datafiles = []
        for item in challenge_data.get("datafiles", []):
            if item not in datafiles:
                datafiles.append(item)

        headers = {**self.__headers, "auth_token": self.__auth_data["auth_token"]}
        downloaded_files = []
        for item in datafiles:
            filename = os.path.join(destination, item["filename"])
            download(
                url=f"{self.__base_api}/{challenge_id}/files/{item['filename']}",
                filename=filename,
                headers=headers,
            )
            downloaded_files.append(filename)
        return downloaded_files

    def submit(self, filepaths=None, comments=None, to_print=None):
        filepaths = filepaths or []
        comments = comments or []
        challenge_id = self.__require_challenge()

        allowed_extensions = {"csv"}
        if len(comments) < len(filepaths):
            comments = comments + ([""] * (len(filepaths) - len(comments)))

        submissions = []
        for filepath, comment in zip(filepaths, comments):
            extension = filepath.split(".")[-1].strip().lower()
            if extension not in allowed_extensions:
                self.__emit(
                    f"\n[ 🔴 ] Submission file must be a CSV file ( .csv ),\n\tplease verify this filepath : {filepath}\n",
                    to_print=to_print,
                )
                submissions.append(
                    {"filepath": filepath, "status": "error", "errors": "invalid_extension"}
                )
                continue

            if not os.path.isfile(filepath):
                self.__emit(
                    f"\n[ 🔴 ] File doesn't exists, please verify this filepath : {filepath}\n",
                    to_print=to_print,
                )
                submissions.append(
                    {"filepath": filepath, "status": "error", "errors": "file_not_found"}
                )
                continue

            response = self.__api_client.submit_file(
                auth_token=self.__auth_data["auth_token"],
                challenge_id=challenge_id,
                filepath=filepath,
                comment=comment,
            )
            if "errors" in response:
                self.__emit(
                    f"\n[ 🔴 ] Something wrong with file :{filepath} ,\n{response['errors']}\n",
                    to_print=to_print,
                )
                submissions.append(
                    {"filepath": filepath, "status": "error", "errors": response["errors"]}
                )
            else:
                self.__emit(
                    f"\n[ 🟢 ] Submission ID: {response['id'] } - File submitted : {filepath}\n",
                    to_print=to_print,
                )
                submissions.append(
                    {
                        "filepath": filepath,
                        "status": "success",
                        "submission_id": response["id"],
                    }
                )
        return submissions

    def leaderboard(self, to_print=True, per_page=50):
        challenge_id = self.__require_challenge()
        self.__challengers_data = self.__api_client.get_leaderboard(
            auth_token=self.__auth_data["auth_token"],
            challenge_id=challenge_id,
            per_page=per_page,
        )
        headers = {**self.__headers, "auth_token": self.__auth_data["auth_token"]}
        self.__rank = user_on_lb(
            challengers_data=self.__challengers_data,
            challenge_id=challenge_id,
            username=self.__auth_data["user"]["username"],
            headers=headers,
        )
        if to_print:
            print_lb(challengers_data=self.__challengers_data, user_rank=self.__rank)
        return {"rank": self.__rank, "leaderboard": self.__challengers_data}

    def submission_board(self, to_print=True, per_page=50):
        challenge_id = self.__require_challenge()
        self.__sb_data = self.__api_client.get_submission_history(
            auth_token=self.__auth_data["auth_token"],
            challenge_id=challenge_id,
            per_page=per_page,
        )
        if to_print:
            print_submission_board(submissions_data=self.__sb_data)
        return self.__sb_data

    def create_team(self, team_name, teammates=None, to_print=None):
        teammates = teammates or []
        challenge_id = self.__require_challenge()
        response = self.__api_client.create_team(
            auth_token=self.__auth_data["auth_token"],
            challenge_id=challenge_id,
            team_name=team_name,
        )

        if ("errors" in response) and ("Leader can only be" not in response["errors"]["base"]):
            raise Exception(f"\n[ 🔴 ] {response['errors']['base']}\n")

        if ("errors" in response) and ("Leader can only be" in response["errors"]["base"]):
            self.__emit("\n[ 🟢 ] You are already the leader of a team.\n", to_print=to_print)
            team_response = {"already_leader": True, "team": None}
        else:
            self.__emit(
                f"\n[ 🟢 ] Your team is well created as :{response['title']}\n",
                to_print=to_print,
            )
            team_response = {"already_leader": False, "team": response}

        invites = self.team_up(teammates, to_print=to_print) if teammates else []
        if not teammates:
            self.__emit(
                "You can send invitation to join your team using teamup function",
                to_print=to_print,
            )
        return {**team_response, "invites": invites}

    def team_up(self, zindians=None, to_print=None):
        zindians = zindians or []
        challenge_id = self.__require_challenge()
        invitations = []
        for zindian in zindians:
            response = self.__api_client.invite_to_team(
                auth_token=self.__auth_data["auth_token"],
                challenge_id=challenge_id,
                username=zindian,
            )
            if "errors" in response:
                if "is already invited" in response["errors"]["base"]:
                    self.__emit(
                        f"\n[ 🟢 ] An invitation has been sent already to join your team to: {zindian}\n",
                        to_print=to_print,
                    )
                    invitations.append({"username": zindian, "status": "already_invited"})
                else:
                    raise Exception(f"\n[ 🔴 ] {response['errors']}\n")
            else:
                self.__emit(
                    f"\n[ 🟢 ] An invitation has been sent to join your team to: {zindian}\n",
                    to_print=to_print,
                )
                invitations.append({"username": zindian, "status": "invited"})
        return invitations

    def disband_team(self):
        challenge_id = self.__require_challenge()
        response = self.__api_client.disband_team(
            auth_token=self.__auth_data["auth_token"],
            challenge_id=challenge_id,
        )
        if "errors" in response:
            raise Exception(f"\n[ 🔴 ] {response['errors']}\n")
        self.__emit(f"\n[ 🟢 ] {response}\n")
        return response
