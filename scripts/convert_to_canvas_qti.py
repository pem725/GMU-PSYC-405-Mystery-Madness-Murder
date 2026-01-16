#!/usr/bin/env python3
"""
Convert PSYC 405 quiz files (.qmd) to Canvas QTI format for import.

This script reads quiz questions from .qmd files and answer keys from .md files,
then generates QTI 1.2 XML files that can be imported directly into Canvas.

Usage:
    python scripts/convert_to_canvas_qti.py spring2026_001
    python scripts/convert_to_canvas_qti.py spring2026_002
    python scripts/convert_to_canvas_qti.py --all

The script will:
1. Read all quiz files from quizzes/{section}/
2. Read corresponding answer keys from quizzes/answer_keys/
3. Generate QTI files in canvas/{section}/
4. Create a manifest file for Canvas import
"""

import argparse
import os
import re
import shutil
import sys
import uuid
import xml.etree.ElementTree as ET
import zipfile
from xml.dom import minidom
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class Question:
    """Represents a single quiz question with answer choices and feedback."""

    def __init__(self, number: int, text: str, choices: Dict[str, str],
                 correct_answer: str, rationale: str = "", distractor_analysis: Dict[str, str] = None):
        self.number = number
        self.text = text
        self.choices = choices  # {"A": "text", "B": "text", ...}
        self.correct_answer = correct_answer
        self.rationale = rationale
        self.distractor_analysis = distractor_analysis or {}
        self.ident = f"q{number}_{uuid.uuid4().hex[:8]}"


class Quiz:
    """Represents a complete quiz with metadata and questions."""

    def __init__(self, title: str, section: str, quiz_number: int):
        self.title = title
        self.section = section
        self.quiz_number = quiz_number
        self.questions: List[Question] = []
        self.ident = f"quiz{quiz_number}_{uuid.uuid4().hex[:8]}"


def parse_quiz_file(filepath: Path) -> Tuple[str, List[Tuple[int, str, Dict[str, str]]]]:
    """
    Parse a .qmd quiz file and extract questions with answer choices.

    Returns:
        Tuple of (quiz_title, list of (question_number, question_text, choices_dict))
    """
    content = filepath.read_text(encoding='utf-8')

    # Extract title from YAML frontmatter
    title_match = re.search(r'^title:\s*["\'](.+?)["\']', content, re.MULTILINE)
    title = title_match.group(1) if title_match else filepath.stem

    questions = []

    # Split by question headers
    question_blocks = re.split(r'###\s*Question\s*(\d+)', content)

    # Process pairs of (number, content)
    for i in range(1, len(question_blocks), 2):
        if i + 1 >= len(question_blocks):
            break

        q_num = int(question_blocks[i])
        q_content = question_blocks[i + 1]

        # Split content into lines and extract question text and choices
        lines = q_content.strip().split('\n')

        question_text_lines = []
        choices = {}
        in_choices = False

        for line in lines:
            line = line.strip()
            if not line or line == '---':
                continue

            # Check if this is an answer choice (A), B), C), etc.)
            choice_match = re.match(r'^([A-E])\)\s*(.+)$', line)
            if choice_match:
                in_choices = True
                letter = choice_match.group(1)
                text = choice_match.group(2)
                choices[letter] = text
            elif not in_choices and line:
                question_text_lines.append(line)

        question_text = ' '.join(question_text_lines)
        if question_text and choices:
            questions.append((q_num, question_text, choices))

    return title, questions


def parse_answer_key(filepath: Path) -> Dict[int, Tuple[str, str, Dict[str, str]]]:
    """
    Parse an answer key .md file and extract correct answers and rationales.

    Returns:
        Dict mapping question number to (correct_answer, rationale, distractor_analysis)
    """
    if not filepath.exists():
        return {}

    content = filepath.read_text(encoding='utf-8')
    answers = {}

    # Split by question headers
    question_blocks = re.split(r'###\s*Question\s*(\d+)', content)

    for i in range(1, len(question_blocks), 2):
        if i + 1 >= len(question_blocks):
            break

        q_num = int(question_blocks[i])
        q_content = question_blocks[i + 1]

        # Extract correct answer
        answer_match = re.search(r'\*\*Correct Answer:\s*([A-E])\*\*', q_content)
        correct_answer = answer_match.group(1) if answer_match else ""

        # Extract rationale
        rationale_match = re.search(
            r'\*\*Rationale for Correct Answer:\*\*\s*\n(.+?)(?=\n\*\*Distractor Analysis|\n---|\Z)',
            q_content, re.DOTALL
        )
        rationale = rationale_match.group(1).strip() if rationale_match else ""

        # Extract distractor analysis
        distractor_analysis = {}
        distractor_section = re.search(
            r'\*\*Distractor Analysis:\*\*\s*\n(.+?)(?=\n\*\*Course Connection|\n---|\Z)',
            q_content, re.DOTALL
        )
        if distractor_section:
            distractors = re.findall(
                r'-\s*\*\*([A-E])\*\*\s*\([^)]+\)\s*-\s*(.+?)(?=\n-|\Z)',
                distractor_section.group(1), re.DOTALL
            )
            for letter, explanation in distractors:
                distractor_analysis[letter] = explanation.strip()

        answers[q_num] = (correct_answer, rationale, distractor_analysis)

    return answers


