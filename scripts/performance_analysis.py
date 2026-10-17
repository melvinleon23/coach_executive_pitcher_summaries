# PURPOSE:
# 1. Select four CMJ performance indicators.
# 2. Compare each indicator with game-average FB velocity.
# 3. Analyze Pitcher A and Pitcher B separately.
# 4. Calculate exploratory Pearson correlations.
# 5. Generate scatterplots and seasonal trend charts.
# 6. Save results in dedicated tables and chart folders.
#
# IMPORTANT:
# Correlations describe associations, not causation.
# Repeated use of a CMJ assessment across games can affect the independence of observations.
# ------------------------------------------------------------
# SECTION 1 — IMPORT REQUIRED LIBRARIES
# ------------------------------------------------------------

from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# pathlib: manages folder and file paths.
# pandas: organizes and analyzes tabular data.
# numpy: performs numerical calculations.
# matplotlib: creates figures and saves charts.


# ------------------------------------------------------------
# SECTION 2 — DEFINE FILE AND OUTPUT LOCATIONS
# ------------------------------------------------------------

# Find the project directory by moving up one level
# from the scripts folder.

PROJECT_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    PROJECT_DIR
    / "outputs"
    / "tables"
    / "cmj_pitch_velocity_matched.csv"
)

# Keep performance tables and charts in separate folders.

TABLE_DIR = PROJECT_DIR / "outputs" / "tables" / "performance"
CHART_DIR = PROJECT_DIR / "outputs" / "charts" / "performance"

SCATTER_DIR = CHART_DIR / "scatterplots"
TREND_DIR = CHART_DIR / "seasonal_trends"

# Create folders automatically if necessary.

for folder in [TABLE_DIR, SCATTER_DIR, TREND_DIR]:
    folder.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# SECTION 3 — DEFINE OUR FOUR PERFORMANCE INDICATORS
# ------------------------------------------------------------

# These are the exact metric names in the original VALD CSV.
#
# We are treating them as summary performance indicators,
# while recognizing that each reflects underlying
# mechanical characteristics of the jump.

PERFORMANCE_METRICS = {
    "Jump Height (Imp-Mom)": {
        "label": "Jump Height",
        "filename": "jump_height"
    },
    "RSI-modified (Imp-Mom)": {
        "label": "RSI-modified",
        "filename": "rsi_modified"
    },
    "Concentric Mean Power / BM": {
        "label": "Concentric Mean Power / BM",
        "filename": "concentric_mean_power_bm"
    },
    "Eccentric Mean Power / BM": {
        "label": "Eccentric Mean Power / BM",
        "filename": "eccentric_mean_power_bm"
    }
}

# Note:
# Eccentric Mean Power / BM is retained as the positive
# measurement exported by VALD. No sign conversion is made.


# ------------------------------------------------------------
# SECTION 4 — LOAD AND VALIDATE THE MATCHED DATA
# ------------------------------------------------------------

df = pd.read_csv(INPUT_FILE)

# Remove accidental whitespace from column headers.

df.columns = df.columns.str.strip()

# Convert date columns from text to datetime objects.

df["game_date"] = pd.to_datetime(df["game_date"])
df["jump_date"] = pd.to_datetime(df["jump_date"])

# Confirm that every required column exists.

required_columns = [
    "player",
    "game_date",
    "jump_date",
    "avg_fastball_velocity",
    "days_since_jump"
] + list(PERFORMANCE_METRICS.keys())

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    raise ValueError(
        "Required columns are missing:\n"
        + "\n".join(missing_columns)
    )

# Convert measurement columns to numeric values.
# Non-numeric entries become missing (NaN).

numeric_columns = [
    "avg_fastball_velocity",
    "days_since_jump"
] + list(PERFORMANCE_METRICS.keys())

for column in numeric_columns:
    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )

# Remove rows without an observed fastball velocity.

df = df.dropna(
    subset=["avg_fastball_velocity"]
).copy()

print("\nDATA LOADED SUCCESSFULLY")
print(f"Matched game observations: {len(df)}")
print(f"Pitchers: {df['player'].unique().tolist()}")


# ------------------------------------------------------------
# SECTION 5 — CHECK REPEATED CMJ-TO-GAME MATCHES
# ------------------------------------------------------------

