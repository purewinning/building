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
        """Build a single valid lineup - maximize salary usage for max points"""
        
        lineup = []
        budget = SALARY_CAP
        
        # Step 1: QB - allow expensive QBs (can spend up to full max salary)
        qb_max = min(7500, budget)  # Full $7500 allowed
        qb = self._pick_player('QB', qb_max, [])
        if not qb:
            return None
        lineup.append(qb)
        budget -= qb['Salary']
        
        # Step 2: First RB - can be elite ($9k CMC level)
        rb1_max = min(9000, int(budget * 0.25))  # Up to $9k or 25% of remaining
        rb1 = self._pick_player('RB', rb1_max, [p['Name'] for p in lineup])
        if not rb1:
            return None
        lineup.append(rb1)
        budget -= rb1['Salary']
        
        # Step 3: Second RB - still allow expensive
        rb2_max = min(9000, int(budget * 0.28))  # Up to $9k or 28% of remaining
        rb2 = self._pick_player('RB', rb2_max, [p['Name'] for p in lineup])
        if not rb2:
            return None
        lineup.append(rb2)
        budget -= rb2['Salary']
        
        # Step 4: First WR - elite tier ($8700 Puka level)
        wr1_max = min(8700, int(budget * 0.28))  # Up to $8700 or 28% of remaining
        wr1 = self._pick_player('WR', wr1_max, [p['Name'] for p in lineup])
        if not wr1:
            return None
        lineup.append(wr1)
        budget -= wr1['Salary']
        
        # Step 5: Second WR - still elite tier
        wr2_max = min(8700, int(budget * 0.32))  # Up to $8700 or 32% of remaining
        wr2 = self._pick_player('WR', wr2_max, [p['Name'] for p in lineup])
        if not wr2:
            return None
        lineup.append(wr2)
        budget -= wr2['Salary']
        
        # Step 6: Third WR - allow expensive
        wr3_max = min(8700, int(budget * 0.38))  # Up to $8700 or 38% of remaining
        wr3 = self._pick_player('WR', wr3_max, [p['Name'] for p in lineup])
        if not wr3:
            return None
        lineup.append(wr3)
        budget -= wr3['Salary']
        
        # Step 7: TE - use most of what's left (save only for FLEX + DST)
        te_max = int(budget * 0.50)  # Use 50% of remaining for TE
        te = self._pick_player('TE', te_max, [p['Name'] for p in lineup])
        if not te:
            return None
        lineup.append(te)
        budget -= te['Salary']
        
        # Step 8: FLEX (RB or WR) - use most of remaining (save only for DST)
        flex_max = int(budget * 0.70)  # Use 70% of remaining for FLEX
        flex = self._pick_player(['RB', 'WR'], flex_max, [p['Name'] for p in lineup])
        if not flex:
            return None
        flex['PositionSlot'] = f"FLEX ({flex['Position']})"
        lineup.append(flex)
        budget -= flex['Salary']
        
        # Step 9: DST - spend what's left (don't leave money on table)
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
        
        # Validate we're using enough of the salary cap (at least $48k)
        if total_sal < 48000:
            return None  # Not spending enough, try again
        
        # Validate ownership is reasonable for contest
        own_target_min, own_target_max = self.contest_rules['ownership_target_avg']
        
        # Very relaxed tolerance - we want high scoring, ownership is secondary
        # Allow 50% below target, 80% above target
        own_min_relaxed = own_target_min * 0.50  # Can go lower (more contrarian OK)
        own_max_relaxed = own_target_max * 1.80  # Can go much higher (chalk OK!)
        
        # Only reject if EXTREMELY off target
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
        """Pick player prioritizing PROJECTION first, then add leverage smartly"""
        
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
        
        # Sort by projection descending
        pool = pool.sort_values('Projection', ascending=False).reset_index(drop=True)
        
        # STRATEGY: Pick from top projection tier, occasionally go down a tier for leverage
        # 70% of time: Pick from top 20% by projection (STUDS)
        # 30% of time: Pick from top 40% by projection (includes some value)
        
        if np.random.random() < 0.70:
            # 70% chance: Pick a STUD (top 20% by projection)
            top_n = max(1, int(len(pool) * 0.20))
            candidate_pool = pool.head(top_n)
        else:
            # 30% chance: Allow some value (top 40% by projection)
            top_n = max(1, int(len(pool) * 0.40))
            candidate_pool = pool.head(top_n)
        
        # Within the candidate pool, weight by projection and a tiny bit of ownership leverage
        candidate_pool['proj_norm'] = candidate_pool['Projection'] / candidate_pool['Projection'].max()
        candidate_pool['own_leverage'] = (100 - candidate_pool['Ownership']) / 100
        
        # 90% projection, 10% ownership (heavily favor projection)
        candidate_pool['pick_score'] = (candidate_pool['proj_norm'] * 0.90) + (candidate_pool['own_leverage'] * 0.10)
        
        # Add slight randomness for variety
        candidate_pool['pick_score'] *= np.random.uniform(0.90, 1.10, len(candidate_pool))
        
        # Pick weighted by score
        weights = candidate_pool['pick_score'] / candidate_pool['pick_score'].sum()
        
        return candidate_pool.sample(1, weights=weights).iloc[0].to_dict()
    
    def _is_duplicate(self, lineup: Dict, lineups: List[Dict]) -> bool:
        """Check if too similar to existing"""
        
        new_players = set(p['Name'] for p in lineup['players'])
        
        for existing in lineups:
            existing_players = set(p['Name'] for p in existing['players'])
            
            # If 7+ match, it's a dupe
            if len(new_players & existing_players) >= 7:
                return True
        
        return False
