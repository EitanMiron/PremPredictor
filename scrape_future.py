#scrape next season's fixtures and team data

import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time

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

#get the matchweek date
#matchweek_date = soup.find("span", class_="match-list__day-date").text.strip()
#print(matchweek_date)

#get the match fixtures from the matchweek
matches = soup.find_all("div", class_="match-card__info")

for match in matches:
    try:
        home_team = match.find("div", class_="match-card__team--home").find("span", class_="match-card__team-name--full").text.strip()
        away_team = match.find("div", class_="match-card__team--away").find("span", class_="match-card__team-name--full").text.strip()
        match_time = match.find("span", class_="match-card__kickoff-time").text.strip()
        #matchweek_date = soup.find("span", class_="match-list__day-date").text.strip()

        #(f"Home: {home_team}, Away: {away_team}, Time: {match_time}, Date: {matchweek_date}")
    except AttributeError:
        # In case any part of the HTML isn't found
        print("Match parsing failed. Skipping.")
