st.session_state.first_roll_made = False
st.session_state.current_player_idx = (st.session_state.current_player_idx + 1) % len(st.session_state.players)
st.rerun()
# --- 8. SCOREBOARD ---
if st.session_state.game_active:
        
# --- 8. SCOREBOARD & TOTALS ---
if st.session_state.game_active or st.session_state.game_over:
st.divider()
    st.subheader("📊 Scorecard")
    
    # CALCULATE RUNNING TOTALS
    # We convert strings and emojis to 0, then sum the numeric penalties
    totals = {}
    for p in st.session_state.players:
        # Sum Master Table (1s-6s, Full House)
        m_vals = st.session_state.master_scores[p].apply(lambda x: int(x) if str(x).isdigit() else 0).sum()
        # Sum Trick Table (Straights, 5 of a Kind)
        t_vals = st.session_state.trick_scores[p].apply(lambda x: int(x) if str(x).isdigit() else 0).sum()
        totals[p] = m_vals + t_vals

    # DISPLAY RUNNING TOTALS
    st.subheader("📊 Current Penalty Totals (Lowest Wins!)")
    cols = st.columns(len(st.session_state.players))
    for idx, p in enumerate(st.session_state.players):
        cols[idx].metric(label=f"{p}'s Score", value=totals[p], delta="Winning" if totals[p] == min(totals.values()) else None)

st.data_editor(st.session_state.master_scores, use_container_width=True, disabled=True)
st.data_editor(st.session_state.trick_scores, use_container_width=True, disabled=True)

    # CHECK FOR END OF GAME
    # Total categories per player = 7 (Master) + 3 (Tricks) = 10
    all_finished = all(len(st.session_state.used_categories[p]) >= 10 for p in st.session_state.players)
    
    if all_finished:
        st.session_state.game_over = True
        st.session_state.game_active = False

# --- 9. WINNER ANNOUNCEMENT & PLAY AGAIN ---
if st.session_state.game_over:
    st.balloons()
    # Find player with lowest score
    winner = min(totals, key=totals.get)
    
    st.markdown(f"""
        <div style="background-color:#ff4b4b; padding:20px; border-radius:15px; text-align:center;">
            <h1 style="color:white; margin:0;">🏆 THE WINNER IS {winner.upper()}! 🏆</h1>
            <p style="color:white; font-size:20px;">Final Penalty Score: {totals[winner]}</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    if st.button("🔄 Play Again (New Match)", use_container_width=True, type="primary"):
        # Reset all game-related state but keep player profiles
        st.session_state.game_over = False
        st.session_state.game_active = False
        st.session_state.dice = [0]*10
        st.session_state.trickA_indices = []
        st.session_state.trickB_indices = []
        st.session_state.rolls_left = 3
        st.session_state.current_player_idx = 0
        st.session_state.used_categories = {}
        st.rerun()
