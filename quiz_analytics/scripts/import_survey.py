#!/usr/bin/env python3
"""
Import and process student survey responses about quiz quality.

Usage:
    python import_survey.py spring2026_001 survey_export.csv
    python import_survey.py spring2026_001 survey_export.csv --regenerate
"""

import os
import sys
import csv
import json
import re
import argparse
from datetime import datetime
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))


def load_config():
    """Load configuration from config.json (or config.yaml if available)."""
    base_path = Path(__file__).parent.parent

    # Try JSON first (no dependencies)
    json_path = base_path / "config.json"
    if json_path.exists():
        with open(json_path) as f:
            return json.load(f)

    # Fall back to YAML if available
    yaml_path = base_path / "config.yaml"
    if yaml_path.exists():
        try:
            import yaml
            with open(yaml_path) as f:
                return yaml.safe_load(f)
        except ImportError:
            pass

    raise FileNotFoundError("No config.json or config.yaml found")


def parse_question_references(text):
    """
    Extract quiz and question references from free-text responses.
    Returns list of (quiz_num, question_num) tuples.
    """
    references = []

    if not text:
        return references

    text = text.lower()

    # Patterns to match:
    # "quiz 2 question 3", "q2 #3", "quiz2 q3", "2.3", "quiz 2, question 3"
    patterns = [
        r'quiz\s*(\d+)\s*(?:,?\s*)?(?:question|q|#)\s*(\d+)',
        r'q(\d+)\s*(?:#|q)?\s*(\d+)',
        r'(\d+)\.(\d+)',
        r'quiz\s*(\d+)',  # Just quiz reference
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if len(match) == 2:
                references.append((int(match[0]), int(match[1])))
            elif len(match) == 1:
                references.append((int(match[0]), None))  # Quiz only

    return references


def import_canvas_survey(csv_file, config):
    """
    Import survey responses from Canvas export.
    Expected columns: student_id, clarity_rating, confusing_questions, unfair_questions, suggestions
    """
    responses = []

    with open(csv_file, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)

        # Normalize column names
        fieldnames = reader.fieldnames
        column_map = {}

        for col in fieldnames:
            col_lower = col.lower()
            if 'clarity' in col_lower or 'rating' in col_lower:
                column_map['clarity'] = col
            elif 'confus' in col_lower:
                column_map['confusing'] = col
            elif 'unfair' in col_lower:
                column_map['unfair'] = col
            elif 'suggest' in col_lower:
                column_map['suggestions'] = col
            elif 'student' in col_lower or 'id' in col_lower:
                column_map['student_id'] = col

        for row in reader:
            response = {
                "student_id": row.get(column_map.get('student_id', ''), 'anonymous'),
                "clarity_rating": None,
                "confusing_questions": [],
                "unfair_questions": [],
                "suggestions": "",
                "raw": row
            }

            # Parse clarity rating
            clarity_val = row.get(column_map.get('clarity', ''), '')
            if clarity_val:
                try:
                    response["clarity_rating"] = int(float(clarity_val))
                except (ValueError, TypeError):
                    pass

            # Parse question references
            confusing_text = row.get(column_map.get('confusing', ''), '')
            response["confusing_questions"] = parse_question_references(confusing_text)
            response["confusing_text"] = confusing_text

            unfair_text = row.get(column_map.get('unfair', ''), '')
            response["unfair_questions"] = parse_question_references(unfair_text)
            response["unfair_text"] = unfair_text

            response["suggestions"] = row.get(column_map.get('suggestions', ''), '')

            responses.append(response)

    return responses


def aggregate_survey_data(responses):
    """
    Aggregate survey responses by quiz/question.
    """
    aggregated = {
        "total_responses": len(responses),
        "clarity_ratings": [],
        "question_feedback": defaultdict(lambda: {
            "confusing_count": 0,
            "unfair_count": 0,
            "comments": []
        }),
        "general_suggestions": []
    }

    for resp in responses:
        # Clarity ratings
        if resp["clarity_rating"] is not None:
            aggregated["clarity_ratings"].append(resp["clarity_rating"])

        # Question-specific feedback
        for quiz_num, q_num in resp["confusing_questions"]:
            key = f"quiz{quiz_num}_q{q_num}" if q_num else f"quiz{quiz_num}"
            aggregated["question_feedback"][key]["confusing_count"] += 1
            if resp.get("confusing_text"):
                aggregated["question_feedback"][key]["comments"].append({
                    "type": "confusing",
                    "text": resp["confusing_text"][:200]
                })

        for quiz_num, q_num in resp["unfair_questions"]:
            key = f"quiz{quiz_num}_q{q_num}" if q_num else f"quiz{quiz_num}"
            aggregated["question_feedback"][key]["unfair_count"] += 1
            if resp.get("unfair_text"):
                aggregated["question_feedback"][key]["comments"].append({
                    "type": "unfair",
                    "text": resp["unfair_text"][:200]
                })

        # General suggestions
        if resp["suggestions"]:
            aggregated["general_suggestions"].append(resp["suggestions"][:500])

    # Calculate clarity statistics
    if aggregated["clarity_ratings"]:
        ratings = aggregated["clarity_ratings"]
        aggregated["clarity_mean"] = sum(ratings) / len(ratings)
        aggregated["clarity_count"] = len(ratings)

    # Convert defaultdict to regular dict
    aggregated["question_feedback"] = dict(aggregated["question_feedback"])

    return aggregated


def merge_with_analysis(survey_data, section_key, config):
    """
    Merge survey feedback into analysis data.
    """
    data_dir = Path(__file__).parent.parent / config["paths"]["processed"]
    analysis_file = data_dir / f"{section_key}_analysis.json"

    if not analysis_file.exists():
        print(f"Warning: No analysis file found at {analysis_file}")
        return

    with open(analysis_file) as f:
        analysis = json.load(f)

    # Add survey data to analysis
    analysis["survey"] = {
        "imported_at": datetime.now().isoformat(),
        "total_responses": survey_data["total_responses"],
        "clarity_mean": survey_data.get("clarity_mean"),
        "clarity_count": survey_data.get("clarity_count", 0)
    }

    # Add feedback to individual questions
    for quiz in analysis.get("quizzes", []):
        quiz_title = quiz.get("title", "")
        # Try to extract quiz number from title
        quiz_match = re.search(r'quiz\s*(\d+)', quiz_title.lower())
        if not quiz_match:
            continue

        quiz_num = int(quiz_match.group(1))

        for i, q in enumerate(quiz.get("questions", []), 1):
            key = f"quiz{quiz_num}_q{i}"
            feedback = survey_data["question_feedback"].get(key, {})

            q["survey_feedback"] = {
                "confusing_count": feedback.get("confusing_count", 0),
                "unfair_count": feedback.get("unfair_count", 0),
                "has_feedback": feedback.get("confusing_count", 0) + feedback.get("unfair_count", 0) > 0
            }

            # Add to flags if multiple students reported issues
            if feedback.get("confusing_count", 0) >= 3:
                if "evaluation" not in q:
                    q["evaluation"] = {"flags": [], "severity": "good"}
                q["evaluation"]["flags"].append({
                    "type": "student_feedback",
                    "issue": f"Reported confusing by {feedback['confusing_count']} students",
                    "recommendation": "Review question wording for clarity"
                })

            if feedback.get("unfair_count", 0) >= 2:
                if "evaluation" not in q:
                    q["evaluation"] = {"flags": [], "severity": "good"}
                q["evaluation"]["flags"].append({
                    "type": "student_feedback",
                    "issue": f"Reported unfair by {feedback['unfair_count']} students",
                    "recommendation": "Verify content was covered in class"
                })

    # Save updated analysis
    with open(analysis_file, "w") as f:
        json.dump(analysis, f, indent=2)

    print(f"Updated analysis file with survey data: {analysis_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Import student survey responses"
    )
    parser.add_argument(
        "section",
        help="Section key (e.g., spring2026_001)"
    )
    parser.add_argument(
        "survey_file",
        help="Path to survey export CSV file"
    )
    parser.add_argument(
        "--regenerate",
        action="store_true",
        help="Regenerate reports after importing survey"
    )

    args = parser.parse_args()

    config = load_config()

    # Import survey
    print(f"Importing survey from {args.survey_file}...")
    responses = import_canvas_survey(args.survey_file, config)
    print(f"  Found {len(responses)} responses")

    # Aggregate
    survey_data = aggregate_survey_data(responses)

    # Save raw survey data
    survey_dir = Path(__file__).parent.parent / config["paths"]["surveys"]
    survey_dir.mkdir(parents=True, exist_ok=True)

    survey_file = survey_dir / f"{args.section}_survey.json"
    with open(survey_file, "w") as f:
        json.dump({
            "imported_at": datetime.now().isoformat(),
            "source_file": args.survey_file,
            "responses": responses,
            "aggregated": survey_data
        }, f, indent=2)

    print(f"  Saved to {survey_file}")

    # Merge with analysis
    merge_with_analysis(survey_data, args.section, config)

    # Report summary
    print(f"\nSurvey Summary:")
    print(f"  Responses: {survey_data['total_responses']}")
    if survey_data.get("clarity_mean"):
        print(f"  Mean Clarity Rating: {survey_data['clarity_mean']:.2f}/5")

    feedback_items = len(survey_data["question_feedback"])
    if feedback_items:
        print(f"  Questions with feedback: {feedback_items}")

    # Regenerate reports if requested
    if args.regenerate:
        print("\nRegenerating reports...")
        from generate_reports import generate_all_reports
        generate_all_reports(args.section, config)

    print("\nSurvey import complete!")


if __name__ == "__main__":
    main()
