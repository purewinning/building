"""
ULTRA SIMPLE Lineup Builder - GUARANTEED TO WORK
"""

import pandas as pd
import numpy as np

SALARY_CAP = 50000

class BasicOptimizer:
    def __init__(self, contest_type):
        self.contest_type = contest_type
        
    def generate_lineups(self, player_pool, num_lineups=20):
        """Generate valid lineups"""
        self.player_pool = player_pool
        lineups = []
        
        for i in range(num_lineups * 10):  # Try up to 10x
            lineup = self._build_lineup()
            if lineup:
                lineups.append(lineup)
            if len(lineups) >= num_lineups:
                break
                
        return lineups if lineups else None
    
    def _build_lineup(self):
        """Build one valid lineup - SIMPLE VALUE-BASED"""
        lineup = []
        budget = SALARY_CAP
        used = []
        
        # Get pools for each position
        qb_pool = self.player_pool[self.player_pool['Position'] == 'QB'].copy()
        rb_pool = self.player_pool[self.player_pool['Position'] == 'RB'].copy()
        wr_pool = self.player_pool[self.player_pool['Position'] == 'WR'].copy()
        te_pool = self.player_pool[self.player_pool['Position'] == 'TE'].copy()
        dst_pool = self.player_pool[self.player_pool['Position'] == 'DST'].copy()
        
        # Add value score (projection per $1k)
        for pool in [qb_pool, rb_pool, wr_pool, te_pool, dst_pool]:
            pool['value_score'] = pool['Projection'] / (pool['Salary'] / 1000)
            pool['random_factor'] = np.random.uniform(0.8, 1.2, len(pool))
            pool['pick_score'] = pool['value_score'] * pool['random_factor']
        
        # Pick by value, avoiding salary cap issues
        # QB - mid-priced
        qb = qb_pool[(qb_pool['Salary'] >= 5000) & (qb_pool['Salary'] <= 7500)].nlargest(1, 'pick_score')
        if qb.empty: return None
        lineup.append(qb.iloc[0].to_dict())
        budget -= qb.iloc[0]['Salary']
        used.append(qb.iloc[0]['Name'])
        
        # RB1 - value pick
        rb1 = rb_pool[(rb_pool['Salary'] <= min(9000, budget - 35000)) & (~rb_pool['Name'].isin(used))].nlargest(1, 'pick_score')
        if rb1.empty: return None
        lineup.append(rb1.iloc[0].to_dict())
        budget -= rb1.iloc[0]['Salary']
        used.append(rb1.iloc[0]['Name'])
        
        # RB2 - value pick
        rb2 = rb_pool[(rb_pool['Salary'] <= min(8000, budget - 27000)) & (~rb_pool['Name'].isin(used))].nlargest(1, 'pick_score')
        if rb2.empty: return None
        lineup.append(rb2.iloc[0].to_dict())
        budget -= rb2.iloc[0]['Salary']
        used.append(rb2.iloc[0]['Name'])
        
        # WR1
        wr1 = wr_pool[(wr_pool['Salary'] <= min(9000, budget - 20000)) & (~wr_pool['Name'].isin(used))].nlargest(1, 'pick_score')
        if wr1.empty: return None
        lineup.append(wr1.iloc[0].to_dict())
        budget -= wr1.iloc[0]['Salary']
        used.append(wr1.iloc[0]['Name'])
        
        # WR2
        wr2 = wr_pool[(wr_pool['Salary'] <= min(8000, budget - 13000)) & (~wr_pool['Name'].isin(used))].nlargest(1, 'pick_score')
        if wr2.empty: return None
        lineup.append(wr2.iloc[0].to_dict())
        budget -= wr2.iloc[0]['Salary']
        used.append(wr2.iloc[0]['Name'])
        
        # WR3
        wr3 = wr_pool[(wr_pool['Salary'] <= min(7000, budget - 8500)) & (~wr_pool['Name'].isin(used))].nlargest(1, 'pick_score')
        if wr3.empty: return None
        lineup.append(wr3.iloc[0].to_dict())
        budget -= wr3.iloc[0]['Salary']
        used.append(wr3.iloc[0]['Name'])
        
        # TE
        te = te_pool[(te_pool['Salary'] <= min(7000, budget - 5000)) & (~te_pool['Name'].isin(used))].nlargest(1, 'pick_score')
        if te.empty: return None
        lineup.append(te.iloc[0].to_dict())
        budget -= te.iloc[0]['Salary']
        used.append(te.iloc[0]['Name'])
        
        # FLEX - any RB/WR/TE
        flex_pool = pd.concat([rb_pool, wr_pool, te_pool])
        flex = flex_pool[(flex_pool['Salary'] <= budget - 2500) & (~flex_pool['Name'].isin(used))].nlargest(1, 'pick_score')
        if flex.empty: return None
        flex_player = flex.iloc[0].to_dict()
        flex_player['PositionSlot'] = f"FLEX ({flex_player['Position']})"
        lineup.append(flex_player)
        budget -= flex.iloc[0]['Salary']
        used.append(flex.iloc[0]['Name'])
        
        # DST
        dst = dst_pool[dst_pool['Salary'] <= budget].nlargest(1, 'pick_score')
        if dst.empty: return None
        lineup.append(dst.iloc[0].to_dict())
        budget -= dst.iloc[0]['Salary']
        
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
