import pandas as pd
import time
import os
from sklearn.ensemble import RandomForestClassifier
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# ---------------------------------------------------------
# 1. SETUP & CONFIGURATION
# ---------------------------------------------------------
# Define paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

# Team name mapping to ensure consistency between schedule and historical data
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
# 2. SCRAPE UPCOMING FIXTURES
# ---------------------------------------------------------
def get_upcoming_fixtures():
    # Check if fixtures are already saved to avoid re-scraping
    try:
        fixtures = pd.read_csv(os.path.join(DATA_DIR, "fixtures.csv"))
        print("Loaded fixtures from fixtures.csv")
        return fixtures
    except FileNotFoundError:
        pass

    print("Scraping upcoming fixtures...")
    
    options = Options()
    # options.add_argument("--headless") 
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    url = "https://fbref.com/en/comps/9/schedule/Premier-League-Scores-and-Fixtures"
    
    try:
        driver.get(url)
        time.sleep(5) # Wait for page to load
        print(f"Page title: {driver.title}")
        
        # Wait for table
        # Try 2024-2025 first, as that is the current season
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "sched_2024-2025_9_1")))
            table_id = "sched_2024-2025_9_1"
        except:
            # Fallback to 2025-2026 if the season rolled over
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "sched_2025-2026_9_1")))
            table_id = "sched_2025-2026_9_1"
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        table = soup.find("table", id=table_id)
        
        fixtures = []
        if table and table.tbody:
            for row in table.tbody.find_all("tr"):
                # Skip spacer rows
                if "spacer" in row.get("class", []):
                    continue
                
                # Check if match is in the future (no result yet)
                score_cell = row.find("td", {"data-stat": "score"})
                if score_cell and not score_cell.text.strip():
                    # This is a future match
                    date = row.find("td", {"data-stat": "date"}).text.strip()
                    home = row.find("td", {"data-stat": "home_team"}).text.strip()
                    away = row.find("td", {"data-stat": "away_team"}).text.strip()
                    
                    if date and home and away:
                        fixtures.append({
                            "date": date,
                            "home_team": clean_team_name(home),
                            "away_team": clean_team_name(away)
                        })
                        
        print(f"Found {len(fixtures)} upcoming matches.")
        df = pd.DataFrame(fixtures)
        df.to_csv(os.path.join(DATA_DIR, "fixtures.csv"), index=False)
        return df
        
    except Exception as e:
        print(f"Error scraping fixtures: {e}")
        return pd.DataFrame()
    finally:
        driver.quit()

# ---------------------------------------------------------
# 3. PREPARE DATA & TRAIN MODEL
# ---------------------------------------------------------
def train_model():
    print("Loading historical data...")
    # Load past data
    matches = pd.read_csv(os.path.join(DATA_DIR, 'matches_data.csv'))
    
    # Load current season played matches
    try:
        current_season = pd.read_csv(os.path.join(DATA_DIR, 'future_matches_2025.csv'))
        # Align columns if necessary
        matches = pd.concat([matches, current_season], ignore_index=True)
    except FileNotFoundError:
        print("future_matches_2025.csv not found, using only historical data.")

    # Preprocessing
    matches["date"] = pd.to_datetime(matches["date"])
    matches["venue_code"] = matches["venue"].astype("category").cat.codes
    matches["opp_code"] = matches["opponent"].astype("category").cat.codes
    matches["hour"] = matches["time"].str.split(":").str[0].astype("int")
    matches["day_code"] = matches["date"].dt.dayofweek
    
    # Create mapping for opponents to codes
    opp_mapping = dict(zip(matches["opponent"], matches["opp_code"]))

    # Target: 0=Loss, 1=Draw, 2=Win
    target_map = {"L": 0, "D": 1, "W": 2}
    matches["target"] = matches["result"].map(target_map)
    
    # Points: 0=Loss, 1=Draw, 3=Win
    points_map = {"L": 0, "D": 1, "W": 3}
    matches["points"] = matches["result"].map(points_map)

    # --- NEW FEATURE: Season Points Per Game (PPG) ---
    def calculate_season_ppg(group):
        group = group.sort_values("date")
        # Cumulative points
        group["cum_points"] = group["points"].cumsum()
        # Cumulative games (using rank)
        group["game_number"] = range(1, len(group) + 1)
        # PPG entering the match (shift 1 so we don't use the match result itself)
        group["season_ppg"] = (group["cum_points"] / group["game_number"]).shift(1)
        # Fill first game with 0 (or 1.0 as neutral, but 0 is safer)
        group["season_ppg"] = group["season_ppg"].fillna(0)
        return group

    matches = matches.groupby(["team", "season"], group_keys=False).apply(calculate_season_ppg)
    # -------------------------------------------------

    # Predictors
    predictors = ["venue_code", "opp_code", "hour", "day_code", "season_ppg"]
    
    # Rolling Averages
    cols = ["goals for", "goals against", "shots total", "shots on target", "points"]
    new_cols = [f"{c}_rolling" for c in cols]
    
    def rolling_averages(group, cols, new_cols):
        group = group.sort_values("date")
        rolling_stats = group[cols].rolling(5, closed='left').mean()
        group[new_cols] = rolling_stats
        group = group.dropna(subset=new_cols)
        return group

    matches_rolling = matches.groupby("team", group_keys=False).apply(lambda x: rolling_averages(x, cols, new_cols)).reset_index(drop=True)
    
    # Add Opponent Rolling Stats
    matches_rolling["new_team"] = matches_rolling["team"].apply(clean_team_name)
    opp_stats = matches_rolling[["date", "new_team", "season_ppg"] + new_cols].copy()
    opp_new_cols = [f"opp_{c}" for c in new_cols]
    # Add opp_season_ppg to the list of columns to rename
    opp_stats.columns = ["date", "opponent", "opp_season_ppg"] + opp_new_cols
    
    matches_rolling = matches_rolling.merge(opp_stats, on=["date", "opponent"], how="left")
    matches_rolling = matches_rolling.dropna()
    
    # Train Random Forest
    print("Training model...")
    # Use sample weights to favor recent seasons
    # Adjusted to balance Current Form (2025) with Historical Class (2023-24)
    # This prevents teams having a "hot start" (like Villa) from being overrated vs consistent giants (Arsenal)
    season_weights = {2020: 0.5, 2021: 0.5, 2022: 1, 2023: 2, 2024: 4, 2025: 6}
    sample_weights = matches_rolling["season"].map(season_weights).fillna(1)

    rf = RandomForestClassifier(n_estimators=100, min_samples_split=10, random_state=1)
    
    full_predictors = predictors + ["opp_season_ppg"] + new_cols + opp_new_cols
    rf.fit(matches_rolling[full_predictors], matches_rolling["target"], sample_weight=sample_weights)
    
    return rf, matches_rolling, full_predictors, cols, new_cols, opp_mapping

