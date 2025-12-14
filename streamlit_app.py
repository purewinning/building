"""
Streamlit Web Interface for DFS Optimizer
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from config import CONTEST_STRUCTURES
from main import DFSOptimizer

st.set_page_config(page_title="DFS Optimizer", page_icon="🏈", layout="wide")

st.title("🏈 DFS Lineup Optimizer")
st.markdown("### Free Alternative to Stokastic - Reverse Engineered")

# Sidebar configuration
st.sidebar.header("⚙️ Configuration")

contest_type = st.sidebar.selectbox(
    "Contest Type",
    options=list(CONTEST_STRUCTURES.keys()),
    format_func=lambda x: CONTEST_STRUCTURES[x]['name']
)

entry_fee = st.sidebar.number_input(
    "Entry Fee ($)",
    min_value=1,
    max_value=1000,
    value=100,
    step=1
)

num_lineups = st.sidebar.slider(
    "Number of Lineups",
    min_value=1,
    max_value=50,
    value=20,
    step=1
)

# Display contest rules
st.sidebar.markdown("---")
st.sidebar.subheader("📋 Contest Rules")
rules = CONTEST_STRUCTURES[contest_type]
st.sidebar.markdown(f"**Entries:** {rules['entries']:,}")
st.sidebar.markdown(f"**Target Ownership:** {rules['ownership_target_avg'][0]}-{rules['ownership_target_avg'][1]}%")
st.sidebar.markdown(f"**Target Projection:** {rules['projection_target'][0]}-{rules['projection_target'][1]} pts")
st.sidebar.markdown(f"**Stack Type:** {', '.join(rules['qb_stack_type'])}")

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
            
            # PLAYER LOCKING SYSTEM
            st.markdown("### 🔒 Lock Core Plays")
            st.markdown("Select players you MUST have in every lineup:")
            
            # Initialize locks in session state
            if 'locked_players' not in st.session_state:
                st.session_state['locked_players'] = []
            
            col_lock1, col_lock2 = st.columns(2)
            
            with col_lock1:
                st.markdown("**🎯 Primary Locks** (Foundation of lineup)")
                
                # QB Lock
                qb_options = ['None'] + sorted(df[df['Position'] == 'QB']['Name'].tolist())
                locked_qb = st.selectbox("Lock QB:", qb_options, key='lock_qb')
                
                # RB Locks
                rb_options = ['None'] + sorted(df[df['Position'] == 'RB']['Name'].tolist())
                locked_rb1 = st.selectbox("Lock RB #1:", rb_options, key='lock_rb1')
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
