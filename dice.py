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
        except: return {"Players": {}}
    return {"Players": {}}

def save_data(data):
    with open(DB_FILE, "w") as f: 
        json.dump(data, f, indent=4)

stats = load_data()

# --- 3. THE "ALL WHITE" OVERRIDE CSS ---
st.markdown("""
    <style>
    .stApp, .stDataFrame, div[data-testid="stColumn"], div[data-testid="stHorizontalBlock"] {
        background-color: white !important;
        color: black !important;
    }
    h1, h2, h3, h4, p, span, label, div[data-testid="stMarkdownContainer"] p {
        color: black !important;
    }
    .stDataFrame thead tr th {
        background-color: #f8f9fa !important;
        color: black !important;
    }
    .stDataFrame tbody tr td {
        background-color: white !important;
        color: black !important;
    }

    /* MEGA DICE STYLING */
    div[data-testid="stColumn"] > div > div > button {
        height: 150px !important;
        width: 120px !important;
        background-color: white !important;
        border: 2px solid #eeeeee !important;
        border-radius: 15px !important;
    }
    div[data-testid="stColumn"] button p {
        font-size: 160px !important;
        color: black !important;
    }

    /* Small A/B Buttons */
    div[data-testid="stHorizontalBlock"] div[data-testid="stHorizontalBlock"] button {
        height: 35px !important;
        background-color: #f0f2f6 !important;
        border: 1px solid #d1d5db !important;
    }
    div[data-testid="stHorizontalBlock"] div[data-testid="stHorizontalBlock"] button p {
        font-size: 16px !important;
        color: black !important;
        font-weight: bold !important;
    }
    div[data-testid="stHorizontalBlock"] div[data-testid="stHorizontalBlock"] button[kind="primary"] {
        background-color: #ff4b4b !important;
    }
    div[data-testid="stHorizontalBlock"] div[data-testid="stHorizontalBlock"] button[kind="primary"] p {
        color: white !important;
    }

    /* BUTTON TEXT VISIBILITY (Start & Roll) */
    button[kind="primary"] p {
        color: white !important;
    }

    .bank-header {
        background-color: #f8f9fa !important;
        color: black !important;
        padding: 10px 20px !important;
        border-radius: 10px !important;
        text-align: center !important;
        border: 1px solid #dee2e6 !important;
    }
    .dice-tray { display: flex !important; justify-content: center !important; width: 100% !important; }
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

# --- 5. SETUP & PROFILE MANAGEMENT ---
if not st.session_state.game_active and not st.session_state.game_over:
    st.title("🎲 Double Cameroon")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Manage Profiles")
        new_player = st.text_input("New Player Name:")
        if st.button("➕ Create Profile") and new_player:
            if new_player not in stats["Players"]:
                stats["Players"][new_player] = {"high_score": 0}
                save_data(stats)
                st.success(f"Added {new_player}!")
                st.rerun()
        
    with col2:
        st.subheader("Start Game")
        selected = st.multiselect("Select Players for this Match:", list(stats["Players"].keys()))
        if st.button("🚀 Start Game", type="primary") and selected:
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
            if i not in locked:
                st.session_state.dice[i] = random.randint(1, 6)
        st.session_state.rolls_left -= 1
        st.session_state.first_roll_made = True
        st.rerun()

    st.write(f"**Rolls Left:** {st.session_state.rolls_left}")

    dice_faces = {0: "?", 1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}
    st.markdown('<div class="dice-tray">', unsafe_allow_html=True)
    d_cols = st.columns(10)
    for i in range(10):
        with d_cols[i]:
            inA, inB = i in st.session_state.trickA_indices, i in st.session_state.trickB_indices
            label = dice_faces[st.session_state.dice[i]] if st.session_state.first_roll_made else "?"
            st.button(label, key=f"v_{i}", disabled=True, type="primary" if (inA or inB) else "secondary")
            
            c1, c2 = st.columns(2)
            if c1.button("A", key=f"tA_{i}", disabled=not st.session_state.first_roll_made, type="primary" if inA else "secondary"):
                if inA: st.session_state.trickA_indices.remove(i)
                else: 
                    if inB: st.session_state.trickB_indices.remove(i)
                    st.session_state.trickA_indices.append(i)
                st.rerun()
            if c2.button("B", key=f"tB_{i}", disabled=not st.session_state.first_roll_made, type="primary" if inB else "secondary"):
                if inB: st.session_state.trickB_indices.remove(i)
                else:
                    if inA: st.session_state.trickA_indices.remove(i)
                    st.session_state.trickB_indices.append(i)
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # --- 7. SCORING ---
    st.divider()
    tA_vals = sorted([st.session_state.dice[idx] for idx in st.session_state.trickA_indices], reverse=True)
    tB_vals = sorted([st.session_state.dice[idx] for idx in st.session_state.trickB_indices], reverse=True)
    
    def get_opts(dice, player):
        opts = ["1s", "2s", "3s", "4s", "5s", "6s"]
        check_dice = sorted(dice)
        counts = Counter(dice)
        sorted_counts = sorted(counts.values(), reverse=True)
        if (len(sorted_counts) == 2 and sorted_counts[0] >= 3 and sorted_counts[1] >= 2) or (len(sorted_counts) == 1 and sorted_counts[0] == 5):
            opts.append("Full House")
        if check_dice == [1, 2, 3, 4, 5]: opts.append("Low Straight")
        if check_dice == [2, 3, 4, 5, 6]: opts.append("High Straight")
        if len(sorted_counts) == 1 and sorted_counts[0] == 5: opts.append("5 of a Kind")
        return [o for o in opts if o not in st.session_state.used_categories[player]]

    ca, cb = st.columns(2)
    with ca:
        st.markdown(f"<div class='bank-header'>Trick A ({len(tA_vals)}/5) &nbsp;&nbsp; {tA_vals if tA_vals else ''}</div>", unsafe_allow_html=True)
        sel_a = st.selectbox("Assign A:", get_opts(tA_vals, current_p), key="sA") if len(tA_vals) == 5 else None
    with cb:
        st.markdown(f"<div class='bank-header'>Trick B ({len(tB_vals)}/5) &nbsp;&nbsp; {tB_vals if tB_vals else ''}</div>", unsafe_allow_html=True)
        sel_b = st.selectbox("Assign B:", get_opts(tB_vals, current_p), key="sB") if len(tB_vals) == 5 else None

    ready_to_confirm = len(tA_vals) == 5 and len(tB_vals) == 5
    confirm_label = "✅ Confirm Turn" if ready_to_confirm else "Assign all dice to confirm"

    if st.button(confirm_label, use_container_width=True, disabled=not (sel_a and sel_b), type="primary"):
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
