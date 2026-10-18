# DELIVERABLE 1:
#   Coach Report
#   - Compact data key
#   - Four combined scatterplots
#   - Complete seasonal overview
#   - Three coaching takeaways per pitcher
#
# DELIVERABLE 2:
#   Executive Summary
#   - Player comparison
#   - Key findings and take-home messages
#   - Notable differences
#   - Larger-scale organizational application
#   - Future data and considerations
#
# This script presents previously calculated results.
# It does not change the original correlation analysis.
# ================================================================

from pathlib import Path
from html import escape
import base64
import mimetypes

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio


# ------------------------------------------------------------
# 1. PROJECT PATHS
# ------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent

PROCESSED_DIR = ROOT / "data" / "processed"
PERFORMANCE_DIR = ROOT / "outputs" / "tables" / "performance"
REPORT_DIR = ROOT / "outputs" / "reports"

REPORT_DIR.mkdir(parents=True, exist_ok=True)

COACH_OUTPUT = REPORT_DIR / "coach_report.html"
EXEC_OUTPUT = REPORT_DIR / "executive_summary.html"

# Header logo: embedded in each HTML file so the reports remain
# self-contained when viewed locally, downloaded, or hosted on GitHub Pages.
LOGO_FILE = REPORT_DIR / "html accessories" / "logo.png"


