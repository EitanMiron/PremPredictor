from flask import Flask, render_template, send_file, redirect, url_for, flash
import pandas as pd
import matplotlib
matplotlib.use('Agg') # Use non-interactive backend
import matplotlib.pyplot as plt
import io
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from project_standings import get_current_standings, run_monte_carlo_simulation

app = Flask(__name__)
app.secret_key = 'premier_league_predictor_secret_key' # Required for flash messages
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

@app.route('/')
def index():
    # Load projected standings if available, otherwise run simulation
    csv_path = os.path.join(DATA_DIR, "projected_standings.csv")
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
    else:
        # Run simulation on the fly if no file exists
        current = get_current_standings()
        if current:
            df = run_monte_carlo_simulation(current, num_simulations=1000)
            df = df.sort_values("Projected Points", ascending=False)
        else:
            return "Error: Could not load data."

    # Convert to list of dicts for template
    standings = df.to_dict('records')
    return render_template('index.html', standings=standings)

@app.route('/run/simulate', methods=['POST'])
def run_simulate():
    try:
        current = get_current_standings()
        if current:
            df = run_monte_carlo_simulation(current, num_simulations=5000)
            df = df.sort_values("Projected Points", ascending=False)
            
            # Save projections
            df.to_csv(os.path.join(DATA_DIR, "projected_standings.csv"), index=False)
            flash("Simulation completed successfully!", "success")
        else:
            flash("Could not get current standings.", "error")
    except Exception as e:
        flash(f"Error during simulation: {str(e)}", "error")
    return redirect(url_for('index'))

@app.route('/plot/title_race')
def plot_title_race():
    try:
        csv_path = os.path.join(DATA_DIR, "projected_standings.csv")
        if not os.path.exists(csv_path):
            print(f"CSV not found at {csv_path}")
            return "No data", 404
        
        df = pd.read_csv(csv_path)
        print(f"Loaded CSV with {len(df)} rows")
        
        # Filter teams with > 0.1% title chance
        title_contenders = df[df["Title %"] > 0.1].sort_values("Title %", ascending=True)
        print(f"Title contenders: {len(title_contenders)}")
        
        if title_contenders.empty:
            print("No title contenders found")
            # Create a dummy plot saying "No Data"
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, 'No Title Contenders (>0.1%)', ha='center', va='center')
        else:
            fig, ax = plt.subplots(figsize=(10, 6))
            bars = ax.barh(title_contenders["Team"], title_contenders["Title %"], color='skyblue')
            ax.set_xlabel("Title Probability (%)")
            ax.set_title("Premier League Title Race Probabilities")
            
            # Add labels
            for bar in bars:
                width = bar.get_width()
                ax.text(width + 0.5, bar.get_y() + bar.get_height()/2, f'{width}%', ha='left', va='center')
        
        plt.tight_layout()
        
        img = io.BytesIO()
        fig.savefig(img, format='png')
        img.seek(0)
        plt.close(fig) # Close the specific figure
        return send_file(img, mimetype='image/png')
    except Exception as e:
        print(f"Error in plot_title_race: {e}")
        return str(e), 500

@app.route('/plot/relegation')
def plot_relegation():
    try:
        csv_path = os.path.join(DATA_DIR, "projected_standings.csv")
        if not os.path.exists(csv_path):
            return "No data", 404
        
        df = pd.read_csv(csv_path)
        # Filter teams with > 1% relegation chance
        relegation_candidates = df[df["Relegation %"] > 1.0].sort_values("Relegation %", ascending=True)
        
        if relegation_candidates.empty:
             fig, ax = plt.subplots(figsize=(10, 6))
             ax.text(0.5, 0.5, 'No Relegation Candidates (>1%)', ha='center', va='center')
        else:
            fig, ax = plt.subplots(figsize=(10, 6))
            bars = ax.barh(relegation_candidates["Team"], relegation_candidates["Relegation %"], color='salmon')
            ax.set_xlabel("Relegation Probability (%)")
            ax.set_title("Relegation Battle Probabilities")
            
            # Add labels
            for bar in bars:
                width = bar.get_width()
                ax.text(width + 0.5, bar.get_y() + bar.get_height()/2, f'{width}%', ha='left', va='center')
        
        plt.tight_layout()
        
        img = io.BytesIO()
        fig.savefig(img, format='png')
        img.seek(0)
        plt.close(fig)
        return send_file(img, mimetype='image/png')
    except Exception as e:
        print(f"Error in plot_relegation: {e}")
        return str(e), 500

if __name__ == '__main__':
    app.run(debug=True)
