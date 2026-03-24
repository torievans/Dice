import streamlit as st
import random

st.set_page_config(page_title="Double Cameroon Scorer", layout="centered")
st.title("🎲 Double Cameroon")

# --- Initialize Session State ---
if 'dice' not in st.session_state:
    st.session_state.dice = [random.randint(1, 6) for _ in range(10)]
    st.session_state.held = [False] * 10
    st.session_state.rolls_left = 3
    st.session_state.scores = {cat: None for cat in ["1s", "2s", "3s", "4s", "5s", "6s", "Little Cameroon", "Big Cameroon", "5-of-a-kind", "Any Sum"]}

# --- Sidebar: Game Status ---
st.sidebar.header("Game Stats")
total_score = sum(v for v in st.session_state.scores.values() if v is not None)
st.sidebar.metric("Total Score", total_score)
st.sidebar.write(f"Rolls left this turn: {st.session_state.rolls_left}")

# --- Dice Section ---
st.subheader("Your 10 Dice")
cols = st.columns(10)
for i in range(10):
    with cols[i]:
        st.button(f"{st.session_state.dice[i]}", key=f"die_{i}", 
                  type="primary" if st.session_state.held[i] else "secondary")
        st.session_state.held[i] = st.checkbox("Hold", value=st.session_state.held[i], key=f"hold_{i}")

if st.button("Roll Dice") and st.session_state.rolls_left > 0:
    for i in range(10):
        if not st.session_state.held[i]:
            st.session_state.dice[i] = random.randint(1, 6)
    st.session_state.rolls_left -= 1
    st.rerun()

# --- Scoring Section ---
st.divider()
st.subheader("Assign Your Groups")
st.info("Pick 5 dice for Category A and 5 for Category B.")

# Helper to let user pick dice for groups
hand_a_indices = st.multiselect("Select 5 dice for Hand A", range(10), max_selections=5)
hand_b_indices = [i for i in range(10) if i not in hand_a_indices]

if len(hand_a_indices) == 5:
    hand_a = [st.session_state.dice[i] for i in hand_a_indices]
    hand_b = [st.session_state.dice[i] for i in hand_b_indices]
    
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"Hand A: {hand_a}")
        cat_a = st.selectbox("Assign Hand A to:", [c for c, v in st.session_state.scores.items() if v is None], key="cat_a")
    with col2:
        st.write(f"Hand B: {hand_b}")
        cat_b = st.selectbox("Assign Hand B to:", [c for c, v in st.session_state.scores.items() if v is None and c != cat_a], key="cat_b")

    if st.button("Submit Turn"):
        st.session_state.scores[cat_a] = calculate_score(hand_a, cat_a)
        st.session_state.scores[cat_b] = calculate_score(hand_b, cat_b)
        # Reset for next round
        st.session_state.dice = [random.randint(1, 6) for _ in range(10)]
        st.session_state.held = [False] * 10
        st.session_state.rolls_left = 3
        st.success("Scores recorded!")
        st.rerun()