def logo_data_uri():
    """Convert the PNG into an inline image for standalone HTML reports."""
    if not LOGO_FILE.is_file():
        raise FileNotFoundError(
            f"Header logo not found: {LOGO_FILE}\n"
            "Confirm the filename is logo.png and the folder is 'html accessories'."
        )
    encoded = base64.b64encode(LOGO_FILE.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"



# ------------------------------------------------------------
# 2. CONFIGURATION
# ------------------------------------------------------------

# Consistent pitcher colors across the reports.

COLORS = {
    "PitcherA": "#087f8c",
    "PitcherB": "#c87928"
}

PLAYERS = ["PitcherA", "PitcherB"]

# Four predetermined CMJ performance indicators.

METRICS = {
    "Jump Height (Imp-Mom)": {
        "label": "Jump Height",
        "unit": "cm"
    },
    "RSI-modified (Imp-Mom)": {
        "label": "RSI-modified",
        "unit": "m/s"
    },
    "Concentric Mean Power / BM": {
        "label": "Concentric Mean Power / BM",
        "unit": "W/kg"
    },
    "Eccentric Mean Power / BM": {
        "label": "Eccentric Mean Power / BM",
        "unit": "W/kg"
    }
}


# ------------------------------------------------------------
# 3. LOAD DATA
# ------------------------------------------------------------

# Complete seasonal data from data_script.py.

cmj_all = pd.read_csv(
    PROCESSED_DIR / "cmj_assessments.csv"
)

games_all = pd.read_csv(
    PROCESSED_DIR / "game_fastball_velocity.csv"
)

# Matched game-level data and correlations.

matched = pd.read_csv(
    PERFORMANCE_DIR / "performance_dashboard_data.csv"
)

correlations = pd.read_csv(
    PERFORMANCE_DIR / "performance_correlations.csv"
)


# ------------------------------------------------------------
# 4. STANDARDIZE COLUMNS
# ------------------------------------------------------------

def rename_column(df, target, alternatives):

    if target in df.columns:
        return df

    for alternative in alternatives:
        if alternative in df.columns:
            return df.rename(
                columns={alternative: target}
            )

    raise ValueError(
        f"Missing column: {target}. "
        f"Available: {list(df.columns)}"
    )


for frame in [cmj_all, games_all, matched, correlations]:
    frame.columns = frame.columns.str.strip()

cmj_all = rename_column(
    cmj_all, "player", ["Pitcher", "pitcher"]
)

cmj_all = rename_column(
    cmj_all, "jump_date", ["Date", "date"]
)

games_all = rename_column(
    games_all, "player", ["Pitcher", "pitcher"]
)

games_all = rename_column(
    games_all, "game_date", ["GameDate", "Date", "date"]
)

games_all = rename_column(
    games_all,
    "avg_fastball_velocity",
    ["avg_velocity", "average_velocity", "ReleaseSpeed"]
)

matched = rename_column(
    matched, "player", ["Pitcher", "pitcher"]
)

# Convert dates.

cmj_all["jump_date"] = pd.to_datetime(
    cmj_all["jump_date"]
)

games_all["game_date"] = pd.to_datetime(
    games_all["game_date"]
)

matched["jump_date"] = pd.to_datetime(
    matched["jump_date"]
)

matched["game_date"] = pd.to_datetime(
    matched["game_date"]
)

# Convert measurements.

for metric in METRICS:

    cmj_all[metric] = pd.to_numeric(
        cmj_all[metric], errors="coerce"
    )

    matched[metric] = pd.to_numeric(
        matched[metric], errors="coerce"
    )

for frame in [games_all, matched]:

    frame["avg_fastball_velocity"] = pd.to_numeric(
        frame["avg_fastball_velocity"],
        errors="coerce"
    )

matched["days_since_jump"] = pd.to_numeric(
    matched["days_since_jump"],
    errors="coerce"
)

correlations["pearson_r"] = pd.to_numeric(
    correlations["pearson_r"],
    errors="coerce"
)

# Verify that both pitchers are present.

for player in PLAYERS:

    if player not in set(matched["player"]):
        raise ValueError(
            f"{player} missing from matched data."
        )


# ------------------------------------------------------------
# 5. SHARED CSS
# ------------------------------------------------------------

CSS = """
:root {
    --navy: #14263b;
    --teal: #087f8c;
    --orange: #c87928;
    --text: #17212b;
    --muted: #617184;
    --border: #dfe5eb;
}

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    background: #f4f6f8;
    color: var(--text);
    font-family: Arial, Helvetica, sans-serif;
    font-size: 13px;
    line-height: 1.45;
}

header {
    background: var(--navy);
    color: white;
    padding: 25px 24px;
}

.header-inner,
main {
    max-width: 1200px;
    margin: auto;
}

/* Keep the heading on the left and the logo on the right. */
.header-inner {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 24px;
}

.header-copy {
    min-width: 0;
}

.header-logo {
    display: block;
    width: auto;
    height: auto;
    max-width: 115px;
    max-height: 86px;
    object-fit: contain;
    flex-shrink: 0;
}

.eyebrow {
    font-size: 10px;
    letter-spacing: 1.3px;
    color: #9dd3d8;
    text-transform: uppercase;
    font-weight: bold;
}

header h1 {
    font-size: 25px;
    margin: 5px 0;
}

header p {
    margin: 0;
    color: #d1dbe4;
    font-size: 12px;
}

main {
    padding: 18px 20px 35px;
}

.panel {
    background: white;
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 18px;
    margin-bottom: 15px;
}

h2 {
    font-size: 19px;
    margin: 0 0 9px;
}

h3 {
    font-size: 15px;
    margin: 0 0 7px;
}

p {
    margin: 7px 0;
}

.muted {
    color: var(--muted);
    font-size: 11px;
}

.key {
    padding: 11px 15px;
}

.key h2 {
    font-size: 13px;
    margin: 0 0 7px;
}

.key-row {
    display: flex;
    flex-wrap: wrap;
    align-items: flex-start;
    gap: 9px 22px;
}

.key-item {
    font-size: 11px;
    color: #4b5a6b;
    max-width: 300px;
}

.key-item strong {
    color: #263647;
}

.dot {
    display: inline-block;
    width: 9px;
    height: 9px;
    border-radius: 50%;
    margin-right: 5px;
}

.teal {
    background: var(--teal);
}

.orange {
    background: var(--orange);
}

.dash {
    display: inline-block;
    width: 19px;
    border-top: 2px dashed #526779;
    vertical-align: middle;
    margin-right: 5px;
}

.chart-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
    margin-top: 13px;
}

.chart-card {
    min-width: 0;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 4px;
}

.chart-card .plotly-graph-div {
    width: 100%;
}

.takeaway-grid,
.comparison-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 14px;
}

.takeaway {
    padding: 13px 16px;
    background: #f7f9fb;
    border: 1px solid var(--border);
    border-radius: 8px;
}

.takeaway ul {
    padding-left: 18px;
    margin: 7px 0 0;
}

.takeaway li {
    margin: 5px 0;
}

.callout {
    background: #f1f8f9;
    border-left: 4px solid var(--teal);
    padding: 13px 17px;
}

.exec-section {
    padding: 18px 21px;
}

.exec-section h2 {
    font-size: 17px;
    color: var(--navy);
    margin-bottom: 11px;
}

.exec-section p {
    font-size: 13px;
    line-height: 1.6;
}

.exec-section ul {
    margin: 8px 0 0;
    padding-left: 20px;
}

.exec-section li {
    margin: 9px 0;
    line-height: 1.55;
}

.exec-card {
    padding: 15px 18px;
    border-radius: 8px;
    border: 1px solid var(--border);
    background: #f7f9fb;
}

.exec-card h3 {
    margin: 0 0 8px;
}

.exec-card p {
    margin: 0;
}

.highlight-line {
    border-left: 3px solid var(--teal);
    padding-left: 13px;
    margin: 13px 0;
}

footer {
    padding: 15px;
    color: var(--muted);
    font-size: 11px;
    text-align: center;
}

@media (max-width: 800px) {

    .chart-grid,
    .takeaway-grid,
    .comparison-grid {
        grid-template-columns: 1fr;
    }

    main {
        padding: 12px;
    }

    header h1 {
        font-size: 22px;
    }

    .header-inner {
        gap: 12px;
    }

    .header-logo {
        max-width: 72px;
        max-height: 58px;
    }
}

@media print {

    body {
        background: white;
    }

    .panel,
    .chart-card,
    .exec-card {
        break-inside: avoid;
    }
}
"""


# ------------------------------------------------------------
# 6. HTML DOCUMENT WRAPPER
# ------------------------------------------------------------

def make_document(title, subtitle, content):

    logo_src = logo_data_uri()

    return f"""
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport"
          content="width=device-width, initial-scale=1">

    <title>{escape(title)}</title>

    <style>{CSS}</style>
</head>

<body>

<header>
    <div class="header-inner">
        <div class="header-copy">
            <div class="eyebrow">
                Detroit Tigers | Performance Science
            </div>

            <h1>{escape(title)}</h1>
            <p>{escape(subtitle)}</p>
        </div>
        <img class="header-logo" src="{logo_src}" alt="Report logo">
    </div>
</header>

<main>
    {content}
</main>

<footer>
    CMJ Performance & Fastball Velocity | 2025 Season
</footer>

</body>
</html>
"""


# ------------------------------------------------------------
# 7. PLOTLY HTML EXPORT
# ------------------------------------------------------------

# Include the Plotly library once.
# The report works offline.

plotly_loaded = False


def to_html(fig):

    global plotly_loaded

    html = pio.to_html(
        fig,
        full_html=False,
        include_plotlyjs=not plotly_loaded,
        config={
            "responsive": True,
            "displaylogo": False,
            "toImageButtonOptions": {
                "format": "png",
                "scale": 2
            }
        }
    )

    plotly_loaded = True

    return html


# ------------------------------------------------------------
# 8. CORRELATION LOOKUP
# ------------------------------------------------------------

# Read correlations from performance_analysis.py.

def get_r(player, metric):

    result = correlations[
        (correlations["player"] == player)
        & (correlations["performance_metric"] == metric)
    ]

    if result.empty:
        return np.nan

    return float(
        result.iloc[0]["pearson_r"]
    )


# ------------------------------------------------------------
# 9. COMBINED SCATTERPLOTS
# ------------------------------------------------------------

# One graph per metric, both pitchers together.
#
# Each pitcher retains:
# - Individual observations
# - Individual trend line
# - Individual Pearson correlation
#
# No pooled correlation is calculated.

def combined_scatter(metric, details):

    fig = go.Figure()

    annotations = []

    for index, player in enumerate(PLAYERS):

        subset = matched[
            matched["player"] == player
        ].dropna(
            subset=[metric, "avg_fastball_velocity"]
        ).copy()

        subset = subset.sort_values(metric)

        color = COLORS[player]

        r = get_r(player, metric)

        x = subset[metric].to_numpy(
            dtype=float
        )

        y = subset["avg_fastball_velocity"].to_numpy(
            dtype=float
        )

        # Hover details for individual games.

        hover_text = []

        for _, row in subset.iterrows():

            hover_text.append(
                f"<b>{player}</b>"
                f"<br>{details['label']}: "
                f"{row[metric]:.3f} {details['unit']}"
                f"<br>Avg. FB: "
                f"{row['avg_fastball_velocity']:.2f} mph"
                f"<br>Game: "
                f"{row['game_date']:%b %d, %Y}"
                f"<br>CMJ: "
                f"{row['jump_date']:%b %d, %Y}"
                f"<br>Interval: "
                f"{int(row['days_since_jump'])} days"
            )

        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode="markers",
                name=player,
                legendgroup=player,
                marker=dict(
                    color=color,
                    size=8,
                    opacity=0.78
                ),
                text=hover_text,
                hovertemplate="%{text}<extra></extra>"
            )
        )

        # Descriptive within-player trend line.

        if len(x) >= 3 and np.unique(x).size > 1:

            slope, intercept = np.polyfit(
                x, y, 1
            )

            line_x = np.linspace(
                x.min(), x.max(), 100
            )

            fig.add_trace(
                go.Scatter(
                    x=line_x,
                    y=slope * line_x + intercept,
                    mode="lines",
                    name=f"{player} trend",
                    legendgroup=player,
                    showlegend=False,
                    line=dict(
                        color=color,
                        width=2,
                        dash="dash"
                    ),
                    hoverinfo="skip"
                )
            )

        r_text = (
            f"{r:+.3f}"
            if np.isfinite(r)
            else "N/A"
        )

        annotations.append(
            dict(
                x=0.98,
                y=0.98 - index * 0.10,
                xref="paper",
                yref="paper",
                xanchor="right",
                yanchor="top",
                text=(
                    f"<span style='color:{color}'>"
                    f"●</span> {player}: "
                    f"r = {r_text}"
                ),
                showarrow=False,
                bgcolor="rgba(255,255,255,0.9)",
                font=dict(size=11)
            )
        )

    fig.update_layout(
        title=dict(
            text=details["label"],
            font=dict(size=15)
        ),
        template="plotly_white",
        height=350,
        margin=dict(
            l=65, r=15, t=55, b=65
        ),
        xaxis_title=(
            f"{details['label']} "
            f"({details['unit']})"
        ),
        yaxis_title="Avg. FB Velocity (mph)",
        font=dict(size=11),
        showlegend=False,
        annotations=annotations
    )

    return fig


