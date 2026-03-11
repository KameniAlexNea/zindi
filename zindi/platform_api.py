import requests

from zindi.utils import upload


class ZindiPlatformAPI:
    """Low-level Zindi HTTP client that returns JSON data payloads."""

    def __init__(self, base_api: str, default_headers: dict):
        self.base_api = base_api
        self.default_headers = default_headers

    def _response_data(self, response):
        try:
            payload = response.json()
        except ValueError:
            body_preview = (response.text or "").strip().replace("\n", " ")[:240]
            raise Exception(
                f"[ 🔴 ] Invalid non-JSON response from Zindi API "
                f"(status={response.status_code}). Body preview: {body_preview}"
            )
        return payload.get("data", payload)

    def _raise_on_errors(self, data):
        if "errors" in data:
            raise Exception(f"[ 🔴 ] {data['errors']}")
        return data

    def _auth_headers(self, auth_token: str, current_url: str = None):
        headers = {**self.default_headers, "auth-token": auth_token}
        if current_url is not None:
            headers["current-url"] = current_url
        return headers

    def signin(self, username: str, password: str):
        url = "https://api.zindi.africa/v1/auth/signin"
        response = requests.post(
            url,
            data={"username": username, "password": password},
            headers=self.default_headers,
        )
        data = self._response_data(response)
        return self._raise_on_errors(data)

    def search_competitions(
        self,
        auth_token: str,
        query: str = None,
        kind: str = "competition",
        reward: str = None,
        active: bool = True,
        per_page: int = 20,
        page: int = 0,
    ):
        url = self.base_api
        kind_value = kind if kind in {"competition", "hackathon"} else "competition"
        reward_value = reward if reward in {"prize", "points", "knowledge"} else None
        params = {
            "active": str(active).lower(),
            "kind[]": kind_value,
            "page": page,
            "per_page": per_page,
            "query": query,
            "prize": reward_value,
        }
        params = {k: v for k, v in params.items() if v is not None}
        response = requests.get(
            url,
            headers=self._auth_headers(
                auth_token, current_url="https://zindi.africa/competitions"
            ),
            params=params,
        )
        data = self._response_data(response)
        return self._raise_on_errors(data)

    def get_competition(self, auth_token: str, challenge_id: str):
        url = f"{self.base_api}/{challenge_id}"
        response = requests.get(
            url,
            headers=self._auth_headers(
                auth_token, current_url="https://zindi.africa/competitions"
            ),
        )
        data = self._response_data(response)
        return self._raise_on_errors(data)

    def join_competition(
        self, auth_token: str, challenge_id: str, secret_code: str = None
    ):
        url = f"{self.base_api}/{challenge_id}/participations"
        params = {"secret_code": secret_code} if secret_code else None
        response = requests.post(
            url, headers=self._auth_headers(auth_token), params=params
        )
        data = self._response_data(response)
        if "errors" in data:
            message = data["errors"].get("message", str(data["errors"]))
            if message in {
                "already in",
                "Great news! You've already joined the competition",
            }:
                return {"joined": True, "message": message}
            raise Exception(f"\n[ 🔴 ] {message}\n")
        return {"joined": True, "message": data}

    def get_submission_limits(self, auth_token: str, challenge_id: str):
        url = f"{self.base_api}/{challenge_id}/submissions/limits"
        response = requests.get(
            url,
            headers=self._auth_headers(
                auth_token, current_url=f"{self.base_api}/{challenge_id}/submit"
            ),
        )
        data = self._response_data(response)
        return self._raise_on_errors(data)

    def get_my_participation(self, auth_token: str, challenge_id: str):
        url = f"{self.base_api}/{challenge_id}/participations/my_participation"
        response = requests.get(
            url,
            headers=self._auth_headers(
                auth_token,
                current_url=f"https://zindi.africa/competitions/{challenge_id}/leaderboard",
            ),
        )
        data = self._response_data(response)
        return self._raise_on_errors(data)

    def get_leaderboard(
        self, auth_token: str, challenge_id: str, per_page: int = 50, page: int = 0
    ):
        url = f"{self.base_api}/{challenge_id}/participations"
        response = requests.get(
            url,
            headers={**self.default_headers, "auth_token": auth_token},
            params={"page": page, "per_page": per_page},
        )
        data = self._response_data(response)
        return self._raise_on_errors(data)

    def get_submission_history(
        self, auth_token: str, challenge_id: str, per_page: int = 50
    ):
        url = f"{self.base_api}/{challenge_id}/submissions"
        response = requests.get(
            url,
            headers=self._auth_headers(auth_token),
            data={"auth-token": auth_token},
            params={"per_page": per_page},
        )
        data = self._response_data(response)
        return self._raise_on_errors(data)

    def submit_file(
        self, auth_token: str, challenge_id: str, filepath: str, comment: str
    ):
        url = f"{self.base_api}/{challenge_id}/submissions"
        response = upload(
            filepath=filepath,
            comment=comment,
            url=url,
            headers={**self.default_headers, "auth_token": auth_token},
        )
        data = self._response_data(response)
        return data

    def create_team(self, auth_token: str, challenge_id: str, team_name: str):
        url = f"{self.base_api}/{challenge_id}/my_team"
        response = requests.post(
            url,
            headers=self.default_headers,
            data={"title": team_name, "auth_token": auth_token},
        )
        data = self._response_data(response)
        return data

    def invite_to_team(self, auth_token: str, challenge_id: str, username: str):
        url = f"{self.base_api}/{challenge_id}/my_team/invite"
        response = requests.post(
            url, headers=self.default_headers, data={"username": username}
        )
        data = self._response_data(response)
        return data

    def disband_team(self, auth_token: str, challenge_id: str):
        url = f"{self.base_api}/{challenge_id}/my_team"
        response = requests.delete(
            url,
            headers=self.default_headers,
            data={"auth_token": auth_token},
        )
        data = self._response_data(response)
        return data
