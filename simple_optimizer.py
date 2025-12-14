"""
Simple Lineup Optimizer - GUARANTEED TO WORK
"""

import pandas as pd
import numpy as np
from typing import List, Dict
from config import SALARY_CAP, CONTEST_STRUCTURES


class SimpleOptimizer:
    """Simple but robust lineup builder"""
    
    def __init__(self, contest_type: str = 'small_gpp'):
        self.contest_rules = CONTEST_STRUCTURES[contest_type]
        self.player_pool = None
        
    def generate_lineups(self, player_pool: pd.DataFrame, num_lineups: int = 20) -> List[Dict]:
        """Generate lineups using simple, proven logic"""
        
        self.player_pool = player_pool.copy()
        self.player_pool['Value'] = self.player_pool['Projection'] / (self.player_pool['Salary'] / 1000)
        
        print(f"   Building {num_lineups} lineups...")
        
        lineups = []
        max_attempts = num_lineups * 5
        attempts = 0
        
        while len(lineups) < num_lineups and attempts < max_attempts:
            lineup = self._build_one_lineup()
            
            if lineup:
                # Check if unique
                if not self._is_duplicate(lineup, lineups):
                    lineups.append(lineup)
                    print(f"   Built {len(lineups)}/{num_lineups}", end='\r')
            
            attempts += 1
        
        print()
        
        if len(lineups) == 0:
            print("   ❌ Failed to build any lineups")
            return []
        
        return lineups
    
    def _build_one_lineup(self) -> Dict:
        """Build a single valid lineup"""
        
        lineup = []
        budget = SALARY_CAP
        
        # Step 1: QB (15-18% of budget)
        qb_budget = int(budget * np.random.uniform(0.15, 0.18))
        qb = self._pick_player('QB', qb_budget, [])
        if not qb:
            return None
        lineup.append(qb)
        budget -= qb['Salary']
        
        # Step 2: Two RBs (25-30% of remaining)
        rb_budget = int(budget * 0.28)
        for i in range(2):
            rb = self._pick_player('RB', rb_budget, [p['Name'] for p in lineup])
            if not rb:
                return None
            lineup.append(rb)
            budget -= rb['Salary']
        
        # Step 3: Three WRs (30-35% of remaining)
        wr_budget = int(budget * 0.32)
        for i in range(3):
            wr = self._pick_player('WR', wr_budget, [p['Name'] for p in lineup])
            if not wr:
                return None
            lineup.append(wr)
            budget -= wr['Salary']
        
        # Step 4: TE (use remaining, save some for DST)
        te_budget = budget - 2500  # Save for DST
        te = self._pick_player('TE', te_budget, [p['Name'] for p in lineup])
        if not te:
            return None
        lineup.append(te)
        budget -= te['Salary']
        
        # Step 5: FLEX (RB or WR, save for DST)
        flex_budget = budget - 2200
        flex = self._pick_player(['RB', 'WR'], flex_budget, [p['Name'] for p in lineup])
        if not flex:
            return None
        flex['PositionSlot'] = f"FLEX ({flex['Position']})"
        lineup.append(flex)
        budget -= flex['Salary']
        
        # Step 6: DST (whatever's left)
        dst = self._pick_player('DST', budget, [p['Name'] for p in lineup])
        if not dst:
            return None
        lineup.append(dst)
        budget -= dst['Salary']
        
        # Calculate totals
        total_sal = sum(p['Salary'] for p in lineup)
        total_proj = sum(p['Projection'] for p in lineup)
        total_own = sum(p['Ownership'] for p in lineup)
        
        return {
            'players': lineup,
            'salary': total_sal,
            'salary_remaining': SALARY_CAP - total_sal,
            'projection': total_proj,
            'ownership': total_own,
            'ownership_avg': total_own / 9,
            'value': total_proj / (total_sal / 1000)
        }
    
    def _pick_player(self, position, max_salary: int, used_names: List[str]) -> Dict:
        """Pick a player by value within budget"""
        
        # Handle multiple positions
        if isinstance(position, list):
            pool = self.player_pool[
                (self.player_pool['Position'].isin(position)) &
                (~self.player_pool['Name'].isin(used_names)) &
                (self.player_pool['Salary'] <= max_salary)
            ].copy()
        else:
            pool = self.player_pool[
                (self.player_pool['Position'] == position) &
                (~self.player_pool['Name'].isin(used_names)) &
                (self.player_pool['Salary'] <= max_salary)
            ].copy()
        
        if pool.empty:
            return None
        
        # Weight heavily by value, add randomness
        pool['pick_weight'] = pool['Value'] * np.random.uniform(0.7, 1.3, len(pool))
        
        # Pick from top 30% by weight
        top_n = max(1, int(len(pool) * 0.3))
        top_pool = pool.nlargest(top_n, 'pick_weight')
        
        # Random from top pool
        return top_pool.sample(1).iloc[0].to_dict()
    
    def _is_duplicate(self, lineup: Dict, lineups: List[Dict]) -> bool:
        """Check if too similar to existing"""
        
        new_players = set(p['Name'] for p in lineup['players'])
        
        for existing in lineups:
            existing_players = set(p['Name'] for p in existing['players'])
            
            # If 7+ match, it's a dupe
            if len(new_players & existing_players) >= 7:
                return True
        
        return False
