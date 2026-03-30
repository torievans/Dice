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

# --- 3. THE "TOTAL WHITEOUT" OVERRIDE CSS ---
st.markdown("""
    <style>
    /* 1. TOP HEADER & GLOBAL */
    header[data-testid="stHeader"] {
        background-color: white !important;
        color: black !important;
    }
    .stApp {
        background-color: white !important;
    }
    h1, h2, h3, h4, p, span, label, li, div[data-testid="stMarkdownContainer"] p {
        color: black !important;
    }

    /* 2. SIDEBAR FIX */
    [data-testid="stSidebar"] {
        background-color: white !important;
        border-right: 1px solid #eeeeee !important;
    }
    div[data-testid="stSidebarCollapseButton"] button, 
    div[data-testid="stSidebarCloseButton"] button {
        background-color: white !important;
        color: black !important;
        border: 1px solid #eeeeee !important;
    }
    div[data-testid="stSidebarCollapseButton"] svg, 
    div[data-testid="stSidebarCloseButton"] svg {
        fill: black !important;
        color: black !important;
    }

    /* 3. MULTISELECT / DROPDOWN (THE "DARK" FIX) */
    
    /* Target the dropdown container globally */
    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"] {
        background-color: white !important;
    }

    /* Target the list items inside the dropdown */
    div[data-baseweb="popover"] li, div[data-baseweb="menu"] li, role["option"] {
        background-color: white !important;
        color: black !important;
    }

    /* Force the text inside the options to be black */
    div[data-baseweb="popover"] span, div[data-baseweb="menu"] span {
        color: black !important;
    }

    /* Hover effect for the list items */
    div[data-baseweb="popover"] li:hover, div[data-baseweb="menu"] li:hover {
        background-color: #f0f2f6 !important;
    }

    /* Selected "tags/chips" in the input box */
    span[data-baseweb="tag"] {
        background-color: #f0f2f6 !important;
        color: black !important;
    }

    /* 4. MEGA DICE STYLING */
    div[data-testid="stColumn"] > div > div > button {
        height: 150px !important;
        width: 120px !important;
        background-color: white !important;
        border: 2px solid #eeeeee !important;
        border-radius: 15px !important;
    }
    div[data-testid="stColumn"] button p { font-size: 160px !important; color: black !important; }

    /* HELD DICE */
    div[data-testid="stColumn"] button[kind="primary"] {
        background-color: #f8f9fa !important;
        border: 2px solid #cccccc !important;
    }
    div[data-testid="stColumn"] button[kind="primary"] p { color: #999999 !important; }

    /* 5. DATA TABLE STYLING */
    .stDataFrame, .stDataEditor {
        background-color: white !important;
    }
    .stDataFrame thead tr th { background-color: #f8f9fa !important; color: black !important; }
    .stDataFrame tbody tr td { background-color: white !important; color: black !important; }

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
    </style>
    """, unsafe_allow_html=True)

# --- 4. INITIALIZE STATE & SYNC ---
for key in ['game_active', 'game_over', 'first_roll_made']:
    if key not in st.session_state: st.session_state[key] = False

if 'dice' not in st.session_state: st.session_state.dice = [0] * 10
if 'trickA_indices' not in st.session_state: st.session_state.trickA_indices = []
if 'trickB_indices' not in st.session_state: st.session_state.trickB_indices = []
if 'rolls_left' not in st.session_state: st.session_state.rolls_left = 3
if 'current_player_idx' not in st.session_state: st.session_state.current_player_idx = 0
if 'used_categories' not in st.session_state: st.session_state.used_categories = {}
if 'game_mode' not in st.session_state: st.session_state.game_mode = "Play Dice"

def sync_manual_scores():
    if "main_table" in st.session_state:
        edits = st.session_state["main_table"].get("edited_rows", {})
        for row_idx, col_map in edits.items():
            for col_name, val in col_map.items():
                cat_name = st.session_state.master_scores.index[row_idx]
                st.session_state.master_scores.at[cat_name, col_name] = val
        
        for p in st.session_state.players:
            st.session_state.used_categories[p] = [
                cat for cat in st.session_state.master_scores.index 
                if str(st.session_state.master_scores.at[cat, p]).strip() != ""
            ]

sync_manual_scores()

# --- SIDEBAR (Mode Selection) ---
with st.sidebar:
    st.header("⚙️ Game Settings")
    st.session_state.game_mode = st.radio(
        "Mode Selector:", 
        ["Play Dice", "Score Only"], 
        index=0 if st.session_state.game_mode == "Play Dice" else 1
    )

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
            rows = ["1s", "2s", "3s", "4s", "5s", "6s", "Full House", "Low Straight", "High Straight", "5 of a Kind"]
            st.session_state.master_scores = pd.DataFrame("", index=rows, columns=selected)
            st.session_state.game_active = True
            st.rerun()

