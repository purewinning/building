# 📊 DFS Lineup Structure Guide
## Reverse Engineered from Stokastic Simulation Data

---

## 🎯 Contest Type 1: Small GPP (4,444 Entries, 25% to 1st)

### Optimal Structure

| Metric | Target | Actual Best Build |
|--------|--------|-------------------|
| **Total Ownership** | 110-150% | 113.8% |
| **Avg Ownership** | 12-17% per player | 12.6% |
| **Projection** | 135-143 pts | 136.9 pts |
| **Expected ROI** | 80-120% | 105.5% |

### Position-by-Position Strategy

**QB (Most Important)**
- Target: 3-10% owned (prefer 3-6%)
- Strategy: Find leverage against chalk
- Example: Lamar (10.4%) beats Josh Allen (3.9%) here because projection matters
- Avoid: Anyone >15% owned

**RB1 + RB2**
- Mix of: 1 safe floor (ETN 14.1%) + 1 leverage (Devin Neal 8.9%)
- Don't play 2 ultra-chalk RBs (CMC + Saquon both >20%)
- Value RBs ($5,300-$6,500) enable stacking

**WR1 + WR2 + WR3**
- MUST include QB's teammates (correlation)
- Can play 1 necessary chalk (Chase 28.7%)
- Need 1-2 leverage WRs (5-10% owned)
- Bring-back from opponent if high-total game

**TE**
- Usually punt (<$4,500)
- Leverage if same team as QB
- Example: Mark Andrews $3,900 with Lamar

**FLEX**
- Use for bring-back or value RB
- Should be 5-15% owned

**DST**
- Min price ($2,300-$2,500)
- Ownership doesn't matter much

### Stack Requirements

**Primary Stack: QB + 2 or QB + 3**
```
Lamar Jackson (BAL) 10.4%
  ↓
Zay Flowers (BAL) 9.4%
Mark Andrews (BAL) 11.1%
```

**Bring-Back (Optional but Recommended)**
```
Mike Gesicki (CIN) 11.9%
  ↑ (opponent in BAL/CIN 50.0 total)
```

### Example Winning Lineup

```
QB:  Lamar Jackson     $6,400   22.0 pts   10.4%  ← Stack anchor
RB:  Travis Etienne    $6,500   18.3 pts   14.1%  ← Safe floor
RB:  Devin Neal        $5,300   14.3 pts    8.9%  ← Leverage
WR:  Jaxon Smith-Njigba$8,600   22.2 pts   15.9%  ← Necessary chalk
WR:  Davante Adams     $7,200   17.7 pts   14.1%  ← Exposure to DET/LAR
WR:  Zay Flowers       $6,300   14.7 pts    9.4%  ← Stack piece
TE:  Mark Andrews      $3,900   10.9 pts   11.1%  ← Stack piece + value
FLX: Mike Gesicki      $3,300   10.1 pts   11.9%  ← Bring-back
DST: Saints            $2,500    6.7 pts    5.8%  ← Punt

Total: $50,000 | 136.9 pts | 113.8% own | 105.5% ROI
```

### Game Theory

**What You're Doing:**
- Playing BAL passing game (QB + 2)
- Bringing back CIN side of shootout
- Mixing in necessary chalk (JSN, Davante)
- Avoiding ultra-chalk (Puka at 34.4%)

**Why It Works:**
- If BAL/CIN goes over 55 combined → your stack crushes
- 12.6% avg ownership = perfect balance
- Not too chalky (most have 15-20%)
- Not too contrarian (some have <8%)

---

## 🎯 Contest Type 2: Mid GPP (14,000 Entries, 10% Payout)

### ⚠️ WARNING: NEGATIVE ROI STRUCTURE

| Metric | Target | Best Build |
|--------|--------|------------|
| **Total Ownership** | 40-90% | 62.6% |
| **Avg Ownership** | 5-10% per player | 7.0% |
| **Projection** | 111-120 pts | 115.0 pts |
| **Expected ROI** | **-77.4% to -89.3%** | **-77.4%** |

