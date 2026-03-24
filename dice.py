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
            with open(DB_FILE, "r") as f: return json.load(f)
        except: return {}
    return {}

def save_data(data):
    with open(DB_FILE, "w") as f: json.dump(data, f, indent=4)

stats = load_data()

# --- Sidebar: Analytics ---
with st.sidebar:
    st.title("📊 Stats & Settings")
    if stats and any(len(d['scores']) > 0 for d in stats.values()):
        with st.expander("🏆 Leaderboard", expanded=True):
            perf = [{"Player": k, "Wins": v["wins"], "Avg": round(sum(v["scores"])/len(v["scores"]),1)} 
                    for k, v in stats.items() if v["scores"]]
            st.table(pd.DataFrame(perf).sort_values(by="Wins", ascending=False).set_index("Player"))

    if st.session_state.get('game_active'):
        if st.button("🚫 Quit Game", type="primary", use_container_width=True):
            st.session_state.game_active = False
            st.rerun()

# --- Main Logic ---
if 'game_active' not in st.session_state:
    st.session_state.game_active = False

if not st.session_state.game_active:
    st.subheader("Start New Game")
    col1, col2 = st.columns(2)
    with col1:
        new_p = st.text_input("Create Profile:")
        if st.button("Add Profile") and new_p:
            if new_p not in stats:
                stats[new_p] = {"scores": [], "wins": 0}; save_data(stats); st.rerun()
    with col2:
        selected = st.multiselect("Select Players", list(stats.keys()), max_selections=6)
        if st.button("🚀 Start Game") and selected:
            st.session_state.players = selected
            # Categories
            rows = ["1s", "2s", "3s", "4s", "5s", "6s", "Full House", "Low Straight", "High Straight", "5 of a Kind"]
            st.session_state.score_grid = pd.DataFrame(0, index=rows, columns=selected)
            # Change trick rows to False for checkbox logic
            for trick in ["Low Straight", "High Straight", "5 of a Kind"]:
                st.session_state.score_grid.loc[trick] = False
            
            st.session_state.game_active = True
            st.session_state.game_finished = False
            st.rerun()

else:
    st.subheader("📝 Live Scorecard")
    
    # --- Dynamic Dropdown Configuration ---
    # We define the options for the first 6 rows specifically
    config = {}
    for player in st.session_state.players:
        config[player] = st.column_config.SelectboxColumn(
            player,
            options=[0, 1, 2, 3, 4, 5, 6, 8, 9, 10, 12, 15, 16, 18, 20, 21, 24, 25, 30, 36, 50, True, False],
            help="Select score or check the box for tricks"
        )

    edited_df = st.data_editor(st.session_state.score_grid, use_container_width=True)
    
    # Running Total (Sum of numeric values, ignoring booleans)
    live_totals = {}
    for p in st.session_state.players:
        # Sum only numeric types to avoid errors with checkboxes during live play
        live_totals[p] = pd.to_numeric(edited_df[p], errors='coerce').fillna(0).sum()

    st.divider()
    st.write("### Live Totals (Pre-Penalty)")
    cols = st.columns(len(st.session_state.players))
    for i, player in enumerate(st.session_state.players):
        cols[i].metric(player, int(live_totals[player]))

    if not st.session_state.get('game_finished'):
        if st.button("🏁 Finish & Save Game", type="primary", use_container_width=True):
            final_scores = {}
            for p in st.session_state.players:
                # 1. Sum up numeric rows (1s-6s and Full House)
                base = pd.to_numeric(edited_df.loc["1s":"Full House", p], errors='coerce').sum()
                
                # 2. Penalty Logic for Tricks
                penalty = 0
                if not edited_df.at["Low Straight", p]: penalty -= 15
                if not edited_df.at["High Straight", p]: penalty -= 20
                if not edited_df.at["5 of a Kind", p]: penalty -= 30
                
                final_scores[p] = base + penalty

            winner = max(final_scores, key=final_scores.get)
            st.balloons()
            
            for p in st.session_state.players:
                stats[p]["scores"].append(int(final_scores[p]))
                if p == winner: stats[p]["wins"] += 1
            save_data(stats)
            
            st.session_state.game_finished = True
            st.session_state.final_results = final_scores
            st.rerun()
    else:
        st.success("🏆 Final Results (After Penalties)")
        res_cols = st.columns(len(st.session_state.players))
        for i, player in enumerate(st.session_state.players):
            res_cols[i].metric(player, int(st.session_state.final_results[player]))
            
        if st.button("🔄 Start New Game", use_container_width=True):
            st.session_state.game_active = False
            st.rerun()
