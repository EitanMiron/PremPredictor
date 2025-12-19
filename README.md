# Premier League Predictor ⚽🏆

**🔴 Live Demo:** [https://prempredictor.onrender.com/](https://prempredictor.onrender.com/)

A comprehensive Python application that predicts the final standings of the English Premier League using Monte Carlo simulations and machine learning. This project scrapes real-time match data, simulates the remainder of the season thousands of times, and visualizes the probabilities for the title race, top 4, and relegation battles via a web dashboard.

## 🚀 Features

*   **Real-Time Data Scraping**: Automatically collects historical match results and upcoming fixtures using **Selenium** and **BeautifulSoup**.
*   **Monte Carlo Simulation**: Simulates the remaining games of the season 1,000+ times to generate statistically robust projections.
*   **Predictive Modeling**: Uses team form and historical performance to estimate match probabilities.
*   **Interactive Dashboard**: A **Flask** web application that displays the projected league table and allows users to trigger new simulations.
*   **Data Visualization**: Generates dynamic charts for "Title Probabilities" and "Relegation Risk" using **Matplotlib**.
*   **Production Ready**: Fully containerized with **Docker** and configured for deployment on **Render**.

## 🛠️ Tech Stack

*   **Language**: Python 3.13.4
*   **Web Framework**: Flask
*   **Data Science**: Pandas, NumPy, Scikit-learn
*   **Scraping**: Selenium (Headless Chrome), BeautifulSoup4
*   **Visualization**: Matplotlib
*   **Server**: Gunicorn
*   **Deployment**: Docker, Render

## 📂 Project Structure

```
PremPredictor/
├── backend/
│   ├── app.py                 # Main Flask application entry point
│   ├── main.py                # Script runner / entry point
│   ├── data/                  # CSV storage for match data and projections
│   │   ├── fixtures.csv
│   │   ├── future_matches_2025.csv
│   │   ├── matches_data.csv
│   │   ├── predictions.csv
│   │   ├── projected_standings.csv
│   │   └── upcoming_predictions.csv
│   ├── output/                # Generated output files
│   └── src/                   # Source code for logic and scraping
│       ├── predict_future_matches.py
│       ├── prediction.py      # Prediction model logic
│       ├── project_standings.py # Core Monte Carlo simulation logic
│       ├── scrape_future.py   # Scrapes upcoming fixtures
│       ├── scrape_prev.py     # Scrapes past match results
│       └── test_thresholds.py
├── docs/                      # Documentation files
│   ├── PREDICTION_PLAN.md
│   ├── README_DEPLOY.md
│   └── README.md
├── frontend/
│   ├── images/                # Static images
│   ├── scripts/               # JavaScript files
│   │   └── script.js
│   ├── styles/                # CSS stylesheets
│   │   └── style.css
│   └── templates/             # HTML templates
│       └── index.html
├── Dockerfile                 # Docker configuration for deployment
├── Procfile                   # Command for Render/Heroku deployment
├── README.md                  # Project documentation
└── requirements.txt           # Python dependencies
```

## ⚙️ Installation & Setup

### Prerequisites
*   Python 3.10+
*   Google Chrome (for local scraping)

### 1. Clone the Repository
```bash
git clone https://github.com/EitanMiron/PremPredictor.git
cd PremPredictor
```

### 2. Create a Virtual Environment
```bash
python -m venv venv
# Windows
.\venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
python backend/app.py
```
The application will be available at `http://127.0.0.1:5000`.

## 🐳 Docker & Deployment

This project is designed to be deployed easily using Docker.

### Build and Run Locally
```bash
docker build -t prem-predictor .
docker run -p 5000:5000 prem-predictor
```

### Deploy to Render
1.  Push your code to GitHub.
2.  Create a new **Web Service** on Render.
3.  Connect your repository.
4.  Select **Docker** as the runtime.
5.  Render will automatically build and deploy the app using the `Dockerfile`.

## 📊 Usage

1.  **Home Page**: View the current projected standings and probability tables.
2.  **Control Panel**: Click **"Run Simulation & Update View"** to scrape the latest data and re-run the Monte Carlo simulation.
3.  **Visualizations**: Scroll down to see graphical representations of the title race and relegation battle.

## 📝 License

This project is open-source and available under the MIT License.
