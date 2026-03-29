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
    
    # 1s through 6s: Penalty = (Dice that are NOT the target) * target_value
    target_map = {"1s": 1, "2s": 2, "3s": 3, "4s": 4, "5s": 5, "6s": 6}
    if category in target_map:
        target = target_map[category]
        score = sum(1 for d in dice if d != target) * target
        return "-" if score == 0 else str(score)

    # Full House: Best 3rd + Best 2nd. 
    # Logic: Penalty = ((6 - highest_triplet_val) * 3) + ((5 - highest_pair_val) * 2)
    if category == "Full House":
        sorted_counts = sorted(counts.items(), key=lambda x: (x[1], x[0]), reverse=True)
        # Attempt to find a triplet and a pair, otherwise take worst case
        val3 = sorted_counts[0][0] if len(sorted_counts) > 0 else 1
        val2 = sorted_counts[1][0] if len(sorted_counts) > 1 else (2 if val3 != 2 else 1)
        score = ((6 - val3) * 3) + ((5 - val2) * 2)
        return "-" if score == 0 else str(score)

    # Straights and 5 of a Kind: If criteria not met, score max penalty
    if category == "Low Straight":
        return "-" if dice == [1, 2, 3, 4, 5] else "25" # Max penalty for missing LS
    if category == "High Straight":
        return "-" if dice == [2, 3, 4, 5, 6] else "30" # Max penalty for missing HS
    if category == "5 of a Kind":
        return "-" if len(counts) == 1 else "50" # Max penalty for missing 5K
        
    return "0"

# --- 2. CONFIG & DATA ---
st.set_page_config(page_title="Double Cameroon", layout="wide")
DB_FILE = "cameroon_stats.json"

def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: return json.load(f)
        except: return {"Players": {}}
    return {"Players": {}}

def save_data(data):
    with open(DB_FILE, "w") as f: 
        json.dump(data, f, indent=4)

stats = load_data()

