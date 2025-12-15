"""
Winning Structure Optimizer - Based on Actual Top 20 Analysis
Replicates the exact patterns from winning lineups
"""

import pandas as pd
import numpy as np

SALARY_CAP = 50000

class WinningStructureOptimizer:
    """
    Based on analysis of Top 20 finishers:
    - Core RB Anchor (18-28% owned) - MANDATORY
    - Leverage QB (3-8% owned) 
    - Balanced WR Core (2-3 players, 10-20% owned)
    - Ultra-Leverage FLEX (<5% owned)
    - Punt TE
    - 12-15% average ownership
    """
    
    def __init__(self, contest_type='single_entry_grinder'):
        self.contest_type = contest_type
        
    def generate_lineups(self, player_pool, num_lineups=20):
        """Generate lineups using winning structure"""
        self.player_pool = player_pool
        lineups = []
        
        # Identify player pools by ownership tier
        self._categorize_players()
        
        for i in range(num_lineups * 5):
            lineup = self._build_winning_structure()
            if lineup:
                lineups.append(lineup)
            if len(lineups) >= num_lineups:
                break
                
        return lineups if lineups else None
    
    def _categorize_players(self):
        """Categorize players by ownership tiers"""
        df = self.player_pool
        
        # QB tiers
        self.leverage_qbs = df[(df['Position'] == 'QB') & (df['Ownership'] >= 3) & (df['Ownership'] <= 8)].copy()
        self.core_qbs = df[(df['Position'] == 'QB') & (df['Ownership'] > 8) & (df['Ownership'] <= 15)].copy()
        
        # RB tiers  
        self.core_rbs = df[(df['Position'] == 'RB') & (df['Ownership'] >= 18) & (df['Ownership'] <= 35)].copy()
        self.mid_rbs = df[(df['Position'] == 'RB') & (df['Ownership'] >= 10) & (df['Ownership'] < 18)].copy()
        self.leverage_rbs = df[(df['Position'] == 'RB') & (df['Ownership'] < 10)].copy()
        
        # WR tiers
        self.core_wrs = df[(df['Position'] == 'WR') & (df['Ownership'] >= 10) & (df['Ownership'] <= 20)].copy()
        self.mid_wrs = df[(df['Position'] == 'WR') & (df['Ownership'] > 20) & (df['Ownership'] <= 30)].copy()
        self.leverage_wrs = df[(df['Position'] == 'WR') & (df['Ownership'] < 10)].copy()
        
        # TE - mostly punt plays
        self.punt_tes = df[(df['Position'] == 'TE') & (df['Salary'] <= 5000)].copy()
        self.mid_tes = df[(df['Position'] == 'TE') & (df['Salary'] > 5000)].copy()
        
        # DST
        self.cheap_dsts = df[(df['Position'] == 'DST') & (df['Salary'] <= 3500)].copy()
        
        # Add value scores
        for pool in [self.leverage_qbs, self.core_qbs, self.core_rbs, self.mid_rbs, 
                     self.leverage_rbs, self.core_wrs, self.mid_wrs, self.leverage_wrs,
                     self.punt_tes, self.mid_tes, self.cheap_dsts]:
            if not pool.empty:
                pool['value_score'] = pool['Projection'] / (pool['Salary'] / 1000)
    
    def _build_winning_structure(self):
        """Build lineup using WINNING STRUCTURE from Top 20 analysis"""
        lineup = []
        budget = SALARY_CAP
        used = []
        
        # STEP 1: LEVERAGE QB (3-8% owned) - 60% of time
        if np.random.random() < 0.6 and not self.leverage_qbs.empty:
            qb_pool = self.leverage_qbs[self.leverage_qbs['Salary'] <= min(7500, budget - 42000)]
        else:
            # Core QB fallback
            qb_pool = self.core_qbs[self.core_qbs['Salary'] <= min(7500, budget - 42000)]
        
        if qb_pool.empty:
            return None
            
        qb = self._pick_random_weighted(qb_pool)
        lineup.append(qb)
        budget -= qb['Salary']
        used.append(qb['Name'])
        
        # STEP 2: CORE RB ANCHOR (18-28% owned) - MANDATORY
        core_rb_pool = self.core_rbs[
            (self.core_rbs['Salary'] <= min(9000, budget - 33000)) &
            (~self.core_rbs['Name'].isin(used))
        ]
        
        if core_rb_pool.empty:
            return None
            
        core_rb = self._pick_random_weighted(core_rb_pool)
        lineup.append(core_rb)
        budget -= core_rb['Salary']
        used.append(core_rb['Name'])
        
        # STEP 3: RB2 - Mix of mid/leverage
        if np.random.random() < 0.5:
            rb2_pool = self.mid_rbs
        else:
            rb2_pool = self.leverage_rbs
            
        rb2_pool = rb2_pool[
            (rb2_pool['Salary'] <= min(8000, budget - 25000)) &
            (~rb2_pool['Name'].isin(used))
        ]
        
        if rb2_pool.empty:
            return None
            
        rb2 = self._pick_random_weighted(rb2_pool)
        lineup.append(rb2)
        budget -= rb2['Salary']
        used.append(rb2['Name'])
        
        # STEP 4: WR1 - Core (10-20% owned)
        wr1_pool = self.core_wrs[
            (self.core_wrs['Salary'] <= min(9000, budget - 18000)) &
            (~self.core_wrs['Name'].isin(used))
        ]
        
        if wr1_pool.empty:
            return None
            
        wr1 = self._pick_random_weighted(wr1_pool)
        lineup.append(wr1)
        budget -= wr1['Salary']
        used.append(wr1['Name'])
        
        # STEP 5: WR2 - Core or mid
        if np.random.random() < 0.7:
            wr2_pool = self.core_wrs
        else:
            wr2_pool = self.mid_wrs
            
        wr2_pool = wr2_pool[
            (wr2_pool['Salary'] <= min(8000, budget - 13000)) &
            (~wr2_pool['Name'].isin(used))
        ]
        
        if wr2_pool.empty:
            return None
            
        wr2 = self._pick_random_weighted(wr2_pool)
        lineup.append(wr2)
        budget -= wr2['Salary']
        used.append(wr2['Name'])
        
        # STEP 6: WR3 - Leverage or core
        if np.random.random() < 0.4:
            wr3_pool = self.leverage_wrs
        else:
            wr3_pool = self.core_wrs
            
        wr3_pool = wr3_pool[
            (wr3_pool['Salary'] <= min(7000, budget - 9000)) &
            (~wr3_pool['Name'].isin(used))
        ]
        
        if wr3_pool.empty:
            return None
            
        wr3 = self._pick_random_weighted(wr3_pool)
        lineup.append(wr3)
        budget -= wr3['Salary']
        used.append(wr3['Name'])
        
        # STEP 7: PUNT TE (80% of time)
        if np.random.random() < 0.8:
            te_pool = self.punt_tes
        else:
            te_pool = self.mid_tes
            
        te_pool = te_pool[
            (te_pool['Salary'] <= min(6000, budget - 6000)) &
            (~te_pool['Name'].isin(used))
        ]
        
        if te_pool.empty:
            return None
            
        te = self._pick_random_weighted(te_pool)
        lineup.append(te)
        budget -= te['Salary']
        used.append(te['Name'])
        
        # STEP 8: ULTRA-LEVERAGE FLEX (<5% owned preferred)
        # Combine leverage RBs/WRs for FLEX
        flex_leverage = pd.concat([
            self.leverage_rbs,
            self.leverage_wrs
        ])
        
        flex_pool = flex_leverage[
            (flex_leverage['Salary'] <= budget - 2500) &
            (~flex_leverage['Name'].isin(used))
        ]
        
        if flex_pool.empty:
            # Fallback to any RB/WR
            flex_pool = pd.concat([self.mid_rbs, self.core_wrs, self.mid_wrs])
            flex_pool = flex_pool[
                (flex_pool['Salary'] <= budget - 2500) &
                (~flex_pool['Name'].isin(used))
            ]
            
        if flex_pool.empty:
            return None
            
        flex = self._pick_random_weighted(flex_pool)
        flex['PositionSlot'] = f"FLEX ({flex['Position']})"
        lineup.append(flex)
        budget -= flex['Salary']
        used.append(flex['Name'])
        
        # STEP 9: CHEAP DST
        dst_pool = self.cheap_dsts[self.cheap_dsts['Salary'] <= budget]
        
        if dst_pool.empty:
            # Any DST
            dst_pool = self.player_pool[self.player_pool['Position'] == 'DST']
            dst_pool = dst_pool[dst_pool['Salary'] <= budget]
            
        if dst_pool.empty:
            return None
            
        dst = self._pick_random_weighted(dst_pool)
        lineup.append(dst)
        budget -= dst['Salary']
        
        # Calculate totals
        total_proj = sum(p['Projection'] for p in lineup)
        total_sal = sum(p['Salary'] for p in lineup)
        total_own = sum(p['Ownership'] for p in lineup)
        
        return {
            'players': lineup,
            'total_projection': total_proj,
            'total_salary': total_sal,
            'total_ownership': total_own,
            'avg_ownership': total_own / 9,
            'salary_remaining': SALARY_CAP - total_sal
        }
    
    def _pick_random_weighted(self, pool):
        """Pick player with randomized weighting by value"""
        pool = pool.copy()
        pool['pick_score'] = pool['value_score'] * np.random.uniform(0.85, 1.15, len(pool))
        return pool.nlargest(1, 'pick_score').iloc[0].to_dict()
