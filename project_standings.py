import pandas as pd
import numpy as np

# ---------------------------------------------------------
# 1. CONFIGURATION
# ---------------------------------------------------------
# Map team names from historical data to prediction data if they differ
map_values = {
    "Brighton and Hove Albion": "Brighton",
    "Manchester United": "Manchester Utd",
    "Newcastle United": "Newcastle Utd",
    "Tottenham Hotspur": "Tottenham",
    "West Ham United": "West Ham",
    "Wolverhampton Wanderers": "Wolves",
    "Nottingham Forest": "Nott'ham Forest",
    "Sheffield United": "Sheffield Utd",
    "Leicester City": "Leicester",
    "Leeds United": "Leeds United"
}

def clean_team_name(name):
    return map_values.get(name, name)

# ---------------------------------------------------------
# 2. CALCULATE CURRENT STANDINGS
# ---------------------------------------------------------
def get_current_standings():
    print("Calculating current standings...")
    try:
        df = pd.read_csv("future_matches_2025.csv")
    except FileNotFoundError:
        print("Error: future_matches_2025.csv not found.")
        return pd.DataFrame()

    # Clean team names
    df["team"] = df["team"].apply(clean_team_name)

    # Initialize standings dictionary
    standings = {}

    for index, row in df.iterrows():
        team = row["team"]
        result = row["result"]
        
        if team not in standings:
            standings[team] = {"Played": 0, "Points": 0, "W": 0, "D": 0, "L": 0}

        standings[team]["Played"] += 1
        
        if result == "W":
            standings[team]["Points"] += 3
            standings[team]["W"] += 1
        elif result == "D":
            standings[team]["Points"] += 1
            standings[team]["D"] += 1
        else:
            standings[team]["L"] += 1

    return standings

# ---------------------------------------------------------
# 3. MONTE CARLO SIMULATION
# ---------------------------------------------------------
def run_monte_carlo_simulation(current_standings, num_simulations=1000):
    print(f"Running {num_simulations} Monte Carlo simulations...")
    try:
        preds = pd.read_csv("upcoming_predictions.csv")
    except FileNotFoundError:
        print("Error: upcoming_predictions.csv not found.")
        return pd.DataFrame()

    # Prepare data for simulation
    matches = []
    for _, row in preds.iterrows():
        p_home = float(row["Home Win %"].strip('%')) / 100
        p_draw = float(row["Draw %"].strip('%')) / 100
        p_away = float(row["Away Win %"].strip('%')) / 100
        
        # Sharpen probabilities to reflect realistic dominance (favorites win more often)
        # This helps fix the "low point total" issue caused by conservative raw probabilities
        probs = np.array([p_home, p_draw, p_away])
        
        # Apply moderate sharpening (1.85) to balance top-team dominance with underdog chances
        # This prevents bottom teams from losing *every* game while keeping title contenders strong
        probs = np.power(probs, 1.85) 
        probs = probs / probs.sum()
        
        matches.append({
            "Home": row["Home"],
            "Away": row["Away"],
            "Probs": probs # [Home Win, Draw, Away Win]
        })

    # Initialize accumulators
    team_stats = {team: {"Points": 0} for team in current_standings.keys()}
    
    # Track finishing positions
    # title_count: How many times team finished 1st
    # top4_count: How many times team finished 1st-4th
    # relegation_count: How many times team finished 18th-20th
    counts = {team: {"Title": 0, "Top4": 0, "Relegation": 0} for team in current_standings.keys()}
    
    # Run Simulations
    for i in range(num_simulations):
        # Temp stats for this single simulation
        sim_points = {team: current_standings[team]["Points"] for team in current_standings}
        
        for match in matches:
            home = match["Home"]
            away = match["Away"]
            probs = match["Probs"]
            
            outcome = np.random.choice([0, 1, 2], p=probs)
            
            if outcome == 0: # Home Win
                if home in sim_points: sim_points[home] += 3
            elif outcome == 1: # Draw
                if home in sim_points: sim_points[home] += 1
                if away in sim_points: sim_points[away] += 1
            else: # Away Win
                if away in sim_points: sim_points[away] += 3

        # Accumulate total points for averaging later
        for team, pts in sim_points.items():
            team_stats[team]["Points"] += pts
            
        # Determine rankings for this simulation
        # Sort by points (descending)
        # Note: This simple sort doesn't handle Goal Difference tie-breakers perfectly, 
        # but points are the primary factor.
        sorted_sim = sorted(sim_points.items(), key=lambda x: x[1], reverse=True)
        
        # Update counts based on rank
        for rank, (team, pts) in enumerate(sorted_sim):
            # Rank is 0-indexed (0 = 1st place)
            if rank == 0:
                counts[team]["Title"] += 1
            if rank < 4:
                counts[team]["Top4"] += 1
            if rank >= 17: # 18th, 19th, 20th (in a 20 team league)
                counts[team]["Relegation"] += 1

    # Compile Final Data
    final_data = []
    for team, stats in team_stats.items():
        current = current_standings[team]
        
        avg_pts = stats["Points"] / num_simulations
        
        title_prob = (counts[team]["Title"] / num_simulations) * 100
        top4_prob = (counts[team]["Top4"] / num_simulations) * 100
        rel_prob = (counts[team]["Relegation"] / num_simulations) * 100
        
        final_data.append({
            "Team": team,
            "Played": 38,
            "Current Points": current["Points"],
            "Projected Points": round(avg_pts),
            "Title %": round(title_prob, 1),
            "Top 4 %": round(top4_prob, 1),
            "Relegation %": round(rel_prob, 1)
        })

    return pd.DataFrame(final_data)

# ---------------------------------------------------------
# 4. MAIN EXECUTION
# ---------------------------------------------------------
if __name__ == "__main__":
    # 1. Get Current Table
    current_dict = get_current_standings()
    
    if current_dict:
        # 2. Run Monte Carlo
        # Running 10,000 simulations to get a robust average of final standings.
        final_table = run_monte_carlo_simulation(current_dict, num_simulations=5000)
        
        # Sort
        final_table = final_table.sort_values("Projected Points", ascending=False)
        
        print("\n" + "="*60)
        print("PROJECTED FINAL PREMIER LEAGUE STANDINGS (Average of 5,000 Simulations)")
        print("="*60)
        # Select relevant columns
        cols = ["Team", "Played", "Current Points", "Projected Points", "Title %", "Top 4 %", "Relegation %"]
        print(final_table[cols].to_string(index=False))
        
        # Save
        final_table.to_csv("projected_standings.csv", index=False)
        print("\nSaved to projected_standings.csv")
