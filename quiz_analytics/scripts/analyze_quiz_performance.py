#!/usr/bin/env python3
"""
Analyze quiz performance data and calculate item statistics.

Usage:
    python analyze_quiz_performance.py spring2026_001
    python analyze_quiz_performance.py spring2026_001 --full
    python analyze_quiz_performance.py --all
"""

import os
import sys
import json
import math
import argparse
from datetime import datetime
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml


def load_config():
    """Load configuration from config.yaml."""
    config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def load_quiz_data(section_key, config):
    """Load all quiz data for a section."""
    data_dir = Path(__file__).parent.parent / config["paths"]["raw_data"] / section_key

    if not data_dir.exists():
        print(f"Error: No data found for {section_key}")
        print(f"Run fetch_canvas_data.py first.")
        sys.exit(1)

    all_quizzes_file = data_dir / "all_quizzes.json"
    if all_quizzes_file.exists():
        with open(all_quizzes_file) as f:
            return json.load(f)

    # Fall back to individual quiz files
    quizzes = []
    for quiz_file in sorted(data_dir.glob("quiz_*.json")):
        with open(quiz_file) as f:
            quizzes.append(json.load(f))

    return {"quizzes": quizzes, "section": section_key}


def load_grades_data(section_key, config):
    """Load grades data for correlation analysis."""
    data_dir = Path(__file__).parent.parent / config["paths"]["raw_data"] / section_key
    grades_file = data_dir / "grades.json"

    if grades_file.exists():
        with open(grades_file) as f:
            data = json.load(f)
            # Build lookup by student_id
            return {e["student_id"]: e for e in data.get("enrollments", [])}

    return {}


def calculate_difficulty(responses, question_id):
    """
    Calculate item difficulty (p-value).
    p = proportion of students who answered correctly
    """
    correct = 0
    total = 0

    for resp in responses:
        q_resp = resp.get("responses", {}).get(str(question_id))
        if q_resp is not None:
            total += 1
            if q_resp.get("correct", False):
                correct += 1

    if total == 0:
        return None

    return correct / total


def calculate_discrimination(responses, question_id, grades, method="top_bottom_27"):
    """
    Calculate discrimination index using top/bottom 27% method.
    D = p_upper - p_lower
    """
    # Get scores for students who answered this question
    student_scores = []
    for resp in responses:
        student_id = resp["student_id"]
        q_resp = resp.get("responses", {}).get(str(question_id))

        if q_resp is not None and student_id in grades:
            final_score = grades[student_id].get("final_score") or grades[student_id].get("current_score")
            if final_score is not None:
                student_scores.append({
                    "student_id": student_id,
                    "correct": q_resp.get("correct", False),
                    "final_score": final_score
                })

    if len(student_scores) < 10:
        return None  # Not enough data

    # Sort by final score
    student_scores.sort(key=lambda x: x["final_score"], reverse=True)

    # Determine group sizes
    n = len(student_scores)
    if method == "top_bottom_27":
        group_size = max(1, int(n * 0.27))
    elif method == "thirds":
        group_size = n // 3
    else:  # median
        group_size = n // 2

    # Upper group (high performers)
    upper_group = student_scores[:group_size]
    upper_correct = sum(1 for s in upper_group if s["correct"])
    p_upper = upper_correct / len(upper_group) if upper_group else 0

    # Lower group (low performers)
    lower_group = student_scores[-group_size:]
    lower_correct = sum(1 for s in lower_group if s["correct"])
    p_lower = lower_correct / len(lower_group) if lower_group else 0

    return {
        "D": p_upper - p_lower,
        "p_upper": p_upper,
        "p_lower": p_lower,
        "upper_n": len(upper_group),
        "lower_n": len(lower_group)
    }


def calculate_distractor_analysis(responses, question_id, question_data):
    """
    Analyze distractor (wrong answer) selection rates.
    """
    # Build answer ID to letter mapping
    answers = question_data.get("answers", [])
    answer_map = {}
    correct_id = None

    for i, ans in enumerate(answers):
        letter = chr(65 + i)  # A, B, C, D...
        answer_map[ans["id"]] = {
            "letter": letter,
            "text": ans.get("text", ""),
            "is_correct": ans.get("weight", 0) == 100
        }
        if ans.get("weight", 0) == 100:
            correct_id = ans["id"]

    # Count selections
    selection_counts = defaultdict(int)
    total_responses = 0
    correct_count = 0

    for resp in responses:
        q_resp = resp.get("responses", {}).get(str(question_id))
        if q_resp is not None:
            total_responses += 1
            answer_id = q_resp.get("answer_id")
            if answer_id:
                selection_counts[answer_id] += 1
                if q_resp.get("correct", False):
                    correct_count += 1

    if total_responses == 0:
        return None

    # Calculate rates
    analysis = []
    wrong_total = total_responses - correct_count

    for ans_id, info in answer_map.items():
        count = selection_counts.get(ans_id, 0)
        rate = count / total_responses if total_responses > 0 else 0

        distractor_rate = None
        if not info["is_correct"] and wrong_total > 0:
            distractor_rate = count / wrong_total

        analysis.append({
            "answer_id": ans_id,
            "letter": info["letter"],
            "text": info["text"][:50] + "..." if len(info.get("text", "")) > 50 else info.get("text", ""),
            "is_correct": info["is_correct"],
            "count": count,
            "selection_rate": rate,
            "distractor_rate": distractor_rate
        })

    # Sort by letter
    analysis.sort(key=lambda x: x["letter"])

    return {
        "total_responses": total_responses,
        "correct_count": correct_count,
        "answers": analysis
    }


