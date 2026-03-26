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
            with open(DB_FILE, "r") as f: return json.load(f)
        except: return {}
    return {}

def save_data(data):
    with open(DB_FILE, "w") as f: json.dump(data, f, indent=4)

stats = load_data()

# --- 3. UPDATED CSS (Centralized Dice & UI Fix) ---
st.markdown("""
    <style>
    /* 1. Dice Button Styling */
    div[data-testid="stColumn"] button p {
        font-size: 80px !important;
        line-height: 1 !important;
        color: black !important;
    }
    div[data-testid="stColumn"] > div > div > button {
        height: 120px !important;
        width: 120px !important;
        background-color: white !important;
        border: 2px solid #333 !important;
        border-radius: 15px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    div[data-testid="stColumn"] button[kind="primary"] {
        background-color: #333 !important;
        border-color: #000 !important;
    }
    div[data-testid="stColumn"] button[kind="primary"] p {
        color: #d3d3d3 !important;
    }

    /* 2. Small A/B Buttons */
    div[data-testid="stHorizontalBlock"] div[data-testid="stHorizontalBlock"] button {
        height: 35px !important;
        width: 100% !important;
        background-color: #f0f2f6 !important;
        border: 1px solid #d1d5db !important;
    }

    /* 3. Centralize ONLY the dice block */
    .dice-container {
        display: flex !important;
        justify-content: center !important;
        width: 100% !important;
        margin-bottom: 20px;
    }
    
    /* 4. Bank Styling */
    .bank-box {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #dee2e6;
        text-align: center;
        min-height: 80px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. INITIALIZE STATE ---
if 'game_active' not in st.session_state: st.session_state.game_active = False
if 'game_over' not in st.session_state: st.session_state.game_over = False
if 'first_roll_made' not in st.session_state: st.session_state.first_roll_made = False
if 'dice' not in st.session_state: st.session_state.dice = [0] * 10
if 'trickA_indices' not in st.session_state: st.session_state.trickA_indices = []
if 'trickB_indices' not in st.session_state: st.session_state.trickB_indices = []
if 'rolls_left' not in st.session_state: st.session_state.rolls_left = 3
if 'current_player_idx' not in st.session_state: st.session_state.current_player_idx = 0
if 'used_categories' not in st.session_state: st.session_state.used_categories = {}

# --- 5. NAVIGATION (PROFILE CREATION) ---
if st.session_state.game_over:
    st.title("🏆 Final Standings")
    sorted_results = sorted(st.session_state.final_results.items(), key=lambda x: x[1])
    res_df = pd.DataFrame(sorted_results, columns=['Player', 'Final Score'])
    st.table(res_df.set_index('Player'))
    if st.button("🔄 Start New Game", use_container_width=True):
        st.session_state.game_over = False
        st.session_state.game_active = False
        st.rerun()

elif not st.session_state.game_active:
    st.markdown("<h1 style='text-align: center;'>🎲 Double Cameroon</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Create Profile")
        new_p = st.text_input("Enter Player Name:")
        if st.button("Add Profile") and new_p:
            if new_p not in stats:
                stats[new_p] = {"scores": [], "wins": 0}
                save_data(stats)
                st.success(f"Profile {new_p} created!")
                st.rerun()
    with c2:
        st.subheader("Start Game")
        selected = st.multiselect("Select Players", list(stats.keys()))
        if st.button("🚀 Start Game") and selected:
            st.session_state.players = selected
            st.session_state.current_player_idx = 0
            st.session_state.used_categories = {p: [] for p in selected}
            rows = ["1s", "2s", "3s", "4s", "5s", "6s", "Full House"]
            st.session_state.master_scores = pd.DataFrame(0, index=rows, columns=selected)
            st.session_state.trick_scores = pd.DataFrame(False, index=["Low Straight", "High Straight", "5 of a Kind"], columns=selected)
            st.session_state.game_active = True
            st.rerun()

# --- 6. SHOW GAMEPLAY ---
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

    # --- THE TRICK BANK (DYNAMIC PREVIEW) ---
    st.write("### 🏦 Trick Bank")
    tA_vals = sorted([st.session_state.dice[idx] for idx in st.session_state.trickA_indices])
    tB_vals = sorted([st.session_state.dice[idx] for idx in st.session_state.trickB_indices])
    
    bank_col1, bank_col2 = st.columns(2)
    with bank_col1:
        st.markdown(f"<div class='bank-box'><b>Trick A:</b><br><span style='font-size: 24px;'>{tA_vals}</span></div>", unsafe_allow_html=True)
    with bank_col2:
        st.markdown(f"<div class='bank-box'><b>Trick B:</b><br><span style='font-size: 24px;'>{tB_vals}</span></div>", unsafe_allow_html=True)

    st.divider()

    # --- THE DICE TRAY ---
    dice_faces = {0: "?", 1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}
    d_cols = st.columns(10)
    for i in range(10):
        with d_cols[i]:
            inA, inB = i in st.session_state.trickA_indices, i in st.session_state.trickB_indices
            label = dice_faces[st.session_state.dice[i]] if st.session_state.first_roll_made else "?"
            st.button(label, key=f"v_{i}", disabled=True, type="primary" if (inA or inB) else "secondary")
            
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

    # --- 7. SCORING DROPDOWNS ---
    st.divider()
    def get_opts(dice, player):
        opts = ["1s", "2s", "3s", "4s", "5s", "6s"]
        counts = Counter(dice)
        sorted_counts = sorted(counts.values(), reverse=True)
        if (len(sorted_counts) == 2 and sorted_counts[0] >= 3 and sorted_counts[1] >= 2) or (len(sorted_counts) == 1 and sorted_counts[0] == 5):
            opts.append("Full House")
        if dice == [1, 2, 3, 4, 5]: opts.append("Low Straight")
        if dice == [2, 3, 4, 5, 6]: opts.append("High Straight")
        if len(sorted_counts) == 1 and sorted_counts[0] == 5: opts.append("5 of a Kind")
        return [o for o in opts if o not in st.session_state.used_categories[player]]

    ca, cb = st.columns(2)
    with ca:
        sel_a = st.selectbox("Assign Trick A to:", get_opts(tA_vals, current_p), key="sA") if len(tA_vals) == 5 else None
    with cb:
        opts_b = get_opts(tB_vals, current_p)
        if sel_a and sel_a in opts_b: opts_b.remove(sel_a)
        sel_b = st.selectbox("Assign Trick B to:", opts_b, key="sB") if len(tB_vals) == 5 else None

    if st.button("✅ Confirm Turn", use_container_width=True, disabled=not (sel_a and sel_b), type="primary"):
        for s, v in [(sel_a, tA_vals), (sel_b, tB_vals)]:
            if s in ["Low Straight", "High Straight", "5 of a Kind"]:
                st.session_state.trick_scores.at[s, current_p] = True
            else:
                st.session_state.master_scores.at[s, current_p] = calculate_score(v, s)
            st.session_state.used_categories[current_p].append(s)
        st.session_state.dice, st.session_state.trickA_indices, st.session_state.trickB_indices = [0]*10, [], []
        st.session_state.rolls_left, st.session_state.first_roll_made = 3, False
        st.session_state.current_player_idx = (st.session_state.current_player_idx + 1) % len(st.session_state.players)
        st.rerun()

# --- 8. SCOREBOARD ---
if st.session_state.game_active:
    st.divider()
    st.subheader("📊 Scorecard")
    st.data_editor(st.session_state.master_scores, use_container_width=True, disabled=True)
    st.data_editor(st.session_state.trick_scores, use_container_width=True, disabled=True)
