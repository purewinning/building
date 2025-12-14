"""
Monte Carlo Tournament Simulator
Simulates thousands of tournaments to calculate expected ROI
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from config import MONTE_CARLO_ITERATIONS


class MonteCarloSimulator:
    """Simulate DFS tournaments to calculate win probability and ROI"""
    
    def __init__(self, contest_entries: int, payout_structure: Dict):
        """
        Args:
            contest_entries: Number of entries in contest
            payout_structure: Dict defining payouts, e.g.:
                {
                    'entry_fee': 100,
                    'places_paid': 1400,  # Top 10% of 14k
                    'payouts': {1: 50000, 2: 25000, ...}
                }
        """
        self.contest_entries = contest_entries
        self.payout_structure = payout_structure
        self.iterations = MONTE_CARLO_ITERATIONS
        
    def simulate_lineup(self, lineup: Dict, field_ownership: pd.DataFrame) -> Dict:
        """
        Simulate tournament performance for a lineup (VECTORIZED for speed)
        
        Args:
            lineup: Dict with players, projections, ownership
            field_ownership: Distribution of field's ownership
            
        Returns:
            Dict with win%, top10%, cash%, expected ROI
        """
        
        try:
            # Vectorized simulation - all iterations at once
            # Generate all lineup scores at once
            lineup_scores = self._simulate_score_vectorized(lineup, self.iterations)
            
            # Generate all field scores at once
            field_scores = self._simulate_field_vectorized(self.iterations)
            
            # Calculate placements (how many field entries beat each lineup score)
            placements = np.sum(field_scores > lineup_scores[:, np.newaxis], axis=1) + 1
            
            # Calculate statistics
            win_count = np.sum(placements == 1)
            top_10pct = int(self.contest_entries * 0.10)
            top10_count = np.sum(placements <= top_10pct)
            
            # Calculate cash and winnings
            payouts = np.array([self._get_payout(p) for p in placements])
            cash_count = np.sum(payouts > 0)
            total_winnings = np.sum(payouts)
            
            # Calculate percentages
            win_pct = (win_count / self.iterations) * 100
            top10_pct = (top10_count / self.iterations) * 100
            cash_pct = (cash_count / self.iterations) * 100
            
            # Calculate expected value and ROI
            avg_winnings = total_winnings / self.iterations
            entry_fee = self.payout_structure['entry_fee']
            expected_roi = ((avg_winnings - entry_fee) / entry_fee) * 100
            
            return {
                'win_pct': win_pct,
                'top10_pct': top10_pct,
                'cash_pct': cash_pct,
                'expected_winnings': avg_winnings,
                'expected_roi': expected_roi,
                'avg_placement': np.mean(placements),
                'median_placement': np.median(placements)
            }
            
        except Exception as e:
            print(f"Error in simulation: {e}")
            # Return default values on error
            return {
                'win_pct': 0.0,
                'top10_pct': 0.0,
                'cash_pct': 0.0,
                'expected_winnings': 0.0,
                'expected_roi': 0.0,
                'avg_placement': self.contest_entries / 2,
                'median_placement': self.contest_entries / 2
            }
    
    def _simulate_score_vectorized(self, lineup: Dict, n_iterations: int) -> np.ndarray:
        """
        Simulate lineup scores for all iterations at once (FAST)
        
        Returns:
            Array of shape (n_iterations,) with lineup scores
        """
        lineup_scores = np.zeros(n_iterations)
        
        for player in lineup['players']:
            mean = player['Projection']
            stddev = player.get('StdDev', 6.0)
            
            # Generate all scores for this player at once
            player_scores = np.random.normal(mean, stddev, n_iterations)
            player_scores = np.maximum(0, player_scores)  # Can't score negative
            
            lineup_scores += player_scores
        
        return lineup_scores
    
    def _simulate_field_vectorized(self, n_iterations: int) -> np.ndarray:
        """
        Simulate field scores for all iterations at once (FAST)
        
        Returns:
            Array of shape (n_iterations, contest_entries) with all field scores
        """
        # Generate all field scores at once
        field_scores = np.random.normal(
            loc=135,  # Average field score
            scale=15,  # Variance in field
            size=(n_iterations, self.contest_entries)
        )
        
        return field_scores
    
    def _simulate_score(self, lineup: Dict) -> float:
        """
        Simulate lineup score using normal distribution
        Each player's score ~ N(projection, stddev)
        """
        total_score = 0
        
        for player in lineup['players']:
            mean = player['Projection']
            stddev = player.get('StdDev', 6.0)  # Default if not provided
            
            # Sample from normal distribution
            player_score = np.random.normal(mean, stddev)
            player_score = max(0, player_score)  # Can't score negative
            
            total_score += player_score
        
        return total_score
    
    def _simulate_field(self, field_ownership: pd.DataFrame) -> np.ndarray:
        """
        Simulate scores for entire field
        More owned players = more field entries have them
        """
        
        # For now, simplified: generate random scores for field
        # In production, would model field lineup construction based on ownership
        
        field_scores = np.random.normal(
            loc=135,  # Average field score
            scale=15,  # Variance in field
            size=self.contest_entries
        )
        
        return field_scores
    
    def _calculate_placement(self, lineup_score: float, field_scores: np.ndarray) -> int:
        """
        Calculate lineup's placement in field
        Returns placement (1 = first place)
        """
        # Count how many field entries scored higher
        better_scores = np.sum(field_scores > lineup_score)
        placement = better_scores + 1
        
        return placement
    
    def _get_payout(self, placement: int) -> float:
        """Get payout amount for placement"""
        
        payouts = self.payout_structure.get('payouts', {})
        
        # Check if this placement gets paid
        if placement in payouts:
            return payouts[placement]
        
        # Check if in paying range (flat payout)
        places_paid = self.payout_structure.get('places_paid', 0)
        if placement <= places_paid:
            # Calculate proportional payout (simplified)
            # In production, would use exact payout structure
            entry_fee = self.payout_structure['entry_fee']
            return entry_fee * 1.5  # Rough estimate
        
        return 0
    
    def batch_simulate(self, lineups: List[Dict], field_ownership: pd.DataFrame) -> pd.DataFrame:
        """
        Simulate multiple lineups and return results
        
        Args:
            lineups: List of lineup dicts
            field_ownership: Field ownership distribution
            
        Returns:
            DataFrame with simulation results for each lineup
        """
        
        results = []
        
        for i, lineup in enumerate(lineups):
            # Progress indicator
            progress = (i + 1) / len(lineups) * 100
            print(f"Simulating lineup {i+1}/{len(lineups)} ({progress:.0f}%)...", end='\r')
            
            sim_result = self.simulate_lineup(lineup, field_ownership)
            
            # Combine lineup info with simulation results
            result = {
                'lineup_id': i + 1,
                'salary': lineup['salary'],
                'projection': lineup['projection'],
                'ownership': lineup['ownership'],
                'win_pct': sim_result['win_pct'],
                'top10_pct': sim_result['top10_pct'],
                'cash_pct': sim_result['cash_pct'],
                'expected_roi': sim_result['expected_roi'],
                'expected_winnings': sim_result['expected_winnings'],
                'avg_placement': sim_result['avg_placement'],
                'players': ', '.join([p['Name'] for p in lineup['players']])
            }
            
            results.append(result)
        
        print()  # New line after progress
        
        df = pd.DataFrame(results)
        
        # Ensure all expected columns exist
        if 'expected_roi' not in df.columns:
            df['expected_roi'] = 0.0
        if 'win_pct' not in df.columns:
            df['win_pct'] = 0.0
        if 'top10_pct' not in df.columns:
            df['top10_pct'] = 0.0
        if 'cash_pct' not in df.columns:
            df['cash_pct'] = 0.0
            
        return df


def create_payout_structure(contest_type: str, entry_fee: float) -> Dict:
    """
    Create payout structure for contest
    
    Args:
        contest_type: 'small_gpp', 'mid_gpp', 'milly_maker'
        entry_fee: Entry fee in dollars
        
    Returns:
        Payout structure dict
    """
    from config import CONTEST_STRUCTURES
    
    rules = CONTEST_STRUCTURES[contest_type]
    entries = rules['entries']
    total_pool = entries * entry_fee
    
    if contest_type == 'small_gpp':
        # 4,444 entries, 25% to 1st
        first_place = total_pool * 0.25
        
        # Simplified payout structure
        payouts = {
            1: first_place,
            2: total_pool * 0.10,
            3: total_pool * 0.06,
            4: total_pool * 0.04,
            5: total_pool * 0.03
            # Continue with declining payouts...
        }
        
        return {
            'entry_fee': entry_fee,
            'places_paid': int(entries * 0.20),  # Top 20% cash
            'payouts': payouts,
            'total_pool': total_pool
        }
    
    elif contest_type == 'mid_gpp':
        # 14k entries, 10% payout
        # Very flat structure (why ROI is negative)
        
        places_paid = int(entries * 0.10)
        avg_payout = (total_pool * 0.90) / places_paid  # 90% to field, 10% rake
        
        payouts = {i: avg_payout * 1.2 for i in range(1, 11)}  # Top 10 get slight boost
        
        return {
            'entry_fee': entry_fee,
            'places_paid': places_paid,
            'payouts': payouts,
            'total_pool': total_pool
        }
    
    elif contest_type == 'milly_maker':
        # 150k entries, $1M to first
        
        payouts = {
            1: 1000000,
            2: 250000,
            3: 150000,
            4: 100000,
            5: 75000
            # Continue with declining payouts...
        }
        
        return {
            'entry_fee': entry_fee,
            'places_paid': int(entries * 0.20),
            'payouts': payouts,
            'total_pool': total_pool
        }
    
    return {}
