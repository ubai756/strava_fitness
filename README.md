# Fitness Analytics Case Study

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-dashboard-FF4B4B?logo=streamlit&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-database-07405E?logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

A Bellabeat-style analytics case study, applied to Fitbit/Fitabase fitness-tracker
data, delivered as an interactive Streamlit dashboard.

## 1. Business Task

**How are consumers using their smart fitness devices?** The goal is to surface
usage patterns (activity, sleep, heart rate) that can inform product and content
recommendations for a fitness-tracking app.

## 2. Data Sources

- **Source:** Fitabase export of Fitbit fitness-tracker data, 33 users, covering
  April 12 – May 9, 2016.
- **Collected via:** Amazon Mechanical Turk, originally distributed on Kaggle
  (CC0 / public domain license).
- **Limitations:** small sample (33 users), short time window (~1 month), no
  demographic data (age, sex), and self-selected participants — findings are
  directional, not statistically representative.
- Files used: `dailyActivity_merged.csv`, `sleepDay_merged.csv`,
  `weightLogInfo_merged.csv`, `heartrate_seconds_merged.csv`,
  `hourlyCalories_merged.csv`, `hourlyIntensities_merged.csv`,
  `hourlySteps_merged.csv`.
  (`dailyCalories_merged.csv`, `dailyIntensities_merged.csv`, and
  `dailySteps_merged.csv` were excluded — they are redundant subsets already
  contained in `dailyActivity_merged.csv`.)

## 3. Data Cleaning & Manipulation

All cleaning is done in `etl.py`, which prints a log of every step it takes.
Summary of what it does:

| Step | Detail |
|---|---|
| Daily activity | 940 rows, 0 exact duplicates. Flagged 77 zero-step days as likely non-wear days (kept, not deleted, to preserve wear-rate signal). |
| Sleep | 410 unique Id/date rows after removing 3 exact duplicates and collapsing multi-record (nap) days by summing minutes. |
| Weight | Only 8 of 33 users logged weight (67 rows) — the `Fat` column is >95% missing and was dropped. |
| Heart rate | 2,483,658 per-second readings aggregated to daily avg/min/max per user (334 rows) — raw granularity was too heavy for a live dashboard. |
| Hourly | Hourly calories, intensities, and steps merged into one table on Id + hour (22,099 rows). |
| Master table | Daily activity is the base table; sleep, heart rate, and weight are left-joined onto it by Id + date. |

## 4. Summary of Analysis

- Users average **~7,600 steps/day** and **~2,300 calories/day**.
- Steps and calories are **moderately correlated (r ≈ 0.59)**.
- Users are sedentary **~16.5 hours/day** on average.
- Sleep duration and sedentary minutes are **negatively correlated (r ≈ -0.60)**.
- Devices were worn on **~92%** of tracked days.
- Data coverage drops off by data type: 33 users have activity data, 24 have
  sleep data, 14 have heart rate data, 8 have weight data.

## 5. Visualizations & Key Findings

See the live dashboard (`app.py`) for interactive charts: steps-over-time trend
with peak annotation, activity-minutes donut, calorie distribution, hourly
activity pattern, sleep trend, heart rate trend, and three correlation
scatterplots (steps vs. calories, sleep vs. sedentary minutes, steps vs. sleep).

## 6. Recommendations

- Use in-app nudges to close the sedentary/sleep gap — e.g. an evening
  wind-down reminder triggered by high sedentary minutes, since that pattern
  tracks with shorter sleep.
- Since steps reliably predict calories burned, surface a simple "steps to
  calorie goal" widget to reinforce the habit loop.
- Prioritize onboarding nudges for sleep and heart-rate tracking specifically —
  they're the weakest-adopted data sources in this dataset (24 and 14 of 33
  users respectively).

---

## Project Structure

```
strava_fitness_app/
├── etl.py              # cleans raw CSVs, builds fitness.db
├── app.py              # Streamlit dashboard
├── fitness.db          # SQLite database (output of etl.py)
├── requirements.txt
└── README.md
```

## Running Locally

```bash
pip install -r requirements.txt
python etl.py --data-dir "./data/Fitabase Data 4.12.16-5.12.16" --out fitness.db
streamlit run app.py
```

## Tools Used

- **SQL / SQLite** — cleaning, joining, and querying the data
- **Python (pandas)** — ETL pipeline
- **Streamlit + Plotly** — interactive dashboard

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for how to
propose changes.

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.
