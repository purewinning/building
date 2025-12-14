"""
DFS Optimizer Configuration
Contest-specific lineup construction rules reverse-engineered from Stokastic
"""

# Contest structure definitions
CONTEST_STRUCTURES = {
    'small_gpp': {
        'name': '4,444 Entries (25% to 1st)',
        'entries': 4444,
        'payout_structure': 'top_heavy',
        'payout_pct_to_first': 0.25,
        'ownership_target_total': (110, 150),  # Total ownership sum across 9 players
        'ownership_target_avg': (12, 17),  # Average per player
        'projection_target': (135, 143),
        'qb_stack_type': ['QB + 2', 'QB + 3'],
        'qb_ownership_max': 10,
        'qb_ownership_preferred': (3, 6),
        'bring_back_required': True,
        'leverage_plays_count': (2, 3),  # Number of 5-10% owned players
        'chalk_allowed': True,  # Can play 1-2 pieces >25%
        'chalk_max_count': 2,
        'projection_weight': 0.70,  # 70% projection, 30% ownership
        'ownership_weight': 0.30,
        'description': 'Balance projection + ownership. Need leverage at QB but can play some chalk.'
    },
    
    'mid_gpp': {
        'name': '14,000 Entries (10% Payout)',
        'entries': 14000,
        'payout_structure': 'flat',
        'payout_pct_to_first': 0.10,
        'ownership_target_total': (40, 90),
        'ownership_target_avg': (5, 10),
        'projection_target': (111, 120),
        'qb_stack_type': ['QB + 1', 'QB + 2'],
        'qb_ownership_max': 5,
        'qb_ownership_preferred': (2, 5),
        'bring_back_required': False,
        'leverage_plays_count': (4, 5),
        'chalk_allowed': False,
        'chalk_max_count': 0,
        'projection_weight': 0.50,  # 50/50 split
        'ownership_weight': 0.50,
        'warning': '⚠️ NEGATIVE ROI EXPECTED - AVOID THIS STRUCTURE',
        'description': 'More contrarian than small fields. All sims show negative ROI.'
    },
    
    'milly_maker': {
        'name': '150,000+ Entries (Millionaire Maker)',
        'entries': 150000,
        'payout_structure': 'ultra_top_heavy',
        'payout_pct_to_first': 0.50,  # Half the prize pool to 1st
        'ownership_target_total': (30, 70),
        'ownership_target_avg': (3, 8),
        'projection_target': (120, 135),
        'qb_stack_type': ['QB + 2', 'QB + 3'],
        'qb_ownership_max': 5,
        'qb_ownership_preferred': (2, 4),
        'bring_back_required': False,
        'leverage_plays_count': (6, 7),
        'chalk_allowed': False,
        'chalk_max_count': 0,
        'projection_weight': 0.30,  # 30% projection, 70% ownership
        'ownership_weight': 0.70,
        'description': 'Extreme differentiation required. Fade all chalk. Need ultra-contrarian stack.'
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
MONTE_CARLO_ITERATIONS = 10000
LINEUP_GENERATION_COUNT = 1000  # Generate this many candidates before filtering

# Output settings
TOP_LINEUPS_TO_RETURN = 20
EXPORT_FORMAT = 'csv'  # For DraftKings upload
