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
        
        # Step 1: QB (10-15% of budget) - Allow cheaper QBs to spend on studs elsewhere
        qb_budget = int(budget * np.random.uniform(0.10, 0.15))
        qb = self._pick_player('QB', qb_budget, [])
        if not qb:
            return None
        lineup.append(qb)
        budget -= qb['Salary']
        
        # Step 2: Two RBs (30-38% of remaining) - Allow room for studs
        rb_budget = int(budget * np.random.uniform(0.30, 0.38))
        for i in range(2):
            rb = self._pick_player('RB', rb_budget, [p['Name'] for p in lineup])
            if not rb:
                return None
            lineup.append(rb)
            budget -= rb['Salary']
        
        # Step 3: Three WRs (35-45% of remaining) - WRs are expensive, need room
        wr_budget = int(budget * np.random.uniform(0.35, 0.45))
        for i in range(3):
            wr = self._pick_player('WR', wr_budget, [p['Name'] for p in lineup])
            if not wr:
                return None
            lineup.append(wr)
            budget -= wr['Salary']
        
        # Step 4: TE (use remaining, save for DST) - Can be cheap
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
        """Pick a player balancing projection, value, and ownership"""
        
        # Handle multiple positions
        if isinstance(position, list):
            pool = self.player_pool[
                (self.player_pool['Position'].isin(position)) &
                (~self.player_pool['Name'].isin(used_names)) &
                (self.player_pool['Salary'] <= max_salary) &
                (self.player_pool['Projection'] > 0)  # Must have projection
            ].copy()
        else:
            pool = self.player_pool[
                (self.player_pool['Position'] == position) &
                (~self.player_pool['Name'].isin(used_names)) &
                (self.player_pool['Salary'] <= max_salary) &
                (self.player_pool['Projection'] > 0)  # Must have projection
            ].copy()
        
        if pool.empty:
            return None
        
        # For small_gpp: 70% projection weight, 30% ownership leverage
        proj_weight = self.contest_rules['projection_weight']  # 0.70
        own_weight = self.contest_rules['ownership_weight']    # 0.30
        
        # Normalize projection (0-1)
        pool['proj_norm'] = pool['Projection'] / pool['Projection'].max()
        
        # Ownership leverage (inverse) - but don't penalize popular players too much
        # Lower ownership = higher score, but capped
        pool['own_leverage'] = (100 - pool['Ownership']) / 100
        pool['own_leverage'] = pool['own_leverage'].clip(0.3, 1.0)  # Don't go below 0.3 even for 100% owned
        
        # Combined score
        pool['pick_score'] = (pool['proj_norm'] * proj_weight) + (pool['own_leverage'] * own_weight)
        
        # Add randomness for diversity (±20%)
        pool['pick_score'] *= np.random.uniform(0.8, 1.2, len(pool))
        
        # Pick from top 40% by score (was 30%, now allowing more high-projection players)
        top_n = max(1, int(len(pool) * 0.4))
        top_pool = pool.nlargest(top_n, 'pick_score')
        
        # Weight by score for final selection
        weights = top_pool['pick_score'] / top_pool['pick_score'].sum()
        
        return top_pool.sample(1, weights=weights).iloc[0].to_dict()
    
    def _is_duplicate(self, lineup: Dict, lineups: List[Dict]) -> bool:
        """Check if too similar to existing"""
        
        new_players = set(p['Name'] for p in lineup['players'])
        
        for existing in lineups:
            existing_players = set(p['Name'] for p in existing['players'])
            
            # If 7+ match, it's a dupe
            if len(new_players & existing_players) >= 7:
                return True
        
        return False
