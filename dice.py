import streamlit as st
import pandas as pd
import json
import os
import random
from collections import Counter

# --- 1. THE PENALTY ENGINE ---
def calculate_score(dice, category):
    dice.sort()
    counts = Counter(dice)
    target_map = {"1s": 1, "2s": 2, "3s": 3, "4s": 4, "5s": 5, "6s": 6}
    if category in target_map:
        target = target_map[category]
        return sum(1 for d in dice if d != target) * target
    if category == "Full House":
        val_counts = list(counts.values())
        if (3 in val_counts and 2 in val_counts) or (5 in val_counts):
            sorted_groups = sorted(counts.items(), key=lambda x: x[1], reverse=True)
            three_val = sorted_groups[0][0]
            two_val = sorted_groups[1][0] if len(sorted_groups) > 1 else three_val
            return ((6 - three_val) * 3) + ((5 - two_val) * 2)
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

# --- 3. INITIALIZE STATE ---
if 'game_active' not in st.session_state: st.session_state.game_active = False
if 'game_over' not in st.session_state: st.session_state.game_over = False
if 'final_results' not in st.session_state: st.session_state.final_results = {}
if 'dice' not in st.session_state: st.session_state.dice = [random.randint(1, 6) for _ in range(10)]
if 'trickA_indices' not in st.session_state: st.session_state.trickA_indices = []
if 'trickB_indices' not in st.session_state: st.session_state.trickB_indices = []
if 'rolls_left' not in st.session_state: st.session_state.rolls_left = 3
if 'current_player_idx' not in st.session_state: st.session_state.current_player_idx = 0
if 'used_categories' not in st.session_state: st.session_state.used_categories = {}

# --- 4. NAVIGATION LOGIC (CRITICAL ORDER) ---

# PRIORITY 1: SHOW RESULTS IF GAME IS OVER
if st.session_state.game_over:
    st.balloons()
    st.title("🏆 Final Standings")
    
    # Sort results: Lowest score is the winner
    sorted_results = sorted(st.session_state.final_results.items(), key=lambda x: x[1])
    winner_name, winner_score = sorted_results[0]
    
    st.success(f"### The Winner is {winner_name} with {winner_score} points!")
    
    # Create Table
    res_df = pd.DataFrame(sorted_results, columns=['Player', 'Final Score'])
    st.table(res_df.set_index('Player'))
    
    if st.button("🔄 Return to Main Menu", use_container_width=True):
        # Reset everything for a fresh start
        st.session_state.game_over = False
        st.session_state.game_active = False
        st.session_state.final_results = {}
        st.rerun()

# PRIORITY 2: SHOW GAME IF ACTIVE
elif st.session_state.game_active:
    current_p = st.session_state.players[st.session_state.current_player_idx]
    st.header(f"👤 {current_p}'s Turn")
    
    # --- DICE TRAY ---
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

    # --- TRICK SELECTION ---
    st.divider()
    tA_vals = sorted([st.session_state.dice[idx] for idx in st.session_state.trickA_indices])
    tB_vals = sorted([st.session_state.dice[idx] for idx in st.session_state.trickB_indices])
    
    def get_opts(dice, player):
        all_opts = ["1s", "2s", "3s", "4s", "5s", "6s", "Full House", "Low Straight", "High Straight", "5 of a Kind"]
        return [o for o in all_opts if o not in st.session_state.used_categories[player]]

    ca, cb = st.columns(2)
    with ca:
        st.markdown(f"### ✨ Trick A ({len(tA_vals)}/5): `{tA_vals}`")
        sel_a = st.selectbox("Assign Trick A to:", get_opts(tA_vals, current_p), key="sA") if len(tA_vals) == 5 else None
    with cb:
        st.markdown(f"### ✨ Trick B ({len(tB_vals)}/5): `{tB_vals}`")
        sel_b = st.selectbox("Assign Trick B to:", get_opts(tB_vals, current_p), key="sB") if len(tB_vals) == 5 else None

    # --- TURN ACTIONS ---
    st.divider()
    col_end, col_finish = st.columns(2)
    
    can_end = (len(tA_vals) == 5 and len(tB_vals) == 5 and sel_a and sel_b and sel_a != sel_b)

    if col_end.button("✅ Confirm & Next Player", use_container_width=True, disabled=not can_end, type="primary"):
        for s, v in [(sel_a, tA_vals), (sel_b, tB_vals)]:
            if s in ["Low Straight", "High Straight", "5 of a Kind"]:
                if (s == "Low Straight" and v == [1,2,3,4,5]) or (s == "High Straight" and v == [2,3,4,5,6]) or (s == "5 of a Kind" and len(set(v)) == 1):
                    st.session_state.scores["Tricks"].at[s, current_p] = True
            else:
                st.session_state.scores[s].at[s, current_p] = calculate_score(v, s)
            st.session_state.used_categories[current_p].append(s)
        
        st.session_state.dice = [random.randint(1, 6) for _ in range(10)]
        st.session_state.trickA_indices, st.session_state.trickB_indices = [], []
        st.session_state.rolls_left = 3
        st.session_state.current_player_idx = (st.session_state.current_player_idx + 1) % len(st.session_state.players)
        st.rerun()

    # --- THE FIX: CALCULATE AND SWITCH TO GAME_OVER ---
    if col_finish.button("🏁 Finish Game & Show Winner", use_container_width=True):
        final_scores = {}
        for p in st.session_state.players:
            # Sum numeric columns
            total = sum(int(st.session_state.scores[cat][p].iloc[0]) for cat in ["1s", "2s", "3s", "4s", "5s", "6s", "Full House"])
            # Add missed trick penalties
            if not st.session_state.scores["Tricks"].at["Low Straight", p]: total += 15
            if not st.session_state.scores["Tricks"].at["High Straight", p]: total += 20
            if not st.session_state.scores["Tricks"].at["5 of a Kind", p]: total += 30
            final_scores[p] = total
        
        # Save results to state and trigger Game Over screen
        st.session_state.final_results = final_scores
        st.session_state.game_active = False # Deactivates gameplay loop
        st.session_state.game_over = True    # Activates results loop
        
        # Record stats
        winner = min(final_scores, key=final_scores.get)
        for p in st.session_state.players:
            stats[p]["scores"].append(final_scores[p])
            if p == winner: stats[p]["wins"] += 1
        save_data(stats)
        st.rerun()

# PRIORITY 3: SHOW START SCREEN IF NOTHING ELSE
else:
    st.title("🎲 Double Cameroon")
    col1, col2 = st.columns(2)
    # [Profiles and Player Selection logic stays here...]
    with col1:
        new_p = st.text_input("Create Profile:")
        if st.button("Add Profile") and new_p:
            if new_p not in stats: stats[new_p] = {"scores": [], "wins": 0}; save_data(stats); st.rerun()
    with col2:
        selected = st.multiselect("Select Players", list(stats.keys()))
        if st.button("🚀 Start Game") and selected:
            st.session_state.players = selected
            st.session_state.current_player_idx = 0
            st.session_state.used_categories = {p: [] for p in selected}
            st.session_state.scores = {cat: pd.DataFrame(0, index=[cat], columns=selected) for cat in ["1s", "2s", "3s", "4s", "5s", "6s", "Full House"]}
            st.session_state.scores["Tricks"] = pd.DataFrame(False, index=["Low Straight", "High Straight", "5 of a Kind"], columns=selected)
            st.session_state.game_active = True
            st.session_state.game_over = False
            st.rerun()
