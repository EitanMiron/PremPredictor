from flask import Flask, render_template, send_file
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

@app.route('/plot/title_race')
def plot_title_race():
    csv_path = os.path.join(DATA_DIR, "projected_standings.csv")
    if not os.path.exists(csv_path):
        return "No data"
    
    df = pd.read_csv(csv_path)
    # Filter teams with > 0.1% title chance
    title_contenders = df[df["Title %"] > 0.1].sort_values("Title %", ascending=True)
    
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
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()
    return send_file(img, mimetype='image/png')

@app.route('/plot/relegation')
def plot_relegation():
    csv_path = os.path.join(DATA_DIR, "projected_standings.csv")
    if not os.path.exists(csv_path):
        return "No data"
    
    df = pd.read_csv(csv_path)
    # Filter teams with > 1% relegation chance
    relegation_candidates = df[df["Relegation %"] > 1.0].sort_values("Relegation %", ascending=True)
    
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
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()
    return send_file(img, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)
