import pandas as pd
import plotly.express as px
from typing import List, Dict, Tuple, Optional
from plotly.graph_objects import Figure
from .chess_game_class import ChessGame


class ChessDataFrame:
    """
    Class that converts chess game data into pandas DataFrames
    """

    def __init__(self, chess_games_collection: list[ChessGame]):
        """
        Initializes chess data frames from a collection of chess games
        """
        self.games = chess_games_collection

        self.basic_info_df, self.move_evaluation_df, self.aggressive_eval_df = (
            self._create_all_df()
        )

    def get_df(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Returns all three DataFrames with chess game analysis.
        """
        return self.basic_info_df, self.move_evaluation_df, self.aggressive_eval_df

    def _create_all_df(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Creates all three DataFrames from chess games collection.
        Returns a tuple of the three DataFrames
        """

        total_basic_data = []
        total_move_eval_data = []
        total_aggressive_eval_data = []

        game_id = 0
        for chess_game in self.games:
            chess_game_dict = chess_game._to_dict()
            total_basic_data.append(
                self._create_basic_info_df(chess_game_dict, game_id)
            )

            total_move_eval_data.extend(
                self._create_move_evaluations_df(chess_game_dict, game_id)
            )

            total_aggressive_eval_data.append(
                self._create_aggressive_eval_df(chess_game_dict, game_id)
            )

            game_id += 1

        return (
            pd.DataFrame(total_basic_data),
            pd.DataFrame(total_move_eval_data),
            pd.DataFrame(total_aggressive_eval_data),
        )

    def _create_basic_info_df(self, chess_game_dict, game_id) -> Dict:
        """
        Creates a dictionary with basic game information
        Returns a Dict of the basic game information for the chess game
        """
        game_basic_data = {
            "game_id": game_id,
            "color": chess_game_dict["color"],
            "opponent_color": chess_game_dict["opponent_color"],
            "result": chess_game_dict["result"],
            "opening": chess_game_dict["opening"],
            "user_elo": int(chess_game_dict["game_elo"]["user_elo"]),
            "opponent_elo": int(chess_game_dict["game_elo"]["opponent_elo"]),
            "game_evaluation_progression": chess_game_dict["game_evaluation_progress"],
            "aggressiveness_eval_total": chess_game_dict["aggressiveness_eval_total"],
            "theory_deviation": int(chess_game_dict["theory_deviation"]),
        }

        return game_basic_data

    def _create_move_evaluations_df(self, chess_game_dict, game_id) -> Dict:
        """
        Creates a dictionary with move evaluations
        Returns a Dict of the move evaluations for the chess game
        """
        cur_game_moves_eval = []
        for phase in ["total", "opening", "middlegame", "endgame"]:
            phase_data = chess_game_dict[f"move_quality_{phase}"]
            phase_move_quality_data = chess_game_dict[f"move_quality_{phase}"][
                f"{phase}_move_quality_counter"
            ]

            if phase_data["phase_winner"] == None:
                continue

            game_phase_eval_data = {
                "game_id": game_id,
                "phase": phase,
                "phase_winner": phase_data["phase_winner"],
                "blunder": phase_move_quality_data["blunder"],
                "mistake": phase_move_quality_data["mistake"],
                "inaccuracy": phase_move_quality_data["inaccuracy"],
                "great_move": phase_move_quality_data["great_move"],
                "good_move": phase_move_quality_data["good_move"],
                "book_move": phase_move_quality_data["book_move"],
            }
            cur_game_moves_eval.append(game_phase_eval_data)

        return cur_game_moves_eval

    def _create_aggressive_eval_df(self, chess_game_dict, game_id):
        """
        Creates a dictionary with aggression evaluation data
        Returns a Dict of the aggression evaluation for the chess game
        """
        game_aggressive_moves = chess_game_dict["aggresiveness_eval_counter"]
        game_aggressive_moves_data = {
            "game_id": game_id,
            "aggressiveness_eval_total": chess_game_dict["aggressiveness_eval_total"],
            "capture": game_aggressive_moves["capture"],
            "recapture": game_aggressive_moves["recapture"],
            "sacrifice": game_aggressive_moves["sacrifice"],
            "check": game_aggressive_moves["check"],
            "center": game_aggressive_moves["center"],
            "promotion": game_aggressive_moves["promotion"],
            "center_attack": game_aggressive_moves["center_attack"],
        }

        return game_aggressive_moves_data


class ChessDataVisualizer:
    """
    Class for creating visualizations of chess game data.
    """

    MOVE_TYPE_LABELS = {
        "blunder": "Blunder",
        "mistake": "Mistake",
        "inaccuracy": "Inaccuracy",
        "great_move": "Great Move",
        "good_move": "Good Move",
        "book_move": "Book Move",
    }

    AGGRESSIVE_MOVE_LABELS = {
        "capture": "Capture",
        "recapture": "Recapture",
        "sacrifice": "Sacrifice",
        "check": "Check",
        "center": "Center Control",
        "promotion": "Promotion",
        "center_attack": "Center Attack",
    }

    USER_RATING_LABELS = {"user_elo": "User Elo", "opponent_elo": "Opponent Elo"}

    RESULT_CATEGORIES = ["WIN", "LOSS", "DRAW"]

    RESULT_COLORS = {
        "WIN": "#2E86C1",
        "LOSS": "#E74C3C",
        "DRAW": "#95A5A6",
    }

    AXIS_LABELS = {
        "game_id": "Game ID",
        "move_type": "Move Type",
        "count": "Number of Moves",
        "result": "Game Result",
        "opening": "Opening",
        "aggressiveness_eval_total": "Aggression Score",
    }

    def __init__(self, all_df: Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]):
        """
        Initializes the visualizer with necessary DataFrames.
        """
        self.basic_info_df, self.move_eval_df, self.aggressive_eval_df = all_df

    def _show_rating_progression(self, user: str) -> Figure:
        """
        Creates a line graph showing Elo rating progression over games.
        Returns a Plotly line graph.
        """
        fig = px.line(
            self.basic_info_df,
            x="game_id",
            y=user,
            title=self.USER_RATING_LABELS[user],
            labels={
                "game_id": self.AXIS_LABELS["game_id"],
                user: self.USER_RATING_LABELS[user],
            },
        )
        average_elo = self.basic_info_df[user].mean()
        fig.add_hline(
            y=average_elo,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Average Elo: {round(average_elo,2)}",
            annotation_position="top right",
        )
        fig.update_traces(mode="lines+markers")
        return fig

    def _graph_evaluations_over_moves(self) -> Figure:
        """
        Creates a line graph showing move evaluation progression over moves.
        Returns a Plotly line graph.
        """
        results_df = []

        for index, game in self.basic_info_df.iterrows():
            evaluations = game["game_evaluation_progression"]
            game_id = game["game_id"]

            for move_number, eval_score in enumerate(evaluations):
                results_df.append(
                    {
                        "game_id": game_id,
                        "move_number": move_number + 1,
                        "evaluation": eval_score,
                    }
                )

        fig = px.line(
            results_df,
            x="move_number",
            y="evaluation",
            color="game_id",
            labels={
                "move_number": "Move Number",
                "evaluation": "Evaluation Score",
                "game_id": "Game ID",
            },
        )

        fig.update_layout(
            showlegend=True,
            xaxis_title="Move Number",
            yaxis_title="Evaluation Score",
            hovermode="x unified",
        )

        return fig

    def _get_move_eval_df(self, phase: str) -> pd.DataFrame:
        """
        Get melted DataFrame of move evaluations for a specific game phase.
        Returns pd.DataFrame containing move quality counts.
        """

        results_df = self.move_eval_df[self.move_eval_df["phase"] == phase].drop(
            ["phase_winner", "phase", "game_id"], axis=1
        )

        melted_df = results_df.melt(
            value_vars=list(self.MOVE_TYPE_LABELS.keys()),
            var_name="move_type",
            value_name="count",
        )
        return melted_df

    def _show_total_move_eval(self, melted_df: pd.DataFrame) -> Figure:
        """
        Create a bar graph showing total counts for each move type.
        Returns a Plotly bar graph of move quality totals.
        """
        melted_df = melted_df.copy()
        melted_df["move_type"] = melted_df["move_type"].map(self.MOVE_TYPE_LABELS)
        fig = px.bar(
            melted_df,
            x="move_type",
            y="count",
            color="count",
            labels={
                "move_type": self.AXIS_LABELS["move_type"],
                "count": self.AXIS_LABELS["count"],
            },
        )
        return fig

    def _show_average_move_eval(self, melted_df: pd.DataFrame) -> Figure:
        """
        Create a bar graph showing total counts for each move type.
        Returns a Plotly bar graph of average move quality.
        """
        melted_df = melted_df.copy()
        melted_df["move_type"] = melted_df["move_type"].map(self.MOVE_TYPE_LABELS)
        results_df = melted_df.groupby("move_type")["count"].mean().reset_index()

        fig = px.bar(
            results_df,
            x="move_type",
            y="count",
            color="count",
            labels={
                "move_type": self.AXIS_LABELS["move_type"],
                "count": "Average Number of Moves",
            },
        )
        return fig

    def _show_win_percentage(self, color: str) -> Figure:
        """
        Create a pie chart showing the percentage of Win/Loss/Draw depending on color/total.
        Returns a Plotly pie chart of the percentages.
        """
        if color is None:
            result_df = (
                self.basic_info_df["result"]
                .value_counts()
                .reindex(self.RESULT_CATEGORIES, fill_value=0)
                .reset_index()
            )
            result_df.columns = ["result", "count"]
            fig = px.pie(
                result_df,
                values="count",
                names="result",
                color="result",
                color_discrete_map=self.RESULT_COLORS,
            )
            return fig

        result_df = (
            self.basic_info_df[self.basic_info_df["color"] == color]["result"]
            .value_counts()
            .reindex(self.RESULT_CATEGORIES, fill_value=0)
            .reset_index()
        )
        result_df.columns = ["result", "count"]
        fig = px.pie(
            result_df,
            values="count",
            names="result",
            color="result",
            color_discrete_map=self.RESULT_COLORS,
        )
        return fig

    def _show_win_percentage_by_phase(self, phase: str) -> Figure:
        """
        Create a pie chart showing the percentage of Win/Loss/Draw depending on the phase of the game/total game.
        Returns a Plotly pie chart of the percentages.
        """
        phase_df = self.move_eval_df[self.move_eval_df["phase"] == phase]
        result_counts = (
            phase_df["phase_winner"]
            .value_counts()
            .reindex(self.RESULT_CATEGORIES, fill_value=0)
        )

        result_df = result_counts.reset_index()
        result_df.columns = ["phase_winner", "count"]

        fig = px.pie(
            result_df,
            values="count",
            names="phase_winner",
            color="phase_winner",
            color_discrete_map=self.RESULT_COLORS,
        )
        return fig

    def _show_aggressiveness_progression(self) -> Figure:
        """
        Creates a line graph showing aggressiveness evaluation progression over games.
        Returns a Plotly line graph.
        """
        fig = px.line(
            self.basic_info_df,
            x="game_id",
            y="aggressiveness_eval_total",
            labels={
                "game_id": self.AXIS_LABELS["game_id"],
                "aggressiveness_eval_total": self.AXIS_LABELS[
                    "aggressiveness_eval_total"
                ],
            },
        )
        average_aggression = self.basic_info_df["aggressiveness_eval_total"].mean()
        fig.add_hline(
            y=average_aggression,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Average Aggression Score: {round(average_aggression,2)}",
            annotation_position="top right",
        )
        fig.update_traces(mode="lines+markers")
        return fig

    def _show_aggressiveness_total_or_average(self, stat_type: str) -> Figure:
        """
        Create a bar chart showing the average/total aggressiveness stat.
        Returns a Plotly bar chart of average/total aggressiveness evaluation.
        """
        result_df = self.aggressive_eval_df.melt(
            value_vars=list(self.AGGRESSIVE_MOVE_LABELS.keys()),
            var_name="move_type",
            value_name="count",
        )
        result_df["move_type"] = result_df["move_type"].map(self.AGGRESSIVE_MOVE_LABELS)
        if stat_type == "Total":
            fig = px.bar(
                result_df,
                x="move_type",
                y="count",
                color="count",
                labels={
                    "move_type": self.AXIS_LABELS["move_type"],
                    "count": self.AXIS_LABELS["count"],
                    **self.AGGRESSIVE_MOVE_LABELS,
                },
            )
        else:
            avg_fig = result_df.groupby("move_type")["count"].mean().reset_index()
            fig = px.bar(
                avg_fig,
                x="move_type",
                y="count",
                title="Aggressive Move Average",
                color="count",
                labels={
                    "move_type": self.AXIS_LABELS["move_type"],
                    "count": self.AXIS_LABELS["count"],
                    **self.AGGRESSIVE_MOVE_LABELS,
                },
            )
        return fig

    def _show_aggression_result_correlation(self) -> Figure:
        """
        Create a box plot showing the distribution of aggressiveness scores by game result.
        Returns a Plotly box plot showing aggressiveness score distribution for each game result
        """

        return px.box(
            self.basic_info_df,
            x="result",
            y="aggressiveness_eval_total",
            labels={
                "result": self.AXIS_LABELS["result"],
                "aggressiveness_eval_total": self.AXIS_LABELS[
                    "aggressiveness_eval_total"
                ],
            },
            color="result",
            color_discrete_map=self.RESULT_COLORS,
        )

    def _show_opening_frequency(self) -> Figure:
        """
        Create a bar chart showing the frequency of openings used.
        Returns a Plotly bar graph of the frequency of openings used down to variation.
        """
        result_df = (
            self.basic_info_df.groupby("opening")["result"]
            .value_counts()
            .unstack(fill_value=0)
            .reindex(columns=self.RESULT_CATEGORIES, fill_value=0)
            .stack()
            .reset_index()
        )

        result_df.columns = ["opening", "result", "count"]

        fig = px.bar(
            result_df,
            x="opening",
            y="count",
            color="result",
            labels={"opening": self.AXIS_LABELS["opening"], "count": "Frequency"},
            color_discrete_map=self.RESULT_COLORS,
        )
        fig.update_xaxes(tickangle=45)
        return fig
