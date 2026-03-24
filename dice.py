import streamlit as st
import pandas as pd
import json
import os

# --- Configuration ---
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

# --- Sidebar ---
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
st.title("🎲 Double Cameroon Scorer")

if 'game_active' not in st.session_state:
    st.session_state.game_active = False

if not st.session_state.game_active:
    st.subheader("Start New Game")
    col1, col2 = st.columns(2)
    with col1:
        new_p = st.text_input("Create Profile:")
        if st.button("Add") and new_p:
            if new_p not in stats:
                stats[new_p] = {"scores": [], "wins": 0}; save_data(stats); st.rerun()
    with col2:
        selected = st.multiselect("Who is playing?", list(stats.keys()), max_selections=6)
        if st.button("🚀 Start Game") and selected:
            st.session_state.players = selected
            # Define all rows
            rows = ["1s", "2s", "3s", "4s", "5s", "6s", "Full House", "Low Straight (15)", "High Straight (20)", "5 of a Kind (30)"]
            # Create a dataframe where the values are strings/numbers
            st.session_state.score_grid = pd.DataFrame(0, index=rows, columns=selected)
            # For the "Trick" rows, we use 0 as "False" and 1 as "True"
            st.session_state.game_active = True
            st.session_state.game_finished = False
            st.rerun()

else:
    st.subheader("📝 Scorecard")
    st.info("For Straights and 5 of a Kind: Enter '1' if achieved, leave as '0' if missed (Penalty).")
    
    # We use a standard editor here because mixing checkboxes and numbers in the same column 
    # requires a complex workaround. Entering '1' for a trick is the most stable method.
    edited_scores = st.data_editor(st.session_state.score_grid, use_container_width=True)
    
    # Live Total (1s through Full House + Trick bonuses)
    # This sums EVERYTHING entered so far.
    live_totals = edited_scores.sum()
    
    st.divider()
    st.write("### Live Score (Before Penalties)")
    cols = st.columns(len(st.session_state.players))
    for i, player in enumerate(st.session_state.players):
        cols[i].metric(player, int(live_totals[player]))

    if not st.session_state.get('game_finished'):
        if st.button("🏁 Finish & Save Game", type="primary", use_container_width=True):
            final_scores = {}
            
            for player in st.session_state.players:
                # 1. Base score from the table
                current_total = edited_scores[player].sum()
                
                # 2. Penalty Logic
                penalty = 0
                # Check if the specific trick rows are still 0
                if edited_scores.at["Low Straight (15)", player] == 0:
                    penalty -= 15
                if edited_scores.at["High Straight (20)", player] == 0:
                    penalty -= 20
                if edited_scores.at["5 of a Kind (30)", player] == 0:
                    penalty -= 30
                
                final_scores[player] = current_total + penalty

            # Determine Winner
            winner = max(final_scores, key=final_scores.get)
            st.balloons()
            
            # Save stats
            for p in st.session_state.players:
                stats[p]["scores"].append(int(final_scores[p]))
                if p == winner: stats[p]["wins"] += 1
            save_data(stats)
            
            st.session_state.game_finished = True
            st.session_state.final_results = final_scores
            st.rerun()
    else:
        st.success("🏆 Final Results (Penalties Applied)")
        res_cols = st.columns(len(st.session_state.players))
        for i, player in enumerate(st.session_state.players):
            res_cols[i].metric(player, int(st.session_state.final_results[player]))
            
        if st.button("🔄 Start New Game", use_container_width=True):
            st.session_state.game_active = False
            st.rerun()
