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

# --- Sidebar ---
with st.sidebar:
    st.title("📊 Stats & Settings")
    if stats and any(len(d['scores']) > 0 for d in stats.values()):
        with st.expander("🏆 Leaderboard", expanded=True):
            perf = [{"Player": k, "Wins": v["wins"], "Avg": round(sum(v["scores"])/len(v["scores"]), 1)} 
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
            # Table 1: Multiples & Full House
            num_rows = ["1s", "2s", "3s", "4s", "5s", "6s", "Full House"]
            st.session_state.num_grid = pd.DataFrame(0, index=num_rows, columns=selected)
            # Table 2: Required Tricks (Checkboxes)
            trick_rows = ["Low Straight", "High Straight", "5 of a Kind"]
            st.session_state.trick_grid = pd.DataFrame(False, index=trick_rows, columns=selected)
            
            st.session_state.game_active = True
            st.session_state.game_finished = False
            st.rerun()

else:
    st.subheader("📝 Live Scorecard")

    # --- TABLE 1: NUMERIC SCORES WITH DROPDOWNS ---
    st.write("### Number Categories")
    
    # We create unique dropdown options for each row
    # Streamlit's data_editor applies config to the COLUMN, so we provide 
    # a master list of all valid multiples for the dropdown.
    all_multiples = [0] + [i*j for i in range(1,7) for j in range(1,7)] + [i for i in range(5, 31)] # Covers Full House too
    all_multiples = sorted(list(set(all_multiples)))

    num_config = {p: st.column_config.SelectboxColumn(p, options=all_multiples, width="medium") for p in st.session_state.players}
    
    edited_nums = st.data_editor(st.session_state.num_grid, column_config=num_config, use_container_width=True, key="num_editor")

    # --- TABLE 2: TRICKS WITH CHECKBOXES ---
    st.write("### Required Tricks")
    
    # Checkbox columns are triggered by the data type (Boolean)
    trick_config = {p: st.column_config.CheckboxColumn(p, default=False) for p in st.session_state.players}
    
    edited_tricks = st.data_editor(st.session_state.trick_grid, column_config=trick_config, use_container_width=True, key="trick_editor")

    # --- TOTALS & FINISH ---
    live_totals = edited_nums.sum()
    st.divider()
    st.write("### Current Totals (Pre-Penalty)")
    cols = st.columns(len(st.session_state.players))
    for i, player in enumerate(st.session_state.players):
        cols[i].metric(player, int(live_totals[player]))

    if not st.session_state.get('game_finished'):
        if st.button("🏁 Finish & Save Game", type="primary", use_container_width=True):
            final_scores = {}
            for p in st.session_state.players:
                base = edited_nums[p].sum()
                penalty = 0
                if not edited_tricks.at["Low Straight", p]: penalty -= 15
                if not edited_tricks.at["High Straight", p]: penalty -= 20
                if not edited_tricks.at["5 of a Kind", p]: penalty -= 30
                
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
