"""
Streamlit DFS Optimizer - CLEAN SIMPLE VERSION
"""

import streamlit as st
import pandas as pd
from config import CONTEST_STRUCTURES
from main import DFSOptimizer

st.set_page_config(page_title="DFS Optimizer", page_icon="🏈", layout="wide")

st.title("🏈 DFS Lineup Optimizer")

# Sidebar
st.sidebar.header("⚙️ Settings")

contest_type = st.sidebar.selectbox(
    "Strategy",
    options=['single_entry_grinder', 'small_gpp', 'mid_gpp', 'milly_maker'],
    format_func=lambda x: {
        'single_entry_grinder': '🎯 Single-Entry Grinder',
        'small_gpp': '🏆 Multi-Entry GPP',
        'mid_gpp': '📊 Mid-GPP',
        'milly_maker': '💰 Milly Maker'
    }[x]
)

num_lineups = st.sidebar.slider("Lineups", 1, 50, 20)

# Show strategy info
rules = CONTEST_STRUCTURES[contest_type]
st.sidebar.markdown("---")
st.sidebar.markdown(f"**Target Own:** {rules['ownership_target_avg'][0]}-{rules['ownership_target_avg'][1]}%")
st.sidebar.markdown(f"**QB Own:** {rules['qb_ownership_target'][0]}-{rules['qb_ownership_target'][1]}%")

# Main
uploaded_file = st.file_uploader("Upload CSV", type=['csv'])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    if 'Player' in df.columns:
        df = df.rename(columns={'Player': 'Name', 'Ownership %': 'Ownership'})
    
    st.success(f"✅ {len(df)} players loaded")
    df.to_csv('/tmp/player_pool.csv', index=False)
    use_demo = False
else:
    st.info("Upload Stokastic CSV")
    use_demo = True

if st.button("🚀 Generate Lineups", type="primary"):
    with st.spinner("Building..."):
        try:
            optimizer = DFSOptimizer(contest_type=contest_type, entry_fee=100)
            
            # Simple call without locks
            if use_demo:
                results, lineups = optimizer.run('demo', num_lineups=num_lineups)
            else:
                results, lineups = optimizer.run('/tmp/player_pool.csv', num_lineups=num_lineups)
            
            if lineups and len(lineups) > 0:
                st.session_state['results'] = results  
                st.session_state['lineups'] = lineups
                st.session_state['contest_type'] = contest_type
                st.success(f"✅ {len(lineups)} lineups built")
            else:
                st.error("Failed to build lineups")
                
        except Exception as e:
            st.error(f"Error: {e}")

# Display
if 'lineups' in st.session_state:
    st.markdown("---")
    lineups = st.session_state['lineups']
    strategy = st.session_state.get('contest_type', 'single_entry_grinder')
    
    for i, lineup in enumerate(lineups[:10]):
        players = lineup.get('players', [])
        proj = lineup.get('total_projection', 0)
        own = lineup.get('avg_ownership', 0)
        
        with st.expander(f"Lineup {i+1} - {proj:.1f} pts | {own:.1f}% own"):
            # Show players
            for p in players:
                pos = p.get('PositionSlot', p.get('Position'))
                st.text(f"{pos:6} {p.get('Name'):25} ${p.get('Salary'):5,} {p.get('Projection'):5.1f} {p.get('Ownership'):5.1f}%")
            
            # Validation for single-entry grinder
            if strategy == 'single_entry_grinder':
                st.markdown("---")
                
                qb = next((p for p in players if p.get('Position') == 'QB'), None)
                core_rb = next((p for p in players if p.get('Position') == 'RB' and 18 <= p.get('Ownership', 0) <= 28), None)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if qb and 3 <= qb.get('Ownership', 100) <= 8:
                        st.success(f"✅ QB {qb.get('Ownership', 0):.1f}%")
                    else:
                        st.warning(f"⚠️ QB {qb.get('Ownership', 0) if qb else 0:.1f}%")
                with col2:
                    if core_rb:
                        st.success("✅ Core RB")
                    else:
                        st.warning("⚠️ No core RB")
                with col3:
                    if 10 <= own <= 13:
                        st.success(f"✅ {own:.1f}%")
                    else:
                        st.info(f"📊 {own:.1f}%")
