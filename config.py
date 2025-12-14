"""
DFS Optimizer Configuration
Contest-specific lineup construction rules reverse-engineered from Stokastic
"""

"""
DFS Optimizer Configuration
WINNING STRUCTURE from $250k 1st place finish (Wildcat 4,170 entries)
"""

# Contest structure definitions - BASED ON ACTUAL WINNING DATA
CONTEST_STRUCTURES = {
    'small_gpp': {
        'name': '4,444 Entries ($250K Winner Blueprint)',
        'entries': 4444,
        'payout_structure': 'top_heavy',
        
        # OWNERSHIP TARGETS (from actual winner: 9.4% avg)
        'ownership_target_avg': (9, 13),  # GOLDILOCKS ZONE
        'ownership_total_range': (80, 120),  # Total combined
        'ownership_target_total': (80, 120),  # Backward compatibility
        
        # PROJECTION TARGETS (backward compatibility)
        'projection_target': (140, 155),  # Expected winning score range
        
        # PLAYER DISTRIBUTION (from actual winner structure)
        'ultra_leverage_required': (3, 4),  # <5% owned (winner had 4)
        'core_players_required': (3, 4),   # 10-25% owned (winner had 4)
        'heavy_chalk_max': 1,               # >25% owned (winner had 0)
        'leverage_plays_count': (3, 4),    # Backward compatibility
        'chalk_allowed': False,
        'chalk_max_count': 0,
        
        # QB STRATEGY (Trevor Lawrence 3.7% won it)
        'qb_ownership_target': (2, 8),      # Ultra-leverage QB range
        'qb_ownership_max': 8,              # Backward compatibility
        'qb_ownership_preferred': (2, 8),   # Backward compatibility
        'qb_salary_range': (5000, 6500),    # Value QB to save money
        'qb_usage_pct': 0.35,               # 35% of lineups get leverage QB
        'qb_stack_type': ['QB + 2', 'QB + 3'],  # Backward compatibility
        
        # STACKING (winner had JAX 3-piece stack)
        'game_stack_pct': 0.40,             # 40% of lineups have 3-piece stack
        'stack_min_players': 3,             # QB + 2 from same team
        'stack_ownership_target': (8, 25),  # Combined stack ownership
        'bring_back_required': False,       # Backward compatibility
        
        # CORE RB ANCHOR (Travis Etienne 22.8% in 70% of Top 10)
        'core_rb_ownership': (18, 25),      # The "must-have" RB
        'core_rb_usage_pct': 0.70,          # In 70% of lineups
        
        # TE STRATEGY (70% punted in winners)
        'te_punt_pct': 0.70,                # Punt 70% of time
        'te_punt_salary_max': 4500,         # Under $4.5k = punt
        
        # WEIGHTS
        'projection_weight': 0.85,          # 85% projection (winner had high scorers)
        'ownership_weight': 0.15,           # 15% ownership (secondary)
        
        'description': 'Exact structure from $250K winner: Leverage QB + Core RB + Game Stack'
    },
    
    'mid_gpp': {
        'name': '14,000 Entries (Mid-Field)',
        'entries': 14000,
        'payout_structure': 'flat',
        
        'ownership_target_avg': (7, 11),
        'ownership_total_range': (65, 100),
        'ownership_target_total': (65, 100),  # Backward compatibility
        
        'projection_target': (135, 150),  # Backward compatibility
        
        'ultra_leverage_required': (4, 5),
        'core_players_required': (2, 3),
        'heavy_chalk_max': 1,
        'leverage_plays_count': (4, 5),
        'chalk_allowed': False,
        'chalk_max_count': 0,
        
        'qb_ownership_target': (3, 10),
        'qb_ownership_max': 10,
        'qb_ownership_preferred': (3, 10),
        'qb_salary_range': (5000, 7000),
        'qb_usage_pct': 0.30,
        'qb_stack_type': ['QB + 2'],
        
        'game_stack_pct': 0.35,
        'stack_min_players': 2,
        'stack_ownership_target': (10, 30),
        'bring_back_required': False,
        
        'core_rb_ownership': (15, 25),
        'core_rb_usage_pct': 0.60,
        
        'te_punt_pct': 0.60,
        'te_punt_salary_max': 4500,
        
        'projection_weight': 0.70,
        'ownership_weight': 0.30,
        
        'description': 'Balanced approach for mid-sized GPPs'
    },
    
    'milly_maker': {
        'name': '150,000+ Entries (Millionaire Maker)',
        'entries': 150000,
        'payout_structure': 'ultra_top_heavy',
        
        'ownership_target_avg': (5, 9),
        'ownership_total_range': (50, 80),
        'ownership_target_total': (50, 80),  # Backward compatibility
        
        'projection_target': (130, 145),  # Backward compatibility
        
        'ultra_leverage_required': (5, 6),
        'core_players_required': (2, 3),
        'heavy_chalk_max': 0,
        'leverage_plays_count': (5, 6),
        'chalk_allowed': False,
        'chalk_max_count': 0,
        
        'qb_ownership_target': (1, 5),
        'qb_ownership_max': 5,
        'qb_ownership_preferred': (1, 5),
        'qb_salary_range': (5000, 6500),
        'qb_usage_pct': 0.50,
        'qb_stack_type': ['QB + 2', 'QB + 3'],
        
        'game_stack_pct': 0.50,
        'stack_min_players': 3,
        'stack_ownership_target': (5, 20),
        'bring_back_required': False,
        
        'core_rb_ownership': (12, 20),
        'core_rb_usage_pct': 0.50,
        
        'te_punt_pct': 0.80,
        'te_punt_salary_max': 4500,
        
        'projection_weight': 0.60,
        'ownership_weight': 0.40,
        
        'description': 'Extreme leverage for massive fields'
    }
}

