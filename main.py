from src.chess_visualizer_helpers import *


def run_user_interface():
    chess_game_collection = None
    visualizer = None
    try:
        uploaded_file, username = display_title_and_upload()

        if username and uploaded_file is not None:
            st.write(f"Username: {username}")
            visualizer, chess_game_collection = initialize_chess_data(
                uploaded_file, username
            )

            display_elo_ratings(visualizer)
            display_opening_analysis(visualizer)
            display_win_percentage_by_color(visualizer)
            display_total_move_evaluation(visualizer)
            display_average_move_evaluation(visualizer)
            display_phase_results(visualizer)
            display_evaluation_over_moves(visualizer)
            display_aggressiveness_analysis(visualizer)
    finally:
        if chess_game_collection:
            chess_game_collection.engine.quit()


if __name__ == "__main__":

    run_user_interface()
