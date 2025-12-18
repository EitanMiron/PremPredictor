# Prediction Model Plan for 2025-2026 Season

## Current State Analysis

### What We Have:
1. **Historical Match Data** (`matches_data.csv`):
   - Team-level match records from 2023-2025 seasons
   - Features: venue, opponent, goals, shots, rolling averages, etc.
   - Format: Each row is from one team's perspective (team vs opponent)

2. **Current Model** (`prediction.py`):
   - Binary classification (Win vs Not-Win) using RandomForest
   - Features: venue_code, opp_code, hour, day_code + rolling averages
   - Predicts only whether a team wins or not (doesn't distinguish Draw vs Loss)

3. **Future Matches** (`future_matches_2025.csv`):
   - Will contain completed 2025-2026 matches (16 matchweeks done)
   - Format matches historical data structure

---

## Required Improvements for Accurate Predictions

### 1. **Multi-Class Classification Model** (Win/Draw/Loss)

**Current Problem**: Model only predicts Win (1) vs Not-Win (0)

**Solution**: 
- Change target variable from binary to 3-class: `W` (Win), `D` (Draw), `L` (Loss)
- Use `RandomForestClassifier` with `class_weight='balanced'` to handle class imbalance
- Output class probabilities for Win/Draw/Loss percentages

**Implementation**:
```python
# Current: matches["objective"] = (matches["result"] == "W").astype("int")
# New: matches["result_code"] = matches["result"].map({"W": 0, "D": 1, "L": 2})

# Use predict_proba() to get probabilities for each class
probabilities = model.predict_proba(X_future)
# Returns [P(Win), P(Draw), P(Loss)] for each prediction
```

---

### 2. **Feature Engineering Enhancements**

**Current Features**: Basic venue, opponent, time, rolling stats

**Additional Features to Add**:
- **Opponent Strength**: Rolling averages of opponent's recent performance
- **Head-to-Head**: Historical win rate vs specific opponent
- **Form**: Points from last 5 matches (Win=3, Draw=1, Loss=0)
- **Home/Away Form**: Separate form metrics for home vs away
- **Goal Difference**: Rolling goal difference
- **Expected Goals (xG)**: If available in data
- **Recent Match Difficulty**: Average opponent strength in last 5 matches

---

### 3. **Match-Level Prediction Logic**

**Current Approach**: Predicts from each team's perspective separately

**Better Approach**: 
1. For each future match (Home vs Away):
   - Predict probabilities for Home team: [P(W), P(D), P(L)]
   - Predict probabilities for Away team: [P(W), P(D), P(L)]
   - Combine these to get match-level probabilities

2. **Combining Probabilities**:
   ```
   Match-level probabilities:
   - P(Home Win) = P(Home team wins) × P(Away team loses) [normalized]
   - P(Draw) = P(Home team draws) × P(Away team draws) [normalized]
   - P(Away Win) = P(Home team loses) × P(Away team wins) [normalized]
   ```
   
   OR use a more sophisticated approach:
   - Train a separate model that takes both teams' features as input
   - Predict match outcome directly (H/D/A)

---

### 4. **Handling Future Matches**

**Steps**:
1. **Load completed 2025-2026 matches** from `future_matches_2025.csv`
2. **Filter remaining matches** (from matchweek 17 onwards)
3. **Calculate rolling averages** up to the latest completed match
4. **For each remaining match**:
   - Get home team's most recent stats (rolling averages)
   - Get away team's most recent stats (rolling averages)
   - Extract match features (date, time, venue, etc.)
   - Predict probabilities using trained model

---

### 5. **Season Simulation for Table Predictions**

**Goal**: Predict final standings (Winner, Top 4, Bottom 3)

**Approach**:
1. **Monte Carlo Simulation**:
   - For each remaining match, use predicted probabilities to randomly sample outcomes
   - Repeat simulation 10,000+ times
   - Track points for each team across all simulations
   - Calculate final probabilities

2. **Expected Points Method** (Simpler):
   - For each remaining match: 
     - Home Win: Home +3pts, Away +0pts
     - Draw: Home +1pt, Away +1pt  
     - Away Win: Home +0pts, Away +3pts
   - Calculate expected points: `E[Points] = P(Win)×3 + P(Draw)×1 + P(Loss)×0`
   - Sum expected points with current points to get predicted final totals

3. **Combine Both Approaches**:
   - Use expected points for baseline predictions
   - Use Monte Carlo to get confidence intervals and probability distributions
   - This helps identify teams with high variance (unpredictable outcomes)

---

## Step-by-Step Implementation Plan

### Phase 1: Model Enhancement
1. ✅ Update target variable to 3-class (W/D/L)
2. ✅ Modify model to output probabilities
3. ✅ Add enhanced features (form, opponent strength, etc.)
4. ✅ Evaluate model performance (accuracy, log-loss, confusion matrix)

### Phase 2: Prediction Pipeline
1. ✅ Update data loading to include completed 2025-2026 matches
2. ✅ Create function to calculate rolling stats up to a given date
3. ✅ Build prediction function for future matches
4. ✅ Implement match-level probability combination logic

### Phase 3: Season Simulation
1. ✅ Implement expected points calculation
2. ✅ Implement Monte Carlo simulation
3. ✅ Generate predicted final table
4. ✅ Calculate probabilities for:
   - League Winner
   - Top 4 (Champions League qualification)
   - Bottom 3 (Relegation)

### Phase 4: Validation & Refinement
1. ✅ Validate predictions against actual results (for completed matches)
2. ✅ Compare model performance metrics
3. ✅ Fine-tune features and hyperparameters
4. ✅ Add confidence intervals and uncertainty quantification

---

## Key Challenges & Solutions

### Challenge 1: Data Format Mismatch
**Issue**: `matches_data.csv` is team-centric, but we need match-centric predictions

**Solution**: 
- Keep team-centric approach for training
- When predicting, create two rows per match (home team's perspective + away team's perspective)
- Combine predictions using the logic in Section 3

### Challenge 2: Team Name Inconsistencies
**Issue**: Different sources use different team names

**Solution**: 
- Expand the existing `map_values` dictionary
- Normalize all team names in preprocessing step

### Challenge 3: Handling Newly Promoted Teams
**Issue**: Teams like Sunderland, Leeds, Burnley may not have enough historical data

**Solution**:
- Use league-average stats as priors
- Reduce rolling window for teams with fewer matches
- Consider separate model for newly promoted teams

### Challenge 4: Time-Dependent Features
**Issue**: Rolling averages need to be calculated up to the match date (not including the match itself)

**Solution**:
- Use `closed='left'` in rolling calculations (already done)
- For future matches, calculate rolling stats using only completed matches up to that date
- Order matches chronologically before calculating features

---

## Recommended Model Architecture

```
Input Features:
├── Basic Features
│   ├── venue_code (Home/Away)
│   ├── opp_code (Opponent)
│   ├── hour (Match time)
│   ├── day_code (Day of week)
│   └── season (for trend detection)
│
├── Team Performance (Rolling 3-5 games)
│   ├── goals_for_rolling
│   ├── goals_against_rolling
│   ├── shots_total_rolling
│   ├── shots_on_target_rolling
│   ├── goal_difference_rolling
│   └── points_rolling (3 for W, 1 for D, 0 for L)
│
├── Opponent Strength
│   ├── opponent_recent_form
│   ├── opponent_goal_difference_rolling
│   └── opponent_points_rolling
│
└── Contextual Features
    ├── head_to_head_win_rate (vs this specific opponent)
    ├── home_form / away_form
    └── match_difficulty (avg opponent strength in last 5)

Model: RandomForestClassifier
├── n_estimators: 100-200 (tune via cross-validation)
├── max_depth: 15-20
├── min_samples_split: 20-30
├── class_weight: 'balanced' (handle W/D/L imbalance)
└── random_state: 1 (reproducibility)

Output: [P(Win), P(Draw), P(Loss)] probabilities
```

---

## Success Metrics

1. **Model Performance**:
   - Multi-class accuracy > 50% (baseline: 33.3% for random)
   - Log-loss < 0.9
   - Well-calibrated probabilities (reliability curve)

2. **Prediction Quality**:
   - For completed matches: How well did we predict?
   - Compare expected vs actual points

3. **Table Prediction**:
   - Correctly identify top 4 with >60% probability
   - Correctly identify bottom 3 with >60% probability
   - Winner prediction confidence interval includes actual winner

---

## Next Steps (Priority Order)

1. **Immediate**: 
   - Restructure model to predict W/D/L probabilities
   - Test on completed 2025-2026 matches for validation

2. **Short-term**:
   - Implement enhanced features
   - Build prediction pipeline for remaining matches

3. **Medium-term**:
   - Implement season simulation
   - Generate final table predictions

4. **Long-term**:
   - Continuous model improvement as new match data arrives
   - Add ensemble methods (combine multiple models)
   - Consider advanced models (XGBoost, Neural Networks)

