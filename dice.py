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
        score = sum(1 for d in dice if d != target) * target
        return "👌" if score == 0 else str(score)
    
    if category == "Full House":
        sorted_items = sorted(counts.items(), key=lambda x: (x[1], x[0]), reverse=True)
        three_val = sorted_items[0][0]
        two_val = sorted_items[1][0] if len(sorted_items) > 1 else three_val
        score = ((6 - three_val) * 3) + ((5 - two_val) * 2)
        return "👌" if score == 0 else str(score)
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
    .stDataFrame thead tr th { background-color: #f8f9fa !important; color: black !important; }
    .stDataFrame tbody tr td { background-color: white !important; color: black !important; }

    /* MEGA DICE STYLING */
    div[data-testid="stColumn"] > div > div > button {
        height: 150px !important;
        width: 120px !important;
        background-color: white !important;
        border: 2px solid #eeeeee !important;
        border-radius: 15px !important;
    }
    div[data-testid="stColumn"] button p { font-size: 160px !important; color: black !important; }

    /* HELD DICE FUNCTIONALITY */
    div[data-testid="stColumn"] button[kind="primary"] {
        background-color: #f8f9fa !important;
        border: 2px solid #cccccc !important;
    }
    div[data-testid="stColumn"] button[kind="primary"] p { color: #999999 !important; }

    /* Small A/B Buttons */
    div[data-testid="stHorizontalBlock"] div[data-testid="stHorizontalBlock"] button {
        height: 35px !important;
        background-color: #f0f2f6 !important;
        border: 1px solid #d1d5db !important;
    }
    div[data-testid="stHorizontalBlock"] div[data-testid="stHorizontalBlock"] button p {
        font-size: 16px !important; color: black !important; font-weight: bold !important;
    }
    div[data-testid="stHorizontalBlock"] div[data-testid="stHorizontalBlock"] button[kind="primary"] {
        background-color: #ff4b4b !important;
    }
    div[data-testid="stHorizontalBlock"] div[data-testid="stHorizontalBlock"] button[kind="primary"] p { color: white !important; }

    button[kind="primary"] p { color: white !important; }

    button[key="create_profile_btn"] {
        background-color: #ff4b4b !important;
        border: none !important;
    }
    button[key="create_profile_btn"] p { color: white !important; }

    .bank-header {
        background-color: #f8f9fa !important; color: black !important; padding: 10px 20px !important;
        border-radius: 10px !important; text-align: center !important; border: 1px solid #dee2e6 !important;
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

# --- 5. SETUP ---
if not st.session_state.game_active and not st.session_state.game_over:
    st.title("🎲 Double Cameroon")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Manage Profiles")
        new_player = st.text_input("New Player Name:")
        if st.button("➕ Create Profile", key="create_profile_btn") and new_player:
            if new_player not in stats["Players"]:
                stats["Players"][new_player] = {"high_score": 0}
                save_data(stats)
                st.rerun()
    with col2:
        st.subheader("Start Game")
        selected = st.multiselect("Select Players:", list(stats["Players"].keys()))
        if st.button("🚀 Start Game", type="primary") and selected:
            st.session_state.players = selected
            st.session_state.current_player_idx = 0
            st.session_state.used_categories = {p: [] for p in selected}
            rows = ["1s", "2s", "3s", "4s", "5s", "6s", "Full House"]
            st.session_state.master_scores = pd.DataFrame("", index=rows, columns=selected)
            st.session_state.trick_scores = pd.DataFrame("", index=["Low Straight", "High Straight", "5 of a Kind"], columns=selected)
            st.session_state.game_active = True
            st.rerun()

# --- 6. SHOW GAMEPLAY ---
if st.session_state.game_active and not st.session_state.game_over:
    current_p = st.session_state.players[st.session_state.current_player_idx]
    
    # Check if this player has finished all categories
    total_needed = len(st.session_state.master_scores.index) + len(st.session_state.trick_scores.index)
    if len(st.session_state.used_categories[current_p]) >= total_needed:
        # Move to next player or end game
        if st.session_state.current_player_idx < len(st.session_state.players) - 1:
            st.session_state.current_player_idx += 1
            st.rerun()
        else:
            st.session_state.game_over = True
            st.rerun()

    st.header(f"👤 {current_p}'s Turn")
    
    # STRICT ROLL BUTTON
    # 1. 'disabled' attribute stops the UI click
    # 2. The 'if' check inside stops the logic if clicks overlap
    if st.button("🎲 ROLL DICE", use_container_width=True, type="primary", disabled=st.session_state.rolls_left <= 0):
        if st.session_state.rolls_left > 0:  # SERVER-SIDE GUARD
            locked = st.session_state.trickA_indices + st.session_state.trickB_indices
            for i in range(10):
                if i not in locked:
                    st.session_state.dice[i] = random.randint(1, 6)
            st.session_state.rolls_left -= 1
            st.session_state.first_roll_made = True
            st.rerun()

    st.write(f"**Rolls Left:** {max(0, st.session_state.rolls_left)}") # Prevents showing negative numbers

   # --- 7. SCORING ---
    st.divider()
    # Sort dice values for easier logic checks
    tA_vals = sorted([st.session_state.dice[idx] for idx in st.session_state.trickA_indices])
    tB_vals = sorted([st.session_state.dice[idx] for idx in st.session_state.trickB_indices])
    
    def get_opts(player):
        # Shows all unused categories so player can choose to 'burn' one for penalty points
        categories = ["1s", "2s", "3s", "4s", "5s", "6s", "Full House", "Low Straight", "High Straight", "5 of a Kind"]
        return [c for c in categories if c not in st.session_state.used_categories[player]]

    unused_opts = get_opts(current_p)
    ca, cb = st.columns(2)
    
    with ca:
        st.markdown(f"<div class='bank-header'>Trick A ({len(tA_vals)}/5) &nbsp;&nbsp; {tA_vals if tA_vals else ''}</div>", unsafe_allow_html=True)
        sel_a = st.selectbox("Assign A:", ["Select Category"] + unused_opts, key="sA") if len(tA_vals) == 5 else None
    with cb:
        st.markdown(f"<div class='bank-header'>Trick B ({len(tB_vals)}/5) &nbsp;&nbsp; {tB_vals if tB_vals else ''}</div>", unsafe_allow_html=True)
        # Prevent picking the same category for both banks in one turn
        filtered_b = [opt for opt in unused_opts if opt != sel_a]
        sel_b = st.selectbox("Assign B:", ["Select Category"] + filtered_b, key="sB") if len(tB_vals) == 5 else None

    # Logic for button appearance and readiness
    full_tray = (len(tA_vals) == 5 and len(tB_vals) == 5)
    confirm_label = "✅ Confirm Turn" if full_tray else "Assign all dice to confirm"
    ready = full_tray and sel_a and sel_b and sel_a != "Select Category" and sel_b != "Select Category"

    if st.button(confirm_label, use_container_width=True, disabled=not ready, type="primary"):
        for s, v in [(sel_a, tA_vals), (sel_b, tB_vals)]:
            display_val = ""
            counts = Counter(v)
            
            if s in ["Low Straight", "High Straight", "5 of a Kind"]:
                if s == "Low Straight":
                    is_correct = (v == [1, 2, 3, 4, 5])
                    display_val = "👌" if is_correct else "25"
                elif s == "High Straight":
                    is_correct = (v == [2, 3, 4, 5, 6])
                    display_val = "👌" if is_correct else "30"
                elif s == "5 of a Kind":
                    if len(counts) == 1:
                        penalty = (6 - v[0]) * 5
                        display_val = "👌" if penalty == 0 else str(penalty)
                    else:
                        display_val = "30"
                st.session_state.trick_scores.at[s, current_p] = display_val
                
            elif s == "Full House":
                # Check if it is actually a Full House (3 of one, 2 of another)
                # Note: 5 of a kind also technically counts as a Full House in many rulesets, 
                # but here we follow the 3+2 structure.
                sorted_counts = sorted(counts.values(), reverse=True)
                if sorted_counts == [3, 2] or sorted_counts == [5]:
                    # Successfully achieved: Use the Penalty Engine logic
                    # Engine returns "👌" or the calculated string penalty
                    display_val = calculate_score(v, s)
                else:
                    # Failed attempt: not a Full House structure
                    display_val = "28"
                st.session_state.master_scores.at[s, current_p] = display_val
                
            else:
                # Standard scoring for 1s-6s
                st.session_state.master_scores.at[s, current_p] = calculate_score(v, s)
            
            # Mark category as used
            st.session_state.used_categories[current_p].append(s)
        
        # Reset turn state for next player
        st.session_state.dice = [0]*10
        st.session_state.trickA_indices, st.session_state.trickB_indices = [], []
        st.session_state.rolls_left = 3
        st.session_state.first_roll_made = False
        st.session_state.current_player_idx = (st.session_state.current_player_idx + 1) % len(st.session_state.players)
        st.rerun()
# --- 8. SCOREBOARD ---
if st.session_state.game_active:
    st.divider()
    st.subheader("📊 Scorecard")
    st.data_editor(st.session_state.master_scores, use_container_width=True, disabled=True)
    st.data_editor(st.session_state.trick_scores, use_container_width=True, disabled=True)
