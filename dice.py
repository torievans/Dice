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
    with open(DB_FILE, "u") as f: # Use standard write mode
        json.dump(data, f, indent=4)

stats = load_data()

# --- 3. UPDATED CSS (Final Centering Fix) ---
st.markdown("""
    <style>
    /* 1. Force White Page Background */
    .stApp {
        background-color: white !important;
    }

    /* 2. Mega Dice Styling */
    div[data-testid="stColumn"] button {
        height: 150px !important;
        width: 120px !important;
        background-color: white !important;
        border: 2px solid #eeeeee !important;
        border-radius: 15px !important;
        opacity: 1 !important;
        margin: 0 auto !important; /* Center the die in the column */
        display: block !important;
    }

    div[data-testid="stColumn"] button p {
        font-size: 160px !important;
        line-height: 1 !important;
        color: black !important;
        margin: 0 !important;
        opacity: 1 !important;
    }

    /* 3. THE CENTER POINT ALIGNMENT FIX */
    /* Target the container holding A and B */
    div[data-testid="stHorizontalBlock"] div[data-testid="stHorizontalBlock"] {
        width: 120px !important;      /* Match the die width */
        display: flex !important;      /* Flexbox for side-by-side */
        flex-direction: row !important;
        justify-content: center !important; /* Center buttons within this 120px */
        align-items: center !important;
        gap: 4px !important;           /* Space between A and B */
        margin: 0 auto !important;     /* CRITICAL: Centers the whole pair under the die */
        padding: 0 !important;
    }

    /* Set fixed widths for the A/B slots to keep the 'center gap' dead center */
    div[data-testid="stHorizontalBlock"] div[data-testid="stHorizontalBlock"] > div {
        width: 55px !important; 
        flex: 0 0 55px !important;
        padding: 0 !important;
        margin: 0 !important;
    }

    div[data-testid="stHorizontalBlock"] div[data-testid="stHorizontalBlock"] button {
        height: 35px !important;
        width: 100% !important;
        background-color: #f0f2f6 !important;
        border: 1px solid #d1d5db !important;
        padding: 0 !important;
    }

    div[data-testid="stHorizontalBlock"] div[data-testid="stHorizontalBlock"] button p {
        font-size: 16px !important;
        color: black !important;
        font-weight: bold !important;
    }
    
    /* Red Selected Buttons */
    div[data-testid="stHorizontalBlock"] div[data-testid="stHorizontalBlock"] button[kind="primary"] {
        background-color: #ff4b4b !important;
        border: 1px solid #d33c3c !important;
    }
    div[data-testid="stHorizontalBlock"] div[data-testid="stHorizontalBlock"] button[kind="primary"] p {
        color: white !important;
    }

    /* 4. Bank Headers */
    .bank-header {
        background-color: #262730 !important;
        color: white !important;
        padding: 10px 20px !important;
        border-radius: 10px !important;
        margin-bottom: 10px !important;
        font-weight: bold !important;
        text-align: center !important;
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

# --- 5. NAVIGATION ---
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
    st.title("🎲 Double Cameroon")
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

    # --- THE CENTRALIZED DICE TRAY ---
    dice_faces = {0: "?", 1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}
    
    # ADD THE CENTRALIZATION WRAPPER
    st.markdown('<div class="dice-tray">', unsafe_allow_html=True)
    
    d_cols = st.columns(10)
    for i in range(10):
        with d_cols[i]:
            inA = i in st.session_state.trickA_indices
            inB = i in st.session_state.trickB_indices
            is_held = inA or inB
            
            # 1. Huge Pips (Displayed on a neutral 'primary' button that fades)
            label = dice_faces[st.session_state.dice[i]] if st.session_state.first_roll_made else "?"
            st.button(label, key=f"v_{i}", disabled=True, type="primary" if is_held else "secondary")
            
            # 2. SELECTION BUTTONS (A/B)
            # The type="primary" logic will now trigger the CSS red color
            c1, c2 = st.columns(2)
            
            # Button A: Set type="primary" if selected for Trick A
            if c1.button("A", key=f"tA_{i}", disabled=not st.session_state.first_roll_made, type="primary" if inA else "secondary"):
                if inA: st.session_state.trickA_indices.remove(i)
                else: 
                    if inB: st.session_state.trickB_indices.remove(i)
                    st.session_state.trickA_indices.append(i)
                st.rerun()
                
            # Button B: Set type="primary" if selected for Trick B
            if c2.button("B", key=f"tB_{i}", disabled=not st.session_state.first_roll_made, type="primary" if inB else "secondary"):
                if inB: st.session_state.trickB_indices.remove(i)
                else:
                    if inA: st.session_state.trickA_indices.remove(i)
                    st.session_state.trickB_indices.append(i)
                st.rerun()

    # CLOSE THE CENTRALIZATION WRAPPER
    st.markdown('</div>', unsafe_allow_html=True)

    # --- 7. SCORING ---
    st.divider()
    tA_vals = sorted([st.session_state.dice[idx] for idx in st.session_state.trickA_indices], reverse=True)
    tB_vals = sorted([st.session_state.dice[idx] for idx in st.session_state.trickB_indices], reverse=True)
    
    ca, cb = st.columns(2)
    with ca:
        # Wrapped in a div with our new 'bank-header' class
        st.markdown(f"<div class='bank-header'>Trick A ({len(tA_vals)}/5) &nbsp;&nbsp; {tA_vals if tA_vals else ''}</div>", unsafe_allow_html=True)
        sel_a = st.selectbox("Assign A:", get_opts(tA_vals, current_p), key="sA") if len(tA_vals) == 5 else None
    with cb:
        # Wrapped in a div with our new 'bank-header' class
        st.markdown(f"<div class='bank-header'>Trick B ({len(tB_vals)}/5) &nbsp;&nbsp; {tB_vals if tB_vals else ''}</div>", unsafe_allow_html=True)
        sel_b = st.selectbox("Assign B:", get_opts(tB_vals, current_p), key="sB") if len(tB_vals) == 5 else None
        
# --- 8. SCOREBOARD ---
if st.session_state.game_active or st.session_state.game_over:
    st.divider()
    st.subheader("📊 Scorecard")
    st.data_editor(st.session_state.master_scores, use_container_width=True, disabled=True)
    st.data_editor(st.session_state.trick_scores, use_container_width=True, disabled=True)