# A pitcher might have one CMJ test followed by two games.
#
# In that situation, both games share the same jump measurement. We want to identify these repetitions.
#
# groupby() groups games by pitcher and jump date.
# transform("size") counts how many games use that test.

df["games_using_same_cmj"] = (
    df.groupby(["player", "jump_date"])["game_date"]
    .transform("size")
)

# Mark games that share a CMJ assessment.

df["reused_cmj_assessment"] = (
    df["games_using_same_cmj"] > 1
)

# Save the information for quality control.

matching_review = df[
    [
        "player",
        "jump_date",
        "game_date",
        "days_since_jump",
        "games_using_same_cmj",
        "reused_cmj_assessment"
    ]
].sort_values(["player", "jump_date", "game_date"])

matching_review.to_csv(
    TABLE_DIR / "repeated_cmj_matches.csv",
    index=False
)

print("\nREPEATED CMJ MATCHES")

print(
    df.groupby("player")["reused_cmj_assessment"]
    .agg(["sum", "count"])
)


# ------------------------------------------------------------
# SECTION 6 — CALCULATE PERFORMANCE CORRELATIONS
# ------------------------------------------------------------

# Pearson's r describes the direction and strength
# of a linear association between two variables.
#
# r ranges from -1 to +1.
#
# Positive r:
# Higher CMJ metric values tend to accompany higher average fastball velocities.
#
# Negative r:
# Higher CMJ metric values tend to accompany lower average fastball velocities.
#
# r near zero:
# Little evidence of a linear relationship.
#
# These are exploratory descriptive correlations.
# We are not treating each game as an independent
# CMJ measurement for statistical inference.

results = []

for player, player_data in df.groupby("player"):

    for metric, details in PERFORMANCE_METRICS.items():

        # Select only rows with valid values for both
        # the CMJ metric and fastball velocity.

        subset = player_data[
            [
                "jump_date",
                metric,
                "avg_fastball_velocity"
            ]
        ].dropna()

        n_games = len(subset)

        # Count unique CMJ dates used in the comparison.

        n_unique_cmj = subset["jump_date"].nunique()

        # Calculate correlation only when there are
        # enough observations and both variables vary.

        if (
            n_games >= 3
            and subset[metric].nunique() > 1
            and subset["avg_fastball_velocity"].nunique() > 1
        ):

            r = subset[metric].corr(
                subset["avg_fastball_velocity"],
                method="pearson"
            )

        else:
            r = np.nan

        results.append({
            "player": player,
            "performance_metric": metric,
            "matched_games": n_games,
            "unique_cmj_assessments": n_unique_cmj,
            "pearson_r": r
        })


# Convert our list of results into a DataFrame.

correlation_table = pd.DataFrame(results)

# Round the correlation values for readability.

correlation_table["pearson_r"] = (
    correlation_table["pearson_r"].round(3)
)

# Save results.

correlation_table.to_csv(
    TABLE_DIR / "performance_correlations.csv",
    index=False
)

print("\nPERFORMANCE CORRELATIONS")
print(correlation_table.to_string(index=False))


# ------------------------------------------------------------
# SECTION 7 — CREATE SCATTERPLOTS
# ------------------------------------------------------------

# Each dot represents one matched pitching game.
#
# X-axis: selected CMJ performance metric.
# Y-axis: game-average fastball velocity.
#
# A fitted line summarizes the linear trend.
# It does not establish a causal relationship.

