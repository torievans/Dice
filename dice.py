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
        # Sort counts by frequency then value to find the best triple and pair
        sorted_items = sorted(counts.items(), key=lambda x: (x[1], x[0]), reverse=True)
        three_val = sorted_items[0][0]
        # If 5 of a kind, pair value is the same as triple value
        two_val = sorted_items[1][0] if len(sorted_items) > 1 else three_val
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

# --- 3. CUSTOM STYLING (Square Dice with Dots) ---
st.markdown("""
    <style>
    /* Make the dice buttons look like real square dice */
    div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"] > div > div > button {
        height: 70px !important;
        width: 70px !important;
        font-size: 45px !important;
        line-height: 1 !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        border-radius: 10px !important;
    }
    
    /* Available Dice: White background, Black text */
    button[kind="secondary"] {
        background-color: white !important;
        color: black !important;
        border: 2px solid black !important;
    }
    
    /* Held Dice: Black background, Grey text */
    button[kind="primary"] {
        background-color: black !important;
        color: #888888 !important;
        border: 2px solid #444 !important;
    }

    /* Reset A/B buttons to standard styling */
    div[data-testid="stHorizontalBlock"] div[data-testid="stHorizontalBlock"] button {
        height: auto !important;
        width: 100% !important;
        font-size: 14px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. INITIALIZE STATE ---
if 'game_active' not in st.session_state: st.session_state.game_active = False
if 'game_over' not in st.session_state: st.session_state.game_over = False
if 'first_roll_made' not in st.session_state: st.session_state.first_roll_made = False
if 'final_results' not in st.session_state: st.session_state.final_results = {}
if 'dice' not in st.session_state: st.session_state.dice = [0] * 10
if 'trickA_indices' not in st.session_state: st.session_state.trickA_indices = []
if 'trickB_indices' not in st.session_state: st.session_state.trickB_indices = []
if 'rolls_left' not in st.session_state: st.session_state.rolls_left = 3
if 'current_player_idx' not in st.session_state: st.session_state.current_player_idx = 0
if 'used_categories' not in st.session_state: st.session_state.used_categories = {}

# --- 5. NAVIGATION LOGIC ---

if st.session_state.game_over:
    st.balloons()
    st.title("🏆 Final Standings")
    sorted_results = sorted(st.session_state.final_results.items(), key=lambda x: x[1])
    winner_name, winner_score = sorted_results[0]
    st.success(f"### The Winner is {winner_name} with {winner_score} points!")
    res_df = pd.DataFrame(sorted_results, columns=['Player', 'Final Score'])
    st.table(res_df.set_index('Player'))
    if st.button("🔄 Start New Game", use_container_width=True):
        st.session_state.game_over = False
        st.session_state.game_active = False
        st.rerun()

elif not st.session_state.game_active:
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
            st.session_state.used_categories = {p: [] for p in selected}
            rows = ["1s", "2s", "3s", "4s", "5s", "6s", "Full House"]
            st.session_state.master_scores = pd.DataFrame(0, index=rows, columns=selected)
            st.session_state.trick_scores = pd.DataFrame(False, index=["Low Straight", "High Straight", "5 of a Kind"], columns=selected)
            st.session_state.game_active = True
            st.session_state.first_roll_made = False
            st.rerun()

# --- 6. SHOW GAMEPLAY ---
if st.session_state.game_active and not st.session_state.game_over:
    current_p = st.session_state.players[st.session_state.current_player_idx]
    turn_num = (len(st.session_state.used_categories[current_p]) // 2) + 1
    st.header(f"👤 {current_p}'s Turn [{turn_num}/5]")
    
    st.subheader(f"Rolls Remaining: {st.session_state.rolls_left}")
    
    if st.button("🎲 ROLL DICE", use_container_width=True, type="primary", disabled=st.session_state.rolls_left == 0):
        locked = st.session_state.trickA_indices + st.session_state.trickB_indices
        for i in range(10):
            if i not in locked: st.session_state.dice[i] = random.randint(1, 6)
        st.session_state.rolls_left -= 1
        st.session_state.first_roll_made = True
        st.rerun()

    # Dice Faces Mapping
    dice_faces = {0: "?", 1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}

    d_cols = st.columns(10)
    for i in range(10):
        with d_cols[i]:
            inA, inB = i in st.session_state.trickA_indices, i in st.session_state.trickB_indices
            is_held = inA or inB
            
            # Show dots only if rolled
            label = dice_faces[st.session_state.dice[i]] if st.session_state.first_roll_made else "?"
            
            st.button(label, key=f"v_{i}", disabled=True, type="primary" if is_held else "secondary")
            
            c1, c2 = st.columns(2)
            if c1.button("A", key=f"tA_{i}", disabled=not st.session_state.first_roll_made):
                if inA: st.session_state.trickA_indices.remove(i)
                else: 
                    if inB: st.session_state.trickB_indices.remove(i)
                    st.session_state.trickA_indices.append(i)
                st.rerun()
            if c2.button("B", key=f"tB_{i}", disabled=not st.session_state.first_roll_made):
                if inB: st.session_state.trickB_indices.remove(i)
                else:
                    if inA: st.session_state.trickA_indices.remove(i)
                    st.session_state.trickB_indices.append(i)
                st.rerun()

    # --- TRICK LOGIC ---
    st.divider()
    tA_vals = sorted([st.session_state.dice[idx] for idx in st.session_state.trickA_indices])
    tB_vals = sorted([st.session_state.dice[idx] for idx in st.session_state.trickB_indices])
    
    def get_opts(dice, player):
        opts = ["1s", "2s", "3s", "4s", "5s", "6s"]
        counts = Counter(dice)
        sorted_counts = sorted(counts.values(), reverse=True)
        
        # FULL HOUSE CHECK
        if len(sorted_counts) == 2:
            if sorted_counts[0] >= 3 and sorted_counts[1] >= 2:
                opts.append("Full House")
        elif len(sorted_counts) == 1 and sorted_counts[0] == 5:
            opts.append("Full House")
            
        # STRAIGHTS
        if dice == [1, 2, 3, 4, 5]: opts.append("Low Straight")
        if dice == [2, 3, 4, 5, 6]: opts.append("High Straight")
            
        # 5 OF A KIND
        if len(sorted_counts) == 1 and sorted_counts[0] == 5:
            opts.append("5 of a Kind")
        
        return [o for o in opts if o not in st.session_state.used_categories[player]]

    # --- UI DISPLAY ---
    ca, cb = st.columns(2)
    with ca:
        st.markdown(f"### ✨ Trick A ({len(tA_vals)}/5)")
        options_a = get_opts(tA_vals, current_p)
        sel_a = st.selectbox("Assign Trick A to:", options_a, key="sA") if len(tA_vals) == 5 else None
        
    with cb:
        st.markdown(f"### ✨ Trick B ({len(tB_vals)}/5)")
        options_b = get_opts(tB_vals, current_p)
        if sel_a and sel_a in options_b:
            options_b.remove(sel_a)
        sel_b = st.selectbox("Assign Trick B to:", options_b, key="sB") if len(tB_vals) == 5 else None

    # TURN ACTIONS
    st.divider()
    col_end, col_finish = st.columns(2)
    can_end = (len(tA_vals) == 5 and len(tB_vals) == 5 and sel_a and sel_b)

    if col_end.button("✅ Confirm & Next Player", use_container_width=True, disabled=not can_end, type="primary"):
        for s, v in [(sel_a, tA_vals), (sel_b, tB_vals)]:
            if s in ["Low Straight", "High Straight", "5 of a Kind"]:
                st.session_state.trick_scores.at[s, current_p] = True
            else:
                st.session_state.master_scores.at[s, current_p] = calculate_score(v, s)
            st.session_state.used_categories[current_p].append(s)
        
        st.session_state.dice = [0] * 10
        st.session_state.first_roll_made = False
        st.session_state.trickA_indices, st.session_state.trickB_indices = [], []
        st.session_state.rolls_left = 3
        st.session_state.current_player_idx = (st.session_state.current_player_idx + 1) % len(st.session_state.players)
        st.rerun()

    if col_finish.button("🏁 Finish Game & Show Results", use_container_width=True):
        final = {}
        for p in st.session_state.players:
            total = st.session_state.master_scores[p].sum()
            if not st.session_state.trick_scores.at["Low Straight", p]: total += 15
            if not st.session_state.trick_scores.at["High Straight", p]: total += 20
            if not st.session_state.trick_scores.at["5 of a Kind", p]: total += 30
            final[p] = total
        st.session_state.final_results = final
        st.session_state.game_over = True
        save_data(stats)
        st.rerun()

# --- 7. PERMANENT SCOREBOARD ---
if st.session_state.game_active or st.session_state.game_over:
    if "master_scores" in st.session_state:
        st.divider()
        st.subheader("📊 Scorecard")
        st.data_editor(st.session_state.master_scores, use_container_width=True, disabled=True, key="m_v")
        st.data_editor(st.session_state.trick_scores, use_container_width=True, disabled=True, key="t_v")