# ------------------------------------------------------------
# 10. FULL-SEASON OVERVIEW
# ------------------------------------------------------------

# Includes all CMJ assessments and all games
# with fastball observations.
#
# Top: Average FB velocity
# Bottom: CMJ jump height
#
# Both pitchers are shown with consistent colors.

def combined_seasonal_overview():

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.17,
        subplot_titles=(
            "Fastball Velocity — All Games",
            "CMJ Jump Height — All Testing Sessions"
        )
    )

    for player in PLAYERS:

        color = COLORS[player]

        games = games_all[
            games_all["player"] == player
        ].sort_values("game_date")

        jumps = cmj_all[
            cmj_all["player"] == player
        ].sort_values("jump_date")

        # All game-level average fastball velocities.

        fig.add_trace(
            go.Scatter(
                x=games["game_date"],
                y=games["avg_fastball_velocity"],
                mode="lines+markers",
                line=dict(
                    color=color,
                    width=2
                ),
                marker=dict(size=6),
                name=player,
                legendgroup=player,
                hovertemplate=(
                    f"<b>{player}</b>"
                    "<br>Game: %{x|%b %d, %Y}"
                    "<br>Avg. FB: %{y:.2f} mph"
                    "<extra></extra>"
                )
            ),
            row=1,
            col=1
        )

        # All CMJ testing sessions.

        fig.add_trace(
            go.Scatter(
                x=jumps["jump_date"],
                y=jumps["Jump Height (Imp-Mom)"],
                mode="lines+markers",
                line=dict(
                    color=color,
                    width=2
                ),
                marker=dict(size=7),
                name=player,
                legendgroup=player,
                showlegend=False,
                hovertemplate=(
                    f"<b>{player}</b>"
                    "<br>CMJ: %{x|%b %d, %Y}"
                    "<br>Jump height: %{y:.2f} cm"
                    "<extra></extra>"
                )
            ),
            row=2,
            col=1
        )

    fig.update_yaxes(
        title_text="Velocity (mph)",
        row=1,
        col=1
    )

    fig.update_yaxes(
        title_text="Jump Height (cm)",
        row=2,
        col=1
    )

    fig.update_xaxes(
        title_text="Date",
        row=2,
        col=1
    )

    fig.update_layout(
        template="plotly_white",
        height=460,
        margin=dict(
            l=65, r=20, t=55, b=50
        ),
        font=dict(size=11),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.12,
            xanchor="right",
            x=1
        ),
        hovermode="closest"
    )

    return fig


