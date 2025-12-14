"""
Lineup Optimizer
Generates optimal DFS lineups with stacking constraints
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from itertools import combinations
from config import SALARY_CAP, DRAFTKINGS_POSITIONS, CONTEST_STRUCTURES


class LineupOptimizer:
    """Build optimal DFS lineups with correlation and ownership constraints"""
    
    def __init__(self, contest_type: str = 'small_gpp'):
        self.contest_rules = CONTEST_STRUCTURES[contest_type]
        self.player_pool = None
        
    def generate_lineups(self, 
                        player_pool: pd.DataFrame,
                        num_lineups: int = 20,
                        contest_type: str = None) -> List[Dict]:
        """
        Generate optimal lineups for contest using table-based approach
        """
        if contest_type:
            self.contest_rules = CONTEST_STRUCTURES[contest_type]
            
        self.player_pool = player_pool.copy()
        
        # Ensure we have clean data
        self.player_pool = self.player_pool.dropna(subset=['Name', 'Position', 'Salary', 'Projection', 'Ownership'])
        
        # Add value column for smart selection
        self.player_pool['Value'] = self.player_pool['Projection'] / (self.player_pool['Salary'] / 1000)
        
        print(f"   Player pool: {len(self.player_pool)} players")
        position_counts = self.player_pool['Position'].value_counts().to_dict()
        print(f"   Positions: {position_counts}")
        
        # Validate we have enough players
        min_required = {'QB': 1, 'RB': 3, 'WR': 4, 'TE': 2, 'DST': 1}
        for pos, min_count in min_required.items():
            actual = position_counts.get(pos, 0)
            if actual < min_count:
                print(f"   ❌ Not enough {pos} players (need {min_count}, have {actual})")
                return []
        
        # Generate lineup candidates
        candidates = []
        attempts = 0
        max_attempts = num_lineups * 20  # Much more aggressive attempts
        
        print(f"   Generating lineups (up to {max_attempts} attempts)...")
        
        while len(candidates) < num_lineups and attempts < max_attempts:
            try:
                lineup = self._build_lineup_from_table()
                
                if lineup and self._is_valid_lineup(lineup):
                    if not self._is_duplicate(lineup, candidates):
                        candidates.append(lineup)
                        if len(candidates) % 5 == 0:  # Progress every 5 lineups
                            print(f"   Generated {len(candidates)}/{num_lineups} lineups", end='\r')
            except Exception as e:
                # Debug: show first error
                if attempts == 0:
                    print(f"   First error: {e}")
            
            attempts += 1
        
        print()  # New line
        
        if len(candidates) == 0:
            print(f"   ❌ Failed to generate any valid lineups after {attempts} attempts")
            return []
        
        if len(candidates) < num_lineups:
            print(f"   ⚠️  Only generated {len(candidates)}/{num_lineups} lineups")
        
        # Score and rank lineups
        scored_lineups = self._score_lineups(candidates)
        
        return scored_lineups[:num_lineups]
    
    def _build_lineup_from_table(self) -> Dict:
        """Build a single lineup using pure DataFrame operations (FAST)"""
        
        # Start with empty lineup
        lineup_players = []
        remaining_salary = SALARY_CAP
        
        # Step 1: Select QB (crucial decision)
        qb_pool = self.player_pool[
            (self.player_pool['Position'] == 'QB') &
            (self.player_pool['Salary'] <= remaining_salary * 0.20)  # Max 20% of cap
        ].copy()
        
        if qb_pool.empty:
            return None
        
        # Weight by value with some randomness
        qb_pool['weight'] = qb_pool['Value'] * np.random.uniform(0.8, 1.2, len(qb_pool))
        qb = qb_pool.nlargest(1, 'weight').iloc[0]
        lineup_players.append(qb.to_dict())
        remaining_salary -= qb['Salary']
        
        # Get QB's team for stacking
        qb_team = qb['Team']
        
        # Step 2: Stack with 2 pass catchers from QB's team
        stack_pool = self.player_pool[
            (self.player_pool['Team'] == qb_team) &
            (self.player_pool['Position'].isin(['WR', 'TE'])) &
            (self.player_pool['Salary'] <= remaining_salary * 0.4)  # Leave room for rest
        ].copy()
        
        stack_count = min(2, len(stack_pool))
        if stack_count > 0:
            stack_pool['weight'] = stack_pool['Value'] * np.random.uniform(0.8, 1.2, len(stack_pool))
            stack_players = stack_pool.nlargest(stack_count, 'weight')
            
            for _, player in stack_players.iterrows():
                lineup_players.append(player.to_dict())
                remaining_salary -= player['Salary']
        
        # Step 3: Fill RBs (need at least 2)
        used_names = [p['Name'] for p in lineup_players]
        rb_pool = self.player_pool[
            (self.player_pool['Position'] == 'RB') &
            (~self.player_pool['Name'].isin(used_names)) &
            (self.player_pool['Salary'] <= remaining_salary * 0.35)
        ].copy()
        
        rb_needed = 2
        if len(rb_pool) >= rb_needed:
            rb_pool['weight'] = rb_pool['Value'] * np.random.uniform(0.8, 1.2, len(rb_pool))
            rbs = rb_pool.nlargest(rb_needed, 'weight')
            
            for _, player in rbs.iterrows():
                lineup_players.append(player.to_dict())
                remaining_salary -= player['Salary']
        else:
            return None
        
        # Step 4: Fill remaining WRs (need total of 3)
        used_names = [p['Name'] for p in lineup_players]
        current_wrs = sum(1 for p in lineup_players if p['Position'] == 'WR')
        wr_needed = 3 - current_wrs
        
        if wr_needed > 0:
            wr_pool = self.player_pool[
                (self.player_pool['Position'] == 'WR') &
                (~self.player_pool['Name'].isin(used_names)) &
                (self.player_pool['Salary'] <= remaining_salary * 0.35)
            ].copy()
            
            if len(wr_pool) >= wr_needed:
                wr_pool['weight'] = wr_pool['Value'] * np.random.uniform(0.8, 1.2, len(wr_pool))
                wrs = wr_pool.nlargest(wr_needed, 'weight')
                
                for _, player in wrs.iterrows():
                    lineup_players.append(player.to_dict())
                    remaining_salary -= player['Salary']
            else:
                return None
        
        # Step 5: Fill TE if not already have one from stack
        current_tes = sum(1 for p in lineup_players if p['Position'] == 'TE')
        if current_tes == 0:
            used_names = [p['Name'] for p in lineup_players]
            te_pool = self.player_pool[
                (self.player_pool['Position'] == 'TE') &
                (~self.player_pool['Name'].isin(used_names)) &
                (self.player_pool['Salary'] <= remaining_salary * 0.35)
            ].copy()
            
            if not te_pool.empty:
                te_pool['weight'] = te_pool['Value'] * np.random.uniform(0.8, 1.2, len(te_pool))
                te = te_pool.nlargest(1, 'weight').iloc[0]
                lineup_players.append(te.to_dict())
                remaining_salary -= te['Salary']
            else:
                return None
        
        # Step 6: Fill FLEX (RB/WR/TE) - prefer RB or WR over TE
        used_names = [p['Name'] for p in lineup_players]
        
        # Count current positions to avoid duplicates
        current_positions = {}
        for p in lineup_players:
            pos = p['Position']
            current_positions[pos] = current_positions.get(pos, 0) + 1
        
        # We already have 1 TE required, so for FLEX prefer RB/WR
        # Only use TE in FLEX if we have good value
        flex_positions = ['RB', 'WR']
        
        # Add TE to flex options with lower probability
        if np.random.random() < 0.15:  # Only 15% chance to consider TE for FLEX
            flex_positions.append('TE')
        
        flex_pool = self.player_pool[
            (self.player_pool['Position'].isin(flex_positions)) &
            (~self.player_pool['Name'].isin(used_names)) &
            (self.player_pool['Salary'] <= remaining_salary * 0.5)
        ].copy()
        
        if not flex_pool.empty:
            flex_pool['weight'] = flex_pool['Value'] * np.random.uniform(0.8, 1.2, len(flex_pool))
            flex = flex_pool.nlargest(1, 'weight').iloc[0]
            lineup_players.append(flex.to_dict())
            remaining_salary -= flex['Salary']
        else:
            return None
        
        # Step 7: Fill DST (usually cheap)
        used_names = [p['Name'] for p in lineup_players]
        dst_pool = self.player_pool[
            (self.player_pool['Position'] == 'DST') &
            (~self.player_pool['Name'].isin(used_names)) &
            (self.player_pool['Salary'] <= remaining_salary)
        ].copy()
        
        if not dst_pool.empty:
            dst_pool['weight'] = dst_pool['Value'] * np.random.uniform(0.8, 1.2, len(dst_pool))
            dst = dst_pool.nlargest(1, 'weight').iloc[0]
            lineup_players.append(dst.to_dict())
            remaining_salary -= dst['Salary']
        else:
            return None
        
        # Build final lineup dict
        total_salary = sum(p['Salary'] for p in lineup_players)
        total_proj = sum(p['Projection'] for p in lineup_players)
        total_own = sum(p['Ownership'] for p in lineup_players)
        
        return {
            'players': lineup_players,
            'salary': total_salary,
            'projection': total_proj,
            'ownership': total_own,
            'stack_size': 3  # QB + 2
        }
    
    
    def _is_valid_lineup(self, lineup: Dict) -> bool:
        """Check if lineup meets all constraints"""
        
        if lineup is None:
            return False
        
        # Check salary cap (allow up to $50k, use at least $48k)
        if lineup['salary'] > SALARY_CAP or lineup['salary'] < 48000:
            return False
        
        # Check ownership range (relaxed - allow wider range)
        own_min, own_max = self.contest_rules['ownership_target_total']
        own_min_relaxed = own_min * 0.7  # Allow 30% below target
        own_max_relaxed = own_max * 1.3  # Allow 30% above target
        
        if not (own_min_relaxed <= lineup['ownership'] <= own_max_relaxed):
            return False
        
        # Check projection range (relaxed)
        proj_min, proj_max = self.contest_rules['projection_target']
        proj_min_relaxed = proj_min * 0.9  # Allow 10% below
        proj_max_relaxed = proj_max * 1.1  # Allow 10% above
        
        if not (proj_min_relaxed <= lineup['projection'] <= proj_max_relaxed):
            return False
        
        # Basic position count check
        position_counts = {}
        for p in lineup['players']:
            pos = p['Position']
            position_counts[pos] = position_counts.get(pos, 0) + 1
        
        # Must have QB
        if position_counts.get('QB', 0) != 1:
            return False
        
        # Must have at least 2 RBs (including FLEX)
        if position_counts.get('RB', 0) < 2:
            return False
        
        # Must have at least 3 WRs (including FLEX)
        if position_counts.get('WR', 0) < 3:
            return False
        
        # Must have exactly 1 TE (not 2)
        if position_counts.get('TE', 0) != 1:
            return False
        
        # Must have DST
        if position_counts.get('DST', 0) != 1:
            return False
        
        # Should have exactly 9 players
        if len(lineup['players']) != 9:
            return False
        
        return True
    
    def _is_duplicate(self, lineup: Dict, existing: List[Dict]) -> bool:
        """Check if lineup is duplicate of existing lineup"""
        
        lineup_players = set(p['Name'] for p in lineup['players'])
        
        for existing_lineup in existing:
            existing_players = set(p['Name'] for p in existing_lineup['players'])
            
            # If 7+ players match, consider it a duplicate
            if len(lineup_players & existing_players) >= 7:
                return True
        
        return False
    
    def _score_lineups(self, lineups: List[Dict]) -> List[Dict]:
        """
        Score and rank lineups
        Higher score = better for the contest type
        """
        
        for lineup in lineups:
            # Score combines projection and ownership based on contest type
            proj_weight = self.contest_rules['projection_weight']
            own_weight = self.contest_rules['ownership_weight']
            
            # Normalize projection (higher is better)
            proj_score = lineup['projection'] / 150  # Normalize to ~0-1
            
            # Ownership score depends on contest type
            # For top-heavy: want low but not too low (sweet spot at ~13%)
            # For GPP: lower is better
            own_avg = lineup['ownership'] / 9
            own_target_min, own_target_max = self.contest_rules['ownership_target_avg']
            own_target = (own_target_min + own_target_max) / 2
            
            # Score based on distance from target
            own_score = 1 - abs(own_avg - own_target) / own_target
            own_score = max(0, own_score)
            
            # Combined score
            lineup['score'] = (proj_score * proj_weight) + (own_score * own_weight)
        
        # Sort by score descending
        lineups.sort(key=lambda x: x['score'], reverse=True)
        
        return lineups
