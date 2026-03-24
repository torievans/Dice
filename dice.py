# --- TRICK SELECTION LOGIC ---
    st.divider()
    tA_vals = sorted([st.session_state.dice[idx] for idx in st.session_state.trickA_indices])
    tB_vals = sorted([st.session_state.dice[idx] for idx in st.session_state.trickB_indices])
    
    def get_opts(dice, player):
        # 1s-6s and Full House are always options if not used
        base_opts = ["1s", "2s", "3s", "4s", "5s", "6s", "Full House"]
        
        # Pattern-based options: Only added if the dice actually match
        if dice == [1, 2, 3, 4, 5]:
            base_opts.append("Low Straight")
        if dice == [2, 3, 4, 5, 6]:
            base_opts.append("High Straight")
        if len(set(dice)) == 1 and len(dice) == 5:
            base_opts.append("5 of a Kind")
            
        # Filter: Remove any category the player has already recorded a score for
        return [o for o in base_opts if o not in st.session_state.used_categories[player]]

    ca, cb = st.columns(2)
    with ca:
        st.markdown(f"### ✨ Trick A ({len(tA_vals)}/5): `{tA_vals}`")
        options_a = get_opts(tA_vals, current_p)
        # We only show the selectbox if the trick is full (5 dice)
        sel_a = st.selectbox("Assign Trick A to:", options_a, key="sA") if len(tA_vals) == 5 else None
        
    with cb:
        st.markdown(f"### ✨ Trick B ({len(tB_vals)}/5): `{tB_vals}`")
        options_b = get_opts(tB_vals, current_p)
        # Filter out what was selected in A so you can't pick the same thing for both in one turn
        if sel_a and sel_a in options_b:
            options_b.remove(sel_a)
        sel_b = st.selectbox("Assign Trick B to:", options_b, key="sB") if len(tB_vals) == 5 else None