### Critical Finding

**ALL SIMULATED LINEUPS LOSE MONEY**

Even the "best" lineup has -77.4% ROI. Here's why:
- 14,000 entries = large field
- 10% payout = only top 1,400 cash
- Payouts are FLAT (not top-heavy enough)
- Need to finish ~top 200 just to break even

### If You Must Play

**More contrarian than small GPP:**
- QB: <5% owned
- RBs: Mix of 2-8% owned
- WRs: Avoid anyone >15%
- Accept lower projection (111-120 range)

**But seriously: DON'T PLAY THIS STRUCTURE**

---

## 🎯 Contest Type 3: Millionaire Maker (150k+ Entries)

### Optimal Structure

| Metric | Target |
|--------|--------|
| **Total Ownership** | 30-70% |
| **Avg Ownership** | 3-8% per player |
| **Projection** | 120-135 pts |
| **Strategy** | Extreme differentiation |

### Position-by-Position Strategy

**QB**
- Target: <5% owned (prefer <4%)
- Examples: Josh Allen (3.9%), Jalen Hurts (3.3%), Mahomes (3.2%)
- Avoid: Lamar (10.4%), Stafford (10.3%)

**RBs**
- Both should be <10% owned
- Can sacrifice projection for leverage
- Example: D'Andre Swift (2.6%), Chuba Hubbard (3.8%)

**WRs**
- All 3 should be <8% owned
- Include 2 QB stack pieces
- Example: Khalil Shakir (2.6%), Chris Olave (5.4%)

**Stack: Still QB + 2 or QB + 3**
```
Josh Allen (3.9%)
  ↓
James Cook (4.6%)  ← Same team RB (elite correlation)
Khalil Shakir (2.6%)
```

### Example Millionaire Maker Lineup

```
QB:  Josh Allen         $7,500   22.9 pts    3.9%
RB:  James Cook         $8,000   18.4 pts    4.6%
RB:  D'Andre Swift      $5,700   13.6 pts    2.6%
WR:  Khalil Shakir      $5,300   11.1 pts    2.6%
WR:  Chris Olave        $6,200   14.5 pts    5.4%
WR:  Courtland Sutton   $5,500   12.6 pts    5.1%
TE:  Hunter Henry       $4,400   10.4 pts    3.6%
FLX: Chuba Hubbard      $4,600   11.1 pts    3.8%
DST: Titans             $2,300    5.6 pts    2.0%

Total: $49,500 | 120.2 pts | 33.6% own | 3.7% avg
```

### The Math

**With 150,000 entries:**
- Josh Allen (3.9%) = 5,850 people have him
- Full stack (Allen + Cook + Shakir) = maybe 1,000 people
- If this stack goes nuclear → you're competing with 1,000 for top spots
- Win equity: ~0.1% (vs 0.0007% random)

**The Trade-Off:**
- Lower projection (120 vs 137)
- But 3x more differentiated
- If Allen + Cook both hit 25+ → YOU WIN

### What You're Fading

**Fade ALL chalk:**
- No Puka Nacua (34.4%)
- No Lamar Jackson (10.4%)
- No Matthew Stafford (10.3%)
- No exposure to DET/LAR game

**The Risk:**
If DET/LAR explodes and your stack busts → you're cooked

**But that's the point:** You need EVERYTHING to go right in Millionaire Maker

---

## 🔑 Universal Principles

### 1. Stack Correlation is Mandatory

**Never play naked QB** (QB with no same-team pieces)

Correlation strength:
1. **QB + RB (same team)** - Elite (when one hits, both hit)
2. **QB + 2 WRs (same team)** - Strong (passing volume helps both)
3. **QB + WR + TE** - Good (target distribution)

### 2. Contest Size Determines Strategy

| Entries | Projection Weight | Ownership Weight |
|---------|-------------------|------------------|
| <5,000 | 70% | 30% |
| 5k-20k | 50% | 50% |
| 20k-100k | 40% | 60% |
| 100k+ | 30% | 70% |

