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

# --- Sidebar: Analytics & Controls ---
with st.sidebar:
    st.title("📊 Stats & Settings")
    if stats and any(len(d['scores']) > 0 for d in stats.values()):
        with st.expander("🏆 Career Leaderboard", expanded=True):
            perf_data = [{"Player": k, "Wins": v["wins"], "Avg": round(sum(v["scores"])/len(v["scores"]),1)} 
                         for k, v in stats.items() if v["scores"]]
            st.table(pd.DataFrame(perf_data).sort_values(by="Wins", ascending=False).set_index("Player"))
        
        with st.expander("📈 Score Trends"):
            chart_dict = {k: v["scores"] for k, v in stats.items() if v["scores"]}
            df_trends = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in chart_dict.items()]))
            st.line_chart(df_trends)

    if st.session_state.get('game_active'):
        if st.button("🚫 Quit Game", type="primary", use_container_width=True):
            st.session_state.game_active = False
            st.rerun()
    
    if st.button("🗑️ Reset All Data", type="secondary", use_container_width=True):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.session_state.clear()
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
                stats[new_p] = {"scores": [], "wins": 0}
                save_data(stats)
                st.rerun()
    with col2:
        selected = st.multiselect("Who is playing?", list(stats.keys()), max_selections=6)
        if st.button("🚀 Start Game") and selected:
            st.session_state.players = selected
            # Unified Categories
            rows = ["1s", "2s", "3s", "4s", "5s", "6s", "Full House", "Low Straight", "High Straight", "5 of a Kind"]
            # We initialize with 0. For the boolean rows, 0 will represent 'False'
            st.session_state.score_grid = pd.DataFrame(0, index=rows, columns=selected)
            st.session_state.game_active = True
            st.session_state.game_finished = False
            st.rerun()

else:
    st.subheader("📝 Live Scorecard")
    
    # Configure the editor so specific rows act as checkboxes
    # Note: Streamlit's data_editor treats column types globally, 
    # so we'll allow numeric input for all, but players treat 
    # the last 3 as 1 (Achieved) or 0 (Missed) for clarity, 
    # or we simply use the numeric input and validate on finish.
    
    edited_scores = st.data_editor(st.session_state.score_grid, use_container_width=True)
    
    # Live Total (No penalties yet)
    live_totals = edited_scores.loc["1s":"Full House"].sum()
    
    st.divider()
    st.write("### Current Running Total (Excluding Penalties)")
    cols = st.columns(len(st.session_state.players))
    for i, player in enumerate(st.session_state.players):
        cols[i].metric(player, int(live_totals[player]))

    if not st.session_state.get('game_finished'):
        if st.button("🏁 Finish & Save Game", type="primary", use_container_width=True):
            final_calculated_scores = {}
            
            for player in st.session_state.players:
                # 1. Sum up the 1s through Full House
                base_score = edited_scores.loc["1s":"Full House", player].sum()
                
                # 2. Check for penalties on the "Tricks"
                # If the value is 0 or False, apply penalty
                penalty = 0
                if not edited_scores.at["Low Straight", player]: penalty -= 15
                if not edited_scores.at["High Straight", player]: penalty -= 20
                if not edited_scores.at["5 of a Kind", player]: penalty -= 30
                
                # 3. Add trick points if they were entered as positive values (e.g. 21, 30, 50)
                # plus the base score, minus any penalties
                trick_points = edited_scores.loc["Low Straight":"5 of a Kind", player].sum()
                
                final_calculated_scores[player] = base_score + trick_points + penalty

            winner = max(final_calculated_scores, key=final_calculated_scores.get)
            st.balloons()
            
            # Save to history
            for p in st.session_state.players:
                stats[p]["scores"].append(int(final_calculated_scores[p]))
                if p == winner: stats[p]["wins"] += 1
            save_data(stats)
            
            st.session_state.game_finished = True
            st.session_state.final_results = final_calculated_scores
            st.rerun()
    else:
        st.success("🏆 Final Scores (Penalties Applied):")
        res_cols = st.columns(len(st.session_state.players))
        for i, player in enumerate(st.session_state.players):
            res_cols[i].metric(player, int(st.session_state.final_results[player]))
            
        if st.button("🔄 Start a New Game", use_container_width=True):
            st.session_state.game_active = False
            st.session_state.game_finished = False
            st.rerun()
