"""
WINNING STRUCTURE OPTIMIZER
Based on $250K 1st place finish (bryden75, Wildcat 4,170 entries)

Exact replication of winning formula:
1. Ultra-leverage QB (3.7% owned)
2. 3-piece game stack (JAX)
3. Core chalk RB anchor (22.8% owned)
4. Ultra-leverage stacked WR (1.3% owned)
5. Ownership discipline (9.4% avg)
6. Punt TE strategy (70% of time)
7. No heavy chalk (0 players >25%)
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from config import SALARY_CAP, CONTEST_STRUCTURES


class WinningOptimizer:
    """Optimizer that builds lineups using proven winning structure"""
    
    def __init__(self, contest_type: str = 'small_gpp'):
        self.contest_rules = CONTEST_STRUCTURES[contest_type]
        self.player_pool = None
        self.locks = {}
        self.core_rb = None  # The "must-have" RB (like Travis Etienne)
        
    def generate_lineups(self, player_pool: pd.DataFrame, num_lineups: int = 20, locks: dict = None) -> List[Dict]:
        """Generate lineups using winning structure"""
        
        self.player_pool = player_pool.copy()
        self.player_pool['Value'] = self.player_pool['Projection'] / (self.player_pool['Salary'] / 1000)
        self.locks = locks if locks else {}
        
        print(f"   🏆 Building {num_lineups} lineups with WINNING STRUCTURE...")
        print(f"   Strategy: {self.contest_rules['description']}")
        
        # Identify core RB anchor (like Travis Etienne 22.8%)
        self._identify_core_rb()
        
        # Show lock info
        if self.locks:
            locked_count = sum([
                1 if self.locks.get('QB') else 0,
                len(self.locks.get('RB', [])),
                len(self.locks.get('WR', [])),
                1 if self.locks.get('TE') else 0,
                1 if self.locks.get('FLEX') else 0,
                1 if self.locks.get('DST') else 0
            ])
            if locked_count > 0:
                print(f"   🔒 {locked_count} players locked")
        
        if self.core_rb:
            print(f"   ⚓ Core RB Anchor: {self.core_rb['Name']} (${self.core_rb['Salary']:,}, {self.core_rb['Ownership']:.1f}% own)")
        
        lineups = []
        max_attempts = num_lineups * 10
        attempts = 0
        
        # Track which lineup types we've built
        leverage_qb_count = 0
        game_stack_count = 0
        
        while len(lineups) < num_lineups and attempts < max_attempts:
            # Determine lineup type based on percentage targets
            lineup_type = self._determine_lineup_type(
                len(lineups), 
                num_lineups, 
                leverage_qb_count,
                game_stack_count
            )
            
            lineup = self._build_winning_structure(lineup_type)
            
            if lineup:
                # Check if unique and valid
                if not self._is_duplicate(lineup, lineups) and self._validate_winning_structure(lineup):
                    lineups.append(lineup)
                    
                    # Track lineup types
                    if lineup.get('has_leverage_qb'):
                        leverage_qb_count += 1
                    if lineup.get('has_game_stack'):
                        game_stack_count += 1
                    
                    print(f"   Built {len(lineups)}/{num_lineups} [{lineup_type}]", end='\r')
            
            attempts += 1
        
        print()
        
        if len(lineups) == 0:
            print("   ❌ Failed to build any lineups")
            return []
        
        # Show final distribution
        print(f"   ✅ Built {len(lineups)} lineups:")
        print(f"      • Leverage QB: {leverage_qb_count}/{len(lineups)} ({leverage_qb_count/len(lineups)*100:.0f}%)")
        print(f"      • Game Stacks: {game_stack_count}/{len(lineups)} ({game_stack_count/len(lineups)*100:.0f}%)")
        
        return lineups
    
    def _identify_core_rb(self):
        """Identify the core RB anchor (18-25% owned, elite matchup)"""
        
        rb_pool = self.player_pool[
            (self.player_pool['Position'] == 'RB') &
            (self.player_pool['Ownership'] >= self.contest_rules['core_rb_ownership'][0]) &
            (self.player_pool['Ownership'] <= self.contest_rules['core_rb_ownership'][1]) &
            (self.player_pool['Projection'] >= 15)  # Must have decent projection
        ].copy()
        
        if not rb_pool.empty:
            # Pick the highest projected in the ownership range
            rb_pool = rb_pool.sort_values('Projection', ascending=False)
            self.core_rb = rb_pool.iloc[0].to_dict()
        else:
            # Fallback: pick highest projected RB
            rb_pool = self.player_pool[self.player_pool['Position'] == 'RB'].copy()
            if not rb_pool.empty:
                rb_pool = rb_pool.sort_values('Projection', ascending=False)
                self.core_rb = rb_pool.iloc[0].to_dict()
    
    def _determine_lineup_type(self, current_count: int, total_count: int, 
                               leverage_qb_count: int, game_stack_count: int) -> str:
        """Determine what type of lineup to build based on targets"""
        
        qb_target_pct = self.contest_rules['qb_usage_pct']
        stack_target_pct = self.contest_rules['game_stack_pct']
        
        # Calculate how many we still need
        leverage_qb_needed = int(total_count * qb_target_pct) - leverage_qb_count
        game_stack_needed = int(total_count * stack_target_pct) - game_stack_count
        
        # Prioritize what we're short on
        if leverage_qb_needed > 0 and game_stack_needed > 0:
            # Need both - do leverage QB + game stack
            return 'leverage_stack'
        elif leverage_qb_needed > 0:
            return 'leverage_qb'
        elif game_stack_needed > 0:
            return 'game_stack'
        else:
            # Hit our targets, build balanced
            return 'balanced'
    
    def _build_winning_structure(self, lineup_type: str) -> Dict:
        """Build lineup using winning structure"""
        
        lineup = []
        budget = SALARY_CAP
        used_names = []
        correlations = []
        
        # Metadata for tracking
        has_leverage_qb = False
        has_game_stack = False
        qb_team = None
        
        # STEP 1: Add locked players first
        for lock_pos, lock_value in self.locks.items():
            if lock_pos == 'QB' and lock_value:
                player = self.player_pool[self.player_pool['Name'] == lock_value].iloc[0].to_dict()
                lineup.append(player)
                budget -= player['Salary']
                used_names.append(player['Name'])
                qb_team = player['Team']
                correlations.append(f"{player['Name']} (LOCKED)")
                
        # Continue with other locks...
        for rb_name in self.locks.get('RB', []):
            if rb_name:
                player = self.player_pool[self.player_pool['Name'] == rb_name].iloc[0].to_dict()
                lineup.append(player)
                budget -= player['Salary']
                used_names.append(player['Name'])
                correlations.append(f"{player['Name']} (LOCKED)")
        
        for wr_name in self.locks.get('WR', []):
            if wr_name:
                player = self.player_pool[self.player_pool['Name'] == wr_name].iloc[0].to_dict()
                lineup.append(player)
                budget -= player['Salary']
                used_names.append(player['Name'])
                correlations.append(f"{player['Name']} (LOCKED)")
        
        if self.locks.get('TE'):
            player = self.player_pool[self.player_pool['Name'] == self.locks['TE']].iloc[0].to_dict()
            lineup.append(player)
            budget -= player['Salary']
            used_names.append(player['Name'])
            correlations.append(f"{player['Name']} (LOCKED)")
        
        if self.locks.get('FLEX'):
            player = self.player_pool[self.player_pool['Name'] == self.locks['FLEX']].iloc[0].to_dict()
            player['PositionSlot'] = f"FLEX ({player['Position']})"
            lineup.append(player)
            budget -= player['Salary']
            used_names.append(player['Name'])
            correlations.append(f"{player['Name']} (LOCKED FLEX)")
        
        if self.locks.get('DST'):
            player = self.player_pool[self.player_pool['Name'] == self.locks['DST']].iloc[0].to_dict()
            lineup.append(player)
            budget -= player['Salary']
            used_names.append(player['Name'])
            correlations.append(f"{player['Name']} (LOCKED)")
        
        # Count filled positions
        positions_filled = {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'DST': 0}
        for p in lineup:
            if p.get('PositionSlot'):
                positions_filled['FLEX'] += 1
            else:
                positions_filled[p['Position']] += 1
        
        # STEP 2: QB Selection based on lineup type
        if positions_filled['QB'] == 0:
            if lineup_type in ['leverage_qb', 'leverage_stack']:
                # ULTRA-LEVERAGE QB (Trevor Lawrence 3.7% type)
                qb = self._pick_leverage_qb(budget, used_names)
                if qb and qb['Ownership'] <= 8:
                    has_leverage_qb = True
                    correlations.append(f"💎 LEVERAGE QB: {qb['Name']} ({qb['Ownership']:.1f}%)")
            else:
                # Balanced QB selection
                qb = self._pick_balanced_qb(budget, used_names)
            
            if not qb:
                return None
            
            lineup.append(qb)
            budget -= qb['Salary']
            used_names.append(qb['Name'])
            qb_team = qb['Team']
        
        # STEP 3: Core RB Anchor (Travis Etienne type - 70% of lineups)
        if positions_filled['RB'] < 2:
            use_core_rb = np.random.random() < self.contest_rules['core_rb_usage_pct']
            
            if use_core_rb and self.core_rb and self.core_rb['Name'] not in used_names:
                lineup.append(self.core_rb)
                budget -= self.core_rb['Salary']
                used_names.append(self.core_rb['Name'])
                positions_filled['RB'] += 1
                correlations.append(f"⚓ CORE RB: {self.core_rb['Name']} ({self.core_rb['Ownership']:.1f}%)")
        
        # STEP 4: Game Stack (if needed)
        if lineup_type in ['leverage_stack', 'game_stack'] and qb_team:
            stack_players = self._build_game_stack(qb_team, budget, used_names, positions_filled)
            if len(stack_players) >= 2:
                for player in stack_players:
                    lineup.append(player)
                    budget -= player['Salary']
                    used_names.append(player['Name'])
                    if player['Position'] == 'RB':
                        positions_filled['RB'] += 1
                    elif player['Position'] == 'WR':
                        positions_filled['WR'] += 1
                
                has_game_stack = True
                correlations.append(f"🎯 GAME STACK: {qb_team} ({len(stack_players)+1} players)")
        
        # STEP 5: Fill remaining positions
        # Fill RBs
        while positions_filled['RB'] < 2:
            rb = self._pick_player('RB', budget * 0.25, used_names, leverage_preferred=True)
            if not rb:
                return None
            lineup.append(rb)
            budget -= rb['Salary']
            used_names.append(rb['Name'])
            positions_filled['RB'] += 1
        
        # Fill WRs (prefer leverage + correlation)
        while positions_filled['WR'] < 3:
            # Try to stack with QB team first
            if qb_team and np.random.random() < 0.30:
                wr = self._pick_stacked_player('WR', qb_team, budget * 0.30, used_names)
                if wr:
                    correlations.append(f"🔗 Stack: {wr['Name']} (same team as QB)")
            else:
                wr = self._pick_player('WR', budget * 0.30, used_names, leverage_preferred=True)
            
            if not wr:
                return None
            lineup.append(wr)
            budget -= wr['Salary']
            used_names.append(wr['Name'])
            positions_filled['WR'] += 1
        
        # Fill TE (70% punt strategy)
        if positions_filled['TE'] == 0:
            punt_te = np.random.random() < self.contest_rules['te_punt_pct']
            if punt_te:
                te_max = self.contest_rules['te_punt_salary_max']
                te = self._pick_player('TE', te_max, used_names)
                if te:
                    correlations.append(f"💰 PUNT TE: {te['Name']} (${te['Salary']:,})")
            else:
                te = self._pick_player('TE', budget * 0.20, used_names)
            
            if not te:
                return None
            lineup.append(te)
            budget -= te['Salary']
            used_names.append(te['Name'])
            positions_filled['TE'] += 1
        
        # Fill FLEX
        if positions_filled['FLEX'] == 0:
            flex_pos = np.random.choice(['RB', 'WR'], p=[0.40, 0.60])
            flex = self._pick_player(flex_pos, budget * 0.80, used_names, leverage_preferred=True)
            if not flex:
                return None
            flex['PositionSlot'] = f"FLEX ({flex['Position']})"
            lineup.append(flex)
            budget -= flex['Salary']
            used_names.append(flex['Name'])
            positions_filled['FLEX'] += 1
        
        # Fill DST
        if positions_filled['DST'] == 0:
            dst = self._pick_player('DST', 4000, used_names)
            if not dst:
                return None
            lineup.append(dst)
            budget -= dst['Salary']
            used_names.append(dst['Name'])
            positions_filled['DST'] += 1
        
        # Calculate totals
        total_sal = sum(p['Salary'] for p in lineup)
        total_proj = sum(p['Projection'] for p in lineup)
        total_own = sum(p['Ownership'] for p in lineup)
        avg_own = total_own / 9
        
        # Return with metadata
        return {
            'players': lineup,
            'total_salary': total_sal,
            'total_projection': total_proj,
            'total_ownership': total_own,
            'avg_ownership': avg_own,
            'correlations': correlations,
            'has_leverage_qb': has_leverage_qb,
            'has_game_stack': has_game_stack,
            'lineup_type': lineup_type
        }
    
    def _pick_leverage_qb(self, max_budget: int, used_names: List[str]) -> Dict:
        """Pick ultra-leverage QB (Trevor Lawrence 3.7% type)"""
        
        qb_min, qb_max = self.contest_rules['qb_salary_range']
        own_min, own_max = self.contest_rules['qb_ownership_target']
        
        qb_pool = self.player_pool[
            (self.player_pool['Position'] == 'QB') &
            (self.player_pool['Salary'] >= qb_min) &
            (self.player_pool['Salary'] <= qb_max) &
            (self.player_pool['Ownership'] >= own_min) &
            (self.player_pool['Ownership'] <= own_max) &
            (self.player_pool['Projection'] >= 18) &
            (~self.player_pool['Name'].isin(used_names))
        ].copy()
        
        if qb_pool.empty:
            # Fallback to any QB
            return self._pick_player('QB', max_budget, used_names)
        
        # Score by projection primarily (85%) + low ownership bonus (15%)
        qb_pool['proj_score'] = qb_pool['Projection'] / qb_pool['Projection'].max()
        qb_pool['own_score'] = (100 - qb_pool['Ownership']) / 100
        qb_pool['qb_score'] = (qb_pool['proj_score'] * 0.85) + (qb_pool['own_score'] * 0.15)
        qb_pool['qb_score'] *= np.random.uniform(0.90, 1.10, len(qb_pool))
        
        weights = qb_pool['qb_score'] / qb_pool['qb_score'].sum()
        return qb_pool.sample(1, weights=weights).iloc[0].to_dict()
    
    def _pick_balanced_qb(self, max_budget: int, used_names: List[str]) -> Dict:
        """Pick balanced QB"""
        return self._pick_player('QB', max_budget, used_names)
    
    def _build_game_stack(self, qb_team: str, budget: int, used_names: List[str], 
                         positions_filled: Dict) -> List[Dict]:
        """Build 3-piece game stack (QB already selected, add RB + WR or 2 WRs)"""
        
        stack_players = []
        
        # Pool of stackable players from QB's team
        stack_pool = self.player_pool[
            (self.player_pool['Team'] == qb_team) &
            (self.player_pool['Position'].isin(['RB', 'WR', 'TE'])) &
            (~self.player_pool['Name'].isin(used_names))
        ].copy()
        
        if stack_pool.empty:
            return stack_players
        
        # Prioritize low-owned players for stack
        stack_pool['stack_score'] = stack_pool['Projection'] / (stack_pool['Ownership'] + 1)
        stack_pool = stack_pool.sort_values('stack_score', ascending=False)
        
        # Try to add 2 players to create 3-piece stack
        needed = []
        if positions_filled['RB'] < 2:
            needed.append('RB')
        if positions_filled['WR'] < 3:
            needed.append('WR')
        
        for pos in needed[:2]:  # Max 2 additional stack pieces
            pos_pool = stack_pool[stack_pool['Position'] == pos].head(3)
            if not pos_pool.empty:
                # Pick one
                player = pos_pool.iloc[0].to_dict()
                if player['Salary'] <= budget * 0.30:
                    stack_players.append(player)
        
        return stack_players
    
    def _pick_stacked_player(self, position: str, team: str, max_budget: int, 
                            used_names: List[str]) -> Dict:
        """Pick player from specific team for stacking"""
        
        pool = self.player_pool[
            (self.player_pool['Position'] == position) &
            (self.player_pool['Team'] == team) &
            (self.player_pool['Salary'] <= max_budget) &
            (~self.player_pool['Name'].isin(used_names))
        ].copy()
        
        if pool.empty:
            return None
        
        # Prefer low ownership
        pool['pick_score'] = pool['Projection'] / (pool['Ownership'] + 1)
        pool = pool.sort_values('pick_score', ascending=False)
        
        return pool.iloc[0].to_dict()
    
    def _pick_player(self, position: str, max_budget: int, used_names: List[str], 
                    leverage_preferred: bool = False) -> Dict:
        """Generic player picker with optional leverage preference"""
        
        pool = self.player_pool[
            (self.player_pool['Position'] == position) &
            (self.player_pool['Salary'] <= max_budget) &
            (~self.player_pool['Name'].isin(used_names))
        ].copy()
        
        if pool.empty:
            return None
        
        # Apply category boosts if present
        if 'Category' in pool.columns:
            pool = pool[pool['Category'] != '🚫 Exclude']
            pool['category_boost'] = 0.0
            
            if self.contest_rules['entries'] >= 100000:
                # Millionaire Maker
                pool.loc[pool['Category'] == '💎 Leverage', 'category_boost'] = 0.30
                pool.loc[pool['Category'] == '⭐ Core', 'category_boost'] = 0.10
                pool.loc[pool['Category'] == '🔥 Chalk', 'category_boost'] = -0.20
            else:
                # Small GPP
                pool.loc[pool['Category'] == '🔥 Chalk', 'category_boost'] = 0.15
                pool.loc[pool['Category'] == '⭐ Core', 'category_boost'] = 0.20
                pool.loc[pool['Category'] == '💎 Leverage', 'category_boost'] = 0.25
        else:
            pool['category_boost'] = 0.0
        
        # Score players
        proj_weight = self.contest_rules['projection_weight']
        own_weight = self.contest_rules['ownership_weight']
        
        pool['proj_norm'] = pool['Projection'] / pool['Projection'].max()
        pool['own_leverage'] = (100 - pool['Ownership']) / 100
        pool['pick_score'] = (pool['proj_norm'] * proj_weight) + (pool['own_leverage'] * own_weight)
        pool['pick_score'] = pool['pick_score'] * (1 + pool['category_boost'])
        pool['pick_score'] *= np.random.uniform(0.90, 1.10, len(pool))
        
        # Pick from top 30%
        top_pct = 0.30
        cutoff = pool['pick_score'].quantile(1 - top_pct)
        pool = pool[pool['pick_score'] >= cutoff]
        
        if pool.empty:
            return None
        
        weights = pool['pick_score'] / pool['pick_score'].sum()
        return pool.sample(1, weights=weights).iloc[0].to_dict()
    
    def _validate_winning_structure(self, lineup_dict: Dict) -> bool:
        """Validate lineup meets winning structure requirements"""
        
        if not lineup_dict or 'players' not in lineup_dict:
            return False
        
        players = lineup_dict['players']
        total_own = lineup_dict['total_ownership']
        avg_own = lineup_dict['avg_ownership']
        
        # Check salary minimum
        if lineup_dict['total_salary'] < 48000:
            return False
        
        # Check ownership targets
        own_min, own_max = self.contest_rules['ownership_total_range']
        if total_own < own_min or total_own > own_max:
            return False
        
        # Count ultra-leverage players (<5% owned)
        ultra_leverage_count = sum(1 for p in players if p['Ownership'] < 5)
        ultra_min, ultra_max = self.contest_rules['ultra_leverage_required']
        if ultra_leverage_count < ultra_min:
            return False
        
        # Count heavy chalk players (>25% owned)
        heavy_chalk_count = sum(1 for p in players if p['Ownership'] > 25)
        if heavy_chalk_count > self.contest_rules['heavy_chalk_max']:
            return False
        
        # Validate stacking
        qb = next((p for p in players if p['Position'] == 'QB'), None)
        if qb:
            qb_team = qb['Team']
            stack_count = sum(1 for p in players if p.get('Team') == qb_team and p['Position'] != 'QB')
            if stack_count == 0:
                return False  # Must have at least 1 teammate
        
        return True
    
    def _is_duplicate(self, new_lineup: Dict, existing_lineups: List[Dict]) -> bool:
        """Check if lineup is duplicate"""
        
        if not new_lineup or 'players' not in new_lineup:
            return True
        
        new_names = set(p['Name'] for p in new_lineup['players'])
        
        for existing in existing_lineups:
            if 'players' in existing:
                existing_names = set(p['Name'] for p in existing['players'])
                if len(new_names.intersection(existing_names)) >= 7:
                    return True
        
        return False