# --- 3. CSS ---
st.markdown("""
    <style>
    .stApp, .stDataFrame, div[data-testid="stColumn"] { background-color: white !important; color: black !important; }
    h1, h2, h3, h4, p, span, label { color: black !important; }
    
    /* Dice buttons */
    div[data-testid="stColumn"] > div > div > button {
        height: 150px !important; width: 120px !important;
        background-color: white !important; border: 2px solid #eeeeee !important; border-radius: 15px !important;
    }
    div[data-testid="stColumn"] button p { font-size: 160px !important; color: black !important; }

    /* Held State */
    div[data-testid="stColumn"] button[kind="primary"] { background-color: #f8f9fa !important; border: 2px solid #cccccc !important; }
    div[data-testid="stColumn"] button[kind="primary"] p { color: #999999 !important; }

    /* A/B Buttons */
    div[data-testid="stHorizontalBlock"] div[data-testid="stHorizontalBlock"] button { height: 35px !important; background-color: #f0f2f6 !important; }
    div[data-testid="stHorizontalBlock"] div[data-testid="stHorizontalBlock"] button[kind="primary"] { background-color: #ff4b4b !important; }
    div[data-testid="stHorizontalBlock"] div[data-testid="stHorizontalBlock"] button[kind="primary"] p { color: white !important; }

    /* Action Buttons */
    button[kind="primary"]:not([key^="v_"]):not([key^="t"]), button[key="create_profile_btn"] { background-color: #ff4b4b !important; }
    button[kind="primary"] p { color: white !important; }

    .bank-header { background-color: #f8f9fa !important; color: black !important; padding: 10px !important; border-radius: 10px !important; text-align: center; border: 1px solid #dee2e6; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. STATE ---
for key in ['game_active', 'game_over', 'first_roll_made']:
    if key not in st.session_state: st.session_state[key] = False
if 'dice' not in st.session_state: st.session_state.dice = [0] * 10
if 'trickA_indices' not in st.session_state: st.session_state.trickA_indices = []
if 'trickB_indices' not in st.session_state: st.session_state.trickB_indices = []
if 'rolls_left' not in st.session_state: st.session_state.rolls_left = 3
if 'current_player_idx' not in st.session_state: st.session_state.current_player_idx = 0
if 'used_categories' not in st.session_state: st.session_state.used_categories = {}

# --- 5. SETUP ---
if not st.session_state.game_active:
    st.title("🎲 Double Cameroon")
    c1, c2 = st.columns(2)
    with c1:
        new_p = st.text_input("New Player Name:")
        if st.button("➕ Create Profile", key="create_profile_btn") and new_p:
            if new_p not in stats["Players"]:
                stats["Players"][new_p] = {"high_score": 0}; save_data(stats); st.rerun()
    with c2:
        sel = st.multiselect("Select Players:", list(stats["Players"].keys()))
        if st.button("🚀 Start Game", type="primary") and sel:
            st.session_state.players = sel
            st.session_state.used_categories = {p: [] for p in sel}
            rows = ["1s", "2s", "3s", "4s", "5s", "6s", "Full House", "Low Straight", "High Straight", "5 of a Kind"]
            st.session_state.master_scores = pd.DataFrame("", index=rows, columns=sel)
            st.session_state.game_active = True
            st.rerun()

# --- 6. GAMEPLAY ---
if st.session_state.game_active:
    current_p = st.session_state.players[st.session_state.current_player_idx]
    st.header(f"👤 {current_p}'s Turn")
    
    if st.button("🎲 ROLL DICE", use_container_width=True, type="primary", disabled=st.session_state.rolls_left == 0):
        locked = st.session_state.trickA_indices + st.session_state.trickB_indices
        for i in range(10):
            if i not in locked: st.session_state.dice[i] = random.randint(1, 6)
        st.session_state.rolls_left -= 1
        st.session_state.first_roll_made = True
        st.rerun()

    st.write(f"**Rolls Left:** {st.session_state.rolls_left}")

    dice_faces = {0: "?", 1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}
    d_cols = st.columns(10)
    for i in range(10):
        with d_cols[i]:
            inA, inB = i in st.session_state.trickA_indices, i in st.session_state.trickB_indices
            st.button(dice_faces[st.session_state.dice[i]], key=f"v_{i}", disabled=True, type="primary" if (inA or inB) else "secondary")
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

    # --- 7. SCORING ---
    st.divider()
    tA_vals = sorted([st.session_state.dice[idx] for idx in st.session_state.trickA_indices])
    tB_vals = sorted([st.session_state.dice[idx] for idx in st.session_state.trickB_indices])
    
    # NEW LOGIC: Always allow selection of any UNUSED category for penalties
    def get_all_unused(player):
        categories = ["1s", "2s", "3s", "4s", "5s", "6s", "Full House", "Low Straight", "High Straight", "5 of a Kind"]
        return [c for c in categories if c not in st.session_state.used_categories[player]]

    ca, cb = st.columns(2)
    unused_opts = get_all_unused(current_p)
    
    with ca:
        st.markdown(f"<div class='bank-header'>Trick A ({len(tA_vals)}/5)</div>", unsafe_allow_html=True)
        sel_a = st.selectbox("Assign A:", ["Select Category"] + unused_opts, key="sA") if len(tA_vals) == 5 else None
    with cb:
        st.markdown(f"<div class='bank-header'>Trick B ({len(tB_vals)}/5)</div>", unsafe_allow_html=True)
        # Ensure we don't pick the same category for both tricks in one turn
        filtered_b = [opt for opt in unused_opts if opt != sel_a]
        sel_b = st.selectbox("Assign B:", ["Select Category"] + filtered_b, key="sB") if len(tB_vals) == 5 else None

    ready = sel_a and sel_b and sel_a != "Select Category" and sel_b != "Select Category"
    if st.button("✅ Confirm Turn", use_container_width=True, disabled=not ready, type="primary"):
        for s, v in [(sel_a, tA_vals), (sel_b, tB_vals)]:
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
    st.table(st.session_state.master_scores)