# ------------------------------------------------------------
# 11. COMPACT DATA KEY
# ------------------------------------------------------------

KEY_HTML = """
<section class="panel key">

<h2>Data Key</h2>

<div class="key-row">

    <div class="key-item">
        <strong>Symbols:</strong>
        <span class="dot teal"></span> Pitcher A;
        <span class="dot orange"></span> Pitcher B;
        <span class="dash"></span> trend line.
        Hover for details.
    </div>

    <div class="key-item">
        <strong>Matched game:</strong>
        A game paired with the most recent
        preceding CMJ test within seven days.
    </div>

    <div class="key-item">
        <strong>Pearson's r:</strong>
        Describes the direction and strength
        of a linear association.
    </div>

    <div class="key-item">
        <strong>Full season vs. matched:</strong>
        Seasonal charts show all available
        games and CMJ sessions. Scatterplots
        show only matched games.
    </div>

</div>

</section>
"""


# ------------------------------------------------------------
# 12. COACH TAKEAWAYS
# ------------------------------------------------------------

COACH_TAKEAWAYS = """
<section class="panel">

<h2>Coaching Takeaways</h2>

<div class="takeaway-grid">

    <div class="takeaway">

        <h3 style="color:#087f8c;">
            Pitcher A
        </h3>

        <ul>
            <li>
                <strong>Trend:</strong>
                Weak negative correlations across
                all four indicators
                (r = −0.163 to −0.216).
            </li>

            <li>
                <strong>Flag:</strong>
                Higher CMJ performance did not
                consistently accompany higher
                fastball velocity.
            </li>

            <li>
                <strong>Action:</strong>
                Continue CMJ monitoring for physical
                performance context rather than
                using these indicators alone to
                anticipate velocity.
            </li>
        </ul>

    </div>

    <div class="takeaway">

        <h3 style="color:#c87928;">
            Pitcher B
        </h3>

        <ul>
            <li>
                <strong>Trend:</strong>
                Moderate positive associations for
                jump height, RSI-modified, and
                concentric mean power/BM
                (r = +0.404 to +0.444).
            </li>

            <li>
                <strong>Flag:</strong>
                Eccentric mean power/BM showed a
                much weaker association
                (r = +0.102).
            </li>

            <li>
                <strong>Action:</strong>
                Track the three positively associated
                indicators alongside fastball velocity
                to see whether these relationships persist.
            </li>
        </ul>

    </div>

</div>

</section>
"""


