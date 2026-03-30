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

# --- 3. CSS (MEGA DICE & STYLING) ---
st.markdown("""
    <style>
    .stApp, .stDataFrame, div[data-testid="stColumn"] { background-color: white !important; color: black !important; }
    h1, h2, h3, h4, p, span, label { color: black !important; }
    
    /* DICE BUTTONS */
    div[data-testid="stColumn"] > div > div > button[key^="v_"] {
        height: 150px !important; width: 120px !important;
        background-color: white !important; border: 2px solid #eeeeee !important; border-radius: 15px !important;
    }
    div[data-testid="stColumn"] button[key^="v_"] p { font-size: 160px !important; color: black !important; }

    /* HELD DICE (Grey) */
    button[key^="v_"][kind="primary"] { background-color: #f8f9fa !important; border: 2px solid #cccccc !important; }
    button[key^="v_"][kind="primary"] p { color: #bbbbbb !important; }

    /* A/B BUTTONS */
    div[data-testid="stHorizontalBlock"] button[key^="t"] { height: 35px !important; background-color: #f0f2f6 !important; }
    button[key^="t"][kind="primary"] { background-color: #ff4b4b !important; }
    button[key^="t"][kind="primary"] p { color: white !important; }

    /* START/ROLL BUTTONS */
    button[kind="primary"]:not([key^="v_"]):not([key^="t"]), button[key="create_profile_btn"] { background-color: #ff4b4b !important; }
    button[kind="primary"] p { color: white !important; }

    .bank-header { background-color: #f8f9fa !important; padding: 10px !important; border-radius: 10px !important; text-align: center; border: 1px solid #dee2e6; }
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
if not st.session_state.game_active and not st.session_state.game_over:
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
            st.session_state.master_scores = pd.DataFrame("", index=["1s","2s","3s","4s","5s","6s","Full House"], columns=sel)
            st.session_state.trick_scores = pd.DataFrame("", index=["Low Straight","High Straight","5 of a Kind"], columns=sel)
            st.session_state.game_active = True
            st.rerun()

# --- 6. GAMEPLAY ---
if st.session_state.game_active:
    current_p = st.session_state.players[st.session_state.current_player_idx]
    st.header(f"👤 {current_p}'s Turn")
    
    # STRICT ROLL BUTTON
    if st.button("🎲 ROLL DICE", use_container_width=True, type="primary", disabled=st.session_state.rolls_left <= 0):
        if st.session_state.rolls_left > 0:
            locked = st.session_state.trickA_indices + st.session_state.trickB_indices
            for i in range(10):
                if i not in locked: st.session_state.dice[i] = random.randint(1, 6)
            st.session_state.rolls_left -= 1
            st.session_state.first_roll_made = True
            st.rerun()

    st.write(f"**Rolls Left:** {max(0, st.session_state.rolls_left)}")

    # THE DICE TRAY (Restoring the 10 columns)
    dice_faces = {0: "?", 1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}
    d_cols = st.columns(10)
    for i in range(10):
        with d_cols[i]:
            inA, inB = i in st.session_state.trickA_indices, i in st.session_state.trickB_indices
            label = dice_faces[st.session_state.dice[i]] if st.session_state.first_roll_made else "?"
            st.button(label, key=f"v_{i}", disabled=True, type="primary" if (inA or inB) else "secondary")
            
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
    
    def get_opts(player):
        categories = ["1s","2s","3s","4s","5s","6s","Full House","Low Straight","High Straight","5 of a Kind"]
        return [c for c in categories if c not in st.session_state.used_categories[player]]

    unused_opts = get_opts(current_p)
    ca, cb = st.columns(2)
    with ca:
        st.markdown(f"<div class='bank-header'>Trick A ({len(tA_vals)}/5)</div>", unsafe_allow_html=True)
        sel_a = st.selectbox("Assign A:", ["Select Category"] + unused_opts, key="sA") if len(tA_vals) == 5 else None
    with cb:
        st.markdown(f"<div class='bank-header'>Trick B ({len(tB_vals)}/5)</div>", unsafe_allow_html=True)
        filtered_b = [opt for opt in unused_opts if opt != sel_a]
        sel_b = st.selectbox("Assign B:", ["Select Category"] + filtered_b, key="sB") if len(tB_vals) == 5 else None

    ready = sel_a and sel_b and sel_a != "Select Category" and sel_b != "Select Category" and len(tA_vals) == 5 and len(tB_vals) == 5
    label = "✅ Confirm Turn" if (len(tA_vals)==5 and len(tB_vals)==5) else "Assign all dice to confirm"

    if st.button(label, use_container_width=True, disabled=not ready, type="primary"):
        for s, v in [(sel_a, tA_vals), (sel_b, tB_vals)]:
            counts = Counter(v)
            if s in ["Low Straight", "High Straight", "5 of a Kind"]:
                if s == "Low Straight": res = "👌" if v == [1,2,3,4,5] else "25"
                elif s == "High Straight": res = "👌" if v == [2,3,4,5,6] else "30"
                elif s == "5 of a Kind":
                    if len(counts) == 1:
                        p = (6 - v[0]) * 5
                        res = "👌" if p == 0 else str(p)
                    else: res = "30"
                st.session_state.trick_scores.at[s, current_p] = res
            elif s == "Full House":
                if sorted(counts.values(), reverse=True) in [[3,2], [5]]:
                    st.session_state.master_scores.at[s, current_p] = calculate_score(v, s)
                else: st.session_state.master_scores.at[s, current_p] = "28"
            else:
                st.session_state.master_scores.at[s, current_p] = calculate_score(v, s)
            st.session_state.used_categories[current_p].append(s)
        
        st.session_state.dice, st.session_state.trickA_indices, st.session_state.trickB_indices = [0]*10, [], []
        st.session_state.rolls_left, st.session_state.first_roll_made = 3, False
        st.session_state.current_player_idx = (st.session_state.current_player_idx + 1) % len(st.session_state.players)
        st.rerun()

# --- 8. SCOREBOARD & TOTALS ---
if st.session_state.game_active or st.session_state.game_over:
    st.divider()
    totals = {}
    for p in st.session_state.players:
        m = st.session_state.master_scores[p].apply(lambda x: int(x) if str(x).isdigit() else 0).sum()
        t = st.session_state.trick_scores[p].apply(lambda x: int(x) if str(x).isdigit() else 0).sum()
        totals[p] = m + t

    st.subheader("📊 Current Penalty Totals (Lowest Wins!)")
    cols = st.columns(len(st.session_state.players))
    for idx, p in enumerate(st.session_state.players):
        cols[idx].metric(label=f"{p}'s Score", value=totals[p], delta="Winning" if totals[p] == min(totals.values()) else None)

    st.data_editor(st.session_state.master_scores, use_container_width=True, disabled=True)
    st.data_editor(st.session_state.trick_scores, use_container_width=True, disabled=True)

    if all(len(st.session_state.used_categories[p]) >= 10 for p in st.session_state.players):
        st.session_state.game_over, st.session_state.game_active = True, False

# --- 9. WINNER ---
if st.session_state.game_over:
    st.balloons()
    winner = min(totals, key=totals.get)
    st.success(f"🏆 THE WINNER IS {winner.upper()} with {totals[winner]} points!")
    if st.button("🔄 Play Again", use_container_width=True):
        st.session_state.game_over = False
        st.session_state.game_active = False
        st.rerun()
