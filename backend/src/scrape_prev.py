import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchWindowException, InvalidSessionIdException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time
import os

# Define paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')


options = Options()
# Running in non-headless mode to avoid Cloudflare bot protection
# Uncomment the next line if you want headless mode (may trigger Cloudflare protection):
# options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("window-size=1920,1080")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.set_page_load_timeout(90)
url = "https://fbref.com/en/comps/9/Premier-League-Stats"
try:
    driver.get(url)
except TimeoutException:
    print("Page load timed out, but continuing...")
    driver.execute_script("window.stop();")
except InvalidSessionIdException:
    print("❌ Browser session lost (browser closed or crashed). Exiting...")
    exit(1)
except WebDriverException as e:
    print(f"WebDriverException encountered: {e}")
    print("Attempting to proceed as the page might have redirected...")

# Give user time to complete Cloudflare challenge manually (only for initial load)
print("\n" + "="*60)
print("ATTENTION: If you see a Cloudflare challenge page,")
print("please complete the verification manually in the browser window.")
print("The script will wait for you to finish...")
print("="*60 + "\n")

# Wait for user to complete Cloudflare challenge - check every 2 seconds
# Up to 2 minutes (120 seconds) for manual verification
max_wait_time = 120
wait_interval = 2
elapsed_time = 0

print("Waiting for page to load and Cloudflare challenge to complete...")
while elapsed_time < max_wait_time:
    try:
        # Check if the page has loaded by looking for the table
        wait = WebDriverWait(driver, 2)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.stats_table")))
        print("✓ Page loaded successfully!")
        time.sleep(2)  # Extra wait to ensure everything is rendered
        break
    except NoSuchWindowException:
        print("❌ Browser window closed. Exiting...")
        exit(1)
    except InvalidSessionIdException:
        print("❌ Browser session lost. Exiting...")
        exit(1)
    except:
        elapsed_time += wait_interval
        if elapsed_time % 10 == 0:  # Print progress every 10 seconds
            print(f"Still waiting... ({elapsed_time}/{max_wait_time} seconds)")
        time.sleep(wait_interval)
else:
    print(f"\n⚠ Warning: Timeout after {max_wait_time} seconds.")
    print("The page may still be loading. Proceeding anyway...")

try:
    soup = BeautifulSoup(driver.page_source, "html.parser")
except NoSuchWindowException:
    print("❌ Browser window closed. Exiting...")
    exit(1)
except InvalidSessionIdException:
    print("❌ Browser session lost. Exiting...")
    exit(1)
except Exception as e:
    print(f"❌ Error getting page source: {e}")
    exit(1)

# driver.quit() # Keeping driver open

# tables = soup.find_all("table")
# print(f"Found {len(tables)} tables")
# for table in tables:
#     print(table.get("id"))


# Try to find the table - check if it exists before using it
current_table = soup.find("table", id="results2024-202591_overall")
if current_table is None:
    # Try alternative: find any table with stats_table class
    current_table = soup.select_one('table.stats_table')
    if current_table is None:
        print("ERROR: Could not find standings table. This may be due to Cloudflare blocking.")
        print("Please ensure the page loaded correctly or try running the script again.")
        driver.quit()
        exit(1)

#print(current_table)

#Extract the data from the table
current_table_data = []
if current_table.tbody is None:
    print("ERROR: Table found but has no tbody element.")
    driver.quit()
    exit(1)

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
# driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
try:
    driver.get(team_url)
except TimeoutException:
    print("Page load timed out, but continuing...")
    driver.execute_script("window.stop();")
except InvalidSessionIdException:
    print("❌ Browser session lost. Exiting...")
    exit(1)
except WebDriverException as e:
    print(f"WebDriverException encountered: {e}")
    print("Attempting to proceed...")

# Wait for team page to load
max_wait_time = 60
wait_interval = 2
elapsed_time = 0

while elapsed_time < max_wait_time:
    try:
        wait = WebDriverWait(driver, 2)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table#matchlogs_for")))
        break
    except:
        elapsed_time += wait_interval
        time.sleep(wait_interval)

team_soup = BeautifulSoup(driver.page_source, "html.parser")
# driver.quit()

# Now look for the fixtures table by ID  'matchlogs_for'
fixtures_table = team_soup.find("table", id="matchlogs_for")
if fixtures_table is None:
    print("ERROR: Could not find fixtures table (matchlogs_for) on team page.")
    print("This is a test section - the main scraping loop will handle this better.")
    driver.quit()
    exit(1)

if fixtures_table.tbody is None:
    print("ERROR: Fixtures table found but has no tbody element.")
    driver.quit()
    exit(1)

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
# driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
try:
    driver.get(shooting_url)
except TimeoutException:
    print("Page load timed out, but continuing...")
    driver.execute_script("window.stop();")
except InvalidSessionIdException:
    print("❌ Browser session lost. Exiting...")
    exit(1)
except WebDriverException as e:
    print(f"WebDriverException encountered: {e}")
    print("Attempting to proceed...")

# Wait for shooting page to load
max_wait_time = 60
wait_interval = 2
elapsed_time = 0

while elapsed_time < max_wait_time:
    try:
        wait = WebDriverWait(driver, 2)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table#matchlogs_for")))
        break
    except:
        elapsed_time += wait_interval
        time.sleep(wait_interval)

shooting_soup = BeautifulSoup(driver.page_source, "html.parser")
# driver.quit()

shooting_table = shooting_soup.find("table", id="matchlogs_for")

if shooting_table is None:
    print("ERROR: Could not find shooting table (matchlogs_for) on shooting page.")
    driver.quit()
    exit(1)

