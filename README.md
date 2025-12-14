# 🏈 DFS Lineup Optimizer

Free alternative to Stokastic's lineup builder - **reverse engineered from actual simulation data**.

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 🎯 What This Does

Generates optimal DFS (Daily Fantasy Sports) lineups for NFL DraftKings contests by:
- **Analyzing contest structure** (4,444 entries vs 150k+ entries = completely different strategies)
- **Enforcing correlation** (QB + pass catcher stacking)
- **Optimizing ownership** (balance projection vs differentiation)
- **Simulating tournaments** (10,000 Monte Carlo iterations)
- **Calculating expected ROI** (know which lineups are +EV)

## 🔬 Reverse Engineered From Stokastic

This tool analyzes actual Stokastic simulation output to understand:

| Contest Type | Ownership Target | Projection Target | Strategy |
|--------------|------------------|-------------------|----------|
| **4,444 entries (25% to 1st)** | 110-150% total | 135-143 pts | Balance projection + ownership |
| **14k entries (10% payout)** | 40-90% total | 111-120 pts | More contrarian (⚠️ negative ROI) |
| **Millionaire Maker (150k+)** | 30-70% total | 120-135 pts | Extreme differentiation |

### Key Findings:

1. **Contest size determines strategy**
   - Small fields (4k): 70% projection, 30% ownership weighting
   - Large fields (150k): 30% projection, 70% ownership weighting

2. **Stack correlation is mandatory**
   - All winning lineups have QB + at least 2 same-team pass catchers
   - Bring-backs from opponent in high-total games

3. **Ownership sweet spots**
   - 4,444 entries: 12-17% avg ownership per player
   - 150k entries: 3-8% avg ownership per player

## 📦 Installation

```bash
# Clone repository
git clone https://github.com/yourusername/dfs-optimizer.git
cd dfs-optimizer

# Install dependencies
pip install -r requirements.txt
```

## 🚀 Quick Start

### Command Line

```bash
# Generate lineups for small GPP
python main.py --contest small_gpp --entry 100 --num-lineups 20

# Millionaire Maker
python main.py --contest milly_maker --entry 25

# With custom player pool
python main.py --contest small_gpp --players my_players.csv
```

### Streamlit Web App

```bash
streamlit run streamlit_app.py
```

Then open `http://localhost:8501` in your browser.

## 📊 Usage

### 1. Prepare Player Pool

Create CSV with these columns:
```csv
Name,Position,Salary,Team,Opponent
Josh Allen,QB,7500,BUF,NE
Lamar Jackson,QB,6400,BAL,CIN
...
```

### 2. Run Optimizer

```python
from main import DFSOptimizer

optimizer = DFSOptimizer(
    contest_type='small_gpp',
    entry_fee=100
)

results, lineups = optimizer.run(
    player_pool_path='players.csv',
    num_lineups=20
)
```

### 3. Get Results

```
🏆 TOP 5 LINEUPS

LINEUP #1
Expected ROI: 105.2%
Win Probability: 0.085%
Top 10% Rate: 0.5%
Cash Rate: 27.5%

Salary: $50,000 / $50,000
Projection: 136.9 pts
Ownership: 113.8%

  QB  | Lamar Jackson            | $6,400 |  22.0 pts | 10.4%
  RB  | Travis Etienne Jr.       | $6,500 |  18.3 pts | 14.1%
  ...
```

## 🏗️ Architecture

```
dfs_optimizer/
├── config.py              # Contest rules & settings
├── projections.py         # Projection engine
├── optimizer.py           # Lineup builder
├── simulator.py           # Monte Carlo simulator
├── main.py               # CLI application
└── streamlit_app.py      # Web interface
```

### Component Overview

**config.py**
- Contest structure definitions
- Stack rules
- Position requirements
- Variance parameters

**projections.py**
- Generates player projections (can scrape free sources)
- Projects field ownership
- Adjusts for game environment (Vegas lines)

**optimizer.py**
- Builds lineups with constraints
- Enforces correlation (QB + pass catchers)
- Targets optimal ownership range
- Ensures position requirements met

**simulator.py**
- Runs 10,000 Monte Carlo simulations
- Models player variance
- Calculates win%, cash%, ROI
- Simulates entire field

## 🎮 Contest Structures

### Small GPP (4,444 entries)

