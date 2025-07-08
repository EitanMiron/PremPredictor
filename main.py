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
url = "https://fbref.com/en/comps/9/Premier-League-Stats"
driver.get(url)
# Wait for the page to load
time.sleep(5)  # Adjust the sleep time as necessary

soup = BeautifulSoup(driver.page_source, "html.parser")
driver.quit()

# tables = soup.find_all("table")
# print(f"Found {len(tables)} tables")
# for table in tables:
#     print(table.get("id"))


current_table = soup.find("table", id="results2024-202591_overall")
#print(current_table)

#Extract the data from the table
current_table_data = []
for row in current_table.tbody.find_all("tr"):
    cols = row.find_all("td")
    if cols:
        current_table_data.append({
            "Position":row.find("th").text.strip(),
            "Team": cols[0].text.strip(),
            "Played": cols[1].text.strip(),
            "Won": cols[2].text.strip(),
            "Drawn": cols[3].text.strip(),
            "Lost": cols[4].text.strip(),
            "Goals For": cols[5].text.strip(),
            "Goals Against": cols[6].text.strip(),
            "Goal Difference": cols[7].text.strip(),
            "Points": cols[8].text.strip(),
            "Pts/MP": cols[9].text.strip(),
            "Expected Goals For": cols[10].text.strip(),
            "Expected Goals Against": cols[11].text.strip(),
            "Expected Goal Difference": cols[12].text.strip(),
            "Expected GD/90": cols[13].text.strip(),
            "Attendance": cols[14].text.strip(),
            "Top Goalscorer": cols[15].text.strip(),
            "Goalkeeper": cols[16].text.strip(),
            "Notes": cols[17].text.strip(),
        })

#print(current_table_data)
# Extract team URLs from the table
team_urls = []

links = current_table.find_all("a", href=True)
for link in links:
    href = link.get("href")
    if href.startswith("/en/squads/"):
        full_url = "https://fbref.com" + href
        if full_url not in team_urls:  # optional: avoid duplicates
            team_urls.append(full_url)
            
#print(team_urls) 
# Print or use the list
#print("Team URLs found:")
# for url in team_urls:
#     print(url)

# Use Selenium instead of requests for the team URL
team_url = team_urls[0]  # Example: using the first team URL
#print(team_url)

# Open team page with Selenium
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get(team_url)
team_soup = BeautifulSoup(driver.page_source, "html.parser")
driver.quit()

# Now look for the fixtures table by ID  'matchlogs_for'
fixtures_table = team_soup.find("table", id="matchlogs_for")
#print(fixtures_table)
#Iterate through the rows of the fixtures table and create a pandas DataFrame
fixtures_data = []
for row in fixtures_table.tbody.find_all("tr"):
    cols = row.find_all("td")
    if cols:
        fixtures_data.append({
            "Date": row.find("th").text.strip(),
            "Time": cols[0].text.strip(),
            "Competition": cols[1].text.strip(),
            "Round": cols[2].text.strip(),
            "Day": cols[3].text.strip(),
            "Venue": cols[4].text.strip(),
            "Result": cols[5].text.strip(),
            "Goals For": cols[6].text.strip(),
            "Goals Against": cols[7].text.strip(),
            "Opponent": cols[8].text.strip(),
            "Expected Goals For": cols[9].text.strip(),
            "Expected Goals Against": cols[10].text.strip(),
            "Possession": cols[11].text.strip(),
            "Attendance": cols[12].text.strip(),
            "Captain": cols[13].text.strip(),
            "Formation": cols[14].text.strip(),
            "Opp Formation": cols[15].text.strip(),
            "Referee": cols[16].text.strip(),
            "Match Report": cols[17].text.strip(),
            "Notes": cols[18].text.strip(),
            
        })

# Create a DataFrame from the fixtures data
fixtures_df = pd.DataFrame(fixtures_data)
# Print the DataFrame
#print(fixtures_df)
#print(fixtures_df[0])




# soup = BeautifulSoup(data.text)
# links = soup.find_all("a")
# links = [link.get("href") for link in links]
# links = [link for link in links if link and 'all_comps/shooting' in link]
# #print(links)


#Extract the shooting stats

# # Use Selenium to get the shooting stats table
shooting_url = "https://fbref.com/en/squads/822bd0ba/2024-2025/matchlogs/all_comps/shooting/Liverpool-Match-Logs-All-Competitions"
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get(shooting_url)
team_soup = BeautifulSoup(driver.page_source, "html.parser")
driver.quit()

# Now look for the shooting table by ID 'stats_shooting_9'
# This ID may vary, so ensure it matches the actual table ID on the page

shooting_table = team_soup.find("table", id="matchlogs_for")

#print(shooting_table)

