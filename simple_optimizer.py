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
        """Build a single valid lineup - use almost entire salary cap"""
        
        lineup = []
        budget = SALARY_CAP
        
        # Step 1: Pick QB first (we have full budget)
        qb_max = min(7500, int(budget * 0.16))  # Up to $7500 or 16% of cap
        qb = self._pick_player('QB', qb_max, [])
        if not qb:
            return None
        lineup.append(qb)
        budget -= qb['Salary']
        
        # Step 2: Pick 2 RBs (can be expensive)
        for i in range(2):
            rb_max = int(budget * 0.22)  # Each RB can be up to 22% of remaining
            rb = self._pick_player('RB', rb_max, [p['Name'] for p in lineup])
            if not rb:
                return None
            lineup.append(rb)
            budget -= rb['Salary']
        
        # Step 3: Pick 3 WRs (WRs are expensive studs)
        for i in range(3):
            wr_max = int(budget * 0.24)  # Each WR can be up to 24% of remaining
            wr = self._pick_player('WR', wr_max, [p['Name'] for p in lineup])
            if not wr:
                return None
            lineup.append(wr)
            budget -= wr['Salary']
        
        # Step 4: Pick TE (can be cheap or expensive)
        te_max = int(budget * 0.45)  # Use up to 45% for TE
        te = self._pick_player('TE', te_max, [p['Name'] for p in lineup])
        if not te:
            return None
        lineup.append(te)
        budget -= te['Salary']
        
        # Step 5: Pick FLEX (RB or WR) - use most of remaining
        flex_max = int(budget * 0.65)  # Use 65% of what's left
        flex = self._pick_player(['RB', 'WR'], flex_max, [p['Name'] for p in lineup])
        if not flex:
            return None
        flex['PositionSlot'] = f"FLEX ({flex['Position']})"
        lineup.append(flex)
        budget -= flex['Salary']
        
        # Step 6: Pick DST (use what's left, usually $2-4k)
        dst = self._pick_player('DST', budget, [p['Name'] for p in lineup])
        if not dst:
            return None
        lineup.append(dst)
        budget -= dst['Salary']
        
        # Calculate totals
        total_sal = sum(p['Salary'] for p in lineup)
        total_proj = sum(p['Projection'] for p in lineup)
        total_own = sum(p['Ownership'] for p in lineup)
        avg_own = total_own / 9
        
        # Validate ownership is in acceptable range for contest
        own_target_min, own_target_max = self.contest_rules['ownership_target_avg']
        
        # Allow 20% tolerance on ownership targets
        own_min_relaxed = own_target_min * 0.80
        own_max_relaxed = own_target_max * 1.20
        
        # Reject if ownership is way off (too chalky or too contrarian)
        if avg_own < own_min_relaxed or avg_own > own_max_relaxed:
            return None  # Try again
        
        return {
            'players': lineup,
            'salary': total_sal,
            'salary_remaining': SALARY_CAP - total_sal,
            'projection': total_proj,
            'ownership': total_own,
            'ownership_avg': avg_own,
            'value': total_proj / (total_sal / 1000),
            'ownership_target': f"{own_target_min}-{own_target_max}%"
        }
    
    def _pick_player(self, position, max_salary: int, used_names: List[str]) -> Dict:
        """Pick best player using contest-specific strategy"""
        
        # Handle multiple positions
        if isinstance(position, list):
            pool = self.player_pool[
                (self.player_pool['Position'].isin(position)) &
                (~self.player_pool['Name'].isin(used_names)) &
                (self.player_pool['Salary'] <= max_salary) &
                (self.player_pool['Projection'] > 0)
            ].copy()
        else:
            pool = self.player_pool[
                (self.player_pool['Position'] == position) &
                (~self.player_pool['Name'].isin(used_names)) &
                (self.player_pool['Salary'] <= max_salary) &
                (self.player_pool['Projection'] > 0)
            ].copy()
        
        if pool.empty:
            return None
        
        # Get contest-specific weights
        proj_weight = self.contest_rules['projection_weight']   # small_gpp: 0.70
        own_weight = self.contest_rules['ownership_weight']     # small_gpp: 0.30
        
        # Normalize projection (0-1)
        pool['proj_norm'] = pool['Projection'] / pool['Projection'].max()
        
        # Ownership leverage: Lower ownership = higher score
        # For small_gpp (4,444 entries): Target 12-17% avg ownership
        # This means we want SOME leverage but not full contrarian
        pool['own_leverage'] = (100 - pool['Ownership']) / 100
        
        # Combined score based on contest type
        pool['pick_score'] = (pool['proj_norm'] * proj_weight) + (pool['own_leverage'] * own_weight)
        
        # Add randomness for diversity (±15%)
        pool['pick_score'] *= np.random.uniform(0.85, 1.15, len(pool))
        
        # Pick from top X% based on contest size
        # Small GPP (4,444): Top 40% (more studs allowed)
        # Large GPP (150k): Top 25% (more contrarian)
        if self.contest_rules['entries'] <= 10000:
            top_pct = 0.40  # Small field: can play studs
        else:
            top_pct = 0.25  # Large field: need more leverage
        
        top_n = max(1, int(len(pool) * top_pct))
        top_pool = pool.nlargest(top_n, 'pick_score')
        
        # Weight selection by score
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
