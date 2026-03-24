import streamlit as st
import pandas as pd
import json
import os
import random

# --- Configuration ---
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
    st.session_state.bank_assignments = [0] * 10 # 0: None, 1: A, 2: B
if 'rolls_left' not in st.session_state:
    st.session_state.rolls_left = 3
if 'current_player_idx' not in st.session_state:
    st.session_state.current_player_idx = 0

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
            st.rerun()

# --- Active Game Area ---
else:
    current_p = st.session_state.players[st.session_state.current_player_idx]
    st.header(f"👤 {current_p}'s Turn")
    
    # --- DICE TRAY ---
    st.subheader(f"Rolls Remaining: {st.session_state.rolls_left}")
    
    # Roll Logic
    if st.button("🎲 ROLL DICE", use_container_width=True, type="primary", disabled=st.session_state.rolls_left == 0):
        for i in range(10):
            if not st.session_state.held[i]:
                st.session_state.dice[i] = random.randint(1, 6)
        st.session_state.rolls_left -= 1
        st.rerun()

    # Display 10 Dice with Controls
    dice_cols = st.columns(10)
    for i in range(10):
        with dice_cols[i]:
            # Die Face
            st.button(f"{st.session_state.dice[i]}", key=f"v_{i}", disabled=True, use_container_width=True)
            
            # Hold Checkbox
            st.session_state.held[i] = st.checkbox("Hold", value=st.session_state.held[i], key=f"h_{i}")
            
            # Banking Buttons
            c1, c2 = st.columns(2)
            if c1.button("A", key=f"ba_{i}", type="primary" if st.session_state.bank_assignments[i]==1 else "secondary"):
                st.session_state.bank_assignments[i] = 1 if st.session_state.bank_assignments[i] != 1 else 0
                st.rerun()
            if c2.button("B", key=f"bb_{i}", type="primary" if st.session_state.bank_assignments[i]==2 else "secondary"):
                st.session_state.bank_assignments[i] = 2 if st.session_state.bank_assignments[i] != 2 else 0
                st.rerun()

    # --- VISUAL BANKS ---
    st.divider()
    bA_col, bB_col = st.columns(2)
    
    with bA_col:
        bank_a = [st.session_state.dice[i] for i in range(10) if st.session_state.bank_assignments[i] == 1]
        st.markdown(f"### 🏦 Bank A: `{bank_a}`")
        if len(bank_a) > 5: st.error("Max 5 dice!")
        
    with bB_col:
        bank_b = [st.session_state.dice[i] for i in range(10) if st.session_state.bank_assignments[i] == 2]
        st.markdown(f"### 🏦 Bank B: `{bank_b}`")
        if len(bank_b) > 5: st.error("Max 5 dice!")

    # --- SCORING TABLES ---
    st.divider()
    st.subheader("📝 Scoring")
    
    def render_row(label, multiplier):
        options = [i * multiplier for i in range(7)]
        config = {p: st.column_config.SelectboxColumn(p, options=options) for p in st.session_state.players}
        st.session_state.scores[label] = st.data_editor(st.session_state.scores[label], column_config=config, use_container_width=True, key=f"ed_{label}")

    for row, mult in [("1s", 1), ("2s", 2), ("3s", 3), ("4s", 4), ("5s", 5), ("6s", 6)]:
        render_row(row, mult)
    
    st.session_state.scores["Full House"] = st.data_editor(st.session_state.scores["Full House"], use_container_width=True, key="ed_fh")
    trick_config = {p: st.column_config.CheckboxColumn(p) for p in st.session_state.players}
    st.session_state.scores["Tricks"] = st.data_editor(st.session_state.scores["Tricks"], column_config=trick_config, use_container_width=True, key="ed_tricks")

    # --- TURN & GAME END ---
    if st.button("✅ End Turn & Next Player", use_container_width=True):
        st.session_state.dice = [random.randint(1, 6) for _ in range(10)]
        st.session_state.held = [False] * 10
        st.session_state.bank_assignments = [0] * 10
        st.session_state.rolls_left = 3
        st.session_state.current_player_idx = (st.session_state.current_player_idx + 1) % len(st.session_state.players)
        st.rerun()

    if st.button("🏁 Finish Game", type="primary"):
        # Penalty calculation logic
        final_scores = {}
        for p in st.session_state.players:
            total = sum(int(st.session_state.scores[cat][p].iloc[0]) for cat in ["1s", "2s", "3s", "4s", "5s", "6s", "Full House"])
            if not st.session_state.scores["Tricks"].at["Low Straight", p]: total += 15
            if not st.session_state.scores["Tricks"].at["High Straight", p]: total += 20
            if not st.session_state.scores["Tricks"].at["5 of a Kind", p]: total += 30
            final_scores[p] = total
        
        winner = max(final_scores, key=final_scores.get)
        for p in st.session_state.players:
            stats[p]["scores"].append(final_scores[p])
            if p == winner: stats[p]["wins"] += 1
        save_data(stats)
        st.session_state.game_active = False
        st.rerun()
