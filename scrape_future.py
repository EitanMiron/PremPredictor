# scrape next season's fixtures and team data

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime

# Set up headless Chrome driver
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("window-size=1920,1080")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Converts date string like "Fri 15 Aug" to "2025-08-15" or "2026-01-05"
def convert_match_date(date_str):
    date_parts = date_str.split()
    if len(date_parts) != 3:
        return None
    day = date_parts[1]
    month = date_parts[2]

    # Decide the correct year based on the month
    year = 2025 if month in ['Aug', 'Sep', 'Oct', 'Nov', 'Dec'] else 2026
    full_date_str = f"{year}-{month}-{day.zfill(2)}"

    try:
        return datetime.strptime(full_date_str, "%Y-%b-%d").date()
    except ValueError:
        return None

# -------- Scrape Matchweek 1 --------
url = "https://www.premierleague.com/en/matches?competition=8&season=2025&matchweek=1&month=07"
driver.get(url)
time.sleep(5)

soup = BeautifulSoup(driver.page_source, "html.parser")
match_days = soup.find_all("div", class_="match-list__day")

matchweek_one_data = []

for day in match_days:
    date_container = day.find("span", class_="match-list__day-date")
    raw_date = date_container.text.strip() if date_container else "Unknown Date"
    match_date = convert_match_date(raw_date)

    matches = day.find_all("div", class_="match-card__info")
    for match in matches:
        try:
            home_team = match.find("div", class_="match-card__team--home").find("span", class_="match-card__team-name--full").text.strip()
            away_team = match.find("div", class_="match-card__team--away").find("span", class_="match-card__team-name--full").text.strip()
            match_time = match.find("span", class_="match-card__kickoff-time").text.strip()

            print(f"Date: {match_date}, Time: {match_time}, Home: {home_team}, Away: {away_team}")

            matchweek_one_data.append({
                "date": match_date,
                "time": match_time,
                "home_team": home_team,
                "away_team": away_team,
                "matchweek": 1
            })
        except AttributeError:
            print("Match parsing failed. Skipping.")

matchweek_one_df = pd.DataFrame(matchweek_one_data)

# -------- Scrape Matchweeks 2 to 38 --------
rest_of_fixtures_url = "https://www.premierleague.com/en/matches?competition=8&season=2025&matchweek={}&month={}"
team_data = []



#create a dictionary to map month names to their numeric values
#reduces redundancy in the code in preventing scraping unnecessary months for matchweeks that cannot possibly be in that month
matchweek_month_map = {
    2: ['08'], 3: ['08'], 4: ['09'], 5: ['09'], 6: ['09'], 7: ['09'], 8: ['10'], 9: ['10'],
    10: ['10'], 11: ['11'], 12: ['11'], 13: ['11'], 14: ['12'], 15: ['12'], 16: ['12'], 17: ['12'], 18: ['01'],
    19: ['01'], 20: ['01'], 21: ['02'], 22: ['02'], 23: ['02'], 24: ['02'], 25: ['02'], 26: ['03'], 27: ['03'],
    28: ['03'], 29: ['03'], 30: ['03'], 31: ['04'], 32: ['04'], 33: ['04'], 34: ['04'], 35: ['04'], 36: ['05'],
    37: ['05'], 38: ['05'],
}



for matchweek, months in matchweek_month_map.items():
    for month in months:
        matchweek_url = rest_of_fixtures_url.format(matchweek, month)
        print(f"Scraping matchweek {matchweek} for month {month}...")

        driver.get(matchweek_url)
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, "html.parser")

        match_days = soup.find_all("div", class_="match-list__day")
        for day in match_days:
            date_container = day.find("span", class_="match-list__day-date")
            raw_date = date_container.text.strip() if date_container else "Unknown Date"
            match_date = convert_match_date(raw_date)

            matches = day.find_all("div", class_="match-card__info")
            for match in matches:
                try:
                    home_team = match.find("div", class_="match-card__team--home").find("span", class_="match-card__team-name--full").text.strip()
                    away_team = match.find("div", class_="match-card__team--away").find("span", class_="match-card__team-name--full").text.strip()
                    match_time = match.find("span", class_="match-card__kickoff-time").text.strip()

                    team_data.append({
                        "date": match_date,
                        "time": match_time,
                        "home_team": home_team,
                        "away_team": away_team,
                        "matchweek": matchweek
                    })
                except AttributeError:
                    print("Match parsing failed. Skipping.")

# Quit browser once all scraping is done
driver.quit()

# Convert to DataFrame and combine
future_matches_df = pd.DataFrame(team_data)
future_matches_df = pd.concat([matchweek_one_df, future_matches_df], ignore_index=True)

# Save to CSV
future_matches_df.to_csv("future_matches_2025.csv", index=False)
print(f"✅ Saved {len(future_matches_df)} matches to future_matches_2025.csv")
