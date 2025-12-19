# Deployment Guide

This project is set up for deployment using **Docker** or standard PaaS providers like **Heroku** or **Render**.

## Option 1: Docker (Recommended)

Docker is recommended because this application uses Selenium for scraping, which requires a specific browser environment (Chrome) that is pre-configured in the Dockerfile.

1.  **Build the image:**
    ```bash
    docker build -t prem-predictor .
    ```

2.  **Run the container:**
    ```bash
    docker run -p 5000:5000 prem-predictor
    ```

3.  Access the app at `http://localhost:5000`.

## Option 2: Render / Heroku (No Docker)

If you deploy without Docker, the scraping functionality (`--scrape`) might fail if the server does not have Chrome installed. However, the web dashboard and simulations (which use existing CSV data) will work fine.

**Procfile** is included for these platforms:
```text
web: gunicorn --chdir PremPredictor backend.app:app
```

## Environment Variables

Ensure you set the following environment variables in your deployment platform if needed:
-   `FLASK_ENV`: `production`
-   `SECRET_KEY`: Set a strong secret key for Flask sessions.
