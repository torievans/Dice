import streamlit as st

# --- 1. PAGE CONFIG ---
st.set_page_config(layout="wide")

# --- 2. UPDATED CSS (Pips & Centralization) ---
st.markdown("""
    <style>
    /* 1. Target the DOTS (pips) inside the massive buttons */
    div[data-testid="stColumn"] button p {
        font-size: 80px !important; /* Dot Size */
        line-height: 1 !important;
        color: black !important;
    }

    /* 2. Target the button box (The outline) */
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

    /* 4. PROTECT THE UI BUTTONS: Make sure regular buttons don't turn into giant dice */
    /* We target buttons NOT inside the dice columns specifically */
    div[data-testid="stHeader"] button, 
    div[data-testid="stSidebar"] button {
        height: auto !important;
        width: auto !important;
    }

    /* 5. === CENTRALIZATION LOGIC === */
    /* This centers the entire block of columns on the page */
    div[data-testid="stHorizontalBlock"] {
        justify-content: center !important;
    }
    
    /* Ensure the columns don't stretch too wide, keeping the dice tight */
    div[data-testid="stColumn"] {
        flex: 0 1 130px !important;
        min-width: 130px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. APP LOGIC / GRID ---
st.title("🎲 Tenzi Dice Roller")

# Create 10 columns for the dice
cols = st.columns(10)

# Example state: let's pretend some are held (primary) and some are rolling (secondary)
for i, col in enumerate(cols):
    with col:
        # We use a simple unicode dot for the 'pip'
        # In a real app, you'd use st.session_state to track which are 'Held'
        is_held = i % 3 == 0  # Just for demonstration
        
        button_type = "primary" if is_held else "secondary"
        
        if st.button("●", key=f"die_{i}", type=button_type):
            pass 

st.divider()

# Controls area (Small buttons)
c1, c2, c3 = st.columns([1,1,1])
with c2:
    if st.button("Roll All Dice", use_container_width=True):
        st.toast("Rolling...")