# DraftKings position requirements
DRAFTKINGS_POSITIONS = {
    'QB': 1,
    'RB': 2,
    'WR': 3,
    'TE': 1,
    'FLEX': 1,  # RB/WR/TE
    'DST': 1
}

SALARY_CAP = 50000

# Stack definitions
STACK_RULES = {
    'QB + 1': {
        'description': 'QB + 1 same-team pass catcher (WR or TE)',
        'min_correlation': 1,
        'positions': ['WR', 'TE']
    },
    'QB + 2': {
        'description': 'QB + 2 same-team pass catchers',
        'min_correlation': 2,
        'positions': ['WR', 'TE']
    },
    'QB + 3': {
        'description': 'QB + 3 same-team pass catchers',
        'min_correlation': 3,
        'positions': ['WR', 'TE']
    },
    'QB + RB': {
        'description': 'QB + same-team RB (elite correlation)',
        'min_correlation': 1,
        'positions': ['RB']
    },
    'bring_back': {
        'description': 'Include 1-2 pieces from opposing team in high-total game',
        'required_for': ['small_gpp']
    }
}

# Ownership tiers for player classification
OWNERSHIP_TIERS = {
    'ultra_chalk': {'min': 30, 'max': 100, 'label': 'Ultra Chalk (>30%)'},
    'chalk': {'min': 20, 'max': 30, 'label': 'Chalk (20-30%)'},
    'popular': {'min': 12, 'max': 20, 'label': 'Popular (12-20%)'},
    'leverage': {'min': 5, 'max': 12, 'label': 'Leverage (5-12%)'},
    'contrarian': {'min': 0, 'max': 5, 'label': 'Contrarian (<5%)'}
}

# Projection variance by position (for Monte Carlo simulation)
POSITION_VARIANCE = {
    'QB': 6.5,   # Standard deviation in DK points
    'RB': 7.0,
    'WR': 6.0,
    'TE': 5.0,
    'DST': 4.0
}

# Free data source URLs
DATA_SOURCES = {
    'fantasypros_projections': 'https://www.fantasypros.com/nfl/projections/',
    'rotogrinders_ownership': 'https://rotogrinders.com/projected-stats/nfl',
    'vegas_lines': 'https://www.espn.com/nfl/lines',
    'dfsboss_ownership': 'https://www.dfsboss.com/nfl-ownership-projections/'
}

# Simulation settings
MONTE_CARLO_ITERATIONS = 1000  # Reduced from 10,000 for speed
LINEUP_GENERATION_COUNT = 1000  # Generate this many candidates before filtering

# Output settings
TOP_LINEUPS_TO_RETURN = 20
EXPORT_FORMAT = 'csv'  # For DraftKings upload
