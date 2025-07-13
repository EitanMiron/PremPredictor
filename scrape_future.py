#scrape next season's fixtures and team data

import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time
import datetime
from datetime import datetime

options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("window-size=1920,1080")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
url = "https://www.premierleague.com/en/matches?competition=8&season=2025&matchweek=1&month=07"
driver.get(url)
# Wait for the page to load
time.sleep(5)  # Adjust the sleep time as necessary

soup = BeautifulSoup(driver.page_source, "html.parser")
driver.quit()

#get the matchweek title 
matchweek_num = soup.find("h2", class_="match-list-header__title").text.strip()
#print(matchweek_one)



#get the match fixtures from the matchweek
matches = soup.find_all("div", class_="match-card__info")
# All the match day containers (each one corresponds to a date)
match_days = soup.find_all("div", class_="match-list__day")

def convert_match_date(date_str):
    #convert date format from e.g "Fri 15 Aug" to YYYY-MM-DD
    date_parts = date_str.split()
    if len(date_parts) != 3:
        return None
    day = date_parts[1]
    month = date_parts[2]

    # Get the current year (either 2025 or 2026 depending on month of the match)
    year = 2025 if month in ['Aug', 'Sep', 'Oct', 'Nov', 'Dec'] else 2026

    full_date_str = f"{year}-{month}-{day.zfill(2)}"

    #convert to datetime object
    try:
        return datetime.strptime(full_date_str, "%Y-%b-%d").date()
    except ValueError:
        return None

for day in match_days:
    # Get the match date
    date_container = day.find("span", class_="match-list__day-date")
    raw_date = date_container.text.strip() if date_container else "Unknown Date"
    match_date = convert_match_date(raw_date)

    # Get all matches under this date
    matches = day.find_all("div", class_="match-card__info")

    for match in matches:
        try:
            home_team = match.find("div", class_="match-card__team--home").find("span", class_="match-card__team-name--full").text.strip()
            away_team = match.find("div", class_="match-card__team--away").find("span", class_="match-card__team-name--full").text.strip()
            match_time = match.find("span", class_="match-card__kickoff-time").text.strip()

            print(f"Date: {match_date}, Time: {match_time}, Home: {home_team}, Away: {away_team}")
        except AttributeError:
            print("Match parsing failed. Skipping.")

#Now need to scrape data for each set of fixtures for all matchweeks

