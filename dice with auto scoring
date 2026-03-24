import streamlit as st
import pandas as pd
import json
import os
import random
from collections import Counter

# --- [Core Scoring Logic - Full House Penalty Version] ---
def get_score_value(dice, category):
    dice.sort()
    counts = Counter(dice)
    val_list = sorted(counts.items(), key=lambda x: x[1], reverse=True)

    if category == "1s": return dice.count(1) * 1
    if category == "2s": return dice.count(2) * 2
    if category == "3s": return dice.count(3) * 3
    if category == "4s": return dice.count(4) * 4
    if category == "5s": return dice.count(5) * 5
    if category == "6s": return dice.count(6) * 6
    if category == "Full House":
        if len(val_list) == 2 and val_list[0][1] == 3 and val_list[1][1] == 2:
            three_val, two_val = val_list[0][0], val_list[1][0]
            return ((6 - three_val) * 3) + ((5 - two_val) * 2)
        return 0
    if category == "Low Straight": return 21 if dice == [1, 2, 3, 4, 5] else 0
    if category == "High Straight": return 30 if dice == [2, 3, 4, 5, 6] else 0
    if category == "5 of a Kind": return 50 if 5 in list(counts.values()) else 0
    return 0

# --- Configuration & Data ---
st.set_page_config(page_title="Double Cameroon", layout="wide")
DB_FILE = "cameroon_stats.json"

def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: return json.load(f)
        except: return {}
    return {}

stats = load_data()

# --- Sidebar Version Toggle ---
with st.sidebar:
    st.title("⚙️ Game Settings")
    auto_mode = st.checkbox("Enable Auto-Scoring", value=True, help="Toggle the automated 'Apply' dropdowns")
    st.divider()
    if st.button("🚫 Quit Current Game"):
        st.session_state.game_active = False
        st.rerun()

# --- Initialize Session State (Same as before) ---
if 'game_active' not in st.session_state: st.session_state.game_active = False

# [Start Screen Logic here...]

# --- Active Game Area ---
if st.session_state.game_active:
    current_p = st.session_state.players[st.session_state.current_player_idx]
    st.header(f"👤 {current_p}'s Turn")
    
    # --- 1. DICE TRAY ---
    # (Existing Dice Tray / Trick A & B Logic here)
    # ...

    # --- 2. OPTIONAL AUTO-SCORER ---
    if auto_mode:
        st.divider()
        tA_vals = sorted([st.session_state.dice[idx] for idx in st.session_state.trickA_indices])
        tB_vals = sorted([st.session_state.dice[idx] for idx in st.session_state.trickB_indices])
        
        col_autoA, col_autoB = st.columns(2)
        
        # Function to only show valid "Trick" options
        def get_valid_opts(dice):
            opts = ["1s", "2s", "3s", "4s", "5s", "6s"]
            if get_score_value(dice, "Full House") > 0: opts.append("Full House")
            if get_score_value(dice, "Low Straight") > 0: opts.append("Low Straight")
            if get_score_value(dice, "High Straight") > 0: opts.append("High Straight")
            if get_score_value(dice, "5 of a Kind") > 0: opts.append("5 of a Kind")
            return opts

        with col_autoA:
            st.markdown(f"### ✨ Trick A ({len(tA_vals)}/5): `{tA_vals}`")
            if len(tA_vals) == 5:
                cat_a = st.selectbox("Assign A to:", get_valid_opts(tA_vals), key="sel_a")
                if st.button("Apply A"):
                    val = get_score_value(tA_vals, cat_a)
                    if cat_a in ["Low Straight", "High Straight", "5 of a Kind"]:
                        st.session_state.scores["Tricks"].at[cat_a, current_p] = True
                    else: st.session_state.scores[cat_a].at[cat_a, current_p] = val
                    st.rerun()

        with col_autoB:
            st.markdown(f"### ✨ Trick B ({len(tB_vals)}/5): `{tB_vals}`")
            if len(tB_vals) == 5:
                cat_b = st.selectbox("Assign B to:", get_valid_opts(tB_vals), key="sel_b")
                if st.button("Apply B"):
                    val = get_score_value(tB_vals, cat_b)
                    if cat_b in ["Low Straight", "High Straight", "5 of a Kind"]:
                        st.session_state.scores["Tricks"].at[cat_b, current_p] = True
                    else: st.session_state.scores[cat_b].at[cat_b, current_p] = val
                    st.rerun()
    else:
        # Simple view if Auto-Scoring is OFF
        st.divider()
        c1, c2 = st.columns(2)
        tA_vals = sorted([st.session_state.dice[idx] for idx in st.session_state.trickA_indices])
        tB_vals = sorted([st.session_state.dice[idx] for idx in st.session_state.trickB_indices])
        c1.markdown(f"### ✨ Trick A: `{tA_vals}`")
        c2.markdown(f"### ✨ Trick B: `{tB_vals}`")

    # --- 3. ACTIONS & SCORECARD ---
    # (Rest of your existing scorecard and End Turn logic)
