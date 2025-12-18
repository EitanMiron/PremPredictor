import pandas as pd

# Load data
try:
    current = pd.read_csv("future_matches_2025.csv")
    preds = pd.read_csv("upcoming_predictions.csv")
except:
    print("Files not found")
    exit()

# Calculate current points
current_points = {}
current_stats = {} # Store W/D/L for current
for _, row in current.iterrows():
    team = row["team"]
    res = row["result"]
    if team not in current_points: 
        current_points[team] = 0
        current_stats[team] = {"W": 0, "D": 0, "L": 0}
    
    if res == "W": 
        current_points[team] += 3
        current_stats[team]["W"] += 1
    elif res == "D": 
        current_points[team] += 1
        current_stats[team]["D"] += 1
    else:
        current_stats[team]["L"] += 1

def simulate_season(win_threshold, draw_threshold_lower=0.0):
    # win_threshold: If prob > this, it's a win
    # draw_threshold_lower: Not used in simple logic, but could be.
    
    sim_stats = {k: v.copy() for k, v in current_stats.items()}
    sim_points = current_points.copy()
    
    for _, row in preds.iterrows():
        home = row["Home"]
        away = row["Away"]
        p_home = float(row["Home Win %"].strip('%')) / 100
        p_draw = float(row["Draw %"].strip('%')) / 100
        p_away = float(row["Away Win %"].strip('%')) / 100
        
        # Logic:
        # 1. If Home or Away is very likely (> win_threshold), give it to them.
        # 2. If not, it's a draw.
        
        if home not in sim_stats: sim_stats[home] = {"W": 0, "D": 0, "L": 0}
        if away not in sim_stats: sim_stats[away] = {"W": 0, "D": 0, "L": 0}

        if p_home > win_threshold:
            sim_points[home] = sim_points.get(home, 0) + 3
            sim_stats[home]["W"] += 1
            sim_stats[away]["L"] += 1
        elif p_away > win_threshold:
            sim_points[away] = sim_points.get(away, 0) + 3
            sim_stats[away]["W"] += 1
            sim_stats[home]["L"] += 1
        else:
            # Draw
            sim_points[home] = sim_points.get(home, 0) + 1
            sim_points[away] = sim_points.get(away, 0) + 1
            sim_stats[home]["D"] += 1
            sim_stats[away]["D"] += 1
            
    return sim_points, sim_stats

print(f"{'Thresh':<6} | {'Winner':<15} | {'Pts':<3} | {'2nd':<15} | {'Pts':<3} | {'Max Draws':<3}")
print("-" * 70)

for t in [0.38, 0.39, 0.40, 0.41, 0.42, 0.43, 0.44, 0.45]:
    pts, stats = simulate_season(t)
    sorted_pts = sorted(pts.items(), key=lambda x: x[1], reverse=True)
    
    winner = sorted_pts[0]
    second = sorted_pts[1]
    
    # Find max draws
    max_draws = 0
    for team in stats:
        if stats[team]["D"] > max_draws: max_draws = stats[team]["D"]
        
    print(f"{t:<6} | {winner[0]:<15} | {winner[1]:<3} | {second[0]:<15} | {second[1]:<3} | {max_draws:<3}")