**Target Profile:**
```python
{
    'ownership_total': (110, 150),  # Sum of all 9 players
    'projection': (135, 143),
    'qb_stack': 'QB + 2 or QB + 3',
    'strategy': 'Balance projection + ownership'
}
```

**Example Lineup:**
- Lamar Jackson (10.4% owned)
- Travis Etienne Jr. + Devin Neal
- JSN + Davante + Zay Flowers
- Total ownership: 113.8% (12.6% avg)
- Expected ROI: 105.5%

### Millionaire Maker (150k+ entries)

**Target Profile:**
```python
{
    'ownership_total': (30, 70),
    'projection': (120, 135),
    'qb_stack': 'QB + 2 or QB + 3 (ultra contrarian)',
    'strategy': 'Extreme differentiation'
}
```

**Example Lineup:**
- Josh Allen (3.9% owned)
- James Cook + D'Andre Swift
- Khalil Shakir + Chris Olave + Courtland Sutton
- Total ownership: 33.6% (3.7% avg)
- Accept lower projection for massive leverage

## 🔧 Configuration

### Modify Contest Rules

Edit `config.py`:

```python
CONTEST_STRUCTURES = {
    'my_custom_gpp': {
        'entries': 10000,
        'ownership_target_total': (80, 120),
        'projection_target': (130, 140),
        'qb_stack_type': ['QB + 2'],
        'projection_weight': 0.60,
        'ownership_weight': 0.40,
        ...
    }
}
```

### Add Projection Sources

Implement web scrapers in `projections.py`:

```python
def scrape_fantasypros() -> pd.DataFrame:
    """Scrape FantasyPros consensus projections"""
    url = "https://www.fantasypros.com/nfl/projections/"
    # ... scraping logic
    return df
```

## 📈 Expected Results

Based on Stokastic's data:

| Contest | Entries | Top ROI | Avg Cash % | Notes |
|---------|---------|---------|------------|-------|
| Small GPP | 4,444 | +105.5% | 27.5% | ✅ Positive EV |
| Mid GPP | 14,000 | -77.4% | 9.0% | ❌ Avoid - negative ROI |
| Milly Maker | 150k+ | Variable | <1% | Lottery ticket |

## 🎓 Key Learnings

### 1. Contest Size Changes Everything

Stokastic's data shows dramatically different strategies:
- **4,444 entries**: Play studs + leverage (Lamar at 10.4%)
- **150,000 entries**: Ultra-contrarian only (Josh Allen at 3.9%)

### 2. Ownership is More Important Than Projection

For top-heavy structures:
- Would rather have 132 pts at 7% ownership
- Than 140 pts at 15% ownership

### 3. Correlation Matters

Every top-20 simulated lineup has QB + at least 1 same-team pass catcher.
Most common: QB + 2 (WR/TE)

### 4. Some Structures Are Unbeatable

14k entries with 10% payout = ALL lineups have negative expected ROI.
Even perfect play loses money over time.

## 🚨 Warnings

### Bankroll Management

- 4,444-entry $100 GPP on $300 bankroll = 33% of roll (RECKLESS)
- Recommended: Never risk more than 5-10% per contest
- For $100 contests, need $1,000+ bankroll

### Data Limitations

- Projections are baseline (not as refined as paid sources)
- Ownership estimates are modeled (not live tracking)
- Late news/injuries require manual adjustment

### Variance

- These are LOTTERY TICKETS
- Even +100% ROI lineups lose 99%+ of the time
- Need many entries to realize long-term EV

## 🤝 Contributing

This is open source - improve it!

**Easy contributions:**
- Add web scrapers for free projection sources
- Improve ownership modeling
- Add NBA/MLB support
- Better UI/UX in Streamlit app

**Technical contributions:**
- Genetic algorithms for lineup diversity
- Machine learning for projection blending
- Live ownership tracking integration
- Pareto optimization for multi-objective

## 📄 License

MIT License - use however you want

## 🙏 Credits

Reverse engineered from Stokastic simulation data.
Built to provide free alternative to $200+/month DFS tools.

## 📞 Support

- **Issues**: Open GitHub issue
- **Questions**: Reddit r/dfsports
- **Updates**: Star the repo for notifications

---

**Disclaimer**: This tool is for research purposes. Always do your own analysis before entering real-money contests. Past performance ≠ future results.
