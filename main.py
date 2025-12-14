"""
DFS Optimizer - Main Application
Free alternative to Stokastic's lineup builder
"""

import sys
import pandas as pd
import argparse
from typing import List, Dict
from config import CONTEST_STRUCTURES, TOP_LINEUPS_TO_RETURN
from projections import ProjectionEngine, OwnershipProjector
from optimizer import LineupOptimizer
from simulator import MonteCarloSimulator, create_payout_structure


class DFSOptimizer:
    """Main application class"""
    
    def __init__(self, contest_type: str = 'small_gpp', entry_fee: float = 100):
        self.contest_type = contest_type
        self.entry_fee = entry_fee
        self.contest_rules = CONTEST_STRUCTURES[contest_type]
        
        # Initialize components
        self.projection_engine = ProjectionEngine()
        self.ownership_projector = OwnershipProjector()
        self.optimizer = LineupOptimizer(contest_type)
        
    def run(self, player_pool_path: str, num_lineups: int = 20) -> pd.DataFrame:
        """
        Main workflow: Load data -> Generate projections -> Build lineups -> Simulate
        
        Args:
            player_pool_path: Path to CSV with DK player pool
            num_lineups: Number of lineups to generate
            
        Returns:
            Tuple of (results DataFrame, lineups list)
        """
        
        print("=" * 80)
        print(f"🏈 DFS OPTIMIZER - {self.contest_rules['name']}")
        print("=" * 80)
        print()
        
        # Step 1: Load player pool
        print("📂 Loading player pool...")
        player_pool = self._load_player_pool(player_pool_path)
        print(f"   Loaded {len(player_pool)} players")
        print()
        
        # Step 2: Generate projections (skip if already present)
        if 'Projection' not in player_pool.columns or player_pool['Projection'].isna().all():
            print("📊 Generating projections...")
            player_pool = self.projection_engine.generate_projections(player_pool)
            print(f"   ✓ Projections generated")
        else:
            print("📊 Using existing projections from file...")
            # Just add Value column if missing
            if 'Value' not in player_pool.columns:
                player_pool['Value'] = player_pool['Projection'] / (player_pool['Salary'] / 1000)
            # Add StdDev if missing
            if 'StdDev' not in player_pool.columns:
                player_pool['StdDev'] = self.projection_engine._position_variance(player_pool)
        print()
        
        # Step 3: Project ownership (skip if already present)
        if 'Ownership' not in player_pool.columns or player_pool['Ownership'].isna().all():
            print("👥 Projecting ownership...")
            player_pool = self.ownership_projector.project_ownership(player_pool)
            print(f"   ✓ Ownership projected")
        else:
            print("👥 Using existing ownership from file...")
        print()
        
        # Step 4: Build lineups
        print(f"🔨 Building {num_lineups} optimized lineups...")
        lineups = self.optimizer.generate_lineups(
            player_pool, 
            num_lineups=num_lineups,
            contest_type=self.contest_type
        )
        
        if not lineups or len(lineups) == 0:
            print("   ❌ Failed to generate any valid lineups")
            print("   This could be due to:")
            print("   - Not enough players in each position")
            print("   - Constraints too strict for available player pool")
            print("   - Salary constraints can't be met")
            return None, None
            
        print(f"   ✓ Generated {len(lineups)} unique lineups")
        print()
        
        # Step 5: Simulate tournaments
        print("🎲 Running Monte Carlo simulations (1,000 iterations per lineup)...")
        payout_structure = create_payout_structure(self.contest_type, self.entry_fee)
        simulator = MonteCarloSimulator(
            self.contest_rules['entries'],
            payout_structure
        )
        
        results = simulator.batch_simulate(lineups, player_pool)
        print("   ✓ Simulations complete")
        print()
        
        # Step 6: Display results (only in CLI mode with --display flag)
        # Don't display in Streamlit or when called programmatically
        
        return results, lineups
    
    def _load_player_pool(self, path: str) -> pd.DataFrame:
        """
        Load player pool from CSV
        Expected columns from Stokastic: Player, Salary, Position, Team, Opponent, Projection, Ownership %
        """
        try:
            df = pd.read_csv(path)
            
            # Map Stokastic column names to our internal names
            column_mapping = {
                'Player': 'Name',
                'Ownership %': 'Ownership',
                'Std Dev': 'StdDev'
            }
            
            # Rename columns
            df = df.rename(columns=column_mapping)
            
            # Validate required columns exist
            required = ['Name', 'Position', 'Salary', 'Team', 'Projection', 'Ownership']
            missing = [col for col in required if col not in df.columns]
            
            if missing:
                print(f"⚠️  Warning: Missing columns: {missing}")
                print("   Using demo data instead...")
                return self._create_demo_player_pool()
            
            # Ensure numeric columns are float
            df['Salary'] = pd.to_numeric(df['Salary'], errors='coerce')
            df['Projection'] = pd.to_numeric(df['Projection'], errors='coerce')
            df['Ownership'] = pd.to_numeric(df['Ownership'], errors='coerce')
            
            # Add StdDev if not present
            if 'StdDev' not in df.columns:
                # Use position-based defaults
                position_std = {'QB': 7.0, 'RB': 7.5, 'WR': 8.5, 'TE': 6.0, 'DST': 4.0}
                df['StdDev'] = df['Position'].map(position_std).fillna(7.0)
            
            # Drop any rows with missing critical data
            df = df.dropna(subset=['Name', 'Position', 'Salary', 'Projection'])
            
            print(f"   ✓ Loaded {len(df)} players from file")
            
            return df
            
        except FileNotFoundError:
            print(f"⚠️  File not found: {path}")
            print("   Creating demo player pool...")
            return self._create_demo_player_pool()
        except Exception as e:
            print(f"⚠️  Error loading file: {e}")
            print("   Creating demo player pool...")
            return self._create_demo_player_pool()
    
    def _create_demo_player_pool(self) -> pd.DataFrame:
        """Create demo player pool for testing"""
        
        players = []
        
        # QBs
        qbs = [
            ('Josh Allen', 'BUF', 7500),
            ('Lamar Jackson', 'BAL', 6400),
            ('Jalen Hurts', 'PHI', 6800),
            ('Patrick Mahomes', 'KC', 6500),
            ('Matthew Stafford', 'LAR', 7000),
            ('Sam Darnold', 'SEA', 5800),
            ('Jared Goff', 'DET', 6200)
        ]
        
        for name, team, salary in qbs:
            players.append({
                'Name': name,
                'Position': 'QB',
                'Team': team,
                'Salary': salary,
                'Opponent': 'OPP'
            })
        
        # RBs
        rbs = [
            ('Christian McCaffrey', 'SF', 9500),
            ('Saquon Barkley', 'PHI', 8800),
            ('Jahmyr Gibbs', 'DET', 8800),
            ('James Cook', 'BUF', 8000),
            ('Travis Etienne Jr.', 'JAX', 6500),
            ('Devin Neal', 'NO', 5300),
            ('Woody Marks', 'HOU', 5600),
            ('Chuba Hubbard', 'CAR', 4600)
        ]
        
        for name, team, salary in rbs:
            players.append({
                'Name': name,
                'Position': 'RB',
                'Team': team,
                'Salary': salary,
                'Opponent': 'OPP'
            })
        
        # WRs
        wrs = [
            ('Puka Nacua', 'LAR', 8700),
            ('Ja\'Marr Chase', 'CIN', 8100),
            ('Jaxon Smith-Njigba', 'SEA', 8600),
            ('A.J. Brown', 'PHI', 6800),
            ('Davante Adams', 'LAR', 7200),
            ('DeVonta Smith', 'PHI', 5800),
            ('Chris Olave', 'NO', 6200),
            ('Courtland Sutton', 'DEN', 5500),
            ('Khalil Shakir', 'BUF', 5300),
            ('Zay Flowers', 'BAL', 6300)
        ]
        
        for name, team, salary in wrs:
            players.append({
                'Name': name,
                'Position': 'WR',
                'Team': team,
                'Salary': salary,
                'Opponent': 'OPP'
            })
        
        # TEs
        tes = [
            ('Mark Andrews', 'BAL', 3900),
            ('Mike Gesicki', 'CIN', 3300),
            ('Trey McBride', 'ARI', 6600),
            ('George Kittle', 'SF', 5800),
            ('Hunter Henry', 'NE', 4400)
        ]
        
        for name, team, salary in tes:
            players.append({
                'Name': name,
                'Position': 'TE',
                'Team': team,
                'Salary': salary,
                'Opponent': 'OPP'
            })
        
        # DSTs
        dsts = [
            ('Titans', 'TEN', 2300),
            ('Saints', 'NO', 2500),
            ('Bears', 'CHI', 2500),
            ('Ravens', 'BAL', 3200)
        ]
        
        for name, team, salary in dsts:
            players.append({
                'Name': name,
                'Position': 'DST',
                'Team': team,
                'Salary': salary,
                'Opponent': 'OPP'
            })
        
        return pd.DataFrame(players)
    
    def _display_results(self, results: pd.DataFrame, lineups: List[Dict]):
        """Display formatted results"""
        
        print("=" * 80)
        print(f"🏆 TOP {min(5, len(results))} LINEUPS")
        print("=" * 80)
        print()
        
        # Ensure expected_roi column exists
        if 'expected_roi' not in results.columns:
            print("⚠️  Warning: Simulation results incomplete. Using projection ranking.")
            results = results.sort_values('projection', ascending=False)
        else:
            # Sort by expected ROI
            results = results.sort_values('expected_roi', ascending=False)
        
        for i, (idx, row) in enumerate(results.head(5).iterrows()):
            lineup_id = int(row['lineup_id']) - 1
            if lineup_id >= len(lineups):
                continue
                
            lineup = lineups[lineup_id]
            
            print(f"LINEUP #{i+1}")
            print("-" * 80)
            
            # Display metrics (with safe defaults)
            roi = row.get('expected_roi', 0.0)
            win_pct = row.get('win_pct', 0.0)
            top10_pct = row.get('top10_pct', 0.0)
            cash_pct = row.get('cash_pct', 0.0)
            
            print(f"Expected ROI: {roi:.1f}%")
            print(f"Win Probability: {win_pct:.3f}%")
            print(f"Top 10% Rate: {top10_pct:.1f}%")
            print(f"Cash Rate: {cash_pct:.1f}%")
            print()
            print(f"Salary: ${row['salary']:,} / $50,000")
            print(f"Projection: {row['projection']:.1f} pts")
            print(f"Ownership: {row['ownership']:.1f}%")
            print()
            
            # Display roster
            for player in lineup['players']:
                print(f"  {player['Position']:3} | {player['Name']:25} | "
                      f"${player['Salary']:>5,} | {player['Projection']:>5.1f} pts | "
                      f"{player['Ownership']:>4.1f}%")
            
            print()
        
        print("=" * 80)
        print()
        
        # Export option
        export = input("Export all lineups to CSV? (y/n): ").strip().lower()
        if export == 'y':
            self._export_lineups(results, lineups)
    
    def _export_lineups(self, results: pd.DataFrame, lineups: List[Dict]):
        """Export lineups to CSV for DraftKings upload"""
        
        export_data = []
        
        for i, lineup in enumerate(lineups[:TOP_LINEUPS_TO_RETURN]):
            row = {}
            
            # DraftKings CSV format expects positions as columns
            for player in lineup['players']:
                pos = player['Position']
                
                # Handle multiple RBs/WRs
                if pos in row:
                    # Find next available slot
                    if pos == 'RB':
                        if 'RB' in row:
                            pos = 'RB2'
                        if 'RB2' in row:
                            pos = 'FLEX'
                    elif pos == 'WR':
                        if 'WR' in row:
                            pos = 'WR2'
                        elif 'WR2' in row:
                            pos = 'WR3'
                        elif 'WR3' in row:
                            pos = 'FLEX'
                    elif pos == 'TE':
                        if 'TE' in row:
                            pos = 'FLEX'
                
                row[pos] = player['Name']
            
            export_data.append(row)
        
        df = pd.DataFrame(export_data)
        filename = f"lineups_{self.contest_type}.csv"
        df.to_csv(filename, index=False)
        
        print(f"✅ Exported to {filename}")
        print()


def main():
    """Command-line interface"""
    
    parser = argparse.ArgumentParser(description='DFS Lineup Optimizer')
    parser.add_argument('--contest', type=str, default='small_gpp',
                       choices=['small_gpp', 'mid_gpp', 'milly_maker'],
                       help='Contest type to optimize for')
    parser.add_argument('--entry', type=float, default=100,
                       help='Entry fee in dollars')
    parser.add_argument('--players', type=str, default='player_pool.csv',
                       help='Path to player pool CSV')
    parser.add_argument('--num-lineups', type=int, default=20,
                       help='Number of lineups to generate')
    
    args = parser.parse_args()
    
    # Initialize optimizer
    optimizer = DFSOptimizer(
        contest_type=args.contest,
        entry_fee=args.entry
    )
    
    # Run optimization
    results, lineups = optimizer.run(
        player_pool_path=args.players,
        num_lineups=args.num_lineups
    )
    
    # Display results for CLI
    if results is not None and lineups is not None:
        optimizer._display_results(results, lineups)


if __name__ == '__main__':
    main()
