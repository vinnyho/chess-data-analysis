from typing import Dict, Any, Tuple, List
import chess.engine
import chess.engine
import chess.pgn
from pathlib import Path
import asyncio
from collections import namedtuple
from .chess_game_helpers import *
from io import StringIO
import json
import sys


Elo = namedtuple("Elo", ["user_elo", "opponent_elo"])

class ChessGame:
    """
    A class to analyze and evaluate chess games.
    Processes chess games, analyzing moves for quality, aggression, opening theory, and position evaluations using the Stockfish engine.
    """

    center_squares = {chess.E4, chess.E5, chess.D4, chess.D5}
    piece_values = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9,
        chess.KING: 0,
    }

    def __init__(
        self,
        chess_game: chess.pgn.Game,
        opening_db: dict,
        user: str,
        stockfish_engine: chess.engine.SimpleEngine
    ) -> None:
        try:
            self.game = chess_game
            self.color, self.opponent_color = self._get_color(user)
            self.board = self.game.board()
            (
                self.move_quality_total,
                self.move_quality_opening,
                self.move_quality_middlegame,
                self.move_quality_endgame,
            ) = (MoveQuality(), MoveQuality(), MoveQuality(), MoveQuality())
            self.opening_database = opening_db
            self.opening = None
            self.theory_deviation = None
            self.result = self._get_winner()
            self.game_elo = self._get_elo()
            self.position_evaluations = []
            self.game_aggression = MoveAggression()
            self.phase = "opening"
            self.engine = stockfish_engine

            self.analyze_moves(self.engine)
        except KeyError as e:
            raise ChessAnalysisError(f"Missing required game header: {str(e)}")
        except Exception as e:
            raise ChessAnalysisError(f"Error initializing chess game: {str(e)}")

    def analyze_moves(self, engine: chess.engine.SimpleEngine) -> str:
        """
        Main loop to analyze all moves in the game.
        Processes each move to evaluate position, track aggression, identify openings, and assess move quality.
        """
        try:

            self.prev_score = 0
            current_moves = ""

            for move_number, move in enumerate(self.game.mainline_moves()):
                self._analyze_aggression(move, engine)
                self._progress_board(move)

                evaluation = self._run_evaluation(engine)
                current_moves += str(move.uci()) + " "

                self._get_opening(current_moves.strip(), move_number)

            self._check_final_evaluation(evaluation, self.phase)

            return self._get_game_phase()
        except chess.engine.EngineTerminatedError:
            raise EngineError("Chess engine terminated")

    def _run_evaluation(self, engine: chess.engine.SimpleEngine) -> None:
        """Evaluate position and analyze move quality only on player's turn"""
        evaluation = self._analyze_evaluation(engine)
        if (self.board.turn == chess.WHITE and self.color == "White") or (
            self.board.turn == chess.BLACK and self.color == "Black"
        ):

            self.position_evaluations.append(self._get_position_eval(evaluation))
            self.prev_score = self._analyze_move_quality(
                self.prev_score, evaluation, self._check_phase_change(evaluation)
            )
        else:
            # When it checks opponent evaluation score it is the opposite of user evaluation
            self.prev_score = -self._get_position_eval(evaluation)

        return evaluation

    def _check_final_evaluation(self, evaluation: Dict[str, Any], phase: str) -> None:
        """
        Check and set the final evaluation for the final game phase.
        """
        if evaluation is None:
            return

        cur_move_quality = getattr(self, f"move_quality_{phase}")
        if not cur_move_quality.result:

            cur_move_quality.result = self._get_phase_winner(evaluation)

    def _check_phase_change(self, evaluation: Dict[str, Any]) -> str:
        """
        Checks and set the current phase of the game.
        Returns the current_phase.
        """
        cur_phase = self._get_game_phase()
        if cur_phase != self.phase:
            self._get_phase_winner(evaluation)
            self.phase = cur_phase
        return cur_phase

    def _get_phase_winner(self, evaluation: Dict[str, Any]) -> PhaseResult:
        """
        Evaluates the winner of the current phase.
        Returns the a PhaseResult object value depending on Win/Loss/Draw.
        """

        score = evaluation["score"].relative.score()

        cur_phase = getattr(self, f"move_quality_{self.phase}")

        if score is None:

            result = self._handle_special_eval_conditions(score)
            cur_phase.handle_result(result)
            return result.value

        if abs(score) < 10:
            result = PhaseResult.DRAW
        elif (self.color == "White" and score > 0) or (
            self.color == "Black" and score < 0
        ):
            result = PhaseResult.WIN
        else:
            result = PhaseResult.LOSS

        cur_phase.handle_result(result)
        return result.value

    def _handle_special_eval_conditions(self, score: float) -> PhaseResult:
        """
        Checks for special evaluation conditions such as mate, stalemate, or insufficient material.
        Returns PhaseResult object depending on the user.

        """
        if score is None:

            if self.board.is_checkmate():

                if self.board.turn == chess.WHITE:

                    return (
                        PhaseResult.LOSS if self.color == "White" else PhaseResult.WIN
                    )
                else:

                    return (
                        PhaseResult.WIN if self.color == "White" else PhaseResult.LOSS
                    )

            if self.board.is_stalemate() or self.board.is_insufficient_material():

                return PhaseResult.DRAW

            return None

    def _analyze_aggression(
        self, move: chess.Move, engine: chess.engine.SimpleEngine
    ) -> None:
        """
        Analyzes the aggression of a move.
        """
        prev_move = (
            self.board.move_stack[-1] if len(self.board.move_stack) > 0 else None
        )

        if self.board.turn == (self.color == "White"):

            self._check_king_check(move)
            self._check_capture(prev_move, move)
            self._check_promotion(move)
            self._check_center_control(move)
            self._check_center_attacked()
            self._check_sacrifice(move, engine)

    def _check_center_control(self, move: chess.Move) -> None:
        """
        Checks if a move controls the center.
        """
        self.board.piece_at(move.to_square)

        if move.to_square in self.center_squares:

            self.game_aggression.handle_center_control()

    def _check_center_attacked(self) -> None:
        """
        Checks if a move attacks the center.
        """
        for square in self.center_squares:
            if self.board.is_attacked_by(self.color == "White", square):

                self.game_aggression.handle_center_attack()

    def _check_promotion(self, move: chess.Move) -> None:
        """
        Checks if a move promotes a pawn.
        """
        if move.promotion:

            self.game_aggression.handle_promotion()

    def _check_sacrifice(
        self, move: chess.Move, engine: chess.engine.SimpleEngine
    ) -> None:
        """
        Checks if a move is a sacrifice.
        """
        evaluation = self._analyze_evaluation(engine)

        if not evaluation or not evaluation["score"].relative.score():
            return

        prev_eval = evaluation["score"].relative.score() / 100
        min_attacker_value = float("inf")
        cur_piece = self.board.piece_at(move.from_square)
        self.board.push(move)

        if self.board.is_attacked_by(self.color != "White", move.to_square):
            for attacker in self.board.attackers(self.color != "White", move.to_square):
                attacker_piece = self.board.piece_at(attacker)
                if attacker_piece:
                    min_attacker_value = min(
                        self.piece_values[attacker_piece.piece_type], min_attacker_value
                    )

        if min_attacker_value < self.piece_values[cur_piece.piece_type]:

            evaluation = self._analyze_evaluation(self.engine)
            cur_eval = evaluation["score"].relative.score() / 100

            if cur_eval - prev_eval > 0.1:
                self.game_aggression.handle_sacrifice(
                    self.piece_values[cur_piece.piece_type]
                )

        self.board.pop()

    def _check_capture(self, prev_move: chess.Move, move: chess.Move) -> None:
        """
        Checks if a move is a capture or recapture.
        """
        if not prev_move:
            return

        is_current_capture = self.board.is_capture(move)

        self.board.pop()
        was_prev_capture = self.board.is_capture(prev_move)
        self.board.push(prev_move)
        piece_value = self.piece_values.get(self.board.piece_at(move.to_square), 1)

        if (
            is_current_capture
            and was_prev_capture
            and move.to_square == prev_move.to_square
        ):
            self.game_aggression.handle_recapture(piece_value)

        elif is_current_capture:

            self.game_aggression.handle_capture(piece_value)

    def _check_king_check(self, move: chess.Move) -> None:
        """
        Checks if a move gives a check.
        """
        if self.board.gives_check(move):

            self.game_aggression.handle_check()

    def _to_dict(self) -> dict:
        """
        Converts game analysis to dictionary format.
        """
        data = {
            "color": self.color,
            "opponent_color": self.opponent_color,
            "result": self.result.value,
            "game_elo": {
                "user_elo": self.game_elo.user_elo,
                "opponent_elo": self.game_elo.opponent_elo,
            },
            "opening": self.opening,
            "theory_deviation": self.theory_deviation,
            "game_evaluation_progress": self.position_evaluations,
            "aggressiveness_eval_total": self.game_aggression.get_total(),
            "aggresiveness_eval_counter": self.game_aggression.get_move_counts(),
            "move_quality_total": {
                "phase_winner": "TOTAL",
                "total_move_quality_counter": self.move_quality_total.get_move_quality_counter(),
            },
            "move_quality_opening": {
                "phase_winner": self.move_quality_opening.result,
                "opening_move_quality_counter": self.move_quality_opening.get_move_quality_counter(),
            },
            "move_quality_middlegame": {
                "phase_winner": self.move_quality_middlegame.result,
                "middlegame_move_quality_counter": self.move_quality_middlegame.get_move_quality_counter(),
            },
            "move_quality_endgame": {
                "phase_winner": self.move_quality_endgame.result,
                "endgame_move_quality_counter": self.move_quality_endgame.get_move_quality_counter(),
            },
        }

        return data

    def _to_json(self, dict: dict) -> str:
        """
        Converts dictionary to JSON string.
        """
        return json.dumps(dict, indent=4)

    def _get_opening(self, current_moves: str, move_number: int) -> None:
        """
        Checks current move sequence against opening database.
        """
        opening = self.opening_database.get_opening(current_moves.strip())
        if opening is not None:
            self.opening = opening
        elif self.theory_deviation is None:
            self.theory_deviation = move_number + 1

    def _progress_board(self, move: chess.Move) -> None:
        """
        Update board state with given move.
        """
        self.board.san(move)
        self.board.push(move)

    def _analyze_evaluation(self, engine: chess.engine.SimpleEngine) -> Dict[str, Any]:
        """
        Analyzes the evaluation of current board
        Returns dictionary of the evaluation scores
        """
        evaluation = engine.analyse(
            self.board, chess.engine.Limit(time=0.2, depth=15, nodes=20000)
        )

        return evaluation

    def _analyze_move_quality(
        self, prev_score: float, evaluation: Dict[str, Any], game_phase: str
    ) -> float:
        """
        Analyzes the quality of a move based on position evaluation change.
        Returns current position score.
        """
        current_score = (
            evaluation["score"].relative.score() / 100
            if evaluation["score"].relative.score() is not None
            else self._get_position_eval(evaluation)
        )

        self.move_quality_total.evaluate(prev_score, current_score)
        move_quality_evaluator = getattr(self, f"move_quality_{game_phase}")
        move_quality_evaluator.evaluate(prev_score, current_score)

        return current_score

    def _get_position_eval(self, position_eval: Dict[str, Any]) -> float:
        """
        Converts engine evaluation to normalized score.
        Returns normalized position score or mate score.
        """
        position_eval = position_eval["score"].relative
        if position_eval.score() is not None:
            return position_eval.score() / 100
        elif position_eval.is_mate():
            mate_moves = position_eval.mate()
            return (
                15 - (mate_moves * 0.5) if mate_moves > 0 else -15 - (mate_moves * 0.5)
            )
        else:

            return 0

    def _get_game_phase(self) -> str:
        """
        Determine the current game phase based on number of pieces.
        Returns game phase, opening, middlegame, or endgame.
        """
        total_pieces = sum(
            len(self.board.pieces(piece_type, color))
            for color in [chess.WHITE, chess.BLACK]
            for piece_type in [
                chess.PAWN,
                chess.KNIGHT,
                chess.BISHOP,
                chess.ROOK,
                chess.QUEEN,
            ]
        )

        if total_pieces >= 28:
            return "opening"
        elif total_pieces >= 15:
            return "middlegame"
        else:
            return "endgame"

    def _get_color(self, user: str) -> Tuple[str, str]:
        """
        Determins the player colors based on username.
        Returns a Tuple of (player_color, opponent_color)
        """
        if self.game.headers["White"] == user:
            return "White", "Black"
        else:
            return "Black", "White"

    def _get_winner(self) -> GameResult:
        """
        Determine game result from player's perspective.
        Returns a GameResult enum value (WIN/LOSS/DRAW).
        """
        result = self.game.headers["Result"]
        if result == "0-1" and self.color == "Black":
            return GameResult.WIN
        elif result == "1-0" and self.color == "White":
            return GameResult.WIN
        elif result == "1/2-1/2":
            return GameResult.DRAW
        else:
            return GameResult.LOSS

    def _get_elo(self) -> Elo:
        """
        Gets the Elo ratings from game headers.
        Returns a namedtuple containing user and oponent ratings.
        """
        return Elo(
            self.game.headers[f"{self.color}Elo"],
            self.game.headers[f"{self.opponent_color}Elo"],
        )


