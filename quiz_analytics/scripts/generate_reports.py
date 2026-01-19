#!/usr/bin/env python3
"""
Generate quiz performance reports from analysis data.

Usage:
    python generate_reports.py spring2026_001
    python generate_reports.py --all
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml


def load_config():
    """Load configuration from config.yaml."""
    config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def load_analysis_data(section_key, config):
    """Load analysis results for a section."""
    data_dir = Path(__file__).parent.parent / config["paths"]["processed"]
    analysis_file = data_dir / f"{section_key}_analysis.json"

    if not analysis_file.exists():
        print(f"Error: No analysis found for {section_key}")
        print(f"Run analyze_quiz_performance.py first.")
        sys.exit(1)

    with open(analysis_file) as f:
        return json.load(f)


def format_percentage(value, decimals=1):
    """Format a decimal as percentage."""
    if value is None:
        return "N/A"
    return f"{value * 100:.{decimals}f}%"


def format_decimal(value, decimals=2):
    """Format a decimal number."""
    if value is None:
        return "N/A"
    return f"{value:.{decimals}f}"


def get_difficulty_label(p):
    """Get descriptive label for difficulty."""
    if p is None:
        return "Unknown"
    if p < 0.30:
        return "Too Difficult"
    if p < 0.40:
        return "Difficult"
    if p <= 0.70:
        return "Ideal"
    if p <= 0.90:
        return "Easy"
    return "Too Easy"


def get_discrimination_label(d):
    """Get descriptive label for discrimination index."""
    if d is None:
        return "Unknown"
    if d < 0:
        return "NEGATIVE"
    if d < 0.20:
        return "Poor"
    if d < 0.30:
        return "Acceptable"
    if d < 0.40:
        return "Good"
    return "Excellent"


def generate_quiz_markdown(quiz_results, section_key, config):
    """Generate Markdown report for a single quiz."""
    title = quiz_results.get("title", "Unknown Quiz")
    summary = quiz_results.get("summary", {})

    report = []
    report.append(f"# {title} - Performance Analysis\n")
    report.append(f"**Section:** {section_key} | **Analyzed:** {datetime.now().strftime('%Y-%m-%d')}")
    report.append(f"**Submissions:** {quiz_results.get('submission_count', 0)} students\n")

    # Summary statistics
    report.append("## Summary Statistics\n")
    if summary.get("mean_score") is not None:
        points = summary.get("points_possible", 50)
        mean = summary.get("mean_score", 0)
        report.append(f"- **Mean Score:** {mean:.1f} / {points} ({mean/points*100:.1f}%)")
        report.append(f"- **Median:** {summary.get('median_score', 0):.1f}")
        report.append(f"- **Std Dev:** {summary.get('std_dev', 0):.2f}")
        report.append(f"- **Range:** {summary.get('min_score', 0):.0f} - {summary.get('max_score', 0):.0f}")
    else:
        report.append("*No score data available*")

    report.append(f"\n**Flagged Issues:** {summary.get('total_flags', 0)}")
    if summary.get("critical_flags", 0) > 0:
        report.append(f"**Critical Issues:** {summary.get('critical_flags', 0)}")
    report.append("")

    # Item analysis
    report.append("## Item Analysis\n")

    for i, q in enumerate(quiz_results.get("questions", []), 1):
        report.append(f"### Question {i}")

        # Question text (truncated)
        q_text = q.get("text", "")
        if q_text:
            # Strip HTML tags
            import re
            q_text = re.sub(r'<[^>]+>', '', q_text)
            if len(q_text) > 150:
                q_text = q_text[:150] + "..."
            report.append(f"> {q_text}\n")

        # Metrics
        difficulty = q.get("difficulty")
        discrimination = q.get("discrimination", {})
        point_biserial = q.get("point_biserial", {})

        report.append(f"**Difficulty (p):** {format_percentage(difficulty)} ({get_difficulty_label(difficulty)})")

        d_value = discrimination.get("D") if discrimination else None
        report.append(f"**Discrimination (D):** {format_decimal(d_value)} ({get_discrimination_label(d_value)})")

        if discrimination:
            report.append(f"  - Upper 27%: {format_percentage(discrimination.get('p_upper'))}")
            report.append(f"  - Lower 27%: {format_percentage(discrimination.get('p_lower'))}")

        r_pb = point_biserial.get("r_pb") if point_biserial else None
        report.append(f"**Point-Biserial r:** {format_decimal(r_pb)}")

        # Distractor analysis table
        distractor = q.get("distractor_analysis")
        if distractor and distractor.get("answers"):
            report.append("\n| Answer | Selected | Rate | Upper 27% | Lower 27% |")
            report.append("|--------|----------|------|-----------|-----------|")

            for ans in distractor.get("answers", []):
                letter = ans.get("letter", "?")
                if ans.get("is_correct"):
                    letter += "*"
                count = ans.get("count", 0)
                rate = format_percentage(ans.get("selection_rate"))
                # Note: We don't have per-answer upper/lower data in current structure
                # This would need enhancement in analyze_quiz_performance.py
                report.append(f"| {letter} | {count} | {rate} | - | - |")

            report.append("")

        # Flags
        evaluation = q.get("evaluation", {})
        flags = evaluation.get("flags", [])
        if flags:
            report.append("**Issues:**")
            for flag in flags:
                severity_icon = "🔴" if flag.get("type") == "discrimination" and flag.get("value", 0) < 0 else "⚠️"
                report.append(f"- {severity_icon} {flag.get('issue')}: {format_decimal(flag.get('value'))}")
                report.append(f"  - *{flag.get('recommendation')}*")
            report.append("")
        else:
            report.append("*No issues flagged*\n")

        report.append("---\n")

    return "\n".join(report)


def generate_flagged_summary(analysis_data, section_key, config):
    """Generate summary of all flagged questions."""
    report = []
    report.append(f"# Flagged Questions - {section_key}\n")
    report.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    critical_items = []
    warning_items = []
    good_items = []

    for quiz in analysis_data.get("quizzes", []):
        quiz_title = quiz.get("title", "Unknown")
        for i, q in enumerate(quiz.get("questions", []), 1):
            evaluation = q.get("evaluation", {})
            severity = evaluation.get("severity", "good")

            item = {
                "quiz": quiz_title,
                "question": i,
                "difficulty": q.get("difficulty"),
                "discrimination": q.get("discrimination", {}).get("D") if q.get("discrimination") else None,
                "flags": evaluation.get("flags", [])
            }

            if severity == "critical":
                critical_items.append(item)
            elif severity == "warning":
                warning_items.append(item)
            else:
                discrimination = q.get("discrimination", {})
                if discrimination and discrimination.get("D", 0) >= 0.40:
                    good_items.append(item)

    # Critical issues
    if critical_items:
        report.append("## 🔴 Critical Issues (Requires Immediate Revision)\n")
        report.append("| Quiz | Q# | Difficulty | Discrimination | Issue |")
        report.append("|------|-----|------------|----------------|-------|")
        for item in critical_items:
            issues = "; ".join(f.get("issue", "") for f in item["flags"])
            report.append(
                f"| {item['quiz'][:30]} | {item['question']} | "
                f"{format_percentage(item['difficulty'])} | "
                f"{format_decimal(item['discrimination'])} | {issues} |"
            )
        report.append("")
    else:
        report.append("## 🔴 Critical Issues\n*None found*\n")

    # Warnings
    if warning_items:
        report.append("## ⚠️ Moderate Issues (Review for Next Semester)\n")
        report.append("| Quiz | Q# | Difficulty | Discrimination | Issue |")
        report.append("|------|-----|------------|----------------|-------|")
        for item in warning_items:
            issues = "; ".join(f.get("issue", "") for f in item["flags"])
            report.append(
                f"| {item['quiz'][:30]} | {item['question']} | "
                f"{format_percentage(item['difficulty'])} | "
                f"{format_decimal(item['discrimination'])} | {issues} |"
            )
        report.append("")
    else:
        report.append("## ⚠️ Moderate Issues\n*None found*\n")

    # Excellent questions
    if good_items:
        report.append("## ✅ Excellent Questions (Models for Future)\n")
        report.append("| Quiz | Q# | Difficulty | Discrimination |")
        report.append("|------|-----|------------|----------------|")
        for item in good_items[:10]:  # Top 10
            report.append(
                f"| {item['quiz'][:30]} | {item['question']} | "
                f"{format_percentage(item['difficulty'])} | "
                f"{format_decimal(item['discrimination'])} |"
            )
        report.append("")

    # Summary statistics
    total_questions = sum(len(q.get("questions", [])) for q in analysis_data.get("quizzes", []))
    report.append("## Summary\n")
    report.append(f"- **Total Questions Analyzed:** {total_questions}")
    report.append(f"- **Critical Issues:** {len(critical_items)}")
    report.append(f"- **Warnings:** {len(warning_items)}")
    report.append(f"- **Excellent Questions:** {len(good_items)}")

    return "\n".join(report)


def generate_html_dashboard(analysis_data, section_key, config):
    """Generate interactive HTML dashboard with Plotly."""
    course_config = config["courses"].get(section_key, {})

    # Collect data for charts
    quiz_names = []
    mean_scores = []
    flag_counts = []
    difficulties = []
    discriminations = []
    question_labels = []

    for quiz in analysis_data.get("quizzes", []):
        quiz_title = quiz.get("title", "Unknown")[:20]
        quiz_names.append(quiz_title)
        summary = quiz.get("summary", {})
        mean_scores.append(summary.get("mean_score", 0))
        flag_counts.append(summary.get("total_flags", 0))

        for i, q in enumerate(quiz.get("questions", []), 1):
            difficulties.append(q.get("difficulty"))
            d = q.get("discrimination", {})
            discriminations.append(d.get("D") if d else None)
            question_labels.append(f"{quiz_title} Q{i}")

    # Filter out None values for scatter plot
    valid_points = [
        (d, disc, label)
        for d, disc, label in zip(difficulties, discriminations, question_labels)
        if d is not None and disc is not None
    ]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quiz Performance Dashboard - {section_key}</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        h1 {{ color: #333; border-bottom: 3px solid #007bff; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .dashboard-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(600px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        .chart-card {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stat-value {{ font-size: 2.5em; font-weight: bold; color: #007bff; }}
        .stat-label {{ color: #666; margin-top: 5px; }}
        .stat-card.critical .stat-value {{ color: #dc3545; }}
        .stat-card.warning .stat-value {{ color: #ffc107; }}
        .stat-card.good .stat-value {{ color: #28a745; }}
        .legend {{
            background: white;
            border-radius: 8px;
            padding: 15px;
            margin-top: 20px;
        }}
        .legend h3 {{ margin-top: 0; }}
        .legend-item {{ display: flex; align-items: center; margin: 10px 0; }}
        .legend-color {{ width: 20px; height: 20px; border-radius: 4px; margin-right: 10px; }}
        footer {{ margin-top: 40px; text-align: center; color: #888; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Quiz Performance Dashboard</h1>
        <p><strong>Section:</strong> {section_key} | <strong>{course_config.get('semester', '')}</strong> | <strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{len(analysis_data.get('quizzes', []))}</div>
                <div class="stat-label">Quizzes Analyzed</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{sum(len(q.get('questions', [])) for q in analysis_data.get('quizzes', []))}</div>
                <div class="stat-label">Total Questions</div>
            </div>
            <div class="stat-card critical">
                <div class="stat-value">{sum(q.get('summary', {}).get('critical_flags', 0) for q in analysis_data.get('quizzes', []))}</div>
                <div class="stat-label">Critical Issues</div>
            </div>
            <div class="stat-card warning">
                <div class="stat-value">{sum(q.get('summary', {}).get('total_flags', 0) for q in analysis_data.get('quizzes', []))}</div>
                <div class="stat-label">Total Flags</div>
            </div>
        </div>

        <div class="dashboard-grid">
            <div class="chart-card">
                <div id="score-chart"></div>
            </div>
            <div class="chart-card">
                <div id="flags-chart"></div>
            </div>
            <div class="chart-card" style="grid-column: 1 / -1;">
                <div id="scatter-chart"></div>
            </div>
        </div>

        <div class="legend">
            <h3>Interpretation Guide</h3>
            <div class="legend-item">
                <div class="legend-color" style="background: #28a745;"></div>
                <span><strong>Ideal Zone:</strong> Difficulty 0.30-0.70, Discrimination &gt; 0.30</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #ffc107;"></div>
                <span><strong>Review:</strong> Difficulty &lt;0.30 or &gt;0.90, or Discrimination &lt;0.20</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #dc3545;"></div>
                <span><strong>Critical:</strong> Negative discrimination (high performers getting it wrong)</span>
            </div>
        </div>

        <footer>
            <p>PSYC 405: Mystery, Madness & Murder - Quiz Analytics</p>
        </footer>
    </div>

    <script>
        // Mean scores by quiz
        Plotly.newPlot('score-chart', [{{
            x: {json.dumps(quiz_names)},
            y: {json.dumps(mean_scores)},
            type: 'bar',
            marker: {{ color: '#007bff' }}
        }}], {{
            title: 'Mean Quiz Scores',
            xaxis: {{ title: 'Quiz', tickangle: -45 }},
            yaxis: {{ title: 'Mean Score', range: [0, 50] }},
            margin: {{ b: 100 }}
        }});

        // Flags by quiz
        Plotly.newPlot('flags-chart', [{{
            x: {json.dumps(quiz_names)},
            y: {json.dumps(flag_counts)},
            type: 'bar',
            marker: {{ color: '#ffc107' }}
        }}], {{
            title: 'Flagged Issues by Quiz',
            xaxis: {{ title: 'Quiz', tickangle: -45 }},
            yaxis: {{ title: 'Number of Flags' }},
            margin: {{ b: 100 }}
        }});

        // Difficulty vs Discrimination scatter
        var scatterData = {json.dumps([{'x': p[0], 'y': p[1], 'label': p[2]} for p in valid_points])};
        var colors = scatterData.map(function(p) {{
            if (p.y < 0) return '#dc3545';  // Critical
            if (p.x < 0.3 || p.x > 0.9 || p.y < 0.2) return '#ffc107';  // Warning
            return '#28a745';  // Good
        }});

        Plotly.newPlot('scatter-chart', [{{
            x: scatterData.map(p => p.x),
            y: scatterData.map(p => p.y),
            text: scatterData.map(p => p.label),
            mode: 'markers',
            type: 'scatter',
            marker: {{
                size: 12,
                color: colors,
                line: {{ width: 1, color: '#333' }}
            }},
            hovertemplate: '%{{text}}<br>Difficulty: %{{x:.2f}}<br>Discrimination: %{{y:.2f}}<extra></extra>'
        }}], {{
            title: 'Item Analysis: Difficulty vs Discrimination',
            xaxis: {{
                title: 'Difficulty (p-value)',
                range: [0, 1],
                gridcolor: '#eee'
            }},
            yaxis: {{
                title: 'Discrimination Index (D)',
                range: [-0.5, 1],
                gridcolor: '#eee'
            }},
            shapes: [
                // Ideal difficulty zone
                {{
                    type: 'rect',
                    x0: 0.3, x1: 0.7,
                    y0: 0.2, y1: 1,
                    fillcolor: 'rgba(40, 167, 69, 0.1)',
                    line: {{ width: 0 }}
                }},
                // Zero discrimination line
                {{
                    type: 'line',
                    x0: 0, x1: 1,
                    y0: 0, y1: 0,
                    line: {{ color: '#dc3545', width: 2, dash: 'dash' }}
                }}
            ],
            annotations: [{{
                x: 0.5,
                y: 0.6,
                text: 'Ideal Zone',
                showarrow: false,
                font: {{ color: '#28a745', size: 14 }}
            }}]
        }});
    </script>
</body>
</html>"""

    return html