### 3. Ownership Tiers

**Ultra Chalk (>30%)**
- Can play 0-1 pieces in small GPP
- Must fade entirely in large GPP
- Examples: Puka (34.4%), Woody Marks (30.7%)

**Chalk (20-30%)**
- Can play 1-2 in small GPP
- Fade in large GPP
- Examples: Ja'Marr Chase (28.7%), CMC (21.7%)

**Popular (12-20%)**
- Safe to play 2-3 in small GPP
- Play 0-1 in large GPP
- Examples: JSN (15.9%), Gibbs (16.9%)

**Leverage (5-12%)**
- Your sweet spot for differentiation
- Play 2-4 of these
- Examples: Zay Flowers (9.4%), Devin Neal (8.9%)

**Contrarian (<5%)**
- Must have 1-2 in small GPP
- Must have 4-6 in Millionaire Maker
- Examples: Allen (3.9%), Hurts (3.3%), Shakir (2.6%)

### 4. Bring-Back Strategy

**When to bring back:**
- High-total games (50.0+ combined)
- Your QB is in that game
- Opponent has pass-heavy script

**Example:**
```
Primary: Lamar + Andrews + Zay (BAL)
Bring-back: Ja'Marr Chase (CIN)

If BAL/CIN goes over 60 combined, both sides hit
```

### 5. Value RBs Enable Stacking

**The math:**
- QB + 2 WRs costs ~$19k-$21k
- Need RBs under $6,500 to afford it
- Woody Marks ($5,600) enables expensive stacks

---

## 🎓 Advanced Concepts

### Leverage Score

```
Leverage = Optimal % - Ownership %
```

- Positive leverage = underowned relative to projection
- Negative leverage = overowned (avoid)

**Example:**
- Chris Olave: 14.5 projection, 5.4% owned
- Expected optimal: 8.0%
- Leverage: +3.6 (GOOD - play him)

### Correlation Matrix

**Highly correlated (play together):**
- QB + same-team WR/TE: +0.65
- QB + same-team RB: +0.55
- WR1 + WR2 (same team): +0.35

**Negatively correlated (don't play together):**
- Opposing QBs: -0.25
- QB + opposing RB: -0.15

### Game Script Theory

**Teams trailing by 14+:**
- Boost passing volume (+20%)
- Reduce RB touches (-30%)

**Teams ahead by 14+:**
- Boost RB volume (+25%)
- Reduce passing (-15%)

**High totals (50+):**
- Both QBs + pass catchers boosted
- Bring-back strategy optimal

---

## 📋 Quick Reference Checklist

### Before Building Lineup:

- [ ] Identify contest type (small/mid/large)
- [ ] Set ownership targets
- [ ] Choose QB with leverage
- [ ] Build 2-3 piece stack
- [ ] Include bring-back if applicable
- [ ] Mix leverage plays (5-10% owned)
- [ ] Check total ownership sum
- [ ] Verify projection range
- [ ] Confirm salary under $50k

### Red Flags:

- ❌ Naked QB (no same-team pieces)
- ❌ Ownership too high for contest (15%+ avg in Milly Maker)
- ❌ Ownership too low for contest (5%- avg in small GPP)
- ❌ Projection too low (<130 in small GPP)
- ❌ No leverage plays (everyone 15%+ owned)
- ❌ Playing mid-size flat payout contests (negative ROI)

---

## 🏆 Real Examples from Stokastic Data

### Top ROI Build (4,444 entries): +105.5%

**Why it works:**
- Lamar stack at 10.4% (not too chalky for this size)
- Bring-back from CIN (Gesicki)
- Mix of leverage (Devin Neal 8.9%)
- 113.8% total ownership = perfect
- 136.9 projection = competitive

### Failed Build (14k entries): -89.3%

**Why it fails:**
- Even though ownership is low (56.7%)
- Even though stack is good (Justin Herbert + 2)
- The contest structure has no winners
- 14k + 10% payout = everyone loses

---

Use this guide as your blueprint. Contest structure determines everything!
