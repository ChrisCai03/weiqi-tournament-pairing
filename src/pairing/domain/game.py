from __future__ import annotations

from dataclasses import asdict, dataclass, field
from uuid import uuid4

from pairing.domain.config import TournamentConfig
from pairing.domain.result import Result
from pairing.domain.validation import require_non_blank, require_positive


@dataclass(slots=True)
class Game:
    id: str
    round_number: int
    board_number: int
    black_player_id: str | None
    white_player_id: str | None
    handicap: int = 0
    komi: float = 0.0
    result: Result = field(default_factory=Result.pending)
    pairing_explanation: list[str] = field(default_factory=list)
    override_origin: str = "engine"

    @classmethod
    def create(
        cls,
        *,
        round_number: int,
        board_number: int,
        black_player_id: str | None,
        white_player_id: str | None,
        pairing_explanation: list[str],
        handicap: int = 0,
        komi: float = 0.0,
        override_origin: str = "engine",
    ) -> "Game":
        return cls(
            id=str(uuid4()),
            round_number=round_number,
            board_number=board_number,
            black_player_id=black_player_id,
            white_player_id=white_player_id,
            handicap=handicap,
            komi=komi,
            pairing_explanation=list(pairing_explanation),
            override_origin=override_origin,
        )

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["result"] = self.result.to_dict()
        return payload

    def validate(self) -> None:
        require_non_blank(self.id, "Game id")
        require_positive(self.round_number, "Game round number")
        require_positive(self.board_number, "Game board number")
        if self.handicap < 0:
            raise ValueError("Game handicap must not be negative.")
        self.result.validate()

    @classmethod
    def from_dict(
        cls,
        data: dict[str, object],
        *,
        config: TournamentConfig | None = None,
    ) -> "Game":
        result = Result.from_dict(dict(data["result"]))
        if config is not None:
            result = result.with_game_context(
                black_player_id=_optional_str(data.get("black_player_id")),
                white_player_id=_optional_str(data.get("white_player_id")),
                config=config,
            )
        game = cls(
            id=str(data["id"]),
            round_number=int(data["round_number"]),
            board_number=int(data["board_number"]),
            black_player_id=_optional_str(data.get("black_player_id")),
            white_player_id=_optional_str(data.get("white_player_id")),
            handicap=int(data.get("handicap", 0)),
            komi=float(data.get("komi", 0.0)),
            result=result,
            pairing_explanation=[str(item) for item in data.get("pairing_explanation", [])],
            override_origin=str(data.get("override_origin", "engine")),
        )
        game.validate()
        return game


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)
