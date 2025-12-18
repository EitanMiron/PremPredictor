import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, classification_report

# Load the dataset
matches = pd.read_csv('matches_data.csv')

# Convert date column to datetime
matches["date"] = pd.to_datetime(matches["date"], format="%Y-%m-%d")

# Feature engineering
matches["venue_code"] = matches["venue"].astype("category").cat.codes
matches["opp_code"] = matches["opponent"].astype("category").cat.codes
matches["hour"] = matches["time"].str.split(":").str[0].astype("int")
matches["day_code"] = matches["date"].dt.dayofweek
# Target: 0=Loss, 1=Draw, 2=Win
target_map = {"L": 0, "D": 1, "W": 2}
matches["target"] = matches["result"].map(target_map)
# Points: 0=Loss, 1=Draw, 3=Win
points_map = {"L": 0, "D": 1, "W": 3}
matches["points"] = matches["result"].map(points_map)

# Define predictors
predictors = ["venue_code", "opp_code", "hour", "day_code"]

# Initial Random Forest model
random_forest = RandomForestClassifier(n_estimators=100, min_samples_split=10, random_state=1)
train = matches[matches["date"] < '2025-01-01']
test = matches[matches["date"] > '2025-01-01']
random_forest.fit(train[predictors], train["target"])
get_predictions = random_forest.predict(test[predictors])
accuracy = accuracy_score(test["target"], get_predictions)
merged_df = pd.DataFrame(dict(actual=test["target"], prediction=get_predictions))

# Define columns for rolling averages
cols = [
    "goals for", "goals against", "shots total", "shots on target",
    "average shot distance", "free kicks", "penalty kicks scored", "penalty kicks attempted",
    "points"
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
fixtures_rolling["new_team"] = fixtures_rolling["team"].map(mapping)

# Merge opponent rolling stats
opp_stats = fixtures_rolling[["date", "new_team"] + new_cols].copy()
opp_new_cols = [f"opp_{c}" for c in new_cols]
opp_stats.columns = ["date", "opponent"] + opp_new_cols

fixtures_rolling = fixtures_rolling.merge(opp_stats, on=["date", "opponent"], how="left")
# Drop rows where opponent stats are missing (e.g. if opponent name mapping failed or no history)
fixtures_rolling = fixtures_rolling.dropna()

# Function to train and evaluate the model
def make_predictions(data, predictors):
    train = data[data["date"] < '2025-01-01']
    test = data[data["date"] > '2025-01-01']
    random_forest.fit(train[predictors], train["target"])
    get_predictions = random_forest.predict(test[predictors])
    merged_df = pd.DataFrame(dict(actual=test["target"], prediction=get_predictions), index=test.index)
    precision = precision_score(test["target"], get_predictions, average='weighted', zero_division=0)
    accuracy = accuracy_score(test["target"], get_predictions)
    report = classification_report(test["target"], get_predictions, target_names=["Loss", "Draw", "Win"], zero_division=0)
    return merged_df, precision, accuracy, report

# Train and evaluate using the enhanced features
merged_df, precision, accuracy, report = make_predictions(fixtures_rolling, predictors + new_cols + opp_new_cols)

# Output scores
print(f"Model Accuracy: {accuracy:.2%}")
print(f"Model Precision (Weighted): {precision:.2%}")
print("\nClassification Report:")
print(report)

#print(merged_df)

merged_df = merged_df.merge(fixtures_rolling[["date", "team", "opponent", "result", "new_team"]], left_index=True, right_index=True)

#merging the dataframes on date and new_team a.k.a merging the dataframe with itself(merging team with opponent)
merged = merged_df.merge(merged_df, left_on=["date", "new_team"], right_on=["date", "opponent"])

#print(merged)

#look at rows where one team was predicted to win and the other team was predicted to lose
#print(merged[(merged["prediction_x"] == 1) & (merged["prediction_y"] == 0)]["actual_x"].value_counts())

print(merged)

# Save the merged dataframe to a CSV file
merged.to_csv("predictions.csv", index=False)
print("Predictions saved to predictions.csv")