# --- 6 & 7. GAMEPLAY & SCORING ---
if st.session_state.game_active and not st.session_state.game_over:
    if st.session_state.game_mode == "Play Dice":
        current_p = st.session_state.players[st.session_state.current_player_idx]
        st.header(f"👤 {current_p}'s Turn")
        
        if st.button("🎲 ROLL DICE", use_container_width=True, type="primary", key="main_roll_btn", disabled=st.session_state.rolls_left <= 0):
            if st.session_state.rolls_left > 0:
                locked = st.session_state.trickA_indices + st.session_state.trickB_indices
                for i in range(10):
                    if i not in locked:
                        st.session_state.dice[i] = random.randint(1, 6)
                st.session_state.rolls_left -= 1
                st.session_state.first_roll_made = True
                st.rerun()

        st.write(f"**Rolls Left:** {max(0, st.session_state.rolls_left)}")

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

        st.divider()
        tA_vals = sorted([st.session_state.dice[idx] for idx in st.session_state.trickA_indices])
        tB_vals = sorted([st.session_state.dice[idx] for idx in st.session_state.trickB_indices])
        
        def get_opts(player):
            categories = ["1s", "2s", "3s", "4s", "5s", "6s", "Full House", "Low Straight", "High Straight", "5 of a Kind"]
            return [c for c in categories if c not in st.session_state.used_categories[player]]

        unused_opts = get_opts(current_p)
        ca, cb = st.columns(2)
        with ca:
            st.markdown(f"<div class='bank-header'>Trick A ({len(tA_vals)}/5) &nbsp;&nbsp; {tA_vals if tA_vals else ''}</div>", unsafe_allow_html=True)
            sel_a = st.selectbox("Assign A:", ["Select Category"] + unused_opts, key="sA") if len(tA_vals) == 5 else None
        with cb:
            st.markdown(f"<div class='bank-header'>Trick B ({len(tB_vals)}/5) &nbsp;&nbsp; {tB_vals if tB_vals else ''}</div>", unsafe_allow_html=True)
            filtered_b = [opt for opt in unused_opts if opt != sel_a]
            sel_b = st.selectbox("Assign B:", ["Select Category"] + filtered_b, key="sB") if len(tB_vals) == 5 else None

        full_tray = (len(tA_vals) == 5 and len(tB_vals) == 5)
        cats_selected = (sel_a and sel_b and sel_a != "Select Category" and sel_b != "Select Category")
        
        if full_tray and cats_selected:
            confirm_label, ready = "✅ Confirm Turn", True
        elif full_tray:
            confirm_label, ready = "Please select categories for both tricks", False
        else:
            confirm_label, ready = "Assign all 10 dice to banks to continue", False

        if st.button(confirm_label, use_container_width=True, disabled=not ready, type="primary", key="confirm_turn_btn"):
            for s, v in [(sel_a, tA_vals), (sel_b, tB_vals)]:
                counts = Counter(v)
                if s == "Low Straight": res = "👌" if (v == [1, 2, 3, 4, 5]) else "25"
                elif s == "High Straight": res = "👌" if (v == [2, 3, 4, 5, 6]) else "30"
                elif s == "5 of a Kind":
                    if len(counts) == 1:
                        p = (6 - v[0]) * 5
                        res = "👌" if p == 0 else str(p)
                    else: res = "30"
                elif s == "Full House":
                    sorted_counts = sorted(counts.values(), reverse=True)
                    if sorted_counts == [3, 2] or sorted_counts == [5]: res = calculate_score(v, s)
                    else: res = "28"
                else: res = calculate_score(v, s)
                
                st.session_state.master_scores.at[s, current_p] = res
                st.session_state.used_categories[current_p].append(s)
            
            st.session_state.dice, st.session_state.trickA_indices, st.session_state.trickB_indices = [0]*10, [], []
            st.session_state.rolls_left, st.session_state.first_roll_made = 3, False
            st.session_state.current_player_idx = (st.session_state.current_player_idx + 1) % len(st.session_state.players)
            st.rerun()
    else:
        st.header("📝 Manual Score Entry")
        st.info("""Physical Dice Mode: Enter scores directly into the table below.  
Penalty points for not achieving certain tricks are as follows:  
**Full House** - 28  
**Low Straight** - 15  
**High Straight** - 20  
**5 of a Kind** - 30""")

# --- 8 & 9. TOTALS, WINNER, AND SCOREBOARD ---
if st.session_state.game_active or st.session_state.game_over:
    st.divider()
    
    totals = {}
    for p in st.session_state.players:
        totals[p] = st.session_state.master_scores[p].apply(
            lambda x: int(x) if str(x).isdigit() else 0
        ).sum()

    all_finished = all(len(st.session_state.used_categories[p]) >= 10 for p in st.session_state.players)
    if all_finished and not st.session_state.game_over:
        st.balloons()
        st.session_state.game_over = True
        st.session_state.game_active = False

    if st.session_state.game_over:
        winner_name = min(totals, key=totals.get)
        st.markdown(f"""
            <div style="background-color:#ff4b4b; padding:30px; border-radius:15px; text-align:center; margin-bottom:25px;">
                <h1 style="color:white; margin:0;">🏆 THE WINNER IS {winner_name.upper()}! 🏆</h1>
                <p style="color:white; font-size:24px; margin:10px 0;">Final Penalty Score: {totals[winner_name]}</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("🔄 Play Again", use_container_width=True, type="primary"):
            st.session_state.game_over = False
            st.session_state.game_active = False
            st.rerun()

    st.subheader("📊 Score (Lowest Wins!)")
    t_cols = st.columns(len(st.session_state.players))
    min_score = min(totals.values())
    for idx, p in enumerate(st.session_state.players):
        t_cols[idx].metric(label=f"{p}'s Score", value=totals[p], 
                           delta="⭐ LEADING" if totals[p] == min_score else None)

    st.divider()
    
    is_manual = st.session_state.game_mode == "Score Only"
    st.data_editor(
        st.session_state.master_scores, 
        use_container_width=True, 
        disabled=not is_manual, 
        key="main_table"
    )