# ------------------------------------------------------------
# 13. BUILD COACH REPORT
# ------------------------------------------------------------

scatter_html = ""

for metric, details in METRICS.items():

    figure = combined_scatter(
        metric,
        details
    )

    scatter_html += f"""
    <div class="chart-card">
        {to_html(figure)}
    </div>
    """

season_html = to_html(
    combined_seasonal_overview()
)

coach_content = f"""

{KEY_HTML}

<section class="panel">

    <h2>
        CMJ Performance vs. Fastball Velocity
    </h2>

    <p class="muted">
        Four within-pitcher comparisons.
        Each point represents one game paired
        with a preceding CMJ assessment
        within seven days.
    </p>

    <div class="chart-grid">
        {scatter_html}
    </div>

</section>


<section class="panel">

    <h2>
        Full-Season Performance Overview
    </h2>

    <p class="muted">
        All available CMJ testing sessions
        and games with fastball observations
        are included. Jump height is displayed
        as the CMJ reference measure.
    </p>

    {season_html}

</section>


{COACH_TAKEAWAYS}
"""

# No interpretation note is added to the coach report.

COACH_OUTPUT.write_text(
    make_document(
        "Coach Report: CMJ & Fastball Velocity",
        "Comparative performance monitoring | 2025 Season",
        coach_content
    ),
    encoding="utf-8"
)


