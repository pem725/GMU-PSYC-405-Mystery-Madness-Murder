# Quiz Performance Analytics

Automated system for analyzing quiz performance data to improve question quality.

## Overview

This system:
1. **Fetches** quiz submission data from Canvas API
2. **Analyzes** item statistics (difficulty, discrimination, distractors)
3. **Generates** reports identifying questions needing revision
4. **Integrates** student survey feedback

## Quick Start

```bash
# Set Canvas API token
export CANVAS_TOKEN="your_token_here"

# Fetch all quiz data for a section
python scripts/fetch_canvas_data.py spring2026_001

# Run analysis
python scripts/analyze_quiz_performance.py spring2026_001

# Generate reports
python scripts/generate_reports.py spring2026_001

# Or do everything at once
python scripts/analyze_quiz_performance.py spring2026_001 --full
```

## Metrics Calculated

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| **Difficulty (p)** | correct / total | <0.30 too hard, >0.90 too easy |
| **Discrimination (D)** | p_upper27% - p_lower27% | <0.20 poor, >0.40 excellent |
| **Point-Biserial r** | correlation with final grade | <0.15 may not measure course objectives |
| **Distractor Analysis** | selection rates per answer | <5% not plausible, >50% may be ambiguous |

## Output Files

```
reports/
├── spring2026_001/
│   ├── quiz_123_shutter_island_analysis.md    # Detailed per-quiz reports
│   └── ...
├── dashboards/
│   └── spring2026_001_dashboard.html          # Interactive Plotly dashboard
└── flagged_questions/
    └── spring2026_001_flagged.md              # Summary of issues
```

## Configuration

Edit `config.yaml` to adjust:
- Flag thresholds (difficulty, discrimination)
- Course IDs and semester info
- Grouping method (top/bottom 27%, thirds, median)

## Student Survey Integration

1. Create Canvas survey with clarity/feedback questions
2. Export responses as CSV
3. Import: `python scripts/import_survey.py spring2026_001 survey.csv --regenerate`

## Privacy

- Raw data stored locally only (gitignored)
- All student IDs anonymized in reports
- Only aggregated statistics committed to repo
