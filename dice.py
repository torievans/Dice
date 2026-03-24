import streamlit as st
import pandas as pd
import json
import os
import random

# --- Configuration & Data ---
st.set_page_config(page_title="Double Cameroon Game", layout="wide")
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
if 'dice' not in st.session_state:
    st.session_state.dice = [random.randint(1, 6) for _ in range(10)]
if 'held' not in st.session_state:
    st.session_state.held = [False] * 10
if 'bank_assignments' not in st.session_state:
    st.session_state.bank_assignments = [0] * 10 # 0=Available, 1=Bank A, 2=Bank B
if 'rolls_left' not in st.session_state:
    st.session_state.rolls_left = 3
if 'current_player_idx' not in st.session_state:
    st.session_state.current_player_idx = 0
if 'scores' not in st.session_state:
    st.session_state.scores = {}

# --- Sidebar ---
with st.sidebar:
    st.title("📊 Stats & Settings")
    if stats and any(len(d['scores']) > 0 for d in stats.values()):
        with st.expander("🏆 Leaderboard"):
            perf = [{"Player": k, "Wins": v["wins"], "Avg": round(sum(v["scores"])/len(v["scores"]), 1)} 
                    for k, v in stats.items() if v["scores"]]
            st.table(pd.DataFrame(perf).sort_values(by="Wins", ascending=False).set_index("Player"))
    
    if st.session_state.game_active:
        if st.button("🚫 Quit Game", type="primary", use_container_width=True):
            st.session_state.game_active = False
            st.rerun()

# --- Start Screen ---
if not st.session_state.game_active:
    st.title("🎲 Double Cameroon")
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
            st.session_state.current_player_idx = 0
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

# --- Active Game Area ---
elif st.session_state.game_active:
    current_p = st.session_state.players[st.session_state.current_player_idx]
    st.title(f"👤 {current_p}'s Turn")
    
    # --- DICE TRAY ---
    st.subheader(f"Rolls Left: {st.session_state.rolls_left}")
    dice_cols = st.columns(10)
    for i in range(10):
        with dice_cols[i]:
            # Visual feedback for banks
            b_val = st.session_state.bank_assignments[i]
            b_label = "Neutral" if b_val == 0 else ("Bank A" if b_val == 1 else "Bank B")
            
            if st.button(f"[{st.session_state.dice[i]}]", key=f"d_{i}", help=f"Currently in {b_label}"):
                st.session_state.bank_assignments[i] = (st.session_state.bank_assignments[i] + 1) % 3
                st.rerun()
            st.session_state.held[i] = st.checkbox("Hold", value=st.session_state.held[i], key=f"h_{i}")

    if st.button("🎲 ROLL DICE", use_container_width=True, disabled=st.session_state.rolls_left == 0):
        for i in range(10):
            if not st.session_state.held[i]:
                st.session_state.dice[i] = random.randint(1, 6)
        st.session_state.rolls_left -= 1
        st.rerun()

    # --- BANK DISPLAY ---
    st.divider()
    ba_col, bb_col = st.columns(2)
    bank_a = [st.session_state.dice[i] for i in range(10) if st.session_state.bank_assignments[i] == 1]
    bank_b = [st.session_state.dice[i] for i in range(10) if st.session_state.bank_assignments[i] == 2]
    
    ba_col.write(f"🏦 **Bank A (5 dice):** {bank_a}")
    bb_col.write(f"🏦 **Bank B (5 dice):** {bank_b}")

    # --- SCORING TABLES ---
    st.divider()
    st.subheader("📝 Record Scores")
    
    def render_row(label, multiplier):
        options = [i * multiplier for i in range(7)]
        config = {p: st.column_config.SelectboxColumn(p, options=options) for p in st.session_state.players}
        st.session_state.scores[label] = st.data_editor(st.session_state.scores[label], column_config=config, use_container_width=True, key=f"ed_{label}")

    for row, mult in [("1s", 1), ("2s", 2), ("3s", 3), ("4s", 4), ("5s", 5), ("6s", 6)]:
        render_row(row, mult)
    
    st.session_state.scores["Full House"] = st.data_editor(st.session_state.scores["Full House"], use_container_width=True, key="ed_fh")
    
    trick_config = {p: st.column_config.CheckboxColumn(p) for p in st.session_state.players}
    st.session_state.scores["Tricks"] = st.data_editor(st.session_state.scores["Tricks"], column_config=trick_config, use_container_width=True, key="ed_tricks")

    # --- FOOTER CONTROLS ---
    st.divider()
    if st.button("✅ End Turn & Next Player", use_container_width=True):
        st.session_state.dice = [random.randint(1, 6) for _ in range(10)]
        st.session_state.held = [False] * 10
        st.session_state.bank_assignments = [0] * 10
        st.session_state.rolls_left = 3
        st.session_state.current_player_idx = (st.session_state.current_player_idx + 1) % len(st.session_state.players)
        st.rerun()

    if st.button("🏁 FINISH GAME & SAVE", type="primary", use_container_width=True):
        final_scores = {}
        for p in st.session_state.players:
            total = sum(int(st.session_state.scores[cat][p].iloc[0]) for cat in ["1s", "2s", "3s", "4s", "5s", "6s", "Full House"])
            if not st.session_state.scores["Tricks"].at["Low Straight", p]: total += 15
            if not st.session_state.scores["Tricks"].at["High Straight", p]: total += 20
            if not st.session_state.scores["Tricks"].at["5 of a Kind", p]: total += 30
            final_scores[p] = total
        
        winner = max(final_scores, key=final_scores.get)
        st.balloons()
        for p in st.session_state.players:
            stats[p]["scores"].append(final_scores[p])
            if p == winner: stats[p]["wins"] += 1
        save_data(stats)
        st.session_state.game_active = False
        st.success(f"Game Saved! Winner: {winner}")
        st.rerun()
