from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from pairing.domain.config import TournamentConfig
from pairing.domain.validation import (
    RESULT_OUTCOME_CODES,
    RESULT_STATUSES,
    RESULT_TYPES,
    require_choice,
    require_finite_number,
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class Result:
    status: str
    result_type: str
    winner_player_id: str | None = None
    black_score: float | None = None
    white_score: float | None = None
    outcome_code: str | None = None
    entered_at: str | None = None
    entered_by: str = "cli"
    notes: str = ""
    correction_of: str | None = None

    @classmethod
    def pending(cls) -> "Result":
        return cls(status="pending", result_type="pending")

    @classmethod
    def completed(
        cls,
        *,
        result_type: str,
        winner_player_id: str | None,
        black_player_id: str | None = None,
        white_player_id: str | None = None,
        config: TournamentConfig | None = None,
        entered_by: str = "cli",
        notes: str = "",
        correction_of: str | None = None,
    ) -> "Result":
        result = cls(
            status="completed",
            result_type=result_type,
            winner_player_id=winner_player_id,
            entered_at=_utc_now_iso(),
            entered_by=entered_by,
            notes=notes,
            correction_of=correction_of,
        )
        if config is None:
            return result
        return result.with_game_context(
            black_player_id=black_player_id,
            white_player_id=white_player_id,
            config=config,
        )

    @classmethod
    def completed_outcome(
        cls,
        *,
        outcome_code: str,
        black_player_id: str | None,
        white_player_id: str | None,
        config: TournamentConfig,
        entered_by: str = "cli",
        notes: str = "",
        correction_of: str | None = None,
    ) -> "Result":
        result_type, winner_player_id, black_score, white_score = _outcome_details(
            outcome_code=outcome_code,
            black_player_id=black_player_id,
            white_player_id=white_player_id,
            config=config,
        )
        return cls(
            status="completed",
            result_type=result_type,
            winner_player_id=winner_player_id,
            black_score=black_score,
            white_score=white_score,
            outcome_code=outcome_code,
            entered_at=_utc_now_iso(),
            entered_by=entered_by,
            notes=notes,
            correction_of=correction_of,
        )

    def with_game_context(
        self,
        *,
        black_player_id: str | None,
        white_player_id: str | None,
        config: TournamentConfig,
    ) -> "Result":
        if self.status != "completed" or self.result_type == "pending" or self.outcome_code is not None:
            return self
        outcome_code = _infer_outcome_code(
            result=self,
            black_player_id=black_player_id,
            white_player_id=white_player_id,
        )
        result_type, winner_player_id, black_score, white_score = _outcome_details(
            outcome_code=outcome_code,
            black_player_id=black_player_id,
            white_player_id=white_player_id,
            config=config,
        )
        return Result(
            status="completed",
            result_type=result_type,
            winner_player_id=winner_player_id,
            black_score=black_score,
            white_score=white_score,
            outcome_code=outcome_code,
            entered_at=self.entered_at or _utc_now_iso(),
            entered_by=self.entered_by,
            notes=self.notes,
            correction_of=self.correction_of,
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    def validate(self) -> None:
        require_choice(self.status, RESULT_STATUSES, "result status")
        require_choice(self.result_type, RESULT_TYPES, "result type")
        if self.status == "pending" and self.result_type != "pending":
            raise ValueError("Pending result status requires pending result type.")
        if self.status == "completed" and self.result_type == "pending":
            raise ValueError("Completed result status cannot use pending result type.")
        if self.outcome_code is not None:
            require_choice(self.outcome_code, RESULT_OUTCOME_CODES, "result outcome")
        if self.black_score is not None:
            require_finite_number(self.black_score, "Black score")
        if self.white_score is not None:
            require_finite_number(self.white_score, "White score")
        if (self.black_score is None) != (self.white_score is None):
            raise ValueError("Completed results must define both scores or neither score.")

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Result":
        result = cls(
            status=str(data["status"]),
            result_type=str(data["result_type"]),
            winner_player_id=_optional_str(data.get("winner_player_id")),
            black_score=_optional_float(data.get("black_score")),
            white_score=_optional_float(data.get("white_score")),
            outcome_code=_optional_str(data.get("outcome_code")),
            entered_at=_optional_str(data.get("entered_at")),
            entered_by=str(data.get("entered_by", "cli")),
            notes=str(data.get("notes", "")),
            correction_of=_optional_str(data.get("correction_of")),
        )
        result.validate()
        return result


def _infer_outcome_code(
    *,
    result: Result,
    black_player_id: str | None,
    white_player_id: str | None,
) -> str:
    if result.result_type == "normal":
        if result.winner_player_id == black_player_id and black_player_id is not None:
            return "black_win"
        if result.winner_player_id == white_player_id and white_player_id is not None:
            return "white_win"
        raise ValueError("Cannot infer normal outcome without matching game players.")
    if result.result_type == "bye":
        return "bye"
    if result.result_type == "draw":
        return "draw"
    if result.result_type == "both_win":
        return "both_win"
    if result.result_type == "both_loss":
        return "both_loss"
    if result.result_type == "forfeit":
        if result.winner_player_id == black_player_id and black_player_id is not None:
            return "black_forfeit"
        if result.winner_player_id == white_player_id and white_player_id is not None:
            return "white_forfeit"
        raise ValueError("Cannot infer forfeit outcome without matching game players.")
    if result.result_type == "no_show":
        if result.winner_player_id is None:
            return "both_no_show"
        if result.winner_player_id == black_player_id and black_player_id is not None:
            return "white_no_show"
        if result.winner_player_id == white_player_id and white_player_id is not None:
            return "black_no_show"
        raise ValueError("Cannot infer no-show outcome without matching game players.")
    if result.result_type == "void":
        return "void"
    raise ValueError(f"Cannot infer outcome code for result type {result.result_type!r}.")


def _outcome_details(
    *,
    outcome_code: str,
    black_player_id: str | None,
    white_player_id: str | None,
    config: TournamentConfig,
) -> tuple[str, str | None, float, float]:
    require_choice(outcome_code, RESULT_OUTCOME_CODES, "result outcome")
    if outcome_code == "draw":
        if not config.allow_draws:
            raise ValueError("Draw outcomes require allow_draws=True.")
        return ("draw", None, config.score_draw, config.score_draw)
    if outcome_code == "black_win":
        return ("normal", black_player_id, config.score_win, config.score_loss)
    if outcome_code == "white_win":
        return ("normal", white_player_id, config.score_loss, config.score_win)
    if outcome_code == "both_win":
        return ("both_win", None, config.score_both_win, config.score_both_win)
    if outcome_code == "both_loss":
        return ("both_loss", None, config.score_both_loss, config.score_both_loss)
    if outcome_code == "black_forfeit":
        return ("forfeit", black_player_id, config.score_forfeit_win, config.score_forfeit_loss)
    if outcome_code == "white_forfeit":
        return ("forfeit", white_player_id, config.score_forfeit_loss, config.score_forfeit_win)
    if outcome_code == "black_no_show":
        return ("no_show", white_player_id, config.score_no_show, config.score_forfeit_win)
    if outcome_code == "white_no_show":
        return ("no_show", black_player_id, config.score_forfeit_win, config.score_no_show)
    if outcome_code == "both_no_show":
        return ("no_show", None, config.score_no_show, config.score_no_show)
    if outcome_code == "void":
        return ("void", None, 0.0, 0.0)
    if black_player_id is not None and white_player_id is not None:
        raise ValueError("Bye outcomes require exactly one real player.")
    if black_player_id is None and white_player_id is None:
        raise ValueError("Bye outcomes require exactly one real player.")
    return (
        "bye",
        black_player_id or white_player_id,
        config.score_bye if black_player_id is not None else 0.0,
        config.score_bye if white_player_id is not None else 0.0,
    )


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    return float(value)
