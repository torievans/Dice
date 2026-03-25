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

# --- 3. CUSTOM STYLING (Freestanding Dice) ---
st.markdown("""
    <style>
    /* Targeting the dice buttons to remove the 'box' look */
    div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"] > div > div > button {
        height: 80px !important;
        width: 80px !important;
        font-size: 65px !important; /* Larger pips */
        line-height: 1 !important;
        padding: 0 !important;
        background-color: transparent !important; /* Remove box background */
        border: none !important; /* Remove box borders */
        box-shadow: none !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    
    /* Available Dice: Standard Black dots */
    button[kind="secondary"] {
        color: black !important;
    }
    
    /* Held Dice: Grey dots to indicate they are "set" */
    button[kind="primary"] {
        color: #bbbbbb !important;
    }

    /* Keep A/B buttons as standard small functional boxes */
    div[data-testid="stHorizontalBlock"] div[data-testid="stHorizontalBlock"] button {
        height: 30px !important;
        width: 100% !important;
        font-size: 14px !important;
        background-color: #f0f2f6 !important;
        border: 1px solid #d1d5db !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ... inside your gameplay loop ...

# Dice Faces Mapping
    dice_faces = {0: "?", 1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}

    d_cols = st.columns(10)
    for i in range(10):
        with d_cols[i]:
            inA, inB = i in st.session_state.trickA_indices, i in st.session_state.trickB_indices
            is_held = inA or inB
            
            # Show dots only if rolled
            label = dice_faces[st.session_state.dice[i]] if st.session_state.first_roll_made else "?"
            
            # We use 'primary' style for Held and 'secondary' for Available
            # The CSS above handles making these transparent/borderless
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

    # --- DICE DISPLAY ---
    # This dictionary must be aligned with the code above it
    dice_faces = {0: "?", 1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}

    d_cols = st.columns(10)
    for i in range(10):
        with d_cols[i]:
            inA, inB = i in st.session_state.trickA_indices, i in st.session_state.trickB_indices
            is_held = inA or inB
            
            # Use dots if rolled, otherwise show "?"
            val = st.session_state.dice[i]
            label = dice_faces[val] if st.session_state.first_roll_made else "?"
            
            # The CSS we added makes 'primary' (held) look grey 
            # and 'secondary' (available) look black/transparent
            st.button(label, key=f"v_{i}", disabled=True, type="primary" if is_held else "secondary")
            
            # Assignment buttons (A/B)
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

# --- 7. PERMANENT SCOREBOARD ---
if st.session_state.game_active or st.session_state.game_over:
    if "master_scores" in st.session_state:
        st.divider()
        st.subheader("📊 Scorecard")
        st.data_editor(st.session_state.master_scores, use_container_width=True, disabled=True, key="m_v")
        st.data_editor(st.session_state.trick_scores, use_container_width=True, disabled=True, key="t_v")
