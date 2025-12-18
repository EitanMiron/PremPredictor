# scrape current season's fixtures and team data from fbref
# This script scrapes the 2025-2026 Premier League season data from fbref
# The format matches matches_data.csv

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

# Set up Chrome driver
# Note: Running in non-headless mode to avoid Cloudflare bot protection
options = Options()
# Uncomment the next line if you want headless mode (may trigger Cloudflare protection):
# options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("window-size=1920,1080")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

# Define base URL - this will default to the current season (2025-2026)
base_url = "https://fbref.com/en/comps/9/Premier-League-Stats"
standings_url = base_url

season_year = 2025  # 2025-2026 season
all_teams_data = []

print(f"Scraping data for the {season_year} season from fbref...")

# Open season standings with Selenium
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.set_page_load_timeout(90)
try:
    driver.get(standings_url)
except TimeoutException:
    print("Page load timed out, but continuing...")
    driver.execute_script("window.stop();")
except InvalidSessionIdException:
    print("❌ Browser session lost (browser closed or crashed). Exiting...")
    exit(1)
except WebDriverException as e:
    print(f"WebDriverException encountered: {e}")
    print("Attempting to proceed as the page might have redirected...")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    print("Attempting to proceed...")

# Give user time to complete Cloudflare challenge manually
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
    page_source = driver.page_source
except NoSuchWindowException:
    print("❌ Browser window closed. Exiting...")
    exit(1)
except InvalidSessionIdException:
    print("❌ Browser session lost. Exiting...")
    exit(1)
except Exception as e:
    print(f"❌ Error getting page source: {e}")
    exit(1)

# driver.quit()

soup = BeautifulSoup(page_source, "html.parser")

# Debug: Check what tables exist on the page
all_tables = soup.find_all("table")
print(f"Found {len(all_tables)} tables on the page")
if len(all_tables) > 0:
    print("Table classes/ids found:")
    for i, table in enumerate(all_tables[:5]):  # Show first 5
        print(f"  Table {i+1}: class='{table.get('class')}', id='{table.get('id')}'")

# Try multiple selectors to find the standings table
standings_table = soup.select_one('table.stats_table')
if standings_table is None:
    # Try alternative selectors (class_ can be a string or list)
    standings_table = soup.find("table", class_=lambda x: x and "stats_table" in x)
if standings_table is None:
    # Try finding by id pattern (like in scrape_prev.py line 31)
    # Current season table typically has id like "results2025-202691_overall"
    for table in soup.find_all("table", id=True):
        table_id = table.get("id", "")
        if "results" in table_id and "overall" in table_id:
            standings_table = table
            print(f"Found table by ID pattern: {table_id}")
            break

if standings_table is None:
    print("Could not find standings table with any method.")
    print("Saving page source for debugging...")
    with open("debug_page.html", "w", encoding="utf-8") as f:
        f.write(page_source)
    print("Page source saved to debug_page.html")
    driver.quit()
    exit(1)

links = [l.get("href") for l in standings_table.find_all('a', href=True)]
team_urls = [f"https://fbref.com{l}" for l in links if '/squads/' in l]

print(f"Found {len(team_urls)} teams to scrape.")

for team_url in team_urls:
    team_name = team_url.split("/")[-1].replace("-Stats", "").replace("-", " ")  # cleans the team name from the team URL
    print(f"Scraping data for {team_name}...")
    
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
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        print("Attempting to proceed...")
    
    try:
        team_soup = BeautifulSoup(driver.page_source, "html.parser")
    except Exception as e:
        print(f"Error getting page source: {e}")
        continue
    # driver.quit()
    
    fixtures_table = team_soup.find("table", id="matchlogs_for")
    if not fixtures_table:
        print(f"  No fixtures table found for {team_name}. Skipping.")
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
        print(f"  No shooting link found for {team_name}. Skipping.")
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
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        print("Attempting to proceed...")
    
    try:
        shooting_soup = BeautifulSoup(driver.page_source, "html.parser")
    except Exception as e:
        print(f"Error getting page source: {e}")
        continue
    # driver.quit()
    
    shooting_table = shooting_soup.find("table", id="matchlogs_for")
    if not shooting_table:
        print(f"  No shooting table found for {team_name}. Skipping.")
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
    
    # Merge with accounting for teams that shooting data is not available as this would give a ValueError 
    try:
        team_df = fixtures_df.merge(shooting_df, on="Date")
    except Exception as e:
        print(f"  Merge failed for {team_name}: {e}. Skipping.")
        continue
    
    # Filter out other competitions than Premier League
    team_df = team_df[team_df["Competition"] == "Premier League"]
    
    # Add season and team name columns to distinguish data for which season and team the data is for
    team_df["Season"] = season_year
    team_df["Team"] = team_name
    
    all_teams_data.append(team_df)
    print(f"  Successfully scraped {len(team_df)} matches for {team_name}.")
    time.sleep(2)  # Be respectful to the server

print(f"Collected data for {len(all_teams_data)} teams.")

# Combine all teams data into a single DataFrame
if all_teams_data:
    combined_df = pd.concat(all_teams_data, ignore_index=True)
    combined_df.columns = [c.lower() for c in combined_df.columns]
    
    # Save the DataFrame to a CSV file
    combined_df.to_csv("future_matches_2025.csv", index=False)
    print(f"✅ Saved {len(combined_df)} matches to future_matches_2025.csv")
else:
    print("❌ No data was collected.")
driver.quit()
