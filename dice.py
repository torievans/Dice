# --- 3. UPDATED CSS (Pips & Centralization) ---
st.markdown("""
    <style>
    /* 1. Target the DOTS (pips) inside the massive buttons */
    div[data-testid="stColumn"] button p {
        font-size: 80px !important; /* Dot Size */
        line-height: 1 !important;
        color: black !important;
    }

    /* 2. Target the button box (The outline in your screenshot) */
    div[data-testid="stColumn"] > div > div > button {
        height: 120px !important;
        width: 120px !important;
        background-color: white !important;
        border: 2px solid #333 !important;
        border-radius: 15px !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    /* 3. Style for 'Held' dice (Grey box indicators) */
    div[data-testid="stColumn"] button[kind="primary"] {
        background-color: #333 !important;
        border-color: #000 !important;
    }
    div[data-testid="stColumn"] button[kind="primary"] p {
        color: #d3d3d3 !important;
    }

    /* 4. PROTECT THE A/B BUTTONS: Make sure they don't inherit 'giant' size */
    div[data-testid="stHorizontalBlock"] div[data-testid="stHorizontalBlock"] button {
        height: 35px !important;
        width: 100% !important;
        font-size: 16px !important;
        background-color: #f0f2f6 !important;
        border: 1px solid #d1d5db !important;
        border-radius: 6px !important;
    }
    div[data-testid="stHorizontalBlock"] div[data-testid="stHorizontalBlock"] button p {
        font-size: 16px !important;
        color: black !important;
    }

    /* 5. === CENTRALIZATION LOGIC === */
    /* Target the container for the 10 columns and center it */
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        justify-content: center !important; /* Move to the center horizontally */
        width: 100% !important;
    }

    /* Force the individual 10 columns to be narrow (tightening the grid) */
    [data-testid="stHorizontalBlock"] .st-b5.st-bd {
        min-width: 130px !important; /* Width just wide enough for the 120px die */
        max-width: 130px !important;
    }
    </style>
    """, unsafe_allow_html=True)