class ChessGamesCollection:
    """
    A collection of ChessGame objects that can be analyzed using Stockfish engine
    """

    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        STOCKFISH_FILENAME = "stockfish-windows-x86-64-avx2.exe"
    else:
        # For Linux/Ubuntu
        STOCKFISH_FILENAME = "stockfish-ubuntu-x86-64-avx2"

    BASE_DIR = Path(__file__).resolve().parents[1]
    ECO_PATH = BASE_DIR / "resources" / "openings.csv"
    STOCKFISH_PATH = BASE_DIR / "resources" / STOCKFISH_FILENAME
    
    def __init__(self, games_pgn: StringIO, user: str):
        """
        Initializes a new chess games collection
        """
        self.opening_db = OpeningDatabase(self.ECO_PATH)
        self.user = user
        self.engine = chess.engine.SimpleEngine.popen_uci(self.STOCKFISH_PATH)

        try:
            if isinstance(games_pgn, str):
                with open(games_pgn, "r") as file:
                    self.chess_games = self.add_games_from_pgn(file)
            else:
                self.chess_games = self.add_games_from_pgn(games_pgn)
        except IOError as e:
            raise ChessAnalysisError(f"Error reading PGN file: {str(e)}")

    
    def add_games_from_pgn(self, games_pgn: StringIO) -> List[ChessGame]:
        """
        Parse PGN data and create ChessGame objects for each game
        Returns a list of ChessGame objects
        """

        chess_games = []
        while True:
            game = chess.pgn.read_game(games_pgn)
            if game is None:
                break

            chess_games.append(ChessGame(game, self.opening_db, self.user, self.engine))
        return chess_games
