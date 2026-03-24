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

# --- Initialize Session State ---
if 'game_active' not in st.session_state:
    st.session_state.game_active = False
if 'scores' not in st.session_state:
    st.session_state.scores = {} # Dictionary to hold individual row DataFrames
if 'players' not in st.session_state:
    st.session_state.players = []

# --- Sidebar ---
with st.sidebar:
    st.title("📊 Stats & Settings")
    if stats and any(len(d['scores']) > 0 for d in stats.values()):
        with st.expander("🏆 Leaderboard", expanded=True):
            perf = [{"Player": k, "Wins": v["wins"], "Avg": round(sum(v["scores"])/len(v["scores"]), 1)} 
                    for k, v in stats.items() if v["scores"]]
            st.table(pd.DataFrame(perf).sort_values(by="Wins", ascending=False).set_index("Player"))
    
    if st.session_state.game_active:
        if st.button("🚫 Quit Game", type="primary", use_container_width=True):
            st.session_state.game_active = False
            st.rerun()

# --- Main Logic ---
st.title("🎲 Double Cameroon Scorer")

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
            # Initialize row-specific grids
            st.session_state.scores = {
                "1s": pd.DataFrame(0, index=["1s"], columns=selected),
                "2s": pd.DataFrame(0, index=["2s"], columns=selected),
                "3s": pd.DataFrame(0, index=["3s"], columns=selected),
                "4s": pd.DataFrame(0, index=["4s"], columns=selected),
                "5s": pd.DataFrame(0, index=["5s"], columns=selected),
                "6s": pd.DataFrame(0, index=["6s"], columns=selected),
                "Full House": pd.DataFrame(0, index=["Full House"], columns=selected),
                "Tricks": pd.DataFrame(False, index=["Low Straight", "High Straight", "5 of a Kind"], columns=selected)
            }
            st.session_state.game_active = True
            st.session_state.game_finished = False
            st.rerun()

else:
    st.subheader("📝 Live Scorecard")
    
    # Helper function to render a row with specific multiples
    def render_row(label, multiplier, players):
        options = [i * multiplier for i in range(6)]
        config = {p: st.column_config.SelectboxColumn(p, options=options) for p in players}
        st.session_state.scores[label] = st.data_editor(
            st.session_state.scores[label], 
            column_config=config, 
            use_container_width=True, 
            key=f"editor_{label}"
        )

    # Render Multiples Rows
    render_row("1s", 1, st.session_state.players)
    render_row("2s", 2, st.session_state.players)
    render_row("3s", 3, st.session_state.players)
    render_row("4s", 4, st.session_state.players)
    render_row("5s", 5, st.session_state.players)
    render_row("6s", 6, st.session_state.players)

    # Full House (Numeric Input)
    st.write("**Full House**")
    st.session_state.scores["Full House"] = st.data_editor(
        st.session_state.scores["Full House"], use_container_width=True, key="editor_fh"
    )

    # Tricks (Checkboxes)
    st.write("**Required Tricks**")
    trick_config = {p: st.column_config.CheckboxColumn(p) for p in st.session_state.players}
    st.session_state.scores["Tricks"] = st.data_editor(
        st.session_state.scores["Tricks"], column_config=trick_config, use_container_width=True, key="editor_tricks"
    )

    # --- Calculation ---
    current_totals = {p: 0 for p in st.session_state.players}
    for label in ["1s", "2s", "3s", "4s", "5s", "6s", "Full House"]:
        for p in st.session_state.players:
            current_totals[p] += int(st.session_state.scores[label][p].iloc[0])

    st.divider()
    st.write("### Current Totals (Pre-Penalty)")
    cols = st.columns(len(st.session_state.players))
    for i, player in enumerate(st.session_state.players):
        cols[i].metric(player, current_totals[player])

    if not st.session_state.get('game_finished'):
        if st.button("🏁 Finish & Save Game", type="primary", use_container_width=True):
            final_scores = {}
            for p in st.session_state.players:
                score = current_totals[p]
                # ADD penalties if unchecked
                if not st.session_state.scores["Tricks"].at["Low Straight", p]: score += 15
                if not st.session_state.scores["Tricks"].at["High Straight", p]: score += 20
                if not st.session_state.scores["Tricks"].at["5 of a Kind", p]: score += 30
                final_scores[p] = score

            winner = max(final_scores, key=final_scores.get)
            st.balloons()
            for p in st.session_state.players:
                stats[p]["scores"].append(final_scores[p])
                if p == winner: stats[p]["wins"] += 1
            save_data(stats)
            st.session_state.game_finished = True
            st.session_state.final_results = final_scores
            st.rerun()
    else:
        st.success("🏆 Final Results (Penalties Added)")
        res_cols = st.columns(len(st.session_state.players))
        for i, player in enumerate(st.session_state.players):
            res_cols[i].metric(player, int(st.session_state.final_results[player]))
            
        if st.button("🔄 Start New Game", use_container_width=True):
            st.session_state.game_active = False
            st.rerun()
