#!/usr/bin/env python3
"""
Fetch quiz performance data from Canvas LMS API.

Usage:
    python fetch_canvas_data.py spring2026_001
    python fetch_canvas_data.py spring2026_001 --grades
    python fetch_canvas_data.py --all
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

# Add parent directory to path for imports
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


def load_env_file():
    """Load environment variables from .env file if it exists."""
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    # Remove quotes if present
                    value = value.strip().strip("'\"")
                    os.environ[key.strip()] = value


def get_canvas_token():
    """Get Canvas API token from .env file or environment variable."""
    # Try loading from .env first
    load_env_file()

    token = os.environ.get("CANVAS_TOKEN")
    if not token:
        print("Error: CANVAS_TOKEN not found.")
        print("Either:")
        print("  1. Create quiz_analytics/.env with: CANVAS_TOKEN='your_token'")
        print("  2. Or set: export CANVAS_TOKEN='your_token_here'")
        sys.exit(1)
    return token


def canvas_api_request(base_url, endpoint, token, params=None):
    """Make a request to the Canvas API."""
    url = f"{base_url}/api/v1{endpoint}"
    if params:
        param_str = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{param_str}"

    headers = {"Authorization": f"Bearer {token}"}
    request = Request(url, headers=headers)

    try:
        with urlopen(request) as response:
            return json.loads(response.read().decode())
    except HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}")
        print(f"URL: {url}")
        return None
    except URLError as e:
        print(f"URL Error: {e.reason}")
        return None


def canvas_api_paginated(base_url, endpoint, token, params=None):
    """Handle paginated Canvas API responses."""
    all_results = []
    page = 1
    per_page = 100

    while True:
        page_params = {"page": page, "per_page": per_page}
        if params:
            page_params.update(params)

        results = canvas_api_request(base_url, endpoint, token, page_params)
        if not results:
            break

        all_results.extend(results)

        if len(results) < per_page:
            break
        page += 1

    return all_results


def fetch_quizzes(base_url, course_id, token):
    """Fetch all quizzes for a course."""
    print(f"  Fetching quizzes for course {course_id}...")
    endpoint = f"/courses/{course_id}/quizzes"
    quizzes = canvas_api_paginated(base_url, endpoint, token)

    if quizzes:
        print(f"    Found {len(quizzes)} quizzes")
    return quizzes or []


def fetch_quiz_questions(base_url, course_id, quiz_id, token):
    """Fetch questions for a specific quiz."""
    endpoint = f"/courses/{course_id}/quizzes/{quiz_id}/questions"
    return canvas_api_paginated(base_url, endpoint, token) or []


def fetch_quiz_submissions(base_url, course_id, quiz_id, token):
    """Fetch all submissions for a quiz."""
    endpoint = f"/courses/{course_id}/quizzes/{quiz_id}/submissions"
    params = {"include[]": "submission"}
    return canvas_api_paginated(base_url, endpoint, token, params) or []


def fetch_submission_questions(base_url, course_id, quiz_id, submission_id, token):
    """Fetch question responses for a specific submission."""
    endpoint = f"/courses/{course_id}/quizzes/{quiz_id}/submissions/{submission_id}/questions"
    return canvas_api_request(base_url, endpoint, token) or []


def fetch_enrollments(base_url, course_id, token):
    """Fetch all student enrollments with final grades."""
    print(f"  Fetching enrollments for course {course_id}...")
    endpoint = f"/courses/{course_id}/enrollments"
    params = {"type[]": "StudentEnrollment", "state[]": "active"}
    enrollments = canvas_api_paginated(base_url, endpoint, token, params)

    if enrollments:
        print(f"    Found {len(enrollments)} students")
    return enrollments or []


def anonymize_id(student_id, id_map):
    """Convert student ID to anonymous ID."""
    if student_id not in id_map:
        id_map[student_id] = f"student_{len(id_map) + 1:03d}"
    return id_map[student_id]


def process_quiz_data(base_url, course_id, quiz, token, id_map):
    """Process a single quiz and extract question-level responses."""
    quiz_id = quiz["id"]
    print(f"    Processing quiz: {quiz.get('title', quiz_id)}")

    # Fetch questions
    questions = fetch_quiz_questions(base_url, course_id, quiz_id, token)

    # Build question lookup
    question_data = []
    for q in questions:
        q_info = {
            "id": q["id"],
            "position": q.get("position", 0),
            "text": q.get("question_text", ""),
            "question_type": q.get("question_type", ""),
            "points": q.get("points_possible", 10),
            "answers": []
        }

        # Extract answer options
        for ans in q.get("answers", []):
            q_info["answers"].append({
                "id": ans.get("id"),
                "text": ans.get("text", ""),
                "weight": ans.get("weight", 0)  # 100 = correct
            })

        question_data.append(q_info)

    # Sort by position
    question_data.sort(key=lambda x: x["position"])

    # Fetch submissions
    submissions_raw = fetch_quiz_submissions(base_url, course_id, quiz_id, token)

    # Extract submissions list from various possible response formats
    submissions_list = []
    if isinstance(submissions_raw, dict):
        # Canvas may return {"quiz_submissions": [...]} or {"submissions": [...]}
        submissions_list = submissions_raw.get("quiz_submissions",
                          submissions_raw.get("submissions", []))
    elif isinstance(submissions_raw, list):
        submissions_list = submissions_raw

    submissions = []
    for sub in submissions_list:
        # Skip non-dict elements (Canvas sometimes includes metadata strings)
        if not isinstance(sub, dict):
            continue
        if not sub.get("user_id"):
            continue

        sub_data = {
            "student_id": anonymize_id(sub["user_id"], id_map),
            "score": sub.get("score", 0),
            "kept_score": sub.get("kept_score", sub.get("score", 0)),
            "attempt": sub.get("attempt", 1),
            "submitted_at": sub.get("finished_at"),
            "time_spent": sub.get("time_spent"),
            "responses": {}
        }

        # Try to get question-level responses
        # Note: This requires quiz to have "show student quiz responses" enabled
        submission_id = sub.get("id")
        if submission_id:
            try:
                q_responses = fetch_submission_questions(
                    base_url, course_id, quiz_id, submission_id, token
                )
                if q_responses and "quiz_submission_questions" in q_responses:
                    for qr in q_responses["quiz_submission_questions"]:
                        q_id = qr.get("id")
                        # Get the answer ID they selected
                        answer_id = qr.get("answer_id")
                        correct = qr.get("correct", False)
                        sub_data["responses"][str(q_id)] = {
                            "answer_id": answer_id,
                            "correct": correct
                        }
            except Exception as e:
                # Question-level data may not be available
                pass

        submissions.append(sub_data)

    return {
        "quiz_id": quiz_id,
        "title": quiz.get("title", ""),
        "points_possible": quiz.get("points_possible", 50),
        "question_count": quiz.get("question_count", len(question_data)),
        "published": quiz.get("published", False),
        "questions": question_data,
        "submissions": submissions,
        "fetched_at": datetime.now().isoformat()
    }


def fetch_section_data(section_key, config, grades_only=False):
    """Fetch all quiz data for a section."""
    if section_key not in config["courses"]:
        print(f"Error: Unknown section '{section_key}'")
        print(f"Available sections: {list(config['courses'].keys())}")
        sys.exit(1)

    course_config = config["courses"][section_key]
    course_id = course_config["course_id"]
    base_url = config["canvas"]["base_url"]
    token = get_canvas_token()

    print(f"\nFetching data for {section_key} (Course ID: {course_id})")

    # Create output directory
    output_dir = Path(__file__).parent.parent / config["paths"]["raw_data"] / section_key
    output_dir.mkdir(parents=True, exist_ok=True)

    # ID mapping for anonymization
    id_map = {}

    # Fetch enrollments/grades
    enrollments = fetch_enrollments(base_url, course_id, token)
    grades_data = []
    for enrollment in enrollments:
        user_id = enrollment.get("user_id")
        if user_id:
            grades_data.append({
                "student_id": anonymize_id(user_id, id_map),
                "current_score": enrollment.get("grades", {}).get("current_score"),
                "final_score": enrollment.get("grades", {}).get("final_score"),
                "current_grade": enrollment.get("grades", {}).get("current_grade"),
                "final_grade": enrollment.get("grades", {}).get("final_grade")
            })

    # Save grades
    grades_file = output_dir / "grades.json"
    with open(grades_file, "w") as f:
        json.dump({
            "section": section_key,
            "course_id": course_id,
            "fetched_at": datetime.now().isoformat(),
            "enrollments": grades_data
        }, f, indent=2)
    print(f"  Saved grades to {grades_file}")

    if grades_only:
        return

    # Fetch quizzes
    quizzes = fetch_quizzes(base_url, course_id, token)

    # Process each quiz
    all_quiz_data = []
    for quiz in quizzes:
        if not quiz.get("published", False):
            continue  # Skip unpublished quizzes

        quiz_data = process_quiz_data(base_url, course_id, quiz, token, id_map)
        all_quiz_data.append(quiz_data)

        # Save individual quiz data
        quiz_file = output_dir / f"quiz_{quiz['id']}.json"
        with open(quiz_file, "w") as f:
            json.dump(quiz_data, f, indent=2)

    # Save combined data
    combined_file = output_dir / "all_quizzes.json"
    with open(combined_file, "w") as f:
        json.dump({
            "section": section_key,
            "course_id": course_id,
            "semester": course_config["semester"],
            "fetched_at": datetime.now().isoformat(),
            "quizzes": all_quiz_data
        }, f, indent=2)

    print(f"\n  Saved {len(all_quiz_data)} quizzes to {output_dir}")

    # Save ID mapping (for reference, also gitignored)
    id_map_file = output_dir / "id_mapping.json"
    with open(id_map_file, "w") as f:
        json.dump(id_map, f, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Fetch quiz performance data from Canvas"
    )
    parser.add_argument(
        "section",
        nargs="?",
        help="Section key (e.g., spring2026_001) or --all for all sections"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Fetch data for all configured sections"
    )
    parser.add_argument(
        "--grades",
        action="store_true",
        help="Fetch only grades (faster, for grade correlation updates)"
    )

    args = parser.parse_args()

    if not args.section and not args.all:
        parser.print_help()
        sys.exit(1)

    config = load_config()

    if args.all:
        for section_key in config["courses"]:
            fetch_section_data(section_key, config, args.grades)
    else:
        fetch_section_data(args.section, config, args.grades)

    print("\nData fetch complete!")


if __name__ == "__main__":
    main()
