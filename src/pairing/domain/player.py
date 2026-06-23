from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from uuid import uuid4


class RankParseError(ValueError):
    """Raised when a dan/kyu rank cannot be parsed."""


@dataclass(frozen=True, slots=True)
class Rank:
    label: str
    sort_value: int


def parse_rank(raw: str | None) -> Rank:
    if raw is None or raw.strip() == "":
        return Rank(label="unranked", sort_value=-999)

    value = raw.strip().lower()
    if value in {"unranked", "unknown", "nr"}:
        return Rank(label="unranked", sort_value=-999)

    dan_match = re.fullmatch(r"(\d+)\s*d(?:an)?", value)
    if dan_match:
        number = int(dan_match.group(1))
        if 1 <= number <= 9:
            return Rank(label=f"{number}d", sort_value=number)
        raise RankParseError(f"Invalid dan rank: {raw}")

    kyu_match = re.fullmatch(r"(\d+)\s*k(?:yu)?", value)
    if kyu_match:
        number = int(kyu_match.group(1))
        if 1 <= number <= 30:
            return Rank(label=f"{number}k", sort_value=-number)
        raise RankParseError(f"Invalid kyu rank: {raw}")

    raise RankParseError(f"Invalid rank: {raw}")


@dataclass(slots=True)
class Player:
    id: str
    display_name: str
    rank: str
    rank_sort_value: int
    country: str = ""
    club: str = ""
    school: str = ""
    team_id: str = ""
    status: str = "active"
    seed_number: int = 0
    notes: str = ""

    @classmethod
    def create(
        cls,
        display_name: str,
        *,
        rank: str | None = None,
        country: str = "",
        club: str = "",
        school: str = "",
        team_id: str = "",
        seed_number: int = 0,
        notes: str = "",
    ) -> "Player":
        parsed_rank = parse_rank(rank)
        return cls(
            id=str(uuid4()),
            display_name=display_name.strip(),
            rank=parsed_rank.label,
            rank_sort_value=parsed_rank.sort_value,
            country=country.strip(),
            club=club.strip(),
            school=school.strip(),
            team_id=team_id.strip(),
            seed_number=seed_number,
            notes=notes.strip(),
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Player":
        parsed_rank = parse_rank(str(data["rank"]))
        rank_sort_value = int(data["rank_sort_value"])
        if rank_sort_value != parsed_rank.sort_value:
            raise ValueError(
                f"Inconsistent rank data for player {data['id']}: "
                f"rank {parsed_rank.label!r} does not match rank_sort_value {rank_sort_value}"
            )

        return cls(
            id=str(data["id"]),
            display_name=str(data["display_name"]),
            rank=parsed_rank.label,
            rank_sort_value=rank_sort_value,
            country=str(data.get("country", "")),
            club=str(data.get("club", "")),
            school=str(data.get("school", "")),
            team_id=str(data.get("team_id", "")),
            status=str(data.get("status", "active")),
            seed_number=int(data.get("seed_number", 0)),
            notes=str(data.get("notes", "")),
        )
