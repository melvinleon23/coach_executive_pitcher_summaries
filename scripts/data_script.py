# PURPOSE:
# Connect each pitcher's CMJ assessment with their game-level
# fastball velocity.
#
# OUTPUT:
# A CSV table containing one row per matched pitching game.
# ------------------------------------------------------------
# SECTION 1 — IMPORT LIBRARIES
# ------------------------------------------------------------

from pathlib import Path
import pandas as pd

# Path: allows us to locate files and folders without hardcoding a specific drive letter.
#
# pandas: allows us to load, organize, filter, and combine tabular datasets.

# ------------------------------------------------------------
# SECTION 2 — DEFINE PROJECT PATHS
# ------------------------------------------------------------

# __file__ is the location of this Python script.
# .resolve() gets its complete file path.
# .parent.parent moves up two levels to the project folder.

PROJECT_DIR = Path(__file__).resolve().parent.parent

RAW_DIR = PROJECT_DIR / "data" / "raw"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
TABLES_DIR = PROJECT_DIR / "outputs" / "tables"

# Create output folders if they don't already exist.
# parents=True creates any missing parent folders.
# exist_ok=True prevents errors if a folder already exists.

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
TABLES_DIR.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# SECTION 3 — LOAD THE ORIGINAL DATASETS
# ------------------------------------------------------------

jump_data = pd.read_csv(RAW_DIR / "jumpdata.csv")
pitch_data = pd.read_csv(RAW_DIR / "pitchdata.csv")

# Display the dimensions of each dataset.
# shape[0] = number of rows.
# shape[1] = number of columns.

print("\nJUMP DATASET:")
print(jump_data.shape)
print(jump_data.columns.tolist())

print("\nPITCH DATASET:")
print(pitch_data.shape)
print(pitch_data.columns.tolist())

# ------------------------------------------------------------
# SECTION 4 — IDENTIFY IMPORTANT COLUMNS
# ------------------------------------------------------------

# These column names come directly from the two CSV files.
#
# JUMP DATA:
# name    = CMJ measurement name
# unit    = measurement unit
# Date    = assessment date
# Value   = recorded measurement
# Pitcher = athlete identifier
#
# PITCH DATA:
# GameDate     = date of pitching appearance
# PitchType    = pitch classification
# ReleaseSpeed = recorded pitch velocity
# Pitcher      = athlete identifier


# Jump dataset columns

jump_player_col = "Pitcher"
jump_date_col = "Date"
jump_metric_col = "name"
jump_value_col = "Value"


# Pitch dataset columns

pitch_player_col = "Pitcher"
pitch_date_col = "GameDate"
pitch_type_col = "PitchType"
pitch_velocity_col = "ReleaseSpeed"


# Confirm that the required columns exist before proceeding.

required_jump_columns = [
    jump_player_col,
    jump_date_col,
    jump_metric_col,
    jump_value_col
]

required_pitch_columns = [
    pitch_player_col,
    pitch_date_col,
    pitch_type_col,
    pitch_velocity_col
]

# Check for missing columns using set differences.

missing_jump = set(required_jump_columns) - set(jump_data.columns)
missing_pitch = set(required_pitch_columns) - set(pitch_data.columns)

if missing_jump:
    raise ValueError(f"Missing jump columns: {missing_jump}")

if missing_pitch:
    raise ValueError(f"Missing pitch columns: {missing_pitch}")

print("\nAll required dataset columns identified successfully.")

# ------------------------------------------------------------
# SECTION 5 — STANDARDIZE COLUMN NAMES AND DATES
# ------------------------------------------------------------

# rename() gives the important columns consistent names.
# pd.to_datetime() converts date strings into actual dates.

jump = jump_data.rename(columns={
    jump_player_col: "player",
    jump_date_col: "jump_date",
    jump_metric_col: "metric",
    jump_value_col: "value"
}).copy()

pitch = pitch_data.rename(columns={
    pitch_player_col: "player",
    pitch_date_col: "game_date",
    pitch_type_col: "pitch_type",
    pitch_velocity_col: "velocity"
}).copy()

jump["jump_date"] = pd.to_datetime(
    jump["jump_date"], errors="coerce"
).dt.normalize()

pitch["game_date"] = pd.to_datetime(
    pitch["game_date"], errors="coerce"
).dt.normalize()

# Convert numeric measurements to numbers.
# Invalid numeric values become NaN (missing).

jump["value"] = pd.to_numeric(
    jump["value"], errors="coerce"
)

pitch["velocity"] = pd.to_numeric(
    pitch["velocity"], errors="coerce"
)

# Standardize player identifiers and pitch labels.

jump["player"] = jump["player"].astype(str).str.strip()
pitch["player"] = pitch["player"].astype(str).str.strip()

pitch["pitch_type"] = (
    pitch["pitch_type"].astype(str).str.strip().str.upper()
)
# CLEAN CMJ METRIC NAMES
# Remove accidental spaces at the beginning or end of metric names.
#
# This prevents the same measurement from appearing as two different columns in our pivot table.

jump["metric"] = jump["metric"].astype(str).str.strip()

# CHECK FOR DUPLICATE CMJ MEASUREMENTS

# A duplicate occurs when the same athlete has multiple values for the same metric on the same testing date.
#
# keep=False marks every occurrence in a duplicate group.

duplicate_mask = jump.duplicated(
    subset=["player", "jump_date", "metric"],
    keep=False
)

duplicate_measurements = jump[
    duplicate_mask
].sort_values(
    ["player", "jump_date", "metric"]
)