def create_qti_assessment(quiz: Quiz, points_per_question: int = 10) -> ET.Element:
    """
    Create QTI 1.2 XML assessment element for a quiz.

    Canvas expects a specific QTI format with:
    - questestinterop root element
    - assessment with metadata
    - section containing items (questions)
    """
    # Create root element with namespaces
    root = ET.Element('questestinterop')
    root.set('xmlns', 'http://www.imsglobal.org/xsd/ims_qtiasiv1p2')

    # Create assessment
    assessment = ET.SubElement(root, 'assessment')
    assessment.set('ident', quiz.ident)
    assessment.set('title', quiz.title)

    # Assessment metadata
    qtimetadata = ET.SubElement(assessment, 'qtimetadata')

    metadata_fields = [
        ('qmd_timelimit', ''),  # No time limit
        ('cc_maxattempts', '1'),  # One attempt
    ]

    for field_label, field_entry in metadata_fields:
        qtimetadatafield = ET.SubElement(qtimetadata, 'qtimetadatafield')
        ET.SubElement(qtimetadatafield, 'fieldlabel').text = field_label
        ET.SubElement(qtimetadatafield, 'fieldentry').text = field_entry

    # Create section for questions
    section = ET.SubElement(assessment, 'section')
    section.set('ident', f'section_{quiz.ident}')

    # Add each question as an item
    for question in quiz.questions:
        item = create_qti_item(question, points_per_question)
        section.append(item)

    return root