if shooting_table.tbody is None:
    print("ERROR: Shooting table found but has no tbody element.")
    driver.quit()
    exit(1)

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
years = list(range(2025, 2019, -1))

all_seasons_data = []

# Define base URL
base_url = "https://fbref.com/en/comps/9/Premier-League-Stats"
standings_url = base_url

all_seasons_data = []

for year in years:
    print(f"Scraping data for the {year} season...")
    
    # Open season standings with Selenium
    # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    try:
        driver.get(standings_url)
    except TimeoutException:
        print("Page load timed out, but continuing...")
        driver.execute_script("window.stop();")
    except InvalidSessionIdException:
        print("❌ Browser session lost. Exiting...")
        exit(1)
    except WebDriverException as e:
        print(f"WebDriverException encountered: {e}")
        print("Attempting to proceed...")
    
    # Wait for the page to load - give more time for Cloudflare challenges
    # Check every 2 seconds, up to 60 seconds for each page
    max_wait_time = 60
    wait_interval = 2
    elapsed_time = 0
    
    while elapsed_time < max_wait_time:
        try:
            wait = WebDriverWait(driver, 2)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.stats_table")))
            time.sleep(2)  # Extra wait to ensure everything is rendered
            break
        except:
            elapsed_time += wait_interval
            time.sleep(wait_interval)
    
    soup = BeautifulSoup(driver.page_source, "html.parser")
    # driver.quit()
    
    # Get team URLs
    standings_table = soup.select_one('table.stats_table')
    if standings_table is None:
        print(f"  Could not find standings table for {year} season. Skipping...")
        # Try to get previous season link anyway
        prev_link = soup.select_one("a.prev")
        if prev_link:
            standings_url = f"https://fbref.com{prev_link.get('href')}"
        continue
    
    links = [l.get("href") for l in standings_table.find_all('a', href=True)]
    team_urls = [f"https://fbref.com{l}" for l in links if '/squads/' in l]
    
    # Get previous season link
    prev_link = soup.select_one("a.prev")
    if prev_link:
        standings_url = f"https://fbref.com{prev_link.get('href')}"
    
    for team_url in team_urls:
        team_name = team_url.split("/")[-1].replace("-Stats", "").replace("-", " ") #cleans the team name from the team URL
        
        # Scrape fixtures using Selenium
        # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        try:
            driver.get(team_url)
        except TimeoutException:
            print("Page load timed out, but continuing...")
            driver.execute_script("window.stop();")
        except InvalidSessionIdException:
            print("❌ Browser session lost. Exiting...")
            exit(1)
        except WebDriverException as e:
            print(f"WebDriverException encountered: {e}")
            print("Attempting to proceed...")
        
        # Wait for team page to load
        max_wait_time_team = 60
        wait_interval_team = 2
        elapsed_time_team = 0
        
        while elapsed_time_team < max_wait_time_team:
            try:
                wait_team = WebDriverWait(driver, 2)
                wait_team.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table#matchlogs_for")))
                break
            except:
                elapsed_time_team += wait_interval_team
                time.sleep(wait_interval_team)
        
        team_soup = BeautifulSoup(driver.page_source, "html.parser")
        # driver.quit()
        
        fixtures_table = team_soup.find("table", id="matchlogs_for")
        if not fixtures_table:
            print(f"  No fixtures table found for {team_name}. Skipping.")
            continue
        
        if fixtures_table.tbody is None:
            print(f"  Fixtures table found but has no tbody for {team_name}. Skipping.")
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
        # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        try:
            driver.get(shooting_link)
        except TimeoutException:
            print("Page load timed out, but continuing...")
            driver.execute_script("window.stop();")
        except InvalidSessionIdException:
            print("❌ Browser session lost. Exiting...")
            exit(1)
        except WebDriverException as e:
            print(f"WebDriverException encountered: {e}")
            print("Attempting to proceed...")
        
        # Wait for shooting page to load
        max_wait_time_shooting = 60
        wait_interval_shooting = 2
        elapsed_time_shooting = 0
        
        while elapsed_time_shooting < max_wait_time_shooting:
            try:
                wait_shooting = WebDriverWait(driver, 2)
                wait_shooting.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table#matchlogs_for")))
                break
            except:
                elapsed_time_shooting += wait_interval_shooting
                time.sleep(wait_interval_shooting)
        
        shooting_soup = BeautifulSoup(driver.page_source, "html.parser")
        # driver.quit()
        
        shooting_table = shooting_soup.find("table", id="matchlogs_for")
        if not shooting_table:
            print(f"  No shooting table found for {team_name}. Skipping.")
            continue
        
        if shooting_table.tbody is None:
            print(f"  Shooting table found but has no tbody for {team_name}. Skipping.")
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
        
        # Merge with accounting for teams that shooting data is not avaible as this would give a ValueError 
        try:
            team_df = fixtures_df.merge(shooting_df, on="Date")
        except Exception as e:
            print(f"Merge failed for {team_name}: {e}")
            continue
        
        #Filter out other competitions than Premier League
        team_df = team_df[team_df["Competition"] == "Premier League"]
        
        # Add season and team name columns to distinguish data for which season and team the data is for
        team_df["Season"] = year
        team_df["Team"] = team_name
        
        all_seasons_data.append(team_df)
        time.sleep(3)

print(f"Collected data for {len(all_seasons_data)} team-seasons.")

#combine all seasons data into a single DataFrame
team_df = pd.concat(all_seasons_data)
team_df.columns = [c.lower() for c in team_df.columns]
#print(team_df)

# Save the DataFrame to a CSV file
team_df.to_csv(os.path.join(DATA_DIR, "matches_data.csv"), index=False)
driver.quit()
#------------------------------------------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------------------------------