def calculate_point_biserial(responses, question_id, grades):
    """
    Calculate point-biserial correlation between item score and final grade.
    r_pb = (M_1 - M_0) / S * sqrt(p * q)
    where:
    - M_1 = mean final grade of students who got item correct
    - M_0 = mean final grade of students who got item wrong
    - S = standard deviation of all final grades
    - p = proportion correct, q = 1 - p
    """
    correct_grades = []
    incorrect_grades = []

    for resp in responses:
        student_id = resp["student_id"]
        q_resp = resp.get("responses", {}).get(str(question_id))

        if q_resp is not None and student_id in grades:
            final_score = grades[student_id].get("final_score") or grades[student_id].get("current_score")
            if final_score is not None:
                if q_resp.get("correct", False):
                    correct_grades.append(final_score)
                else:
                    incorrect_grades.append(final_score)

    if len(correct_grades) < 2 or len(incorrect_grades) < 2:
        return None

    # Calculate means
    m1 = sum(correct_grades) / len(correct_grades)
    m0 = sum(incorrect_grades) / len(incorrect_grades)

    # Calculate overall standard deviation
    all_grades = correct_grades + incorrect_grades
    mean_all = sum(all_grades) / len(all_grades)
    variance = sum((x - mean_all) ** 2 for x in all_grades) / len(all_grades)
    std_dev = math.sqrt(variance) if variance > 0 else 1

    # Calculate proportions
    n = len(all_grades)
    p = len(correct_grades) / n
    q = 1 - p

    # Point-biserial correlation
    if std_dev > 0 and p > 0 and q > 0:
        r_pb = (m1 - m0) / std_dev * math.sqrt(p * q)
    else:
        r_pb = 0

    return {
        "r_pb": r_pb,
        "mean_correct": m1,
        "mean_incorrect": m0,
        "n_correct": len(correct_grades),
        "n_incorrect": len(incorrect_grades)
    }


def evaluate_metrics(difficulty, discrimination, point_biserial, config):
    """
    Evaluate metrics against thresholds and generate flags.
    """
    thresholds = config["thresholds"]
    flags = []
    severity = "good"

    # Difficulty flags
    if difficulty is not None:
        if difficulty > thresholds["difficulty"]["too_easy"]:
            flags.append({
                "type": "difficulty",
                "issue": "Too easy",
                "value": difficulty,
                "threshold": thresholds["difficulty"]["too_easy"],
                "recommendation": "Consider making question more challenging or removing"
            })
            severity = "warning"
        elif difficulty < thresholds["difficulty"]["too_hard"]:
            flags.append({
                "type": "difficulty",
                "issue": "Too difficult",
                "value": difficulty,
                "threshold": thresholds["difficulty"]["too_hard"],
                "recommendation": "Review question wording, ensure content was covered in class"
            })
            severity = "warning"

    # Discrimination flags
    if discrimination is not None:
        d_value = discrimination["D"]
        if d_value < thresholds["discrimination"]["critical"]:
            flags.append({
                "type": "discrimination",
                "issue": "Negative discrimination",
                "value": d_value,
                "threshold": 0,
                "recommendation": "CRITICAL: High performers getting this wrong. Check answer key and question clarity."
            })
            severity = "critical"
        elif d_value < thresholds["discrimination"]["flag_below"]:
            flags.append({
                "type": "discrimination",
                "issue": "Poor discrimination",
                "value": d_value,
                "threshold": thresholds["discrimination"]["flag_below"],
                "recommendation": "Question doesn't distinguish between high and low performers"
            })
            if severity != "critical":
                severity = "warning"

    # Point-biserial flags
    if point_biserial is not None:
        r_pb = point_biserial["r_pb"]
        if r_pb < thresholds["point_biserial"]["flag_below"]:
            flags.append({
                "type": "point_biserial",
                "issue": "Low correlation with final grade",
                "value": r_pb,
                "threshold": thresholds["point_biserial"]["flag_below"],
                "recommendation": "Question may not measure intended course objectives"
            })
            if severity == "good":
                severity = "warning"

    return {
        "flags": flags,
        "severity": severity,
        "flag_count": len(flags)
    }


