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
        sorted_items = sorted(counts.items(), key=lambda x: (x[1], x[0]), reverse=True)
        three_val = sorted_items[0][0]
        two_val = sorted_items[1][0] if len(sorted_items) > 1 else three_val
        return ((6 - three_val) * 3) + ((5 - two_val) * 2)
    return 0 

# --- 2. CONFIG & DATA ---
st.set_page_config(page_title="Double Cameroon", layout="wide")
DB_FILE = "cameroon_stats.json"

def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                data = json.load(f)
                return data if "Players" in data else {"Players": {}}
        except: return {"Players": {}}
    return {"Players": {}}

def save_data(data):
    with open(DB_FILE, "w") as f: 
        json.dump(data, f, indent=4)

stats = load_data()

# --- 3. THE DEEP-TARGET CSS ---
st.markdown("""
    <style>
    /* 1. Force White Background */
    .stApp { background-color: white !important; }
    h1, h2, h3, h4, p, span, label { color: black !important; }

    /* 2. MEGA DICE: Target the button AND the paragraph inside it */
    /* Target specifically buttons with keys starting with 'v_' */
    div[data-testid="stColumn"] button[key*="v_"], 
    button[key*="v_"] {
        height: 150px !important;
        width: 120px !important;
        min-width: 120px !important;
        background-color: white !important;
        border: 2px solid #eeeeee !important;
        border-radius: 15px !important;
        padding: 0 !important;
    }

    /* THE CRITICAL FIX: Target the 'p' tag inside the die button */
    button[key*="v_"] p {
        font-size: 160px !important;
        line-height: 150px !important; /* Match button height to center vertically */
        height: 150px !important;
        display: block !important;
        color: black !important;
        margin: 0 !important;
    }

    /* 3. A/B BUTTONS: Keep them small and functional */
    button[key*="tA_"], button[key*="tB_"] {
        height: 35px !important;
        background-color: #f0f2f6 !important;
        border: 1px solid #d1d5db !important;
    }
    button[key*="tA_"] p, button[key*="tB_"] p {
        font-size: 16px !important;
        color: black !important;
        font-weight: bold !important;
    }

    /* 4. ACTION BUTTONS: Red background with white text */
    button[kind="primary"] {
        background-color: #ff4b4b !important;
    }
    button[kind="primary"] p {
        color: white !important;
        font-size: 16px !important;
    }

    /* 5. SETUP BUTTONS: Ensure 'Create Profile' is normal size */
    /* Target buttons that ARE NOT dice and ARE NOT A/B toggles */
    button[kind="secondary"]:not([key*="v_"]):not([key*="tA_"]):not([key*="tB_"]) {
        height: auto !important;
        padding: 8px 16px !important;
    }

    .bank-header {
        background-color: #f8f9fa !important;
        color: black !important;
        padding: 10px 20px !important;
        border-radius: 10px !important;
        text-align: center !important;
        border: 1px solid #dee2e6 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. INITIALIZE STATE ---
for key in ['game_active', 'game_over', 'first_roll_made']:
    if key not in st.session_state: st.session_state[key] = False
if 'dice' not in st.session_state: st.session_state.dice = [0] * 10
if 'trickA_indices' not in st.session_state: st.session_state.trickA_indices = []
if 'trickB_indices' not in st.session_state: st.session_state.trickB_indices = []
if 'rolls_left' not in st.session_state: st.session_state.rolls_left = 3
if 'current_player_idx' not in st.session_state: st.session_state.current_player_idx = 0
if 'used_categories' not in st.session_state: st.session_state.used_categories = {}

# --- 5. SETUP ---
if not st.session_state.game_active and not st.session_state.game_over:
    st.title("🎲 Double Cameroon")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Manage Profiles")
        new_p = st.text_input("New Player Name:")
        if st.button("➕ Create Profile") and new_p:
            if new_p not in stats["Players"]:
                stats["Players"][new_p] = {"high_score": 0}
                save_data(stats)
                st.rerun()
    with c2:
        st.subheader("Start Game")
        p_list = list(stats["Players"].keys())
        sel = st.multiselect("Select Players:", p_list)
        if st.button("🚀 Start Game", type="primary") and sel:
            st.session_state.players = sel
            st.session_state.current_player_idx = 0
            st.session_state.used_categories = {p: [] for p in sel}
            rows = ["1s", "2s", "3s", "4s", "5s", "6s", "Full House"]
            st.session_state.master_scores = pd.DataFrame(0, index=rows, columns=sel)
            st.session_state.trick_scores = pd.DataFrame(False, index=["Low Straight", "High Straight", "5 of a Kind"], columns=sel)
            st.session_state.game_active = True
            st.rerun()

# --- 6. GAMEPLAY ---
if st.session_state.game_active and not st.session_state.game_over:
    current_p = st.session_state.players[st.session_state.current_player_idx]
    st.header(f"👤 {current_p}'s Turn")
    
    if st.button("🎲 ROLL DICE", use_container_width=True, type="primary", disabled=st.session_state.rolls_left == 0):
        locked = st.session_state.trickA_indices + st.session_state.trickB_indices
        for i in range(10):
            if i not in locked: st.session_state.dice[i] = random.randint(1, 6)
        st.session_state.rolls_left -= 1
        st.session_state.first_roll_made = True
        st.rerun()

    dice_faces = {0: "?", 1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}
    d_cols = st.columns(10)
    for i in range(10):
        with d_cols[i]:
            inA, inB = i in st.session_state.trickA_indices, i in st.session_state.trickB_indices
            label = dice_faces[st.session_state.dice[i]] if st.session_state.first_roll_made else "?"
            # DIE
            st.button(label, key=f"v_{i}", disabled=True)
            
            c1, c2 = st.columns(2)
            # A/B
            if c1.button("A", key=f"tA_{i}", type="primary" if inA else "secondary", disabled=not st.session_state.first_roll_made):
                if inA: st.session_state.trickA_indices.remove(i)
                else: 
                    if inB: st.session_state.trickB_indices.remove(i)
                    st.session_state.trickA_indices.append(i)
                st.rerun()
            if c2.button("B", key=f"tB_{i}", type="primary" if inB else "secondary", disabled=not st.session_state.first_roll_made):
                if inB: st.session_state.trickB_indices.remove(i)
                else:
                    if inA: st.session_state.trickA_indices.remove(i)
                    st.session_state.trickB_indices.append(i)
                st.rerun()

    st.divider()
    tA_vals = sorted([st.session_state.dice[idx] for idx in st.session_state.trickA_indices], reverse=True)
    tB_vals = sorted([st.session_state.dice[idx] for idx in st.session_state.trickB_indices], reverse=True)
    
    # ... (Rest of scoring and scoreboard logic remains the same) ...