# Save duplicates for inspection before aggregating.

duplicate_measurements.to_csv(
    TABLES_DIR / "cmj_duplicate_measurements.csv",
    index=False
)

print("\nDUPLICATE CMJ MEASUREMENTS:")
print(duplicate_measurements.to_string(index=False))


# ------------------------------------------------------------
# SECTION 6 — ORGANIZE THE CMJ ASSESSMENTS
# ------------------------------------------------------------

# The jump dataset is in long format:
#
# Player | Date | Metric | Value
#
# Want wide format:
#
# Player | Date | Jump Height | Braking Force 
#
# pivot_table() turns metric names into separate columns.
# aggfunc="mean" handles duplicate measurements for the same athlete, date, and metric.
# Identify the measurement unit associated with each metric.
# drop_duplicates() removes repeated metric/unit combinations.

metric_units = (
    jump_data[["name", "unit"]]
    .drop_duplicates()
    .sort_values("name")
)

# Save the measurement reference table.

metric_units.to_csv(
    PROCESSED_DIR / "cmj_metric_units.csv",
    index=False
)

print("\nCMJ measurement units saved.")

jump_wide = jump.pivot_table(
    index=["player", "jump_date"],
    columns="metric",
    values="value",
    aggfunc="mean"
).reset_index()

# Remove the pivot-generated column index name.

jump_wide.columns.name = None

# Save the organized jump assessments.

jump_wide.to_csv(
    PROCESSED_DIR / "cmj_assessments.csv",
    index=False
)
# ASSESS CMJ METRIC COMPLETENESS
# Count how many athlete-date assessments have a recorded value for each CMJ metric.
#
# notna() returns True for available measurements.
# sum() counts those True values.
#
# This helps identify metrics with insufficient data for meaningful correlation analysis.

metric_coverage = (
    jump_wide
    .drop(columns=["player", "jump_date"])
    .notna()
    .sum()
    .reset_index()
)

metric_coverage.columns = [
    "metric",
    "available_assessments"
]

# Calculate the percentage of assessments containing each measurement.

total_assessments = len(jump_wide)

metric_coverage["coverage_percent"] = (
    metric_coverage["available_assessments"]
    / total_assessments
    * 100
)

# Sort from least complete to most complete.

metric_coverage = metric_coverage.sort_values(
    "coverage_percent"
)

metric_coverage.to_csv(
    TABLES_DIR / "cmj_metric_coverage.csv",
    index=False
)

print("\nCMJ METRIC COVERAGE:")
print(metric_coverage.head(15).to_string(index=False))


# ------------------------------------------------------------
# SECTION 7 — CALCULATE GAME-LEVEL FASTBALL VELOCITY
# ------------------------------------------------------------

# FB = fastball.
# Exclude other pitch types from this initial analysis
# so that pitch-type differences don't distort the results.

fastballs = pitch[
    pitch["pitch_type"] == "FB"
].copy()

# groupby() groups all fastballs for the same player/date.
#
# mean() = average velocity across those fastballs.
# max() = highest recorded velocity.
# count() = number of fastballs recorded.

game_velocity = (
    fastballs
    .groupby(["player", "game_date"])
    .agg(
        avg_fastball_velocity=("velocity", "mean"),
        peak_fastball_velocity=("velocity", "max"),
        fastball_count=("velocity", "count")
    )
    .reset_index()
)

game_velocity.to_csv(
    PROCESSED_DIR / "game_fastball_velocity.csv",
    index=False
)


# ------------------------------------------------------------
# SECTION 8 — MATCH CMJ ASSESSMENTS TO PITCHING GAMES
# ------------------------------------------------------------

# Use the most recent CMJ assessment on or before a game.
#
# merge_asof() matches records based on their dates.
#
# direction="backward" prevents using a future CMJ test to explain an earlier pitching performance.
#
# tolerance=7 days restricts the maximum time gap.
#
# by="player" ensures pitchers are matched only to their own jump assessments.

game_velocity = game_velocity.sort_values(
    ["game_date", "player"]
)

jump_wide = jump_wide.sort_values(
    ["jump_date", "player"]
)

matched = pd.merge_asof(
    game_velocity,
    jump_wide,
    left_on="game_date",
    right_on="jump_date",
    by="player",
    direction="backward",
    tolerance=pd.Timedelta(days=7)
)

# Calculate the number of days between testing and pitching.

matched["days_since_jump"] = (
    matched["game_date"] - matched["jump_date"]
).dt.days


# ------------------------------------------------------------
# SECTION 9 — QUALITY CONTROL
# ------------------------------------------------------------

# Check which games received a valid jump assessment.

matched["has_cmj_match"] = matched["jump_date"].notna()

print("\nMATCHING SUMMARY:")

print(
    matched.groupby("player")["has_cmj_match"]
    .agg(["count", "sum"])
)

# Remove games without a matching CMJ assessment.
# These games remain available in the original data.

analysis_table = matched[
    matched["has_cmj_match"]
].copy()


# ------------------------------------------------------------
# SECTION 10 — SAVE THE ANALYSIS TABLE
# ------------------------------------------------------------

analysis_table.to_csv(
    TABLES_DIR / "cmj_pitch_velocity_matched.csv",
    index=False
)

matched.to_csv(
    TABLES_DIR / "matching_quality_control.csv",
    index=False
)

print("\nAnalysis table successfully created!")
print(f"Matched observations: {len(analysis_table)}")
print(f"Saved to: {TABLES_DIR}")

print("\nFIRST FIVE ROWS:")
print(analysis_table.head().to_string(index=False))