def create_qti_item(question: Question, points: int) -> ET.Element:
    """Create a QTI item element for a single multiple choice question."""
    item = ET.Element('item')
    item.set('ident', question.ident)
    item.set('title', f'Question {question.number}')

    # Item metadata
    itemmetadata = ET.SubElement(item, 'itemmetadata')
    qtimetadata = ET.SubElement(itemmetadata, 'qtimetadata')

    metadata_fields = [
        ('question_type', 'multiple_choice_question'),
        ('points_possible', str(points)),
        ('assessment_question_identifierref', question.ident),
    ]

    for field_label, field_entry in metadata_fields:
        qtimetadatafield = ET.SubElement(qtimetadata, 'qtimetadatafield')
        ET.SubElement(qtimetadatafield, 'fieldlabel').text = field_label
        ET.SubElement(qtimetadatafield, 'fieldentry').text = field_entry

    # Presentation (question text and answer choices)
    presentation = ET.SubElement(item, 'presentation')

    # Question text as material
    material = ET.SubElement(presentation, 'material')
    mattext = ET.SubElement(material, 'mattext')
    mattext.set('texttype', 'text/html')
    mattext.text = f'<p>{escape_html(question.text)}</p>'

    # Response (answer choices)
    response_lid = ET.SubElement(presentation, 'response_lid')
    response_lid.set('ident', f'response_{question.ident}')
    response_lid.set('rcardinality', 'Single')

    render_choice = ET.SubElement(response_lid, 'render_choice')

    # Add each answer choice
    for letter, text in sorted(question.choices.items()):
        response_label = ET.SubElement(render_choice, 'response_label')
        response_label.set('ident', letter)

        material = ET.SubElement(response_label, 'material')
        mattext = ET.SubElement(material, 'mattext')
        mattext.set('texttype', 'text/html')
        mattext.text = f'<p>{escape_html(text)}</p>'

    # Response processing (correct answer)
    resprocessing = ET.SubElement(item, 'resprocessing')
    outcomes = ET.SubElement(resprocessing, 'outcomes')

    decvar = ET.SubElement(outcomes, 'decvar')
    decvar.set('maxvalue', '100')
    decvar.set('minvalue', '0')
    decvar.set('varname', 'SCORE')
    decvar.set('vartype', 'Decimal')

    # Correct answer condition
    respcondition = ET.SubElement(resprocessing, 'respcondition')
    respcondition.set('continue', 'No')

    conditionvar = ET.SubElement(respcondition, 'conditionvar')
    varequal = ET.SubElement(conditionvar, 'varequal')
    varequal.set('respident', f'response_{question.ident}')
    varequal.text = question.correct_answer

    setvar = ET.SubElement(respcondition, 'setvar')
    setvar.set('action', 'Set')
    setvar.set('varname', 'SCORE')
    setvar.text = '100'

    # Item feedback (rationale)
    if question.rationale:
        # Correct answer feedback
        itemfeedback = ET.SubElement(item, 'itemfeedback')
        itemfeedback.set('ident', f'correct_fb_{question.ident}')

        flow_mat = ET.SubElement(itemfeedback, 'flow_mat')
        material = ET.SubElement(flow_mat, 'material')
        mattext = ET.SubElement(material, 'mattext')
        mattext.set('texttype', 'text/html')
        mattext.text = f'<p><strong>Correct!</strong></p><p>{escape_html(question.rationale)}</p>'

        # Incorrect answer feedback
        itemfeedback_wrong = ET.SubElement(item, 'itemfeedback')
        itemfeedback_wrong.set('ident', f'incorrect_fb_{question.ident}')

        flow_mat = ET.SubElement(itemfeedback_wrong, 'flow_mat')
        material = ET.SubElement(flow_mat, 'material')
        mattext = ET.SubElement(material, 'mattext')
        mattext.set('texttype', 'text/html')

        # Build distractor feedback
        feedback_html = f'<p><strong>The correct answer is {question.correct_answer}.</strong></p>'
        feedback_html += f'<p>{escape_html(question.rationale)}</p>'

        if question.distractor_analysis:
            feedback_html += '<p><strong>Why other answers are incorrect:</strong></p><ul>'
            for letter, explanation in sorted(question.distractor_analysis.items()):
                if letter != question.correct_answer:
                    feedback_html += f'<li><strong>{letter}:</strong> {escape_html(explanation)}</li>'
            feedback_html += '</ul>'

        mattext.text = feedback_html

    return item


def escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#39;'))


def prettify_xml(elem: ET.Element) -> str:
    """Return a pretty-printed XML string for the Element."""
    rough_string = ET.tostring(elem, encoding='unicode')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent='  ')


def create_manifest(quizzes: List[Quiz], output_dir: Path) -> ET.Element:
    """Create IMS manifest file for Canvas package import."""
    manifest = ET.Element('manifest')
    manifest.set('identifier', f'psyc405_{uuid.uuid4().hex[:8]}')
    manifest.set('xmlns', 'http://www.imsglobal.org/xsd/imsccv1p1/imscp_v1p1')
    manifest.set('xmlns:lom', 'http://ltsc.ieee.org/xsd/imsccv1p1/LOM/resource')

    # Metadata
    metadata = ET.SubElement(manifest, 'metadata')
    schema = ET.SubElement(metadata, 'schema')
    schema.text = 'IMS Content'
    schemaversion = ET.SubElement(metadata, 'schemaversion')
    schemaversion.text = '1.1.3'

    # Organizations (empty for quiz package)
    organizations = ET.SubElement(manifest, 'organizations')

    # Resources
    resources = ET.SubElement(manifest, 'resources')

    for quiz in quizzes:
        resource = ET.SubElement(resources, 'resource')
        resource.set('identifier', quiz.ident)
        resource.set('type', 'imsqti_xmlv1p2')

        filename = f'quiz{quiz.quiz_number:02d}.xml'
        file_elem = ET.SubElement(resource, 'file')
        file_elem.set('href', filename)

    return manifest


