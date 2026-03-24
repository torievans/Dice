import streamlit as st
import pandas as pd
import json
import os

# --- Configuration & Data Persistence ---
st.set_page_config(page_title="Double Cameroon Scorer", layout="wide")
DB_FILE = "cameroon_stats.json"

def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

stats = load_data()

# --- App Header ---
st.title("🎲 Double Cameroon Scorer")

# --- Sidebar: Setup & Reset ---
with st.sidebar:
    st.header("Settings")
    if st.session_state.get('game_active'):
        if st.button("🚫 Quit Current Game", type="primary"):
            st.session_state.game_active = False
            st.rerun()
    
    st.divider()
    if st.button("Reset All Player Data", type="secondary", help="This deletes all profiles and history!"):
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
            st.session_state.clear()
            st.rerun()

# --- Game Logic & State ---
if 'game_active' not in st.session_state:
    st.session_state.game_active = False

if not st.session_state.game_active:
    st.subheader("Start New Game")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("### 1. Manage Profiles")
        new_player = st.text_input("Create New Profile:", placeholder="Enter name...")
        if st.button("Add Profile") and new_player:
            if new_player not in stats:
                stats[new_player] = {"scores": [], "wins": 0}
                save_data(stats)
                st.success(f"Added {new_player}!")
                st.rerun()

    with col2:
        st.write("### 2. Select Players")
        all_players = list(stats.keys())
        selected_players = st.multiselect("Select up to 6 players:", all_players, max_selections=6)
        
        if st.button("🚀 Start Game") and len(selected_players) > 0:
            st.session_state.players = selected_players
            categories = ["1s", "2s", "3s", "4s", "5s", "6s", "Full House", "Low Straight", "High Straight", "5 of a Kind"]
            # Initialize empty score grid
            st.session_state.score_grid = pd.DataFrame(0, index=categories, columns=selected_players)
            st.session_state.game_active = True
            st.rerun()

else:
    # --- Active Game Screen ---
    st.subheader("📝 Live Scorecard")
    st.info("Tap a cell to enter points. Totals update automatically at the bottom.")
    
    # Editable dataframe for scores
    edited_df = st.data_editor(st.session_state.score_grid, use_container_width=True)
    
    # Calculate Totals
    totals = edited_df.sum()
    st.divider()
    
    # Display Score Badges
    cols = st.columns(len(st.session_state.players))
    for i, player in enumerate(st.session_state.players):
        cols[i].metric(player, int(totals[player]))

    # Finalize Game
    if st.button("🏁 Finish & Save Game", type="primary"):
        winner = totals.idxmax()
        st.balloons()
        st.success(f"🏆 The winner is {winner} with {int(totals[winner])} points!")
        
        # Update Stats dictionary
        for player in st.session_state.players:
            if player not in stats: 
                stats[player] = {"scores": [], "wins": 0}
            stats[player]["scores"].append(int(totals[player]))
            if player == winner:
                stats[player]["wins"] += 1
        
        save_data(stats)
        
        # Mark game as finished to show the Play Again option
        st.session_state.game_finished = True

    # Show Start New Game option ONLY after finishing
    if st.session_state.get('game_finished'):
        if st.button("🔄 Start a New Game"):
            st.session_state.game_active = False
            st.session_state.game_finished = False
            st.rerun()

# --- Performance Section ---
st.divider()
st.header("📊 Performance & Analytics")

if stats and any(len(d['scores']) > 0 for d in stats.values()):
    perf_data = []
    chart_dict = {}

    for name, data in stats.items():
        scores = data.get("scores", [])
        if scores:
            avg = sum(scores) / len(scores)
            perf_data.append({
                "Player": name,
                "Wins": data["wins"],
                "Avg Score": round(avg, 1),
                "Best": max(scores)
            })
            chart_dict[name] = scores

    # Display Career Table
    st.table(pd.DataFrame(perf_data).sort_values(by="Wins", ascending=False).set_index("Player"))

    # Display Trend Chart
    st.subheader("Score Trends")
    df_trends = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in chart_dict.items()]))
    df_trends.index = [f"Game {i+1}" for i in range(len(df_trends))]
    st.line_chart(df_trends)
else:
    st.info("No career data available yet. Complete a game to see your stats here!")