for player, player_data in df.groupby("player"):

    # Create a dedicated folder for each pitcher.

    player_folder = SCATTER_DIR / str(player)
    player_folder.mkdir(parents=True, exist_ok=True)

    for metric, details in PERFORMANCE_METRICS.items():

        subset = player_data[
            [metric, "avg_fastball_velocity"]
        ].dropna()

        if len(subset) < 3:
            continue

        x = subset[metric].to_numpy()
        y = subset["avg_fastball_velocity"].to_numpy()

        fig, ax = plt.subplots(figsize=(8, 5))

        # Plot observed game-level measurements.

        ax.scatter(
            x,
            y,
            alpha=0.75,
            s=55
        )

        # Add a fitted line when the CMJ metric varies.

        if np.unique(x).size > 1:

            slope, intercept = np.polyfit(x, y, 1)

            x_line = np.linspace(
                x.min(),
                x.max(),
                100
            )

            y_line = slope * x_line + intercept

            ax.plot(
                x_line,
                y_line,
                linewidth=2
            )

            r = np.corrcoef(x, y)[0, 1]

        else:
            r = np.nan

        # Label the chart clearly.

        ax.set_title(
            f"{player}: {details['label']} vs FB Velocity"
        )

        ax.set_xlabel(details["label"])
        ax.set_ylabel("Game-Average Fastball Velocity (mph)")

        # Display correlation and sample size.

        ax.text(
            0.03,
            0.97,
            f"Pearson r = {r:.3f}\nMatched games = {len(subset)}",
            transform=ax.transAxes,
            verticalalignment="top",
            bbox={
                "facecolor": "white",
                "alpha": 0.85,
                "edgecolor": "gray"
            }
        )

        ax.grid(alpha=0.25)

        fig.tight_layout()

        # Save the figure as a PNG.

        output_file = (
            player_folder
            / f"{details['filename']}_vs_velocity.png"
        )

        fig.savefig(
            output_file,
            dpi=200,
            bbox_inches="tight"
        )

        # Close the figure to release memory.

        plt.close(fig)


# ------------------------------------------------------------
# SECTION 8 — CREATE SEASONAL TREND CHARTS
# ------------------------------------------------------------

# These charts show how each CMJ performance indicator changes over the season.
#
# Plot each unique CMJ assessment once, rather than repeating it for every game matched to that assessment.
#
# These charts help us examine whether seasonal changes might influence the observed correlations.

for player, player_data in df.groupby("player"):

    player_folder = TREND_DIR / str(player)
    player_folder.mkdir(parents=True, exist_ok=True)

    for metric, details in PERFORMANCE_METRICS.items():

        # Retain one record per CMJ testing date.

        subset = (
            player_data[
                ["jump_date", metric]
            ]
            .dropna()
            .drop_duplicates(subset=["jump_date"])
            .sort_values("jump_date")
        )

        if subset.empty:
            continue

        fig, ax = plt.subplots(figsize=(9, 4.5))

        ax.plot(
            subset["jump_date"],
            subset[metric],
            marker="o",
            linewidth=1.8
        )

        ax.set_title(
            f"{player}: Seasonal {details['label']}"
        )

        ax.set_xlabel("CMJ Assessment Date")
        ax.set_ylabel(details["label"])

        ax.grid(alpha=0.25)

        fig.autofmt_xdate()
        fig.tight_layout()

        output_file = (
            player_folder
            / f"{details['filename']}_seasonal_trend.png"
        )

        fig.savefig(
            output_file,
            dpi=200,
            bbox_inches="tight"
        )

        plt.close(fig)


# ------------------------------------------------------------
# SECTION 9 — SAVE PERFORMANCE ANALYSIS DATA
# ------------------------------------------------------------

# Export a smaller dataset containing the variables
# needed for our performance dashboard.
#
# This keeps the future HTML report focused and avoids
# importing all 100+ CMJ metrics unnecessarily.

dashboard_columns = [
    "player",
    "game_date",
    "jump_date",
    "days_since_jump",
    "avg_fastball_velocity",
    "games_using_same_cmj"
] + list(PERFORMANCE_METRICS.keys())

performance_data = df[dashboard_columns].copy()

performance_data.to_csv(
    TABLE_DIR / "performance_dashboard_data.csv",
    index=False
)


# ------------------------------------------------------------
# SECTION 10 — FINAL EXECUTION SUMMARY
# ------------------------------------------------------------

print("\n========================================")
print("PERFORMANCE ANALYSIS COMPLETE")
print("========================================")

print("\nMetrics analyzed:")
for metric in PERFORMANCE_METRICS:
    print(f" - {metric}")

print(f"\nTables saved to:\n{TABLE_DIR}")
print(f"\nScatterplots saved to:\n{SCATTER_DIR}")
print(f"\nSeasonal trends saved to:\n{TREND_DIR}")

print("\nNOTE:")
print(
    "Correlations are exploratory and may be affected "
    "by repeated CMJ matches and seasonal trends."
)
