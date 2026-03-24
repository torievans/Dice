import streamlit as st
import pandas as pd
import json
import os
import random
from collections import Counter

# --- 1. SCORING ENGINE ---
def calculate_score(dice, category):
    dice.sort()
    counts = Counter(dice)
    val_counts = list(counts.values())

    if category == "1s": return dice.count(1) * 1
    if category == "2s": return dice.count(2) * 2
    if category == "3s": return dice.count(3) * 3
    if category == "4s": return dice.count(4) * 4
    if category == "5s": return dice.count(5) * 5
    if category == "6s": return dice.count(6) * 6
    
    if category == "Full House":
        # Check for 3 of one, 2 of another (or 5 of a kind as a perfect FH)
        if (3 in val_counts and 2 in val_counts) or (5 in val_counts):
            # Identify which number is the set of 3 and which is the set of 2
            # If 5-of-a-kind, we treat the number as both for the best score
            sorted_groups = sorted(counts.items(), key=lambda x: x[1], reverse=True)
            three_val = sorted_groups[0][0]
            two_val = sorted_groups[1][0] if len(sorted_groups) > 1 else three_val
            
            # Distance from 6-6-6 and 5-5
            return ((6 - three_val) * 3) + ((5 - two_val) * 2)
        return 0

    if category == "Low Straight": return 21 if dice == [1, 2, 3, 4, 5] else 0
    if category == "High Straight": return 30 if dice == [2, 3, 4, 5, 6] else 0
    if category == "5 of a Kind": return 50 if 5 in val_counts else 0
    return 0

# --- 2. CONFIG & DATA ---
st.set_page_config(page_title="Double Cameroon", layout="wide")
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

# --- 3. SESSION STATE ---
if 'game_active' not in st.session_state: st.session_state.game_active = False
if 'dice' not in st.session_state: st.session_state.dice = [random.randint(1, 6) for _ in range(10)]
if 'trickA_indices' not in st.session_state: st.session_state.trickA_indices = []
if 'trickB_indices' not in st.session_state: st.session_state.trickB_indices = []
if 'rolls_left' not in st.session_state: st.session_state.rolls_left = 3
if 'current_player_idx' not in st.session_state: st.session_state.current_player_idx = 0

# --- 4. START SCREEN ---
if not st.session_state.game_active:
    st.title("🎲 Double Cameroon")
    col1, col2 = st.columns(2)
    with col1:
        new_p = st.text_input("Create Profile:")
        if st.button("Add Profile") and new_p:
            if new_p not in stats: stats[new_p] = {"scores": [], "wins": 0}; save_data(stats); st.rerun()
    with col2:
        selected = st.multiselect("Select Players", list(stats.keys()))
        if st.button("🚀 Start Game") and selected:
            st.session_state.players = selected
            st.session_state.current_player_idx = 0
            # Initialize Score Tables
            rows = ["1s", "2s", "3s", "4s", "5s", "6s", "Full House"]
            st.session_state.scores = {cat: pd.DataFrame(0, index=[cat], columns=selected) for cat in rows}
            st.session_state.scores["Tricks"] = pd.DataFrame(False, index=["Low Straight", "High Straight", "5 of a Kind"], columns=selected)
            st.session_state.game_active = True
            st.rerun()