#extract the data from the shooting table
shooting_data = []
for row in shooting_table.tbody.find_all("tr"):
    cols = row.find_all("td")
    if cols:
        shooting_data.append({
            "Date": row.find("th").text.strip(),
            "Time": cols[0].text.strip(),
            "Competition": cols[1].text.strip(),
            "Round": cols[2].text.strip(),
            "Day": cols[3].text.strip(),
            "Venue": cols[4].text.strip(),
            "Result": cols[5].text.strip(),
            "Goals For": cols[6].text.strip(),
            "Goals Against": cols[7].text.strip(),
            "Opponent": cols[8].text.strip(),
            "Goals Scored": cols[9].text.strip(),
            "Shots Total": cols[10].text.strip(),
            "Shots on Target": cols[11].text.strip(),
            "Shots on Target %": cols[12].text.strip(),
            "Goals/Shot": cols[13].text.strip(),
            "Goals/Shots on Target": cols[14].text.strip(),
            "Average Shot Distance": cols[15].text.strip(),
            "Free Kicks": cols[16].text.strip(),
            "Penalty Kicks Scored": cols[17].text.strip(),
            "Penalty Kicks Attempted": cols[18].text.strip(),
            "Expected Goals": cols[19].text.strip(),
            "Non-Penalty Expected Goals": cols[20].text.strip(),
            "Non-Penalty Expected Goals/Shot": cols[21].text.strip(),
            "Goals minus Expected Goals": cols[22].text.strip(),
            "Non-Penalty Goals minus Non-Penalty Expected Goals": cols[23].text.strip(),
            "Match Report": cols[24].text.strip(),
        })
 
shooting_df = pd.DataFrame(shooting_data)

# Print the DataFrame
#print(shooting_df)

merged_df = pd.merge(
    fixtures_df,
    shooting_df[
        ["Date", "Shots Total", "Shots on Target", "Average Shot Distance", 
         "Free Kicks", "Penalty Kicks Scored", "Penalty Kicks Attempted"]
    ],
    on="Date"
)
#print(merged_df.head)


#now create a loop to scrape multiple seasons
years = list(range(2025, 2022, -1))

all_seasons_data = []

# Define base URL
base_url = "https://fbref.com/en/comps/9/Premier-League-Stats"
standings_url = base_url

all_seasons_data = []

for year in years:
    print(f"Scraping data for the {year} season...")
    
    # Open season standings with Selenium
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(standings_url)
    time.sleep(5)
    
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()
    
    # Get team URLs
    standings_table = soup.select_one('table.stats_table')
    if standings_table is None:
        print("Could not find standings table.")
        continue
    
    links = [l.get("href") for l in standings_table.find_all('a', href=True)]
    team_urls = [f"https://fbref.com{l}" for l in links if '/squads/' in l]
    
    # Get previous season link
    prev_link = soup.select_one("a.prev")
    if prev_link:
        standings_url = f"https://fbref.com{prev_link.get('href')}"
    
    for team_url in team_urls:
        team_name = team_url.split("/")[-1].replace("-Stats", "").replace("-", " ")
        
        # Scrape fixtures using Selenium
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(team_url)
        team_soup = BeautifulSoup(driver.page_source, "html.parser")
        driver.quit()
        
        fixtures_table = team_soup.find("table", id="matchlogs_for")
        if not fixtures_table:
            continue
        
        fixtures_data = []
        for row in fixtures_table.tbody.find_all("tr"):
            cols = row.find_all("td")
            if cols:
                fixtures_data.append({
                    "Date": row.find("th").text.strip(),
                    "Time": cols[0].text.strip(),
                    "Competition": cols[1].text.strip(),
                    "Round": cols[2].text.strip(),
                    "Day": cols[3].text.strip(),
                    "Venue": cols[4].text.strip(),
                    "Result": cols[5].text.strip(),
                    "Goals For": cols[6].text.strip(),
                    "Goals Against": cols[7].text.strip(),
                    "Opponent": cols[8].text.strip(),
                })
        
        fixtures_df = pd.DataFrame(fixtures_data)
        
        # Find shooting link
        shooting_link = next((f"https://fbref.com{l.get('href')}" for l in team_soup.find_all("a", href=True)
                              if 'all_comps/shooting/' in l.get('href')), None)
        if not shooting_link:
            continue
        
        # Scrape shooting data
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(shooting_link)
        shooting_soup = BeautifulSoup(driver.page_source, "html.parser")
        driver.quit()
        
        shooting_table = shooting_soup.find("table", id="matchlogs_for")
        if not shooting_table:
            continue
        
        shooting_data = []
        for row in shooting_table.tbody.find_all("tr"):
            cols = row.find_all("td")
            if cols:
                shooting_data.append({
                    "Date": row.find("th").text.strip(),
                    "Shots Total": cols[10].text.strip(),
                    "Shots on Target": cols[11].text.strip(),
                    "Average Shot Distance": cols[15].text.strip(),
                    "Free Kicks": cols[16].text.strip(),
                    "Penalty Kicks Scored": cols[17].text.strip(),
                    "Penalty Kicks Attempted": cols[18].text.strip(),
                })
        
        shooting_df = pd.DataFrame(shooting_data)
        
        # Merge
        try:
            team_df = fixtures_df.merge(shooting_df, on="Date")
        except Exception as e:
            print(f"Merge failed for {team_name}: {e}")
            continue
        
        team_df["Season"] = year
        team_df["Team"] = team_name
        all_seasons_data.append(team_df)
        time.sleep(3)

print(f"Collected data for {len(all_seasons_data)} team-seasons.")

team_df = pd.concat(all_seasons_data)
team_df.columns = [c.lower() for c in team_df.columns]
print(team_df)
team_df.to_csv("matches_data.csv", index=False)
#------------------------------------------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------------------------------

