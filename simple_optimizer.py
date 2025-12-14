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
        """Build a single valid lineup with INTELLIGENT CORRELATION STACKING"""
        
        lineup = []
        budget = SALARY_CAP
        correlations = []  # Track all correlations
        
        # Step 1: Pick QB first
        qb_max = min(7500, budget)
        qb = self._pick_player('QB', qb_max, [])
        if not qb:
            return None
        lineup.append(qb)
        budget -= qb['Salary']
        
        qb_team = qb['Team']
        qb_opponent = qb.get('Opponent', '')
        
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
        rbs_needed = 2 - positions_filled.get('RB', 0)
        for i in range(rbs_needed):
            rb_max = min(9000, int(budget * 0.25))
            rb = self._pick_player('RB', rb_max, used_names)
            if not rb:
                return None
            lineup.append(rb)
            budget -= rb['Salary']
            used_names.append(rb['Name'])
            positions_filled['RB'] = positions_filled.get('RB', 0) + 1
        
        # Step 5: Fill remaining WRs (need 3 total)
        wrs_needed = 3 - positions_filled['WR']
        for i in range(wrs_needed):
            wr_max = min(8700, int(budget * (0.28 if i == 0 else 0.32)))
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
        
        # CONTEST-SPECIFIC ownership validation
        own_target_min, own_target_max = self.contest_rules['ownership_target_avg']
        contest_entries = self.contest_rules['entries']
        
        if contest_entries >= 100000:
            if avg_own > 15:
                return None
        elif contest_entries >= 10000:
            if avg_own > 20:
                return None
        else:
            own_min_relaxed = own_target_min * 0.50
            own_max_relaxed = own_target_max * 1.80
            if avg_own < own_min_relaxed or avg_own > own_max_relaxed:
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
        """Pick player using CONTEST-SPECIFIC strategy"""
        
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
        
        # CONTEST-SPECIFIC STRATEGY
        contest_entries = self.contest_rules['entries']
        
        if contest_entries >= 100000:
            # MILLIONAIRE MAKER STRATEGY (150k+ entries)
            # Need extreme leverage + ceiling
            # 30% projection, 70% ownership leverage
            
            pool['proj_norm'] = pool['Projection'] / pool['Projection'].max()
            pool['own_leverage'] = (100 - pool['Ownership']) / 100
            
            # Heavily favor LOW ownership (70/30 split)
            pool['pick_score'] = (pool['proj_norm'] * 0.30) + (pool['own_leverage'] * 0.70)
            
            # Add boom% consideration if available
            if 'Boom' in pool.columns:
                pool['boom_norm'] = pool['Boom'] / pool['Boom'].max()
                pool['pick_score'] = (pool['proj_norm'] * 0.25) + (pool['own_leverage'] * 0.60) + (pool['boom_norm'] * 0.15)
            
            # Pick from top 30% by leverage score (more contrarian)
            top_n = max(1, int(len(pool) * 0.30))
            
        elif contest_entries >= 10000:
            # MID-SIZE GPP (14k entries)
            # Balanced: 50% projection, 50% ownership
            
            pool['proj_norm'] = pool['Projection'] / pool['Projection'].max()
            pool['own_leverage'] = (100 - pool['Ownership']) / 100
            
            pool['pick_score'] = (pool['proj_norm'] * 0.50) + (pool['own_leverage'] * 0.50)
            
            # Pick from top 35%
            top_n = max(1, int(len(pool) * 0.35))
            
        else:
            # SMALL GPP (4,444 entries)
            # Favor projection: 70% projection, 30% ownership leverage
            # This is what we tested earlier
            
            pool['proj_norm'] = pool['Projection'] / pool['Projection'].max()
            pool['own_leverage'] = (100 - pool['Ownership']) / 100
            
            pool['pick_score'] = (pool['proj_norm'] * 0.70) + (pool['own_leverage'] * 0.30)
            
            # 70% chance pick from top 20% (studs), 30% chance from top 40% (value)
            if np.random.random() < 0.70:
                top_n = max(1, int(len(pool) * 0.20))
            else:
                top_n = max(1, int(len(pool) * 0.40))
        
        # Add randomness for variety
        pool['pick_score'] *= np.random.uniform(0.90, 1.10, len(pool))
        
        # Select from top pool
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
