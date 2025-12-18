import argparse
import sys
import os
import pandas as pd

# Add src to path so we can import modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from scrape_future import scrape_current_season
from predict_future_matches import get_upcoming_fixtures, train_model, predict_matches
from project_standings import get_current_standings, run_monte_carlo_simulation

def main():
    parser = argparse.ArgumentParser(description="Premier League Predictor Pipeline")
    parser.add_argument("--scrape", action="store_true", help="Scrape latest data from FBRef")
    parser.add_argument("--predict", action="store_true", help="Generate predictions for upcoming matches")
    parser.add_argument("--simulate", action="store_true", help="Run Monte Carlo simulation for final standings")
    parser.add_argument("--all", action="store_true", help="Run the full pipeline (Scrape -> Predict -> Simulate)")
    
    args = parser.parse_args()
    
    # If no arguments provided, print help
    if not any(vars(args).values()):
        parser.print_help()
        return

    # 1. SCRAPE
    if args.scrape or args.all:
        print("\n" + "="*40)
        print("STEP 1: SCRAPING DATA")
        print("="*40)
        success = scrape_current_season()
        if not success:
            print("Scraping failed or no data found. Aborting.")
            return

    # 2. PREDICT
    if args.predict or args.all:
        print("\n" + "="*40)
        print("STEP 2: GENERATING PREDICTIONS")
        print("="*40)
        
        # Get Schedule
        fixtures = get_upcoming_fixtures()
        
        if not fixtures.empty:
            # Train
            rf_model, historical_data, predictors, cols, new_cols, opp_mapping = train_model()
            
            # Predict
            results = predict_matches(fixtures, rf_model, historical_data, predictors, cols, new_cols, opp_mapping)
            
            print("\nPredictions generated successfully.")
            
            # Save (already handled inside predict_matches, but good to confirm)
            # results.to_csv(os.path.join("data", "upcoming_predictions.csv"), index=False)
        else:
            print("No upcoming fixtures found. Skipping prediction.")

    # 3. SIMULATE
    if args.simulate or args.all:
        print("\n" + "="*40)
        print("STEP 3: RUNNING SIMULATION")
        print("="*40)
        
        # Get Current Table
        current_dict = get_current_standings()
        
        if current_dict:
            # Run Monte Carlo
            final_table = run_monte_carlo_simulation(current_dict, num_simulations=5000)
            
            # Sort
            final_table = final_table.sort_values("Projected Points", ascending=False)
            
            print("\n" + "="*60)
            print("PROJECTED FINAL PREMIER LEAGUE STANDINGS (Average of 5,000 Simulations)")
            print("="*60)
            # Select relevant columns
            cols = ["Team", "Played", "Current Points", "Projected Points", "Title %", "Top 4 %", "Relegation %"]
            print(final_table[cols].to_string(index=False))
            
            # Save (already handled inside run_monte_carlo_simulation)
            # final_table.to_csv(os.path.join("data", "projected_standings.csv"), index=False)
            print("\nSimulation complete.")

if __name__ == "__main__":
    main()
