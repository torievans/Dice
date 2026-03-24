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
            # Numeric Categories
            nums = ["1s", "2s", "3s", "4s", "5s", "6s", "Full House"]
            st.session_state.score_grid = pd.DataFrame(0, index=nums, columns=selected)
            # Boolean Tricks (Checkboxes)
            tricks = ["Low Straight", "High Straight", "5 of a Kind"]
            st.session_state.trick_grid = pd.DataFrame(False, index=tricks, columns=selected)
            st.session_state.game_active = True
            st.session_state.game_finished = False
            st.rerun()

else:
    st.subheader("📝 Live Scorecard")
    
    # Section 1: Points
    st.markdown("### 🔢 Numeric Scores")
    edited_scores = st.data_editor(st.session_state.score_grid, use_container_width=True)
    
    # Section 2: Required Tricks (Checkboxes)
    st.markdown("### ✨ Required Tricks")
    st.caption("Check the box if achieved. Unchecked boxes incur penalties.")
    edited_tricks = st.data_editor(st.session_state.trick_grid, use_container_width=True)
    
    # Calculation Logic
    final_totals = {}
    for player in st.session_state.players:
        p_score = edited_scores[player].sum()
        # Penalties
        penalty = 0
        if not edited_tricks.at["Low Straight", player]: penalty -= 15
        if not edited_tricks.at["High Straight", player]: penalty -= 20
        if not edited_tricks.at["5 of a Kind", player]: penalty -= 30
        
        final_totals[player] = p_score + penalty

    st.divider()
    cols = st.columns(len(st.session_state.players))
    for i, player in enumerate(st.session_state.players):
        cols[i].metric(player, int(final_totals[player]))

    if not st.session_state.get('game_finished'):
        if st.button("🏁 Finish & Save Game", type="primary", use_container_width=True):
            winner = max(final_totals, key=final_totals.get)
            st.balloons()
            for p in st.session_state.players:
                stats[p]["scores"].append(int(final_totals[p]))
                if p == winner: stats[p]["wins"] += 1
            save_data(stats)
            st.session_state.game_finished = True
            st.rerun()
    else:
        st.success(f"🏆 Game Saved!")
        if st.button("🔄 Start a New Game", use_container_width=True):
            st.session_state.game_active = False
            st.rerun()
