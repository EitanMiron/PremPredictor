import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score

# Load the dataset
matches = pd.read_csv('matches_data.csv')

# Convert date column to datetime
matches["date"] = pd.to_datetime(matches["date"], format="%Y-%m-%d")

# Feature engineering
matches["venue_code"] = matches["venue"].astype("category").cat.codes
matches["opp_code"] = matches["opponent"].astype("category").cat.codes
matches["hour"] = matches["time"].str.split(":").str[0].astype("int")
matches["day_code"] = matches["date"].dt.dayofweek
matches["objective"] = (matches["result"] == "W").astype("int")

# Define predictors
predictors = ["venue_code", "opp_code", "hour", "day_code"]

# Initial Random Forest model
random_forest = RandomForestClassifier(n_estimators=70, min_samples_split=20, random_state=1)
train = matches[matches["date"] < '2025-01-01']
test = matches[matches["date"] > '2025-01-01']
random_forest.fit(train[predictors], train["objective"])
get_predictions = random_forest.predict(test[predictors])
accuracy = accuracy_score(test["objective"], get_predictions)
merged_df = pd.DataFrame(dict(actual=test["objective"], prediction=get_predictions))

# Define columns for rolling averages
cols = [
    "goals for", "goals against", "shots total", "shots on target",
    "average shot distance", "free kicks", "penalty kicks scored", "penalty kicks attempted"
]
new_cols = [f"{col}_rolling" for col in cols]

# Function to calculate rolling averages
def rolling_averages(group, cols, new_cols):
    group = group.sort_values("date")
    rolling_stats = group[cols].rolling(3, closed='left').mean()
    group[new_cols] = rolling_stats
    group = group.dropna(subset=new_cols)
    return group

# Apply rolling averages to each team group
fixtures_rolling = matches.groupby("team", group_keys=False).apply(
    lambda x: rolling_averages(x, cols, new_cols)
).reset_index(drop=True)

# Function to train and evaluate the model
def make_predictions(data, predictors):
    train = data[data["date"] < '2025-01-01']
    test = data[data["date"] > '2025-01-01']
    random_forest.fit(train[predictors], train["objective"])
    get_predictions = random_forest.predict(test[predictors])
    merged_df = pd.DataFrame(dict(actual=test["objective"], prediction=get_predictions), index=test.index)
    score = precision_score(test["objective"], get_predictions)
    return merged_df, score

# Train and evaluate using the enhanced features
merged_df, score = make_predictions(fixtures_rolling, predictors + new_cols)

# Output precision score
#print(score)

#print(merged_df)

merged_df = merged_df.merge(fixtures_rolling[["date", "team", "opponent", "result"]], left_index=True, right_index=True)

#print(merged_df) 
#print(merged_df.head(10))

#create a class for mapping team names to handle inconsistencies
class Missing(dict):
    __missing__ = lambda self, key: key

#map names that are sometimes inconsistent
# e.g. Brighton and Hove Albion vs Brighton
map_values = {
    "Brighton and Hove Albion": "Brighton",
    "Manchester United": "Manchester Utd",
    "Newcastle United": "Newcastle",
    "Tottenham Hotspur": "Tottenham",
    "West Ham United": "West Ham",
    "Wolverhampton Wanderers": "Wolves",

}

mapping = Missing(**map_values)

#print(mapping["Brighton and Hove Albion"])  # Output: Brighton


merged_df["new_team"] = merged_df["team"].map(mapping)

#merging the dataframes on date and new_team a.k.a merging the dataframe with itself(merging team with opponent)
merged = merged_df.merge(merged_df, left_on=["date", "new_team"], right_on=["date", "opponent"])

#print(merged)

#look at rows where one team was predicted to win and the other team was predicted to lose
#print(merged[(merged["prediction_x"] == 1) & (merged["prediction_y"] == 0)]["actual_x"].value_counts())

print(merged)