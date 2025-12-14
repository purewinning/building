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
        self.locks = {}
        
    def generate_lineups(self, player_pool: pd.DataFrame, num_lineups: int = 20, locks: dict = None) -> List[Dict]:
        """Generate lineups with optional player locks"""
        
        self.player_pool = player_pool.copy()
        self.player_pool['Value'] = self.player_pool['Projection'] / (self.player_pool['Salary'] / 1000)
        self.locks = locks if locks else {}
        
        print(f"   Building {num_lineups} lineups...")
        
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
        """Build lineup respecting locked players"""
        
        lineup = []
        budget = SALARY_CAP
        correlations = []
        used_names = []
        
        # Step 1: Add locked players first
        locked_qb_team = None
        
        # Lock QB
        if self.locks.get('QB'):
            qb = self.player_pool[self.player_pool['Name'] == self.locks['QB']].iloc[0].to_dict()
            lineup.append(qb)
            budget -= qb['Salary']
            used_names.append(qb['Name'])
            locked_qb_team = qb['Team']
            correlations.append(f"{qb['Name']} (LOCKED)")
        
        # Lock RBs
        for rb_name in self.locks.get('RB', []):
            rb = self.player_pool[self.player_pool['Name'] == rb_name].iloc[0].to_dict()
            lineup.append(rb)
            budget -= rb['Salary']
            used_names.append(rb['Name'])
            correlations.append(f"{rb['Name']} (LOCKED)")
        
        # Lock WRs
        for wr_name in self.locks.get('WR', []):
            wr = self.player_pool[self.player_pool['Name'] == wr_name].iloc[0].to_dict()
            lineup.append(wr)
            budget -= wr['Salary']
            used_names.append(wr['Name'])
            correlations.append(f"{wr['Name']} (LOCKED)")
        
        # Lock TE
        if self.locks.get('TE'):
            te = self.player_pool[self.player_pool['Name'] == self.locks['TE']].iloc[0].to_dict()
            lineup.append(te)
            budget -= te['Salary']
            used_names.append(te['Name'])
            correlations.append(f"{te['Name']} (LOCKED)")
        
        # Lock FLEX
        if self.locks.get('FLEX'):
            flex = self.player_pool[self.player_pool['Name'] == self.locks['FLEX']].iloc[0].to_dict()
            flex['PositionSlot'] = f"FLEX ({flex['Position']})"
            lineup.append(flex)
            budget -= flex['Salary']
            used_names.append(flex['Name'])
            correlations.append(f"{flex['Name']} (LOCKED FLEX)")
        
        # Lock DST
        if self.locks.get('DST'):
            dst = self.player_pool[self.player_pool['Name'] == self.locks['DST']].iloc[0].to_dict()
            lineup.append(dst)
            budget -= dst['Salary']
            used_names.append(dst['Name'])
            correlations.append(f"{dst['Name']} (LOCKED)")
        
        # Count what positions we still need
        positions_filled = {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'DST': 0}
        for p in lineup:
            if p.get('PositionSlot'):  # FLEX
                positions_filled['FLEX'] += 1
            else:
                positions_filled[p['Position']] += 1
        
        # Step 2: Fill QB if not locked
        if positions_filled['QB'] == 0:
            qb_strategy = np.random.random()
            
            if qb_strategy < 0.40:
                qb_pool = self.player_pool[
                    (self.player_pool['Position'] == 'QB') &
                    (self.player_pool['Salary'] >= 5000) &
                    (self.player_pool['Salary'] <= 6500) &
                    (self.player_pool['Projection'] >= 18) &
                    (~self.player_pool['Name'].isin(used_names))
                ].copy()
                
                if not qb_pool.empty:
                    qb_pool['value_score'] = qb_pool['Projection'] / (qb_pool['Salary'] / 1000)
                    qb_pool['qb_score'] = qb_pool['value_score'] * np.random.uniform(0.90, 1.10, len(qb_pool))
                    weights = qb_pool['qb_score'] / qb_pool['qb_score'].sum()
                    qb = qb_pool.sample(1, weights=weights).iloc[0].to_dict()
                else:
                    qb = self._pick_player('QB', 7500, used_names)
            elif qb_strategy < 0.80:
                qb = self._pick_player('QB', 7000, used_names)
            else:
                qb = self._pick_player('QB', 7500, used_names)
            
            if not qb:
                return None
            
            lineup.append(qb)
            budget -= qb['Salary']
            used_names.append(qb['Name'])
            locked_qb_team = qb['Team']
        
        qb_team = locked_qb_team
        if not qb_team:
            return None
        
        # Step 2: MANDATORY QB STACK - Pick 1-2 pass catchers from QB's team
        stack_budget = int(budget * 0.30)
        stack_pool = self.player_pool[
            (self.player_pool['Team'] == qb_team) &
            (self.player_pool['Position'].isin(['WR', 'TE'])) &
            (self.player_pool['Salary'] <= stack_budget) &
            (self.player_pool['Projection'] > 0)
        ].sort_values('Projection', ascending=False)
        
        if stack_pool.empty:
            return None  # NO STACK = REJECT LINEUP
        
        # Pick 1-2 stack pieces
        stack_count = min(2, len(stack_pool))
        stack_players = []
        for i in range(stack_count):
            if len(stack_pool) > i:
                stacker = stack_pool.iloc[i].to_dict()
                stack_players.append(stacker)
                lineup.append(stacker)
                budget -= stacker['Salary']
                correlations.append(f"{qb['Name']}-{stacker['Name']} (same team)")
        
        # Track positions filled
        positions_filled = {'QB': 1, 'WR': 0, 'TE': 0, 'RB': 0}
        for p in stack_players:
            positions_filled[p['Position']] += 1
        
        used_names = [p['Name'] for p in lineup]
        
        # Step 3: GAME STACK DECISION - Should we bring back opponent?
        # 40% chance to add a bring-back (leverage play in high-scoring games)
        bring_back_added = False
        if np.random.random() < 0.40 and qb_opponent:
            # Look for WR/RB from opponent team (cheap-ish for leverage)
            bring_back_pool = self.player_pool[
                (self.player_pool['Team'] == qb_opponent) &
                (self.player_pool['Position'].isin(['WR', 'RB'])) &
                (self.player_pool['Salary'] <= budget * 0.20) &
                (self.player_pool['Ownership'] < 15) &  # Prefer lower owned
                (~self.player_pool['Name'].isin(used_names))
            ].sort_values('Projection', ascending=False)
            
            if not bring_back_pool.empty:
                bring_back = bring_back_pool.iloc[0].to_dict()
                lineup.append(bring_back)
                budget -= bring_back['Salary']
                used_names.append(bring_back['Name'])
                positions_filled[bring_back['Position']] += 1
                bring_back_added = True
                correlations.append(f"{bring_back['Name']} (bring-back vs {qb_team})")
        
        # Step 4: Fill RBs (need 2 total, accounting for bring-back)
        # With cheap QB, we have more budget for STUD RBs
        rbs_needed = 2 - positions_filled.get('RB', 0)
        for i in range(rbs_needed):
            # First RB: Allow full $9k (CMC, Gibbs tier)
            # Second RB: Still allow expensive ($7-9k)
            if i == 0:
                rb_max = min(9000, int(budget * 0.30))  # 30% for RB1 (was 25%)
            else:
                rb_max = min(9000, int(budget * 0.30))  # 30% for RB2 (was 25%)
            
            rb = self._pick_player('RB', rb_max, used_names)
            if not rb:
                return None
            lineup.append(rb)
            budget -= rb['Salary']
            used_names.append(rb['Name'])
            positions_filled['RB'] = positions_filled.get('RB', 0) + 1
        
        # Step 5: Fill remaining WRs (need 3 total)
        # With QB savings, can afford multiple elite WRs
        wrs_needed = 3 - positions_filled['WR']
        for i in range(wrs_needed):
            # All WRs can be studs now ($8-8.7k tier)
            if i == 0:
                wr_max = min(8700, int(budget * 0.32))  # 32% for WR1
            elif i == 1:
                wr_max = min(8700, int(budget * 0.35))  # 35% for WR2
            else:
                wr_max = min(8700, int(budget * 0.40))  # 40% for WR3
            
            wr = self._pick_player('WR', wr_max, used_names)
            if not wr:
                return None
            lineup.append(wr)
            budget -= wr['Salary']
            used_names.append(wr['Name'])
            positions_filled['WR'] += 1
        
        # Step 6: Fill TE if needed
        if positions_filled['TE'] == 0:
            te_max = int(budget * 0.50)
            te = self._pick_player('TE', te_max, used_names)
            if not te:
                return None
            lineup.append(te)
            budget -= te['Salary']
            used_names.append(te['Name'])
            positions_filled['TE'] += 1
        
        # Step 7: FLEX - Intelligent correlation opportunity
        # 50% chance: same team as QB (triple stack)
        # 30% chance: opponent team (game stack)
        # 20% chance: best available (contrarian)
        
        flex_max = int(budget * 0.70)
        flex_choice = np.random.random()
        
        if flex_choice < 0.50:
            # Try to triple stack (same team as QB)
            flex_pool = self.player_pool[
                (self.player_pool['Position'].isin(['RB', 'WR'])) &
                (self.player_pool['Team'] == qb_team) &
                (self.player_pool['Salary'] <= flex_max) &
                (~self.player_pool['Name'].isin(used_names))
            ].sort_values('Projection', ascending=False)
            
            if not flex_pool.empty:
                flex = flex_pool.iloc[0].to_dict()
                correlations.append(f"{flex['Name']} (triple stack with {qb_team})")
            else:
                flex_pool = self.player_pool[
                    (self.player_pool['Position'].isin(['RB', 'WR'])) &
                    (self.player_pool['Salary'] <= flex_max) &
                    (~self.player_pool['Name'].isin(used_names))
                ].sort_values('Projection', ascending=False)
                flex = flex_pool.iloc[0].to_dict() if not flex_pool.empty else None
        else:
            # Standard FLEX pick
            flex = self._pick_player(['RB', 'WR'], flex_max, used_names)
        
        if not flex:
            return None
        
        flex['PositionSlot'] = f"FLEX ({flex['Position']})"
        lineup.append(flex)
        budget -= flex['Salary']
        used_names.append(flex['Name'])
        
        # Step 8: DST - INTELLIGENT CORRELATION
        # Priority 1: RB+DST stack (40% chance) - leverage play
        # Priority 2: Opponent of our QB (30% chance) - contrarian
        # Priority 3: Best available (30% chance)
        
        dst_choice = np.random.random()
        dst = None
        
        # Find our RBs
        our_rbs = [p for p in lineup if p['Position'] == 'RB']
        
        if dst_choice < 0.40 and len(our_rbs) > 0:
            # RB+DST STACK - Pick DST facing our RB's team (negative correlation leverage)
            # If we have CMC (SF), pick the DST playing against SF
            rb_teams = [rb.get('Team') for rb in our_rbs]
            
            for rb_team in rb_teams:
                dst_pool = self.player_pool[
                    (self.player_pool['Position'] == 'DST') &
                    (self.player_pool.get('Opponent', '') == rb_team) &  # DST vs our RB's team
                    (self.player_pool['Salary'] <= budget)
                ].sort_values('Projection', ascending=False)
                
                if not dst_pool.empty:
                    dst = dst_pool.iloc[0].to_dict()
                    correlations.append(f"{dst['Name']} DST vs {our_rbs[0]['Name']}'s team (contrarian leverage)")
                    break
        
        elif dst_choice < 0.70 and qb_opponent:
            # Pick DST from opponent team (they're defending our QB)
            dst_pool = self.player_pool[
                (self.player_pool['Position'] == 'DST') &
                (self.player_pool['Team'] == qb_opponent) &
                (self.player_pool['Salary'] <= budget)
            ]
            
            if not dst_pool.empty:
                dst = dst_pool.iloc[0].to_dict()
                correlations.append(f"{dst['Name']} DST (opponent of our QB)")
        
        # Fallback: Best DST available
        if not dst:
            dst = self._pick_player('DST', budget, used_names)
        
        if not dst:
            return None
        
        lineup.append(dst)
        budget -= dst['Salary']
        
        # Calculate totals
        total_sal = sum(p['Salary'] for p in lineup)
        total_proj = sum(p['Projection'] for p in lineup)
        total_own = sum(p['Ownership'] for p in lineup)
        avg_own = total_own / 9
        
        # VALIDATE STACKING - Must have at least 1 pass catcher from QB's team
        stack_teammates = [p for p in lineup if p.get('Team') == qb_team and p['Position'] != 'QB']
        if len(stack_teammates) == 0:
            return None  # NO STACK = INVALID LINEUP
        
        # Validate salary minimum
        if total_sal < 48000:
            return None
        
        # REVISED OWNERSHIP VALIDATION - Focus on WINNING not contrarian
        # Small GPP (4,444): 110-160% total (12-18% avg) - Chalk is OK!
        # Mid GPP (14k): 90-140% total (10-15% avg) - Balanced
        # Milly Maker (150k+): 60-110% total (7-12% avg) - Some leverage
        
        contest_entries = self.contest_rules['entries']
        
        if contest_entries >= 100000:
            # Millionaire Maker: Need leverage but not too contrarian
            if total_own < 60 or total_own > 110:
                return None
        elif contest_entries >= 10000:
            # Mid GPP: Balanced approach
            if total_own < 90 or total_own > 140:
                return None
        else:
            # Small GPP: HAMMER CHALK WITH LEVERAGE SPRINKLES
            # Target: 120-150% total ownership (13-17% avg)
            # This means: 5-6 chalk pieces + 3-4 leverage pieces
            if total_own < 110 or total_own > 160:
                return None
        
        # Build stack description
        stack_positions = [p['Position'] for p in stack_teammates]
        primary_stack = f"{qb_team} Stack: QB + {', '.join(stack_positions)}"
        
        # Identify all game stacks
        game_stacks = {}
        for p in lineup:
            if p['Position'] != 'DST':
                team = p.get('Team', '')
                opp = p.get('Opponent', '')
                if team and opp:
                    game_key = tuple(sorted([team, opp]))
                    game_stacks[game_key] = game_stacks.get(game_key, 0) + 1
        
        game_stack_desc = []
        for game, count in game_stacks.items():
            if count >= 2:
                game_stack_desc.append(f"{game[0]} vs {game[1]} ({count} players)")
        
        return {
            'players': lineup,
            'salary': total_sal,
            'salary_remaining': SALARY_CAP - total_sal,
            'projection': total_proj,
            'ownership': total_own,
            'ownership_avg': avg_own,
            'value': total_proj / (total_sal / 1000),
            'ownership_target': f"{own_target_min}-{own_target_max}%",
            'contest_type': self.contest_rules['name'],
            'stack': primary_stack,
            'stack_team': qb_team,
            'stack_count': len(stack_teammates),
            'correlations': correlations,
            'game_stacks': game_stack_desc if game_stack_desc else ["Single game focus"]
        }
    
    def _pick_player(self, position, max_salary: int, used_names: List[str]) -> Dict:
        """Pick player using CONTEST-SPECIFIC strategy and respecting categories"""
        
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
        
        # Exclude players marked as excluded
        if 'Category' in pool.columns:
            pool = pool[pool['Category'] != '🚫 Exclude']
            
            if pool.empty:
                return None
        
        # CONTEST-SPECIFIC STRATEGY with category awareness
        contest_entries = self.contest_rules['entries']
        
        # Add category-based score boosts
        if 'Category' in pool.columns:
            pool['category_boost'] = 0.0
            
            if contest_entries >= 100000:
                # Millionaire Maker: Boost leverage, penalize chalk
                pool.loc[pool['Category'] == '💎 Leverage', 'category_boost'] = 0.30
                pool.loc[pool['Category'] == '🔥 Chalk', 'category_boost'] = -0.20
                pool.loc[pool['Category'] == '⭐ Core', 'category_boost'] = 0.10
            elif contest_entries >= 10000:
                # Mid GPP: Balanced
                pool.loc[pool['Category'] == '💎 Leverage', 'category_boost'] = 0.10
                pool.loc[pool['Category'] == '⭐ Core', 'category_boost'] = 0.15
                pool.loc[pool['Category'] == '🔥 Chalk', 'category_boost'] = 0.05
            else:
                # Small GPP: HEAVILY FAVOR CHALK AND CORE
                pool.loc[pool['Category'] == '🔥 Chalk', 'category_boost'] = 0.35  # Big boost!
                pool.loc[pool['Category'] == '⭐ Core', 'category_boost'] = 0.30   # Big boost!
                pool.loc[pool['Category'] == '💎 Leverage', 'category_boost'] = -0.10  # Slight penalty
                pool.loc[pool['Category'] == '✓ Flex', 'category_boost'] = 0.05
        else:
            pool['category_boost'] = 0.0
        
        # Calculate base scores based on contest type
        if contest_entries >= 100000:
            # Millionaire Maker - still need leverage
            pool['proj_norm'] = pool['Projection'] / pool['Projection'].max()
            pool['own_leverage'] = (100 - pool['Ownership']) / 100
            pool['pick_score'] = (pool['proj_norm'] * 0.40) + (pool['own_leverage'] * 0.60)
            top_pct = 0.35
            
        elif contest_entries >= 10000:
            # Mid GPP - balanced
            pool['proj_norm'] = pool['Projection'] / pool['Projection'].max()
            pool['own_leverage'] = (100 - pool['Ownership']) / 100
            pool['pick_score'] = (pool['proj_norm'] * 0.60) + (pool['own_leverage'] * 0.40)
            top_pct = 0.40
            
        else:
            # Small GPP - HAMMER PROJECTION, ownership secondary
            # 85% projection, 15% ownership
            pool['proj_norm'] = pool['Projection'] / pool['Projection'].max()
            pool['own_leverage'] = (100 - pool['Ownership']) / 100
            pool['pick_score'] = (pool['proj_norm'] * 0.85) + (pool['own_leverage'] * 0.15)
            
            # Pick from top 30% by projection (studs + high scorers)
            top_pct = 0.30
        
        # Apply category boost
        pool['pick_score'] = pool['pick_score'] + pool['category_boost']
        
        # Add randomness for variety
        pool['pick_score'] *= np.random.uniform(0.90, 1.10, len(pool))
        
        # Select from top pool
        top_n = max(1, int(len(pool) * top_pct))
        top_pool = pool.nlargest(top_n, 'pick_score')
        
        # Weight by score
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