def generate_all_reports(section_key, config):
    """Generate all reports for a section."""
    print(f"\nGenerating reports for {section_key}...")

    analysis_data = load_analysis_data(section_key, config)
    base_dir = Path(__file__).parent.parent

    # Create report directories
    report_dir = base_dir / config["paths"]["reports"] / section_key
    report_dir.mkdir(parents=True, exist_ok=True)

    dashboard_dir = base_dir / config["paths"]["dashboards"]
    dashboard_dir.mkdir(parents=True, exist_ok=True)

    flagged_dir = base_dir / config["paths"]["flagged"]
    flagged_dir.mkdir(parents=True, exist_ok=True)

    # Generate per-quiz Markdown reports
    for quiz in analysis_data.get("quizzes", []):
        quiz_id = quiz.get("quiz_id", "unknown")
        quiz_title = quiz.get("title", "unknown").lower().replace(" ", "_")[:30]
        filename = f"quiz_{quiz_id}_{quiz_title}_analysis.md"

        report_content = generate_quiz_markdown(quiz, section_key, config)
        report_file = report_dir / filename

        with open(report_file, "w") as f:
            f.write(report_content)

        print(f"  Generated: {filename}")

    # Generate flagged questions summary
    flagged_content = generate_flagged_summary(analysis_data, section_key, config)
    flagged_file = flagged_dir / f"{section_key}_flagged.md"
    with open(flagged_file, "w") as f:
        f.write(flagged_content)
    print(f"  Generated: {section_key}_flagged.md")

    # Generate HTML dashboard
    dashboard_content = generate_html_dashboard(analysis_data, section_key, config)
    dashboard_file = dashboard_dir / f"{section_key}_dashboard.html"
    with open(dashboard_file, "w") as f:
        f.write(dashboard_content)
    print(f"  Generated: {section_key}_dashboard.html")

    print(f"\n  Reports saved to {report_dir}")
    print(f"  Dashboard: {dashboard_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate quiz performance reports"
    )
    parser.add_argument(
        "section",
        nargs="?",
        help="Section key (e.g., spring2026_001)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate reports for all sections"
    )

    args = parser.parse_args()

    if not args.section and not args.all:
        parser.print_help()
        sys.exit(1)

    config = load_config()

    if args.all:
        for section_key in config["courses"]:
            generate_all_reports(section_key, config)
    else:
        generate_all_reports(args.section, config)

    print("\nReport generation complete!")


if __name__ == "__main__":
    main()