# ------------------------------------------------------------
# 14. EXECUTIVE SUMMARY
# ------------------------------------------------------------

# The executive summary directly follows the requested
# front-office deliverable structure.
#
# Sections:
#   1. Player comparison
#   2. Key findings and take-home messages
#   3. Notable differences
#   4. Larger-scale application
#   5. Future data and considerations

exec_content = """

<!-- SECTION 1: PLAYER COMPARISON -->

<section class="panel exec-section">

    <h2>1. Player Comparison</h2>

    <div class="comparison-grid">

        <div class="exec-card">

            <h3 style="color:#087f8c;">
                Pitcher A
            </h3>

            <p>
                All four CMJ performance indicators
                demonstrated weak negative correlations
                with average fastball velocity
                (r = −0.163 to −0.216).
                No clear positive association emerged.
            </p>

        </div>

        <div class="exec-card">

            <h3 style="color:#c87928;">
                Pitcher B
            </h3>

            <p>
                Jump height, RSI-modified, and concentric
                mean power/BM demonstrated moderate
                positive correlations with average
                fastball velocity (r = +0.404 to +0.444).
                Eccentric mean power/BM showed a weak
                positive correlation (r = +0.102).
            </p>

        </div>

    </div>

</section>


<!-- SECTION 2: KEY FINDINGS AND TAKE-HOME MESSAGES -->

<section class="panel exec-section">

    <h2>2. Key Findings & Take-Home Messages</h2>

    <div class="highlight-line">
        <strong>Key finding:</strong>
        The relationship between CMJ performance and
        fastball velocity differed between the two pitchers.
    </div>

    <div class="highlight-line">
        <strong>Take-home message:</strong>
        CMJ performance should be interpreted at the
        individual-athlete level rather than assuming
        that better jump performance consistently
        corresponds to higher pitching velocity.
    </div>

    <div class="highlight-line">
        <strong>Practical implication:</strong>
        CMJ assessments can contribute to physical
        performance monitoring, but should complement
        pitching-specific measures rather than serve
        as standalone indicators of velocity.
    </div>

</section>


<!-- SECTION 3: NOTABLE DIFFERENCES -->

<section class="panel exec-section">

    <h2>3. Notable Differences Between Players</h2>

    <ul>

        <li>
            <strong>Direction of association:</strong>
            Pitcher A showed consistently weak negative
            relationships, whereas Pitcher B showed
            positive relationships across all four metrics.
        </li>

        <li>
            <strong>Strength of association:</strong>
            Pitcher B demonstrated stronger relationships
            for jump height, RSI-modified, and concentric
            mean power/BM than Pitcher A.
        </li>

        <li>
            <strong>Metric-specific behavior:</strong>
            Pitcher B's eccentric mean power/BM
            correlation was substantially weaker than
            the other three metrics, suggesting that
            different CMJ indicators may provide
            different information within the same athlete.
        </li>

    </ul>

</section>


<!-- SECTION 4: LARGER-SCALE APPLICATION -->

<section class="panel exec-section">

    <h2>4. Application at a Larger Scale</h2>

    <p>
        These findings provide a starting point for an
        athlete-specific CMJ monitoring framework
        across a larger pitching population.
    </p>

    <ul>

        <li>
            <strong>Establish individual baselines:</strong>
            Track each pitcher's typical CMJ performance
            and fastball velocity over time.
        </li>

        <li>
            <strong>Evaluate within-athlete trends:</strong>
            Determine whether changes in specific CMJ
            indicators consistently accompany changes
            in fastball velocity for each pitcher.
        </li>

        <li>
            <strong>Identify common patterns:</strong>
            With a larger sample, examine whether
            similar relationships emerge across
            pitchers or whether individualized
            interpretation remains most appropriate.
        </li>

    </ul>

</section>


<!-- SECTION 5: FUTURE DATA AND CONSIDERATIONS -->

<section class="panel exec-section">

    <h2>5. Future Data & Considerations</h2>

    <ul>

        <li>
            <strong>Pitching workload:</strong>
            Pitch counts, throwing volume, and recovery
            intervals may help explain game-to-game
            fluctuations in fastball velocity.
        </li>

        <li>
            <strong>Readiness and recovery:</strong>
            Subjective readiness, soreness, and fatigue
            measures may provide context for changes
            in CMJ performance.
        </li>

        <li>
            <strong>Additional physical qualities:</strong>
            Lower-body strength, rotational power, and
            mobility assessments could capture
            performance characteristics not directly
            represented by vertical CMJ testing.
        </li>

        <li>
            <strong>Standardized testing schedules:</strong>
            Consistent timing between CMJ assessments
            and pitching appearances would improve
            longitudinal comparisons and reduce
            variability in assessment intervals.
        </li>

    </ul>

</section>
"""

# No Study Context section is included.

EXEC_OUTPUT.write_text(
    make_document(
        "Executive Summary: CMJ & Fastball Velocity",
        "Key findings, player differences, and organizational application",
        exec_content
    ),
    encoding="utf-8"
)


# ------------------------------------------------------------
# 15. PRINT REPORT LOCATIONS AND DATA COVERAGE
# ------------------------------------------------------------

print("\n======================================")
print("REPORTS GENERATED SUCCESSFULLY")
print("======================================")

for player in PLAYERS:

    total_games = len(
        games_all[
            games_all["player"] == player
        ]
    )

    total_cmj = len(
        cmj_all[
            cmj_all["player"] == player
        ]
    )

    matched_games = len(
        matched[
            matched["player"] == player
        ]
    )

    print(
        f"{player}: "
        f"{total_games} FB games | "
        f"{total_cmj} CMJ sessions | "
        f"{matched_games} matched games"
    )

print(f"\nCoach Report:\n{COACH_OUTPUT}")
print(f"\nExecutive Summary:\n{EXEC_OUTPUT}")
