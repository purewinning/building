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
        Generate optimal lineups for contest
        
        Args:
            player_pool: DataFrame with [Name, Position, Salary, Projection, Ownership, Team]
            num_lineups: Number of unique lineups to generate
            contest_type: Override contest type from initialization
            
        Returns:
            List of lineup dicts
        """
        if contest_type:
            self.contest_rules = CONTEST_STRUCTURES[contest_type]
            
        self.player_pool = player_pool.copy()
        
        print(f"   Player pool: {len(self.player_pool)} players")
        print(f"   Positions: {self.player_pool['Position'].value_counts().to_dict()}")
        
        # Generate lineup candidates
        candidates = []
        attempts = 0
        max_attempts = num_lineups * 50  # Reduced from 100 to 50
        
        while len(candidates) < num_lineups and attempts < max_attempts:
            try:
                lineup = self._build_single_lineup()
                
                if lineup and self._is_valid_lineup(lineup):
                    # Check if unique
                    if not self._is_duplicate(lineup, candidates):
                        candidates.append(lineup)
                        print(f"   Generated {len(candidates)}/{num_lineups} lineups", end='\r')
            except Exception as e:
                pass  # Silently continue on individual lineup failures
            
            attempts += 1
        
        print()  # New line
        
        if len(candidates) == 0:
            print(f"   ⚠️ Failed to generate any valid lineups after {attempts} attempts")
            print(f"   Check that player pool has enough players in each position")
            return []
        
        if len(candidates) < num_lineups:
            print(f"   ⚠️ Only generated {len(candidates)}/{num_lineups} lineups")
        
        # Score and rank lineups
        scored_lineups = self._score_lineups(candidates)
        
        return scored_lineups[:num_lineups]
    
    def _build_single_lineup(self) -> Dict:
        """Build a single lineup with stacking constraints"""
        
        # Step 1: Select QB (most important decision)
        qb = self._select_qb()
        if qb is None:
            return None
        
        # Step 2: Build stack around QB
        stack_players = self._build_stack(qb)
        if not stack_players:
            return None
        
        # Step 3: Fill remaining positions
        lineup = self._fill_remaining_positions(qb, stack_players)
        
        return lineup
    
    def _select_qb(self) -> pd.Series:
        """
        Select QB based on contest rules and value
        """
        qbs = self.player_pool[self.player_pool['Position'] == 'QB'].copy()
        
        if qbs.empty:
            return None
        
        # Filter by ownership constraints
        max_own = self.contest_rules['qb_ownership_max']
        pref_min, pref_max = self.contest_rules['qb_ownership_preferred']
        
        # Prefer QBs in preferred range
        preferred_qbs = qbs[
            (qbs['Ownership'] >= pref_min) & 
            (qbs['Ownership'] <= pref_max)
        ]
        
        if not preferred_qbs.empty:
            # Weight by value (projection per $1k), not just projection
            preferred_qbs['TempValue'] = preferred_qbs['Projection'] / (preferred_qbs['Salary'] / 1000)
            weights = preferred_qbs['TempValue'] / preferred_qbs['TempValue'].sum()
            qb = preferred_qbs.sample(n=1, weights=weights).iloc[0]
        else:
            # Fall back to any QB under max ownership
            valid_qbs = qbs[qbs['Ownership'] <= max_own]
            if valid_qbs.empty:
                return None
            valid_qbs['TempValue'] = valid_qbs['Projection'] / (valid_qbs['Salary'] / 1000)
            weights = valid_qbs['TempValue'] / valid_qbs['TempValue'].sum()
            qb = valid_qbs.sample(n=1, weights=weights).iloc[0]
        
        return qb
    
    def _build_stack(self, qb: pd.Series) -> List[pd.Series]:
        """
        Build correlated stack with QB
        Returns list of pass catchers from same team
        """
        qb_team = qb['Team']
        
        # Get all pass catchers from same team
        teammates = self.player_pool[
            (self.player_pool['Team'] == qb_team) &
            (self.player_pool['Position'].isin(['WR', 'TE', 'RB']))
        ].copy()
        
        # Determine stack size based on contest rules
        stack_types = self.contest_rules['qb_stack_type']
        
        # Prefer QB + 2 if allowed
        if 'QB + 2' in stack_types:
            target_stack_size = 2
        elif 'QB + 3' in stack_types:
            target_stack_size = 3
        else:
            target_stack_size = 1
        
        # Prioritize WRs and TEs over RBs for correlation
        pass_catchers = teammates[teammates['Position'].isin(['WR', 'TE'])]
        
        if len(pass_catchers) < target_stack_size:
            return []
        
        # Select top projected pass catchers with some randomness
        pass_catchers = pass_catchers.sort_values('Projection', ascending=False)
        
        # Take top options but add some variation
        stack_size = np.random.choice([target_stack_size, target_stack_size - 1, target_stack_size + 1])
        stack_size = max(1, min(stack_size, len(pass_catchers), 3))
        
        # Weight by projection
        weights = pass_catchers['Projection'] / pass_catchers['Projection'].sum()
        selected = pass_catchers.sample(n=stack_size, weights=weights, replace=False)
        
        return selected.to_dict('records')
    
    def _fill_remaining_positions(self, qb: pd.Series, stack: List[Dict]) -> Dict:
        """Fill remaining roster spots"""
        
        lineup = {
            'QB': qb,
            'stack': stack,
            'remaining': []
        }
        
        used_salary = qb['Salary'] + sum(p['Salary'] for p in stack)
        remaining_salary = SALARY_CAP - used_salary
        
        # Count positions filled
        positions_filled = {'QB': 1, 'RB': 0, 'WR': 0, 'TE': 0, 'DST': 0}
        for player in stack:
            positions_filled[player['Position']] += 1
        
        # Determine what positions we still need
        needs = []
        for pos, required in DRAFTKINGS_POSITIONS.items():
            if pos == 'FLEX':
                continue  # Handle FLEX last
            filled = positions_filled.get(pos, 0)
            if filled < required:
                needs.extend([pos] * (required - filled))
        
        # Fill required positions
        for pos in needs:
            player = self._select_player_for_position(
                pos, 
                used_players=[qb['Name']] + [p['Name'] for p in stack],
                budget=remaining_salary
            )
            
            if player is None:
                return None  # Can't build valid lineup
            
            lineup['remaining'].append(player)
            remaining_salary -= player['Salary']
        
        # Fill FLEX (RB/WR/TE)
        flex = self._select_flex(
            used_players=[qb['Name']] + [p['Name'] for p in stack] + [p['Name'] for p in lineup['remaining']],
            budget=remaining_salary
        )
        
        if flex is None:
            return None
        
        lineup['remaining'].append(flex)
        remaining_salary -= flex['Salary']
        
        # Select DST
        dst = self._select_dst(
            used_players=[qb['Name']] + [p['Name'] for p in stack] + [p['Name'] for p in lineup['remaining']],
            budget=remaining_salary
        )
        
        if dst is None:
            return None
        
        lineup['remaining'].append(dst)
        
        return self._format_lineup(lineup)
    
    def _select_player_for_position(self, position: str, used_players: List[str], budget: int) -> Dict:
        """Select best available player for position within budget"""
        
        available = self.player_pool[
            (self.player_pool['Position'] == position) &
            (~self.player_pool['Name'].isin(used_players)) &
            (self.player_pool['Salary'] <= budget)
        ].copy()
        
        if available.empty:
            return None
        
        # For expensive positions early in fill, prefer cheaper options to save cap space
        # Weight by value (pts/$) rather than raw projection
        available['TempValue'] = available['Projection'] / (available['Salary'] / 1000)
        
        # Add some randomness - weight by value but allow variation
        weights = available['TempValue'] ** 2  # Square to emphasize value
        weights = weights / weights.sum()
        
        selected = available.sample(n=1, weights=weights).iloc[0]
        
        return selected.to_dict()
    
    def _select_flex(self, used_players: List[str], budget: int) -> Dict:
        """Select FLEX (RB/WR/TE) - prefer value plays to use remaining budget"""
        available = self.player_pool[
            (self.player_pool['Position'].isin(['RB', 'WR', 'TE'])) &
            (~self.player_pool['Name'].isin(used_players)) &
            (self.player_pool['Salary'] <= budget)
        ].copy()
        
        if available.empty:
            return None
        
        # Weight by value
        available['TempValue'] = available['Projection'] / (available['Salary'] / 1000)
        weights = available['TempValue'] ** 2
        weights = weights / weights.sum()
        
        selected = available.sample(n=1, weights=weights).iloc[0]
        
        return selected.to_dict()
    
    def _select_dst(self, used_players: List[str], budget: int) -> Dict:
        """Select defense - usually min price"""
        available = self.player_pool[
            (self.player_pool['Position'] == 'DST') &
            (~self.player_pool['Name'].isin(used_players)) &
            (self.player_pool['Salary'] <= budget)
        ].copy()
        
        if available.empty:
            return None
        
        # Prefer cheap DSTs (common strategy) but with some variance
        available['TempValue'] = available['Projection'] / (available['Salary'] / 1000)
        weights = available['TempValue']
        weights = weights / weights.sum()
        
        selected = available.sample(n=1, weights=weights).iloc[0]
        
        return selected.to_dict()
    
    def _calculate_selection_weights(self, players: pd.DataFrame) -> pd.Series:
        """Calculate selection probability weights based on contest type"""
        
        proj_weight = self.contest_rules['projection_weight']
        own_weight = self.contest_rules['ownership_weight']
        
        # Normalize projections and inverse ownership
        proj_norm = players['Projection'] / players['Projection'].max()
        own_norm = (100 - players['Ownership']) / 100  # Invert so low ownership = high weight
        
        # Combine weighted
        weights = (proj_norm * proj_weight) + (own_norm * own_weight)
        
        return weights / weights.sum()
    
    def _format_lineup(self, lineup_dict: Dict) -> Dict:
        """Format lineup into standard structure"""
        
        all_players = [lineup_dict['QB']] + lineup_dict['stack'] + lineup_dict['remaining']
        
        # Convert Series/dict to consistent format
        players = []
        for p in all_players:
            if isinstance(p, pd.Series):
                players.append(p.to_dict())
            else:
                players.append(p)
        
        total_salary = sum(p['Salary'] for p in players)
        total_proj = sum(p['Projection'] for p in players)
        total_own = sum(p['Ownership'] for p in players)
        
        return {
            'players': players,
            'salary': total_salary,
            'projection': total_proj,
            'ownership': total_own,
            'stack_size': len(lineup_dict['stack']) + 1  # +1 for QB
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
        
        # Must have TE
        if position_counts.get('TE', 0) < 1:
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