# --- 5. ACTIVE GAME AREA ---
else:
    current_p = st.session_state.players[st.session_state.current_player_idx]
    st.header(f"👤 {current_p}'s Turn")
    
    # DICE TRAY
    st.subheader(f"Rolls Remaining: {st.session_state.rolls_left}")
    if st.button("🎲 ROLL DICE", use_container_width=True, type="primary", disabled=st.session_state.rolls_left == 0):
        locked = st.session_state.trickA_indices + st.session_state.trickB_indices
        for i in range(10):
            if i not in locked: st.session_state.dice[i] = random.randint(1, 6)
        st.session_state.rolls_left -= 1
        st.rerun()

    d_cols = st.columns(10)
    for i in range(10):
        with d_cols[i]:
            inA, inB = i in st.session_state.trickA_indices, i in st.session_state.trickB_indices
            st.button(f"{st.session_state.dice[i]}", key=f"v_{i}", disabled=True, use_container_width=True, type="primary" if (inA or inB) else "secondary")
            c1, c2 = st.columns(2)
            if c1.button("A", key=f"tA_{i}", type="primary" if inA else "secondary"):
                if inA: st.session_state.trickA_indices.remove(i)
                else: 
                    if inB: st.session_state.trickB_indices.remove(i)
                    st.session_state.trickA_indices.append(i)
                st.rerun()
            if c2.button("B", key=f"tB_{i}", type="primary" if inB else "secondary"):
                if inB: st.session_state.trickB_indices.remove(i)
                else:
                    if inA: st.session_state.trickA_indices.remove(i)
                    st.session_state.trickB_indices.append(i)
                st.rerun()

    # TRICK ALLOCATION & DROPDOWNS
    st.divider()
    tA_vals = sorted([st.session_state.dice[idx] for idx in st.session_state.trickA_indices])
    tB_vals = sorted([st.session_state.dice[idx] for idx in st.session_state.trickB_indices])
    
    def get_options(dice):
        opts = ["1s", "2s", "3s", "4s", "5s", "6s"]
        if calculate_score(dice, "Full House") > 0 or len(set(dice)) == 1: opts.append("Full House")
        if dice == [1, 2, 3, 4, 5]: opts.append("Low Straight")
        if dice == [2, 3, 4, 5, 6]: opts.append("High Straight")
        if len(set(dice)) == 1 and len(dice) == 5: opts.append("5 of a Kind")
        return opts

    ca, cb = st.columns(2)
    with ca:
        st.markdown(f"### ✨ Trick A ({len(tA_vals)}/5): `{tA_vals}`")
        if len(tA_vals) == 5:
            sel_a = st.selectbox("Assign Trick A:", get_options(tA_vals), key="sA")
            if st.button("Apply A", use_container_width=True):
                val = calculate_score(tA_vals, sel_a)
                if sel_a in ["Low Straight", "High Straight", "5 of a Kind"]: st.session_state.scores["Tricks"].at[sel_a, current_p] = True
                else: st.session_state.scores[sel_a].at[sel_a, current_p] = val
                st.success(f"Applied {val} to {sel_a}")

    with cb:
        st.markdown(f"### ✨ Trick B ({len(tB_vals)}/5): `{tB_vals}`")
        if len(tB_vals) == 5:
            sel_b = st.selectbox("Assign Trick B:", get_options(tB_vals), key="sB")
            if st.button("Apply B", use_container_width=True):
                val = calculate_score(tB_vals, sel_b)
                if sel_b in ["Low Straight", "High Straight", "5 of a Kind"]: st.session_state.scores["Tricks"].at[sel_b, current_p] = True
                else: st.session_state.scores[sel_b].at[sel_b, current_p] = val
                st.success(f"Applied {val} to {sel_b}")

    # ACTIONS
    st.divider()
    c_next, c_done = st.columns(2)
    if c_next.button("✅ End Turn & Next Player", use_container_width=True):
        st.session_state.dice = [random.randint(1, 6) for _ in range(10)]
        st.session_state.trickA_indices, st.session_state.trickB_indices = [], []
        st.session_state.rolls_left = 3
        st.session_state.current_player_idx = (st.session_state.current_player_idx + 1) % len(st.session_state.players)
        st.rerun()

    if c_done.button("🏁 Finish Game", type="primary", use_container_width=True):
        final = {}
        for p in st.session_state.players:
            score = sum(int(st.session_state.scores[c][p].iloc[0]) for c in ["1s", "2s", "3s", "4s", "5s", "6s", "Full House"])
            if not st.session_state.scores["Tricks"].at["Low Straight", p]: score += 15
            if not st.session_state.scores["Tricks"].at["High Straight", p]: score += 20
            if not st.session_state.scores["Tricks"].at["5 of a Kind", p]: score += 30
            final[p] = score
        winner = max(final, key=final.get)
        for p in st.session_state.players:
            stats[p]["scores"].append(final[p])
            if p == winner: stats[p]["wins"] += 1
        save_data(stats); st.session_state.game_active = False; st.rerun()

    # SCORECARD
    with st.expander("📝 View Scorecard", expanded=True):
        for row, mult in [("1s", 1), ("2s", 2), ("3s", 3), ("4s", 4), ("5s", 5), ("6s", 6)]:
            opts = [i * mult for i in range(7)]
            st.session_state.scores[row] = st.data_editor(st.session_state.scores[row], column_config={p: st.column_config.SelectboxColumn(p, options=opts) for p in st.session_state.players}, use_container_width=True, key=f"edit_{row}")
        st.session_state.scores["Full House"] = st.data_editor(st.session_state.scores["Full House"], use_container_width=True)
        st.session_state.scores["Tricks"] = st.data_editor(st.session_state.scores["Tricks"], column_config={p: st.column_config.CheckboxColumn(p) for p in st.session_state.players}, use_container_width=True)
