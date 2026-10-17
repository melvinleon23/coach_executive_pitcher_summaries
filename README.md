# CMJ Performance & Fastball Velocity Analysis

## Overview
Examining within-pitcher relationships between CMJ performance and fastball velocity for two pitchers.
## Deliverables
- [Coach Report] (outputs/reports/coach_report.html)
- [Executive Summary] (outputs/reports/executive_summary.html)

## Methodology
Four CMJ performance indicators were evaluated:
- Jump Height (Impulse-Momentum)
- RSI-modified (Impulse-Momentum)
- Concentric Mean Power / Body Mass
- Eccentric Mean Power / Body Mass

Each pitching game was paired with the most recent preceding CMJ assessment within seven days. Pearson correlations were calculated separately for each pitcher. Full-season visuals show all available CMJs and pitching games, while scatter plots use matched observations.

## Project Structure
- 'scripts/data_script.py' - data cleaning and matching
- 'scripts/performance_analysis.py' - correlation analysis
- 'scripts/report_builder.py' - interactive HTML reports
- 'outputs/reports/' - final deliverables

## Interpretation
Findings are exploratory.

## Data Availability
Underlying athlete datasets are excluded from the public repository.