def convert_section(section: str, base_dir: Path, output_dir: Path) -> List[Quiz]:
    """Convert all quizzes for a section to QTI format."""
    quiz_dir = base_dir / 'quizzes' / section
    answer_key_dir = base_dir / 'quizzes' / 'answer_keys'
    section_output_dir = output_dir / section

    if not quiz_dir.exists():
        print(f"Error: Quiz directory not found: {quiz_dir}")
        return []

    section_output_dir.mkdir(parents=True, exist_ok=True)

    quizzes = []
    quiz_files = sorted(quiz_dir.glob('quiz*.qmd'))

    for quiz_file in quiz_files:
        # Extract quiz number from filename
        match = re.search(r'quiz(\d+)', quiz_file.stem)
        if not match:
            continue
        quiz_num = int(match.group(1))

        print(f"  Processing {quiz_file.name}...")

        # Parse quiz file
        title, raw_questions = parse_quiz_file(quiz_file)

        # Parse answer key
        answer_key_file = answer_key_dir / f'{section}_quiz{quiz_num:02d}.md'
        answers = parse_answer_key(answer_key_file)

        # Create Quiz object
        quiz = Quiz(title=title, section=section, quiz_number=quiz_num)

        for q_num, q_text, choices in raw_questions:
            correct_answer, rationale, distractors = answers.get(q_num, ('', '', {}))

            if not correct_answer:
                print(f"    Warning: No answer key found for Question {q_num}")

            question = Question(
                number=q_num,
                text=q_text,
                choices=choices,
                correct_answer=correct_answer,
                rationale=rationale,
                distractor_analysis=distractors
            )
            quiz.questions.append(question)

        quizzes.append(quiz)

        # Generate QTI XML
        qti_root = create_qti_assessment(quiz)
        xml_content = prettify_xml(qti_root)

        output_file = section_output_dir / f'quiz{quiz_num:02d}.xml'
        output_file.write_text(xml_content, encoding='utf-8')
        print(f"    Created {output_file.name}")

    # Create manifest for the section
    manifest = create_manifest(quizzes, section_output_dir)
    manifest_content = prettify_xml(manifest)
    manifest_file = section_output_dir / 'imsmanifest.xml'
    manifest_file.write_text(manifest_content, encoding='utf-8')
    print(f"  Created manifest: {manifest_file.name}")

    return quizzes


def create_zip_package(section: str, output_dir: Path) -> Path:
    """Create a ZIP package for Canvas import from a section's QTI files."""
    section_dir = output_dir / section
    zip_path = output_dir / f'{section}_canvas_quizzes.zip'

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in section_dir.iterdir():
            if file.suffix == '.xml':
                zipf.write(file, file.name)

    return zip_path


def main():
    parser = argparse.ArgumentParser(
        description='Convert PSYC 405 quizzes to Canvas QTI format'
    )
    parser.add_argument(
        'section',
        nargs='?',
        help='Section to convert (e.g., spring2026_001) or --all'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Convert all sections'
    )
    parser.add_argument(
        '--zip',
        action='store_true',
        help='Create ZIP packages for Canvas import'
    )
    parser.add_argument(
        '--output-dir',
        default='canvas',
        help='Output directory for QTI files (default: canvas)'
    )

    args = parser.parse_args()

    # Determine base directory
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent
    output_dir = base_dir / args.output_dir

    print(f"PSYC 405 Quiz to Canvas QTI Converter")
    print(f"=====================================")
    print(f"Base directory: {base_dir}")
    print(f"Output directory: {output_dir}")
    print()

    if args.all:
        # Find all section directories
        quiz_base = base_dir / 'quizzes'
        sections = [d.name for d in quiz_base.iterdir()
                   if d.is_dir() and not d.name.startswith('answer')]
    elif args.section:
        sections = [args.section]
    else:
        parser.print_help()
        sys.exit(1)

    total_quizzes = 0
    zip_files = []

    for section in sorted(sections):
        print(f"Converting section: {section}")
        quizzes = convert_section(section, base_dir, output_dir)
        total_quizzes += len(quizzes)

        if args.zip and quizzes:
            zip_path = create_zip_package(section, output_dir)
            zip_files.append(zip_path)
            print(f"  Created ZIP: {zip_path.name}")

        print()

    print(f"Conversion complete!")
    print(f"  Total quizzes converted: {total_quizzes}")
    print(f"  Output location: {output_dir}")

    if zip_files:
        print(f"\nZIP packages created for Canvas import:")
        for zf in zip_files:
            print(f"  - {zf}")

    print()
    print("To import into Canvas:")
    print("  1. Go to your Canvas course")
    print("  2. Navigate to Settings > Import Course Content")
    print("  3. Select 'QTI .zip file'")
    if zip_files:
        print("  4. Upload the ZIP file (e.g., spring2026_001_canvas_quizzes.zip)")
    else:
        print("  4. Upload files from canvas/{section}/ (or re-run with --zip)")
    print("  5. Select 'All quizzes' during import")


if __name__ == '__main__':
    main()
