import streamlit as st
import random
import pandas as pd

# --- Initialize Game State for Banking ---
if 'dice' not in st.session_state:
    st.session_state.dice = [random.randint(1, 6) for _ in range(10)]
if 'bank_assignments' not in st.session_state:
    st.session_state.bank_assignments = [0] * 10 # 0=None, 1=Bank A, 2=Bank B
if 'rolls_left' not in st.session_state:
    st.session_state.rolls_left = 3

st.title("🎲 Double Cameroon: The Dice Tray")

# --- 1. THE DICE TRAY ---
st.subheader(f"Rolls Left: {st.session_state.rolls_left}")
cols = st.columns(10)

for i in range(10):
    with cols[i]:
        # Visual indicator of which bank the die is in
        label = f"⚀ {st.session_state.dice[i]}" # Simplified dice icon
        
        # Color coding buttons based on bank
        btn_type = "secondary"
        if st.session_state.bank_assignments[i] == 1: btn_type = "primary" # Bank A
        if st.session_state.bank_assignments[i] == 2: btn_type = "secondary" # Bank B (or use custom CSS)

        if st.button(label, key=f"die_{i}", type=btn_type, use_container_width=True):
            # Cycle through: Available -> Bank A -> Bank B -> Available
            st.session_state.bank_assignments[i] = (st.session_state.bank_assignments[i] + 1) % 3
            st.rerun()
        
        # Checkbox for holding during rolls
        st.checkbox("Hold", key=f"hold_{i}")

# --- 2. THE BANKS ---
st.divider()
bank_a_cols, bank_b_cols = st.columns(2)

with bank_a_cols:
    st.markdown("### 🏦 Bank A")
    bank_a_dice = [st.session_state.dice[i] for i in range(10) if st.session_state.bank_assignments[i] == 1]
    st.write(f"Dice: {bank_a_dice}")
    if len(bank_a_dice) > 5:
        st.error("Too many dice in Bank A! (Max 5)")
    elif len(bank_a_dice) == 5:
        st.success("Bank A Ready")

with bank_b_cols:
    st.markdown("### 🏦 Bank B")
    bank_b_dice = [st.session_state.dice[i] for i in range(10) if st.session_state.bank_assignments[i] == 2]
    st.write(f"Dice: {bank_b_dice}")
    if len(bank_b_dice) > 5:
        st.error("Too many dice in Bank B! (Max 5)")
    elif len(bank_b_dice) == 5:
        st.success("Bank B Ready")

# --- 3. AUTO-SCORING HINT ---
if len(bank_a_dice) == 5 and len(bank_b_dice) == 5:
    st.info("Both banks are full! Scroll down to record these sets in your scorecard.")
    
    # Check for Cameroon Hands automatically
    def check_cameroon(dice):
        d = sorted(dice)
        if d == [1, 2, 3, 4, 5]: return "Little Cameroon (21 pts)"
        if d == [2, 3, 4, 5, 6]: return "Big Cameroon (30 pts)"
        if len(set(d)) == 1: return "5-of-a-Kind (50 pts)"
        return "No Special Trick"

    st.write(f"**Bank A Analysis:** {check_cameroon(bank_a_dice)}")
    st.write(f"**Bank B Analysis:** {check_cameroon(bank_b_dice)}")
