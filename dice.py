import streamlit as st
import pandas as pd
import json
import os

# --- Configuration & Data Persistence ---
st.set_page_config(page_title="Double Cameroon Scorer", layout="wide")
DB_FILE = "cameroon_stats.json"

def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

stats = load_data()

# --- Sidebar: Setup, Reset & Analytics ---
with st.sidebar:
    st.title("📊 Stats & Settings")
    
    # 1. Performance Section (Moved to Sidebar)
    if stats and any(len(d['scores']) > 0 for d in stats.values()):
        with st.expander("🏆 Career Leaderboard", expanded=True):
            perf_data = []
            chart_dict = {}
            for name, data in stats.items():
                scores = data.get("scores", [])
                if scores:
                    avg = sum(scores) / len(scores)
                    perf_data.append({
                        "Player": name,
                        "Wins": data["wins"],
                        "Avg": round(avg, 1)
                    })
                    chart_dict[name] = scores
            
            summary_df = pd.DataFrame(perf_data).sort_values(by="Wins", ascending=False)
            st.table(summary_df.set_index("Player"))

        with st.expander("📈 Score Trends"):
            df_trends = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in chart_dict.items()]))
            df_trends.index = [f"G{i+1}" for i in range(len(df_trends))]
            st.line_chart(df_trends)
    else:
        st.info("Complete a game to see stats here!")

    st.divider()
    
    # 2. Controls
    if st.session_state.get('game_active'):
        if st.button("🚫 Quit Current Game", type="primary", use_container_width=True):
            st.session_state.game_active = False
            st.rerun()
    
    if st.button("🗑️ Reset All Data", type="secondary", use_container_width=True):
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
            st.session_state.clear()
            st.rerun()

# --- Main Game Logic ---
st.title("🎲 Double Cameroon Scorer")

if 'game_active' not in st.session_state:
    st.session_state.game_active = False

if not st.session_state.game_active:
    st.subheader("Start New Game")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("### 1. Create Profile")
        new_player = st.text_input("Enter name:", placeholder="e.g. Alice")
        if st.button("Add Profile") and new_player:
            if new_player not in stats:
                stats[new_player] = {"scores": [], "wins": 0}
                save_data(stats)
                st.success(f"Added {new_player}!")
                st.rerun()

    with col2:
        st.write("### 2. Select Players")
        all_players = list(stats.keys())
        selected_players = st.multiselect("Who is playing? (Max 6)", all_players, max_selections=6)
        
        if st.button("🚀 Start Game") and len(selected_players) > 0:
            st.session_state.players = selected_players
            categories = ["1s", "2s", "3s", "4s", "5s", "6s", "Full House", "Low Straight", "High Straight", "5 of a Kind"]
            st.session_state.score_grid = pd.DataFrame(0, index=categories, columns=selected_players)
            st.session_state.game_active = True
            st.session_state.game_finished = False
            st.rerun()

else:
    # --- Active Game Screen ---
    st.subheader("📝 Live Scorecard")
    
    edited_df = st.data_editor(st.session_state.score_grid, use_container_width=True)
    
    # Calculate Totals
    totals = edited_df.sum()
    st.divider()
    
    # Display Score Metrics
    cols = st.columns(len(st.session_state.players))
    for i, player in enumerate(st.session_state.players):
        cols[i].metric(player, int(totals[player]))

    # Finish Logic
    if not st.session_state.get('game_finished'):
        if st.button("🏁 Finish & Save Game", type="primary", use_container_width=True):
            winner = totals.idxmax()
            st.balloons()
            
            for player in st.session_state.players:
                if player not in stats: stats[player] = {"scores": [], "wins": 0}
                stats[player]["scores"].append(int(totals[player]))
                if player == winner:
                    stats[player]["wins"] += 1
            
            save_data(stats)
            st.session_state.game_finished = True
            st.success(f"🏆 {winner} wins with {int(totals[winner])}!")
            st.rerun()
    else:
        # Show "New Game" button only after finishing
        if st.button("🔄 Start a New Game", use_container_width=True):
            st.session_state.game_active = False
            st.session_state.game_finished = False
            st.rerun()
