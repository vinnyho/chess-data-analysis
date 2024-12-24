import pandas as pd
from enum import Enum
from typing import Dict, Optional


class OpeningDatabase:
    """
    An ECO databse for chess openigns loaded from a CSV file.
    """

    def __init__(self, csv_path: str):
        df = pd.read_csv(csv_path, usecols=["name", "uci"])
        self.openings_dict = dict(zip(df["uci"], df["name"]))

    def get_opening(self, game_moves: str) -> Optional[str]:
        """
        Get the opening name for a sequence of moves.
        Returns an opening if found, None otherwise
        """
        return self.openings_dict.get(game_moves, None)


class PhaseResult(Enum):
    """
    Enumeration of possible results for a game phase.
    """

    WIN = "WIN"
    DRAW = "DRAW"
    LOSS = "LOSS"


class MoveType(Enum):
    """
    Enumeration of move types and their evaluation scores.
    """

    BLUNDER = -3.0
    MISTAKE = -1.0
    INACCURACY = -0.5
    GREAT_MOVE = 1.0
    GOOD_MOVE = 0.5
    BOOK_MOVE = 0


class MoveQuality:
    """
    Class to track and evaluate the quality of moves in a chess game.
    """

    def __init__(self):
        """
        Initializes move quality tracking counters
        """
        self.move_counts = {
            "blunder": 0,
            "mistake": 0,
            "inaccuracy": 0,
            "great_move": 0,
            "good_move": 0,
            "book_move": 0,
        }
        self.result = None

    def evaluate(self, prev_val: float, cur_val: float) -> None:
        """
        Evaluates the quality of a move based on position evaluation difference.
        """
        eval_diff = prev_val - cur_val

        if eval_diff <= MoveType.BLUNDER.value:
            self.move_counts["blunder"] += 1

        elif eval_diff <= MoveType.MISTAKE.value:
            self.move_counts["mistake"] += 1

        elif eval_diff <= MoveType.INACCURACY.value:
            self.move_counts["inaccuracy"] += 1

        elif eval_diff >= MoveType.GREAT_MOVE.value:
            self.move_counts["great_move"] += 1

        elif eval_diff >= MoveType.GOOD_MOVE.value:
            self.move_counts["good_move"] += 1
        else:
            self.move_counts["book_move"] += 1

    def handle_result(self, result: PhaseResult) -> str:
        """
        Set and returns the phase result
        """
        self.result = result.value
        return self.result

    def get_move_quality_counter(self) -> Dict[str, int]:
        """
        Get the coutns of different move qualities
        Returns a Dict[str, int] containing the conuts of each move quality type
        """
        return self.move_counts


class GameResult(Enum):
    """
    Enumeration of possible game results.
    """

    WIN = "WIN"
    DRAW = "DRAW"
    LOSS = "LOSS"


class AggressionMoveType(Enum):
    """
    Enumeration of aggressive move types with their scores.
    """

    CAPTURE = 1.0
    RECAPTURE = 0.2
    SACRIFICE = 3.0
    CHECK = 1.5
    CENTER = 1.5

    PROMOTION = 3.0
    CENTER_ATTACK = 0.3


class MoveAggression:
    """
    Tracks and evaluates the aggressiveness of moves in a chess game.
    """

    def __init__(self):
        self.total_score = 0
        self.move_counts = {
            "capture": 0,
            "recapture": 0,
            "sacrifice": 0,
            "check": 0,
            "center": 0,
            "promotion": 0,
            "center_attack": 0,
        }

    def handle_check(self) -> None:
        """
        Handle a checking move.
        """

        self.move_counts["check"] += 1
        self.total_score += AggressionMoveType.CHECK.value

    def handle_recapture(self, piece_value) -> None:
        """
        Handle a recapture move.
        """

        self.move_counts["recapture"] += 1
        self.total_score += (
            AggressionMoveType.CAPTURE.value * (piece_value / 2)
            - AggressionMoveType.RECAPTURE.value
        )

    def handle_promotion(self) -> None:
        """
        Handle a pawn promotion move.
        """

        self.move_counts["promotion"] += 1
        self.total_score += AggressionMoveType.PROMOTION.value

    def handle_capture(self, piece_value) -> None:
        """
        Handle a capture move.
        """
        self.move_counts["capture"] += 1
        self.total_score += AggressionMoveType.CAPTURE.value * (piece_value / 2)

    def handle_center_control(self) -> None:
        """
        Handle center control move
        """

        self.move_counts["center"] += 1
        self.total_score += AggressionMoveType.CENTER.value

    def handle_center_attack(self) -> None:
        """
        Handle center attack move
        """

        self.move_counts["center_attack"] += 1
        self.total_score += AggressionMoveType.CENTER_ATTACK.value

    def handle_sacrifice(self, piece_value) -> None:
        """
        Handle sacrifice move
        """

        self.move_counts["sacrifice"] += 1
        self.total_score += AggressionMoveType.SACRIFICE.value * (piece_value / 2)

    def get_total(self) -> float:
        """
        Gets the total aggression score
        Returns a flaot
        """
        return self.total_score

    def get_move_counts(self) -> Dict[str, int]:
        """
        Gets the counts of different aggressive move types.
        """
        return self.move_counts


class ChessAnalysisError(Exception):
    """
    Base exception class for chess analysis errors.
    """

    pass


class EngineError(ChessAnalysisError):
    """
    Raised when there are issues with the chess engine.
    """

    pass


class GameParsingError(ChessAnalysisError):
    """
    Raised when there are issues parsing chess games.
    """

    pass


class InvalidMoveError(ChessAnalysisError):
    """
    Raised when there are issues with chess moves.
    """

    pass