# ---------------------------------------------------------
# 4. PREDICT FUTURE MATCHES
# ---------------------------------------------------------
def predict_matches(fixtures, model, data, predictors, cols, new_cols, opp_mapping):
    print("\nGenerating predictions for upcoming matches...")
    
    predictions = []
    
    for index, row in fixtures.iterrows():
        home_team = row["home_team"]
        away_team = row["away_team"]
        date = pd.to_datetime(row["date"])
        
        # Get latest stats for Home Team
        home_stats = data[data["new_team"] == home_team].sort_values("date").iloc[-1:]
        if home_stats.empty:
            print(f"Insufficient data for {home_team}")
            continue
            
        # Get latest stats for Away Team
        away_stats = data[data["new_team"] == away_team].sort_values("date").iloc[-1:]
        if away_stats.empty:
            print(f"Insufficient data for {away_team}")
            continue
            
        # Helper to get next rolling stats
        def get_next_rolling(team_name):
            team_data = data[data["new_team"] == team_name].sort_values("date")
            # We take the last 5 games to calculate the average for the next one
            last_5 = team_data.iloc[-5:]
            return last_5[cols].mean()

        # Helper to get current season PPG
        def get_current_ppg(team_name):
            # Filter for current season (2025)
            team_data = data[(data["new_team"] == team_name) & (data["season"] == 2025)].sort_values("date")
            if team_data.empty:
                return 0
            # Calculate total points / total games
            total_points = team_data["points"].sum()
            total_games = len(team_data)
            return total_points / total_games if total_games > 0 else 0

        home_rolling = get_next_rolling(home_team)
        away_rolling = get_next_rolling(away_team)
        
        home_ppg = get_current_ppg(home_team)
        away_ppg = get_current_ppg(away_team)
        
        # Build input row
        input_data = {
            "venue_code": 1, # Home
            "opp_code": opp_mapping.get(away_team, -1), # Use mapping
            "hour": 15, # Default to 3pm if unknown
            "day_code": date.dayofweek,
            "season_ppg": home_ppg,
            "opp_season_ppg": away_ppg
        }
        
        # Add Home Rolling Stats
        for col, val in zip(new_cols, home_rolling):
            input_data[col] = val
            
        # Add Away Rolling Stats (as Opponent Stats)
        for col, val in zip(new_cols, away_rolling):
            input_data[f"opp_{col}"] = val
            
        # Create DataFrame for prediction
        X = pd.DataFrame([input_data])
        
        # Predict
        # 0=Loss, 1=Draw, 2=Win
        probs = model.predict_proba(X)[0]
        
        predictions.append({
            "Date": date.date(),
            "Home": home_team,
            "Away": away_team,
            "Home Win %": f"{probs[2]:.2%}",
            "Draw %": f"{probs[1]:.2%}",
            "Away Win %": f"{probs[0]:.2%}", # Home Loss = Away Win
            "Prediction": ["Away Win", "Draw", "Home Win"][probs.argmax()]
        })
        
    return pd.DataFrame(predictions)

# ---------------------------------------------------------
# MAIN EXECUTION
# ---------------------------------------------------------
if __name__ == "__main__":
    # 1. Get Schedule
    fixtures = get_upcoming_fixtures()
    
    if not fixtures.empty:
        # 2. Train
        rf_model, historical_data, predictors, cols, new_cols, opp_mapping = train_model()
        
        # 3. Predict
        results = predict_matches(fixtures, rf_model, historical_data, predictors, cols, new_cols, opp_mapping)
        
        print("\n" + "="*50)
        print("PREDICTIONS FOR UPCOMING MATCHES")
        print("="*50)
        print(results.to_string(index=False))
        
        # Save
        results.to_csv(os.path.join(DATA_DIR, "upcoming_predictions.csv"), index=False)
        print("\nSaved to upcoming_predictions.csv")
    else:
        print("No upcoming fixtures found.")
