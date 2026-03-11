from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


def _pick(raw: Dict[str, Any], *keys, default=None):
    for key in keys:
        if key in raw and raw[key] is not None:
            return raw[key]
    return default


def _to_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]


class ChallengeSummary(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str
    subtitle: str = ""
    kind: Optional[str] = None
    reward: Optional[str] = None
    type_of_problem: List[str] = Field(default_factory=list)
    data_type: List[str] = Field(default_factory=list)
    secret_code_required: bool = False
    sealed: bool = False
    extras: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_raw(cls, raw: Dict[str, Any]):
        known = {
            "id",
            "slug",
            "subtitle",
            "title",
            "name",
            "kind",
            "type",
            "reward",
            "prize",
            "type_of_problem",
            "problem_type",
            "problem_types",
            "data_type",
            "data_types",
            "dataset_type",
            "secret_code_required",
            "private",
            "sealed",
        }
        challenge_id = _pick(raw, "id", "slug", default="")
        return cls(
            id=str(challenge_id),
            subtitle=str(_pick(raw, "subtitle", "title", "name", default="")),
            kind=_pick(raw, "kind", "type"),
            reward=_pick(raw, "reward", "prize"),
            type_of_problem=_to_list(
                _pick(raw, "type_of_problem", "problem_type", "problem_types")
            ),
            data_type=_to_list(_pick(raw, "data_type", "data_types", "dataset_type")),
            secret_code_required=bool(
                _pick(raw, "secret_code_required", "private", default=False)
            ),
            sealed=bool(_pick(raw, "sealed", default=False)),
            extras={k: v for k, v in raw.items() if k not in known},
        )


class LeaderboardEntry(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    rank: Optional[int]
    score: Optional[float]
    username: Optional[str]
    team_title: Optional[str]
    submission_count: int = 0
    last_submission_at: Optional[str] = None
    extras: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_raw(cls, raw: Dict[str, Any]):
        known = {
            "public_rank",
            "private_rank",
            "best_public_score",
            "best_private_score",
            "user",
            "team",
            "submission_count",
            "best_public_submitted_at",
            "best_private_submitted_at",
        }
        user = raw.get("user") or {}
        team = raw.get("team") or {}
        return cls(
            rank=_pick(raw, "private_rank", "public_rank"),
            score=_pick(raw, "best_private_score", "best_public_score"),
            username=user.get("username"),
            team_title=team.get("title"),
            submission_count=int(raw.get("submission_count") or 0),
            last_submission_at=_pick(
                raw, "best_private_submitted_at", "best_public_submitted_at"
            ),
            extras={k: v for k, v in raw.items() if k not in known},
        )


class SubmissionEntry(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str
    status: str
    filename: str
    created_at: Optional[str] = None
    public_score: Optional[float] = None
    private_score: Optional[float] = None
    comment: Optional[str] = None
    status_description: Optional[str] = None
    extras: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_raw(cls, raw: Dict[str, Any]):
        known = {
            "id",
            "status",
            "filename",
            "created_at",
            "public_score",
            "private_score",
            "comment",
            "status_description",
        }
        return cls(
            id=str(raw.get("id", "")),
            status=str(raw.get("status", "")),
            filename=str(raw.get("filename", "")),
            created_at=raw.get("created_at"),
            public_score=raw.get("public_score"),
            private_score=raw.get("private_score"),
            comment=raw.get("comment"),
            status_description=raw.get("status_description"),
            extras={k: v for k, v in raw.items() if k not in known},
        )


class JoinResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    joined: bool
    message: Any = None


class ChallengeSelectionResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    challenge: Optional[ChallengeSummary]
    joined: JoinResult
    message: Optional[str] = None

    @classmethod
    def from_raw(cls, raw: Dict[str, Any]):
        joined_raw = raw.get("joined", {}) or {}
        if isinstance(joined_raw, bool):
            joined = JoinResult(joined=joined_raw)
        else:
            joined = JoinResult(
                joined=bool(joined_raw.get("joined", False)),
                message=joined_raw.get("message"),
            )
        return cls(
            challenge=(
                ChallengeSummary.from_raw(raw.get("challenge", {}))
                if raw.get("challenge")
                else None
            ),
            joined=joined,
            message=raw.get("message"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    def __repr__(self) -> str:
        challenge_id = None if not self.challenge else self.challenge.id
        return (
            f"ChallengeSelectionResult(challenge_id={challenge_id!r}, "
            f"joined={self.joined.joined}, message={self.message!r})"
        )


class LeaderboardResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    rank: int
    leaderboard: List[LeaderboardEntry]

    @property
    def total_rows(self) -> int:
        return len(self.leaderboard)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    def __repr__(self) -> str:
        return f"LeaderboardResult(rank={self.rank}, total_rows={self.total_rows})"


class SubmissionBoardResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    submissions: List[SubmissionEntry]

    @property
    def total_rows(self) -> int:
        return len(self.submissions)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    def __repr__(self) -> str:
        return f"SubmissionBoardResult(total_rows={self.total_rows})"
