"""
Streamlit DFS Optimizer - STREAMLINED VERSION
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
                st.success(f"✅ {len(lineups)} lineups built")
            else:
                st.error("Failed to build lineups")
                
        except Exception as e:
            st.error(f"Error: {e}")

# Display
if 'lineups' in st.session_state:
    st.markdown("---")
    lineups = st.session_state['lineups']
    
    for i, lineup in enumerate(lineups[:10]):
        players = lineup.get('players', [])
        proj = lineup.get('total_projection', 0)
        own = lineup.get('avg_ownership', 0)
        
        with st.expander(f"Lineup {i+1} - {proj:.1f} pts | {own:.1f}% own"):
            for p in players:
                pos = p.get('PositionSlot', p.get('Position'))
                st.text(f"{pos:6} {p.get('Name'):25} ${p.get('Salary'):5,} {p.get('Projection'):5.1f} {p.get('Ownership'):5.1f}%")

st.sidebar.markdown(f"**Target Ownership:** {rules['ownership_target_avg'][0]}-{rules['ownership_target_avg'][1]}%")
st.sidebar.markdown(f"**QB Ownership:** {rules['qb_ownership_target'][0]}-{rules['qb_ownership_target'][1]}%")
st.sidebar.markdown(f"**Core RB Usage:** {int(rules['core_rb_usage_pct']*100)}%")
st.sidebar.markdown(f"**Ultra-Leverage Required:** {rules['ultra_leverage_required'][0]}-{rules['ultra_leverage_required'][1]} players")
st.sidebar.markdown(f"**Max Chalk:** {rules['heavy_chalk_max']} player(s)")

# Show cheat sheet reminder for single-entry grinder
if selected_strategy == 'single_entry_grinder':
    st.sidebar.markdown("---")
    st.sidebar.success("💡 **PRO TIP:** Use CHEAT_SHEET.md for weekly prep!")
    st.sidebar.markdown("""
    **Quick Process:**
    1. Identify leverage QB (3-8%)
    2. Identify core RB (18-28%)
    3. Lock both below
    4. Generate lineups
    5. Repeat for all 150 tournaments
    """)

if 'warning' in rules:
    st.sidebar.warning(rules['warning'])

# Main content
tab1, tab2, tab3 = st.tabs(["📊 Generate Lineups", "📈 Analysis", "ℹ️ About"])

with tab1:
    st.header("Generate Optimized Lineups")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # File uploader
        uploaded_file = st.file_uploader(
            "Upload Player Pool CSV",
            type=['csv'],
            help="CSV should have columns: Name, Position, Salary, Team, Opponent, Projection, Ownership"
        )
        
        if uploaded_file is None:
            st.info("💡 No file uploaded - using demo player pool")
            use_demo = True
        else:
            use_demo = False
            
            # PLAYER CATEGORIZATION INTERFACE
            st.markdown("---")
            st.markdown("### 🎯 Categorize Players")
            
            # Load data
            import pandas as pd
            df = pd.read_csv(uploaded_file)
            
            # Rename columns
            if 'Player' in df.columns:
                df = df.rename(columns={'Player': 'Name', 'Ownership %': 'Ownership'})
            
            # Auto-categorize
            def auto_categorize(row):
                own = row.get('Ownership', 0)
                if own >= 25:
                    return "🔥 Chalk"
                elif own <= 5:
                    return "💎 Leverage"
                elif own <= 15:
                    return "⭐ Core"
                else:
                    return "✓ Flex"
            
            if 'Category' not in df.columns:
                df['Category'] = df.apply(auto_categorize, axis=1)
            
            # Category breakdown
            col_a, col_b, col_c, col_d = st.columns(4)
            with col_a:
                st.metric("🔥 Chalk", len(df[df['Category'] == '🔥 Chalk']))
            with col_b:
                st.metric("💎 Leverage", len(df[df['Category'] == '💎 Leverage']))
            with col_c:
                st.metric("⭐ Core", len(df[df['Category'] == '⭐ Core']))
            with col_d:
                st.metric("✓ Flex", len(df[df['Category'] == '✓ Flex']))
            
            # Show top players by category
            with st.expander("📋 View/Edit Player Categories"):
                category_options = ['🔥 Chalk', '💎 Leverage', '⭐ Core', '✓ Flex', '🚫 Exclude']
                
                edited_df = st.data_editor(
                    df[['Name', 'Position', 'Team', 'Salary', 'Projection', 'Ownership', 'Category']].head(50),
                    column_config={
                        "Category": st.column_config.SelectboxColumn(
                            "Category",
                            options=category_options,
                            required=True,
                        ),
                        "Salary": st.column_config.NumberColumn(format="$%d"),
                        "Projection": st.column_config.NumberColumn(format="%.1f"),
                        "Ownership": st.column_config.NumberColumn(format="%.1f%%"),
                    },
                    hide_index=True,
                    height=300
                )
                
                if st.button("💾 Save Edits"):
                    # Update categories
                    for idx, row in edited_df.iterrows():
                        df.loc[df['Name'] == row['Name'], 'Category'] = row['Category']
                    st.success("✅ Categories updated!")
            
            # Save categorized data
            df.to_csv('/tmp/player_pool.csv', index=False)
            st.markdown("---")
            
            # PLAYER LOCKING SYSTEM with SMART SUGGESTIONS
            st.markdown("### 🔒 Lock Core Plays")
            
            # Show strategy-specific guidance
            if selected_strategy == 'single_entry_grinder':
                st.info("""
                **🎯 SINGLE-ENTRY GRINDER LOCKS:**
                - **QB:** Pick ONE ultra-leverage (3-8% owned) - Use in ALL 150 tournaments
                - **RB:** Pick the core RB anchor (18-28% owned) - MANDATORY
                - **FLEX:** Leave empty - optimizer will find leverage plays
                """)
                
                # Auto-suggest leverage QB
                leverage_qbs = df[
                    (df['Position'] == 'QB') & 
                    (df['Ownership'] >= 3) & 
                    (df['Ownership'] <= 8)
                ].sort_values('Projection', ascending=False)
                
                if not leverage_qbs.empty:
                    st.success(f"💡 **Suggested Leverage QB:** {leverage_qbs.iloc[0]['Name']} ({leverage_qbs.iloc[0]['Ownership']:.1f}% owned, ${leverage_qbs.iloc[0]['Salary']:,})")
                else:
                    leverage_qbs = pd.DataFrame()  # Empty dataframe for later checks
                
                # Auto-suggest core RB
                core_rbs = df[
                    (df['Position'] == 'RB') & 
                    (df['Ownership'] >= 18) & 
                    (df['Ownership'] <= 28)
                ].sort_values('Projection', ascending=False)
                
                if not core_rbs.empty:
                    st.success(f"⚓ **Suggested Core RB:** {core_rbs.iloc[0]['Name']} ({core_rbs.iloc[0]['Ownership']:.1f}% owned, ${core_rbs.iloc[0]['Salary']:,})")
                else:
                    core_rbs = pd.DataFrame()  # Empty dataframe for later checks
                
            else:
                # Initialize empty dataframes if not single-entry grinder
                leverage_qbs = pd.DataFrame()
                core_rbs = pd.DataFrame()
                
                if selected_strategy == 'small_gpp_multi':
                    st.info("""
                    **🏆 MULTI-ENTRY LOCKS:**
                    - **QB:** Leave empty - optimizer diversifies across 5-8 QBs
                    - **RB:** Optionally lock core RB for 70% of builds
                    - **WR:** Can lock one stacking WR
                    """)
            
            # Initialize locks in session state
            if 'locked_players' not in st.session_state:
                st.session_state['locked_players'] = {}
            
            col_lock1, col_lock2 = st.columns(2)
            
            with col_lock1:
                st.markdown("**🎯 Primary Locks** (Foundation of lineup)")
                
                # QB Lock with smart default
                qb_options = ['None'] + sorted(df[df['Position'] == 'QB']['Name'].tolist())
                
                # Pre-select suggested QB for single-entry grinder
                default_qb = 'None'
                if selected_strategy == 'single_entry_grinder' and not leverage_qbs.empty:
                    suggested_qb = leverage_qbs.iloc[0]['Name']
                    if suggested_qb in qb_options:
                        default_qb_index = qb_options.index(suggested_qb)
                    else:
                        default_qb_index = 0
                else:
                    default_qb_index = 0
                
                locked_qb = st.selectbox(
                    "Lock QB:", 
                    qb_options, 
                    index=default_qb_index,
                    key='lock_qb',
                    help="For Single-Entry Grinder: Pick ONE 3-8% owned QB and use in all 150 tournaments"
                )
                
                # RB Locks with smart default
                rb_options = ['None'] + sorted(df[df['Position'] == 'RB']['Name'].tolist())
                
                # Pre-select suggested RB for single-entry grinder
                if selected_strategy == 'single_entry_grinder' and not core_rbs.empty:
                    suggested_rb = core_rbs.iloc[0]['Name']
                    if suggested_rb in rb_options:
                        default_rb_index = rb_options.index(suggested_rb)
                    else:
                        default_rb_index = 0
                else:
                    default_rb_index = 0
                
                locked_rb1 = st.selectbox(
                    "Lock RB #1:", 
                    rb_options, 
                    index=default_rb_index,
                    key='lock_rb1',
                    help="For Single-Entry Grinder: MUST lock the core RB (18-28% owned)"
                )
                locked_rb2 = st.selectbox("Lock RB #2:", rb_options, key='lock_rb2')
                
                # WR Locks
                wr_options = ['None'] + sorted(df[df['Position'] == 'WR']['Name'].tolist())
                locked_wr1 = st.selectbox("Lock WR #1:", wr_options, key='lock_wr1')
                locked_wr2 = st.selectbox("Lock WR #2:", wr_options, key='lock_wr2')
            
            with col_lock2:
                st.markdown("**⚙️ Flex Locks** (Optional)")
                
                locked_wr3 = st.selectbox("Lock WR #3:", wr_options, key='lock_wr3')
                
                te_options = ['None'] + sorted(df[df['Position'] == 'TE']['Name'].tolist())
                locked_te = st.selectbox("Lock TE:", te_options, key='lock_te')
                
                flex_options = ['None'] + sorted(df[df['Position'].isin(['RB', 'WR', 'TE'])]['Name'].tolist())
                locked_flex = st.selectbox("Lock FLEX:", flex_options, key='lock_flex')
                
                dst_options = ['None'] + sorted(df[df['Position'] == 'DST']['Name'].tolist())
                locked_dst = st.selectbox("Lock DST:", dst_options, key='lock_dst')
            
            # Collect all locks
            locks = {
                'QB': locked_qb if locked_qb != 'None' else None,
                'RB': [locked_rb1 if locked_rb1 != 'None' else None, 
                       locked_rb2 if locked_rb2 != 'None' else None],
                'WR': [locked_wr1 if locked_wr1 != 'None' else None,
                       locked_wr2 if locked_wr2 != 'None' else None,
                       locked_wr3 if locked_wr3 != 'None' else None],
                'TE': locked_te if locked_te != 'None' else None,
                'FLEX': locked_flex if locked_flex != 'None' else None,
                'DST': locked_dst if locked_dst != 'None' else None
            }
            
            # Remove None values
            locks['RB'] = [rb for rb in locks['RB'] if rb]
            locks['WR'] = [wr for wr in locks['WR'] if wr]
            
            # Save locks
            st.session_state['locked_players'] = locks
            
            # Show locked lineup summary
            locked_count = sum([
                1 if locks['QB'] else 0,
                len(locks['RB']),
                len(locks['WR']),
                1 if locks['TE'] else 0,
                1 if locks['FLEX'] else 0,
                1 if locks['DST'] else 0
            ])
            
            if locked_count > 0:
                st.info(f"🔒 {locked_count} players locked. Optimizer will fill remaining {9 - locked_count} spots.")
                
                # Calculate locked salary
                locked_names = []
                if locks['QB']: locked_names.append(locks['QB'])
                locked_names.extend(locks['RB'])
                locked_names.extend(locks['WR'])
                if locks['TE']: locked_names.append(locks['TE'])
                if locks['FLEX']: locked_names.append(locks['FLEX'])
                if locks['DST']: locked_names.append(locks['DST'])
                
                locked_df = df[df['Name'].isin(locked_names)]
                locked_salary = locked_df['Salary'].sum()
                locked_proj = locked_df['Projection'].sum()
                locked_own = locked_df['Ownership'].sum()
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Locked Salary", f"${locked_salary:,}")
                with col2:
                    st.metric("Locked Projection", f"{locked_proj:.1f} pts")
                with col3:
                    st.metric("Locked Own%", f"{locked_own:.1f}%")
            
            st.markdown("---")
    
    with col2:
        st.markdown("### Quick Actions")
        generate_button = st.button("🚀 Generate Lineups", type="primary", use_container_width=True)
    
    if generate_button:
        with st.spinner("Generating optimized lineups..."):
            try:
                # Initialize optimizer
                optimizer = DFSOptimizer(contest_type=contest_type, entry_fee=entry_fee)
                
                # Get locks from session state
                locks = st.session_state.get('locked_players', {})
                
                # Run optimization
                # Try with locks first, fall back to without if method doesn't support it
                try:
                    if use_demo:
                        results, lineups = optimizer.run('demo', num_lineups=num_lineups, locks=locks)
                    else:
                        # Save uploaded file temporarily
                        with open('/tmp/player_pool.csv', 'wb') as f:
                            f.write(uploaded_file.getbuffer())
                        results, lineups = optimizer.run('/tmp/player_pool.csv', num_lineups=num_lineups, locks=locks)
                except TypeError as e:
                    # Old version doesn't support locks - run without them
                    if 'locks' in str(e):
                        st.warning("⚠️ Running without player locks (using older optimizer version). Please clear Streamlit cache to enable locks.")
                        if use_demo:
                            results, lineups = optimizer.run('demo', num_lineups=num_lineups)
                        else:
                            results, lineups = optimizer.run('/tmp/player_pool.csv', num_lineups=num_lineups)
                    else:
                        raise  # Different error, re-raise it
                
                # Verify results
                if results is None or lineups is None or len(lineups) == 0:
                    st.error("Failed to generate lineups. Please check your player pool.")
                else:
                    # Store in session state
                    st.session_state['results'] = results
                    st.session_state['lineups'] = lineups
                    st.success("✅ Lineups generated successfully!")
                    
            except Exception as e:
                st.error(f"Error generating lineups: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
    
    # Display results if available
    if 'results' in st.session_state:
        st.markdown("---")
        st.subheader("🏆 Top Lineups")
        
        results = st.session_state['results']
        lineups = st.session_state['lineups']
        
        # Ensure expected columns exist
        if 'expected_roi' not in results.columns:
            st.warning("⚠️ Simulation incomplete. Showing lineups ranked by projection.")
            results_sorted = results.sort_values('projection', ascending=False)
        else:
            # Sort by ROI
            results_sorted = results.sort_values('expected_roi', ascending=False)
        
        # Display top 5 lineups
        for i, (idx, row) in enumerate(results_sorted.head(5).iterrows()):
            lineup_id = int(row['lineup_id']) - 1
            
            if lineup_id >= len(lineups):
                continue
                
            lineup = lineups[lineup_id]
            
            # Get metrics with safe defaults
            roi = row.get('expected_roi', 0.0)
            win_pct = row.get('win_pct', 0.0)
            top10_pct = row.get('top10_pct', 0.0)
            cash_pct = row.get('cash_pct', 0.0)
            
            # Get lineup metrics
            salary_rem = lineup.get('salary_remaining', 0)
            value = lineup.get('value', 0)
            stack_info = lineup.get('stack', 'Unknown')
            
            with st.expander(f"**Lineup #{i+1}** - ROI: {roi:.1f}% | Proj: {row['projection']:.1f} pts | Stack: {stack_info}", expanded=(i==0)):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Expected ROI", f"{roi:.1f}%")
                with col2:
                    st.metric("Win %", f"{win_pct:.3f}%")
                with col3:
                    st.metric("Top 10%", f"{top10_pct:.1f}%")
                with col4:
                    st.metric("Cash %", f"{cash_pct:.1f}%")
                
                # STRATEGY VALIDATION for single-entry grinder
                if selected_strategy == 'single_entry_grinder':
                    st.markdown("---")
                    st.markdown("#### 🎯 Strategy Validation")
                    
                    # Get players from lineup
                    players = lineup.get('players', [])
                    
                    # Calculate metrics
                    ultra_leverage_count = sum(1 for p in players if p.get('Ownership', 100) < 5)
                    core_count = sum(1 for p in players if 10 <= p.get('Ownership', 0) <= 25)
                    chalk_count = sum(1 for p in players if p.get('Ownership', 0) > 25)
                    avg_own = lineup.get('avg_ownership', lineup.get('total_ownership', 0) / 9)
                    
                    # Find QB and FLEX
                    qb = next((p for p in players if p.get('Position') == 'QB'), None)
                    flex = next((p for p in players if p.get('PositionSlot', '').startswith('FLEX')), None)
                    
                    # Validation checks
                    val_col1, val_col2, val_col3 = st.columns(3)
                    
                    with val_col1:
                        # QB check
                        qb_valid = qb and 3 <= qb.get('Ownership', 100) <= 8
                        if qb_valid:
                            st.success(f"✅ QB: {qb['Name']} ({qb.get('Ownership', 0):.1f}%)")
                        elif qb:
                            st.warning(f"⚠️ QB: {qb['Name']} ({qb.get('Ownership', 0):.1f}%) - Should be 3-8%")
                        
                        # Ultra-leverage check
                        if 3 <= ultra_leverage_count <= 4:
                            st.success(f"✅ Ultra-Leverage: {ultra_leverage_count} players")
                        else:
                            st.warning(f"⚠️ Ultra-Leverage: {ultra_leverage_count} (need 3-4)")
                    
                    with val_col2:
                        # Core RB check
                        core_rb = next((p for p in players if p.get('Position') == 'RB' and 18 <= p.get('Ownership', 0) <= 28), None)
                        if core_rb:
                            st.success(f"✅ Core RB: {core_rb['Name']} ({core_rb.get('Ownership', 0):.1f}%)")
                        else:
                            st.error("❌ No Core RB (18-28% owned)")
                        
                        # Chalk check
                        if chalk_count <= 1:
                            st.success(f"✅ Chalk: {chalk_count} player (max 1)")
                        else:
                            st.warning(f"⚠️ Chalk: {chalk_count} players (should be ≤1)")
                    
                    with val_col3:
                        # FLEX check
                        flex_valid = flex and flex.get('Ownership', 100) <= 5
                        if flex_valid:
                            st.success(f"✅ FLEX: {flex['Name']} ({flex.get('Ownership', 0):.1f}%)")
                        elif flex:
                            st.warning(f"⚠️ FLEX: {flex['Name']} ({flex.get('Ownership', 0):.1f}%) - Should be <5%")
                        
                        # Ownership check
                        if 10 <= avg_own <= 13:
                            st.success(f"✅ Avg Own: {avg_own:.1f}%")
                        elif 9 <= avg_own <= 14:
                            st.info(f"📊 Avg Own: {avg_own:.1f}% (acceptable)")
                        else:
                            st.warning(f"⚠️ Avg Own: {avg_own:.1f}% (should be 10-13%)")
                    
                    # Overall verdict
                    all_valid = (qb_valid and core_rb and chalk_count <= 1 and 
                                3 <= ultra_leverage_count <= 4 and 9 <= avg_own <= 14)
                    
                    if all_valid:
                        st.success("🎯 **PERFECT!** This lineup follows the winning formula!")
                    else:
                        st.info("💡 Review validation above. Rebuild if needed for optimal structure.")
                
                st.markdown("---")
                
                # Additional metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Salary Left", f"${salary_rem:,}")
                with col2:
                    st.metric("Value", f"{value:.2f} pts/$1k")
                with col3:
                    own_avg = lineup.get('ownership_avg', row['ownership']/9)
                    st.metric("Avg Own%", f"{own_avg:.1f}%")
                
                st.markdown("---")
                
                # Display roster in proper order with emojis
                roster_data = []
                for p in lineup['players']:
                    # Handle FLEX display
                    pos = p.get('PositionSlot', p['Position'])
                    
                    # Add emoji indicators
                    own_pct = p['Ownership']
                    if own_pct > 25:
                        indicator = "🔥 Chalk"
                    elif own_pct < 5:
                        indicator = "💎 Leverage"
                    else:
                        indicator = "✓ Core"
                    
                    roster_data.append({
                        'Position': pos,
                        'Player': p['Name'],
                        'Team': p.get('Team', 'N/A'),
                        'Salary': f"${p['Salary']:,}",
                        'Projection': f"{p['Projection']:.1f}",
                        'Own%': f"{own_pct:.1f}%",
                        'Type': indicator
                    })
                
                roster_df = pd.DataFrame(roster_data)
                st.dataframe(roster_df, use_container_width=True, hide_index=True)
                
                # Game stacks info
                game_stacks = lineup.get('game_stacks', [])
                if game_stacks and game_stacks != ["No game stacks"]:
                    st.info(f"🎯 Game Stacks: {', '.join(game_stacks)}")
                
                # Summary row
                st.markdown(f"**Total: ${row['salary']:,} / $50,000 | {row['projection']:.1f} pts | {row['ownership']:.1f}% own**")
        
        # Export button
        st.markdown("---")
        if st.button("📥 Export All Lineups to CSV"):
            csv = results.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"lineups_{contest_type}.csv",
                mime="text/csv"
            )

with tab2:
    st.header("📈 Lineup Analysis")
    
    if 'results' not in st.session_state:
        st.info("Generate lineups first to see analysis")
    else:
        results = st.session_state['results']
        
        # ROI Distribution
        fig1 = px.histogram(
            results,
            x='expected_roi',
            title='Expected ROI Distribution',
            labels={'expected_roi': 'Expected ROI (%)'},
            nbins=20
        )
        st.plotly_chart(fig1, use_container_width=True)
        
        # Projection vs Ownership scatter - with error handling
        try:
            # Clean data for scatter plot
            scatter_data = results[['ownership', 'projection', 'expected_roi', 'win_pct', 'cash_pct']].copy()
            scatter_data = scatter_data.dropna()  # Remove any NaN values
            
            # Ensure numeric types
            scatter_data['ownership'] = pd.to_numeric(scatter_data['ownership'], errors='coerce')
            scatter_data['projection'] = pd.to_numeric(scatter_data['projection'], errors='coerce')
            scatter_data['expected_roi'] = pd.to_numeric(scatter_data['expected_roi'], errors='coerce')
            
            fig2 = px.scatter(
                scatter_data,
                x='ownership',
                y='projection',
                size='expected_roi',
                color='expected_roi',
                title='Projection vs Ownership',
                labels={
                    'ownership': 'Total Ownership (%)',
                    'projection': 'Projected Points',
                    'expected_roi': 'Expected ROI (%)'
                },
                hover_data=['win_pct', 'cash_pct']
            )
            st.plotly_chart(fig2, use_container_width=True)
        except Exception as e:
            st.warning(f"Could not generate scatter plot: {str(e)}")
            # Show simple table instead
            st.dataframe(results[['projection', 'ownership', 'expected_roi']].head(10))
        
        # Summary statistics
        st.subheader("📊 Summary Statistics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Avg ROI", f"{results['expected_roi'].mean():.1f}%")
            st.metric("Best ROI", f"{results['expected_roi'].max():.1f}%")
        
        with col2:
            st.metric("Avg Projection", f"{results['projection'].mean():.1f} pts")
            st.metric("Avg Ownership", f"{results['ownership'].mean():.1f}%")
        
        with col3:
            st.metric("Avg Win %", f"{results['win_pct'].mean():.3f}%")
            st.metric("Avg Cash %", f"{results['cash_pct'].mean():.1f}%")

with tab3:
    st.header("ℹ️ About This Tool")
    
    st.markdown("""
    ### DFS Optimizer - Free Stokastic Alternative
    
    This tool reverse-engineers Stokastic's lineup optimization approach to provide
    free DFS lineup building for NFL DraftKings contests.
    
    #### Features
    
    - ✅ **Contest-Specific Optimization** - Different strategies for different field sizes
    - ✅ **Stack Correlation** - Enforces QB + pass catcher stacking
    - ✅ **Ownership Targeting** - Balances projection vs leverage based on contest
    - ✅ **Monte Carlo Simulation** - 1,000 tournament simulations per lineup (fast!)
    - ✅ **Expected ROI Calculation** - See which lineups have positive expected value
    
    #### Contest Structures Supported
    
    **Small GPP (4,444 entries, 25% to 1st)**
    - Target: 110-150% total ownership
    - Strategy: Balance projection + ownership
    - Stack: QB + 2 or QB + 3
    
    **Mid GPP (14,000 entries, 10% payout)**  
    - Target: 40-90% total ownership
    - Strategy: More contrarian
    - ⚠️ Warning: Structure often has negative ROI
    
    **Millionaire Maker (150k+ entries)**
    - Target: 30-70% total ownership  
    - Strategy: Extreme differentiation
    - Stack: Ultra-contrarian QB + 2/3
    
    #### How It Works
    
    1. **Projections** - Uses salary-based baseline (can integrate free sources)
    2. **Ownership** - Models field behavior based on value and position
    3. **Optimization** - Generates lineups meeting contest-specific constraints
    4. **Simulation** - Runs 10,000 Monte Carlo iterations per lineup
    5. **Results** - Returns top lineups ranked by expected ROI
    
    #### Data Sources (Can Be Integrated)
    
    - FantasyPros (free consensus projections)
    - RotoGrinders (free ownership estimates)
    - ESPN/OddsShark (Vegas lines)
    - DFSBoss (ownership projections)
    
    #### Limitations
    
    - Projections less refined than paid services
    - Ownership estimates are modeled, not live
    - Doesn't account for late news/injuries automatically
    
    #### Built By
    
    Reverse engineered from Stokastic simulation data.
    Open source - customize as needed!
    
    ---
    
    **Disclaimer:** This is a tool to assist with research. Always do your own
    analysis before entering real-money contests.
    """)

# Footer
st.markdown("---")
st.markdown("Built with ❤️ using Streamlit | Free Stokastic Alternative")