def analyze_quiz(quiz_data, grades, config):
    """Analyze a single quiz and return item statistics."""
    results = {
        "quiz_id": quiz_data.get("quiz_id"),
        "title": quiz_data.get("title", ""),
        "question_count": len(quiz_data.get("questions", [])),
        "submission_count": len(quiz_data.get("submissions", [])),
        "questions": [],
        "summary": {}
    }

    submissions = quiz_data.get("submissions", [])
    questions = quiz_data.get("questions", [])

    if not submissions or not questions:
        results["summary"]["error"] = "No submission or question data available"
        return results

    # Calculate quiz-level statistics
    scores = [s.get("score", 0) or 0 for s in submissions]
    if scores:
        results["summary"]["mean_score"] = sum(scores) / len(scores)
        results["summary"]["median_score"] = sorted(scores)[len(scores) // 2]
        variance = sum((s - results["summary"]["mean_score"]) ** 2 for s in scores) / len(scores)
        results["summary"]["std_dev"] = math.sqrt(variance)
        results["summary"]["min_score"] = min(scores)
        results["summary"]["max_score"] = max(scores)
        results["summary"]["points_possible"] = quiz_data.get("points_possible", 50)

    # Analyze each question
    total_flags = 0
    critical_flags = 0

    for q in questions:
        q_id = q["id"]

        difficulty = calculate_difficulty(submissions, q_id)
        discrimination = calculate_discrimination(
            submissions, q_id, grades,
            config["grouping"]["method"]
        )
        distractor = calculate_distractor_analysis(submissions, q_id, q)
        point_biserial = calculate_point_biserial(submissions, q_id, grades)

        evaluation = evaluate_metrics(difficulty, discrimination, point_biserial, config)

        q_result = {
            "question_id": q_id,
            "position": q.get("position", 0),
            "text": q.get("text", "")[:200],
            "difficulty": difficulty,
            "discrimination": discrimination,
            "distractor_analysis": distractor,
            "point_biserial": point_biserial,
            "evaluation": evaluation
        }

        results["questions"].append(q_result)
        total_flags += evaluation["flag_count"]
        if evaluation["severity"] == "critical":
            critical_flags += 1

    # Sort by position
    results["questions"].sort(key=lambda x: x["position"])

    results["summary"]["total_flags"] = total_flags
    results["summary"]["critical_flags"] = critical_flags
    results["summary"]["questions_analyzed"] = len(results["questions"])

    return results


def analyze_section(section_key, config):
    """Analyze all quizzes for a section."""
    print(f"\nAnalyzing {section_key}...")

    # Load data
    quiz_data = load_quiz_data(section_key, config)
    grades = load_grades_data(section_key, config)

    if not grades:
        print("  Warning: No grades data found. Discrimination and correlation analysis limited.")

    results = {
        "section": section_key,
        "analyzed_at": datetime.now().isoformat(),
        "config": {
            "thresholds": config["thresholds"],
            "grouping": config["grouping"]
        },
        "quizzes": []
    }

    for quiz in quiz_data.get("quizzes", []):
        quiz_results = analyze_quiz(quiz, grades, config)
        results["quizzes"].append(quiz_results)
        print(f"  Analyzed: {quiz_results['title']} - {quiz_results['summary'].get('total_flags', 0)} flags")

    # Save results
    output_dir = Path(__file__).parent.parent / config["paths"]["processed"]
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"{section_key}_analysis.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n  Analysis saved to {output_file}")

    # Summary
    total_quizzes = len(results["quizzes"])
    total_flags = sum(q["summary"].get("total_flags", 0) for q in results["quizzes"])
    critical = sum(q["summary"].get("critical_flags", 0) for q in results["quizzes"])

    print(f"\n  Summary:")
    print(f"    Quizzes analyzed: {total_quizzes}")
    print(f"    Total flagged issues: {total_flags}")
    print(f"    Critical issues: {critical}")

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Analyze quiz performance data"
    )
    parser.add_argument(
        "section",
        nargs="?",
        help="Section key (e.g., spring2026_001)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Analyze all sections"
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run full analysis including report generation"
    )

    args = parser.parse_args()

    if not args.section and not args.all:
        parser.print_help()
        sys.exit(1)

    config = load_config()

    if args.all:
        for section_key in config["courses"]:
            analyze_section(section_key, config)
    else:
        analyze_section(args.section, config)

    if args.full:
        print("\nGenerating reports...")
        # Import and run report generator
        from generate_reports import generate_all_reports
        if args.all:
            for section_key in config["courses"]:
                generate_all_reports(section_key, config)
        else:
            generate_all_reports(args.section, config)

    print("\nAnalysis complete!")


if __name__ == "__main__":
    main()
