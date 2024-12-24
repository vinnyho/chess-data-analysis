
import streamlit as st
from io import StringIO
from .chess_game_class import *
from .chess_stat_visualizer import *

def display_title_and_upload():
    st.title("Chess Data Analysis")
    uploaded_file = st.file_uploader("Choose a PGN Chess.com File", type="pgn")
    username = st.text_input("Enter Chess.com username")
    return uploaded_file, username


def initialize_chess_data(uploaded_file, username):
    file_content = StringIO(uploaded_file.getvalue().decode("utf-8"))
    chess_games_collection = ChessGamesCollection(file_content, username)
    chess_games_df = ChessDataFrame(chess_games_collection.chess_games)
    return ChessDataVisualizer(chess_games_df.get_df()), chess_games_collection


@st.fragment
def display_elo_ratings(visualizer):
    st.header("Elo Rating Progression")
    user_options = ["User", "Opponent"]
    user_options_map = {"User": "user_elo", "Opponent": "opponent_elo"}
    select_phase = st.selectbox("Select User", user_options, key="elo_selector")
    st.plotly_chart(visualizer._show_rating_progression(user_options_map[select_phase]))


@st.fragment
def display_opening_analysis(visualizer):
    st.header("Opening Frequency")
    st.plotly_chart(visualizer._show_opening_frequency())


@st.fragment
def display_win_percentage_by_color(visualizer):
    st.header("Win/Loss/Draw Percentage")
    color_options = ["Total", "White", "Black"]
    color_options_map = {"Total": None, "White": "White", "Black": "Black"}
    select_phase = st.selectbox("Select Color", color_options, key="color_selector")
    st.plotly_chart(visualizer._show_win_percentage(color_options_map[select_phase]))


@st.fragment
def display_total_move_evaluation(visualizer):
    st.header("Total Move Evaluation by Phase")
    move_eval_options = [
        "Total Game Move Evaluation",
        "Total Opening Move Evaluation",
        "Total Middlegame Move Evaluation",
        "Total Endgame Move Evaluation",
    ]
    move_eval_map = {
        "Total Game Move Evaluation": "total",
        "Total Opening Move Evaluation": "opening",
        "Total Middlegame Move Evaluation": "middlegame",
        "Total Endgame Move Evaluation": "endgame",
    }
    select_phase = st.selectbox(
        "Select Game Move Evaluation Phase",
        move_eval_options,
        key="total_move_eval_selector",
    )
    move_melted_df = visualizer._get_move_eval_df(move_eval_map[select_phase])
    st.plotly_chart(visualizer._show_total_move_eval(move_melted_df))


@st.fragment
def display_average_move_evaluation(visualizer):
    st.header("Average Move Evaluation by Phase")
    move_eval_options = [
        "Average Game Move Evaluation",
        "Average Opening Move Evaluation",
        "Average Middlegame Move Evaluation",
        "Average Endgame Move Evaluation",
    ]
    move_eval_map = {
        "Average Game Move Evaluation": "total",
        "Average Opening Move Evaluation": "opening",
        "Average Middlegame Move Evaluation": "middlegame",
        "Average Endgame Move Evaluation": "endgame",
    }
    select_phase = st.selectbox(
        "Select Game Move Evaluation Phase",
        move_eval_options,
        key="avg_move_eval_selector",
    )
    move_melted_df = visualizer._get_move_eval_df(move_eval_map[select_phase])
    st.plotly_chart(visualizer._show_average_move_eval(move_melted_df))


@st.fragment
def display_evaluation_over_moves(visualizer):
    st.header("Move Evaluation Progression over Moves")

    st.plotly_chart(visualizer._graph_evaluations_over_moves())


@st.fragment
def display_phase_results(visualizer):
    st.header("Win/Loss/Draw Percentage by Phase")
    phase_options = ["Opening Result", "Middlegame Result", "Endgame Result"]
    phase_map = {
        "Opening Result": "opening",
        "Middlegame Result": "middlegame",
        "Endgame Result": "endgame",
    }
    select_phase = st.selectbox(
        "Select Game Phase", phase_options, key="phase_results_selector"
    )
    st.plotly_chart(visualizer._show_win_percentage_by_phase(phase_map[select_phase]))


@st.fragment
def display_aggressiveness_analysis(visualizer):
    st.header("Aggression Evaluation Progression")
    st.plotly_chart(visualizer._show_aggressiveness_progression())
    aggressive_options = ["Total", "Average"]
    select_phase = st.selectbox(
        "Select Aggressive Stat type", aggressive_options, key="aggressive_selector"
    )
    st.header("Aggression Evaluation by Total/Average")
    st.plotly_chart(visualizer._show_aggressiveness_total_or_average(select_phase))
    st.header("Aggression Score by Result")
    st.plotly_chart(visualizer._show_aggression_result_correlation())
