#!/usr/bin/env python3
"""
Convert PSYC 405 syllabus files (.qmd) to Canvas Common Cartridge format.

This script reads syllabus files and generates IMS Common Cartridge 1.3 packages
with 15 weekly modules containing film information, discussion questions, and quiz links.

Usage:
    python scripts/convert_to_canvas_cc.py spring2026_001
    python scripts/convert_to_canvas_cc.py --all
    python scripts/convert_to_canvas_cc.py --all --include-quizzes

The script will:
1. Parse syllabus .qmd files for schedule, films, and discussion questions
2. Generate HTML pages for each week's content
3. Create IMS Common Cartridge manifest
4. Package as .imscc ZIP file for Canvas import
"""

import argparse
import os
import re
import shutil
import sys
import uuid
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from xml.dom import minidom
from html import escape as html_escape


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class DiscussionQuestion:
    """A single discussion question with its governing area."""
    governing_area: str  # BELIEF, PURPOSE, MOTIVATION, etc.
    text: str


@dataclass
class Film:
    """Represents a film with metadata and discussion questions."""
    title: str
    year: int
    slug: str  # URL-safe identifier
    imdb_url: str = ""
    imdb_rating: str = ""
    rt_url: str = ""
    rt_score: str = ""
    wikipedia_url: str = ""
    themes: List[str] = field(default_factory=list)
    discussion_questions: List[DiscussionQuestion] = field(default_factory=list)


@dataclass
class WeekModule:
    """Represents a single week's Canvas module."""
    week_number: int
    module_name: str  # "Intro", "Mystery", "Madness", "Murder", "SPRING BREAK", "Epilogue"
    title: str  # Full week title
    films: List[Film] = field(default_factory=list)
    quiz_number: Optional[int] = None
    quiz_url: str = ""
    is_spring_break: bool = False
    is_transition: bool = False  # True for weeks covering two films


@dataclass
class CourseSection:
    """Full course section data."""
    section_id: str  # "spring2026_001"
    semester: str  # "Spring 2026"
    section_number: str  # "001"
    course_title: str
    meeting_time: str
    weeks: List[WeekModule] = field(default_factory=list)
    all_films: Dict[str, Film] = field(default_factory=dict)


# =============================================================================
# PARSING FUNCTIONS
# =============================================================================

def slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    slug = text.lower()
    slug = re.sub(r"[''`]", "", slug)  # Remove apostrophes
    slug = re.sub(r"[^a-z0-9]+", "_", slug)  # Replace non-alphanumeric
    slug = slug.strip("_")
    return slug


def parse_syllabus(filepath: Path) -> CourseSection:
    """Parse a .qmd syllabus file and extract all structured data."""
    content = filepath.read_text(encoding='utf-8')

    # Extract section info from filename (PSYC405_S2026_001.qmd)
    match = re.search(r'PSYC405_S(\d{4})_(\d{3})\.qmd', filepath.name)
    if match:
        year = match.group(1)
        section_num = match.group(2)
        section_id = f"spring{year}_{section_num}"
        semester = f"Spring {year}"
    else:
        section_id = "unknown_section"
        semester = "Unknown Semester"
        section_num = "000"

    # Extract title from YAML
    title_match = re.search(r'^title:\s*["\'](.+?)["\']', content, re.MULTILINE)
    course_title = title_match.group(1) if title_match else "PSYC 405"

    # Extract meeting time
    time_match = re.search(r'\(Section \d+\):\s*\*\*(.+?)\*\*', content)
    meeting_time = time_match.group(1) if time_match else ""

    section = CourseSection(
        section_id=section_id,
        semester=semester,
        section_number=section_num,
        course_title=course_title,
        meeting_time=meeting_time
    )

    # Parse film themes first
    film_themes = parse_film_themes(content)

    # Parse discussion questions
    film_discussions = parse_all_discussion_questions(content)

    # Parse schedule table
    section.weeks = parse_schedule_table(content, film_themes, film_discussions)

    # Build all_films dictionary
    for week in section.weeks:
        for film in week.films:
            section.all_films[film.slug] = film

    return section


def parse_film_themes(content: str) -> Dict[str, List[str]]:
    """Extract film themes from the 'Film Themes' section."""
    themes = {}

    # Find the Film Themes section
    themes_section = re.search(
        r'### Section \d+ Film Themes\s*\n(.*?)(?=\n## |\n### Film Resources|\Z)',
        content, re.DOTALL
    )

    if not themes_section:
        return themes

    section_text = themes_section.group(1)

    # Parse each film's themes (format: "- **Film Title** - theme1, theme2, theme3")
    film_pattern = re.compile(r'-\s*\*\*([^*]+)\*\*\s*-\s*(.+)')

    for match in film_pattern.finditer(section_text):
        film_title = match.group(1).strip()
        theme_text = match.group(2).strip()
        theme_list = [t.strip() for t in theme_text.split(',')]
        themes[film_title] = theme_list

    return themes


def parse_all_discussion_questions(content: str) -> Dict[str, List[DiscussionQuestion]]:
    """Extract all discussion questions organized by film title."""
    discussions = {}

    # Find each film's discussion section
    # Pattern: "#### Film Title (Year)\n**Links:**...\n::: {.callout-tip}\n## Discussion Questions\n..."
    film_sections = re.split(r'\n####\s+', content)

    for section in film_sections[1:]:  # Skip content before first ####
        # Extract film title
        title_match = re.match(r'([^(\n]+)\s*\((\d{4})\)', section)
        if not title_match:
            continue

        film_title = title_match.group(1).strip()

        # Find discussion questions callout
        callout_match = re.search(
            r'::: \{\.callout-tip\}\s*\n## Discussion Questions\s*\n(.*?)\n:::',
            section, re.DOTALL
        )

        if not callout_match:
            continue

        questions_text = callout_match.group(1)
        questions = []

        # Parse numbered questions with governing areas
        # Format: "1. **BELIEF:** Question text here?"
        q_pattern = re.compile(r'\d+\.\s*\*\*(\w+):\*\*\s*(.+?)(?=\n\d+\.|\Z)', re.DOTALL)

        for q_match in q_pattern.finditer(questions_text):
            area = q_match.group(1).strip()
            text = q_match.group(2).strip()
            questions.append(DiscussionQuestion(governing_area=area, text=text))

        discussions[film_title] = questions

    return discussions


def parse_schedule_table(content: str, themes: Dict[str, List[str]],
                         discussions: Dict[str, List[DiscussionQuestion]]) -> List[WeekModule]:
    """Parse the schedule table and build week modules."""
    weeks = []

    # Find the schedule table
    table_match = re.search(
        r'\| Week \| Module \| Film \| Assessment \|\s*\n\|[:\-\|]+\|\s*\n(.*?)(?=\n\n|\n\[|\Z)',
        content, re.DOTALL
    )

    if not table_match:
        return weeks

    table_content = table_match.group(1)

    # Parse each row by splitting lines and handling escaped pipes
    for line in table_content.strip().split('\n'):
        line = line.strip()
        if not line or not line.startswith('|'):
            continue

        # Split by unescaped pipes: first replace \| with placeholder, split, then restore
        placeholder = '\x00PIPE\x00'
        temp_line = line.replace('\\|', placeholder)
        cells = [c.strip().replace(placeholder, '\\|') for c in temp_line.split('|')]
        # Remove empty first/last cells from leading/trailing pipes
        cells = [c for c in cells if c]

        if len(cells) < 4:
            continue

        # Try to parse week number
        try:
            week_num = int(cells[0])
        except ValueError:
            continue

        module_name = cells[1].strip()
        film_cell = cells[2].strip()
        assessment_cell = cells[3].strip()

        # Unescape the pipes for content processing
        film_cell = film_cell.replace('\\|', '|')
        assessment_cell = assessment_cell.replace('\\|', '|')

        # Check for spring break
        is_spring_break = "SPRING BREAK" in module_name.upper() or "R-E-L-A-X" in film_cell

        # Parse films from the film cell
        films = parse_film_cell(film_cell, themes, discussions)

        # Check if this is a transition week (two films)
        is_transition = "/" in film_cell and len(films) == 2

        # Parse quiz number
        quiz_match = re.search(r'\[Quiz\s*(\d+)\]', assessment_cell)
        quiz_number = int(quiz_match.group(1)) if quiz_match else None

        # Parse quiz URL
        quiz_url_match = re.search(r'\[Quiz\s*\d+\]\(([^)]+)\)', assessment_cell)
        quiz_url = quiz_url_match.group(1) if quiz_url_match else ""

        # Build title
        if is_spring_break:
            title = "SPRING BREAK - No Classes"
        elif films:
            film_titles = " / ".join(f.title for f in films)
            title = f"{module_name}: {film_titles}"
        else:
            title = film_cell

        week = WeekModule(
            week_number=week_num,
            module_name=module_name,
            title=title,
            films=films,
            quiz_number=quiz_number,
            quiz_url=quiz_url,
            is_spring_break=is_spring_break,
            is_transition=is_transition
        )
        weeks.append(week)

    return weeks


def parse_film_cell(cell: str, themes: Dict[str, List[str]],
                    discussions: Dict[str, List[DiscussionQuestion]]) -> List[Film]:
    """Parse film information from a schedule table cell."""
    films = []

    # Pattern for film with full links (handles {target="_blank"} attributes):
    # [Title](imdb_url){target="_blank"} (year) 🎬 rating | [🍅 score%](rt_url){target="_blank"} | [📖](wiki_url){target="_blank"}
    # Note: pipes are already unescaped at this point
    film_pattern = re.compile(
        r'\[([^\]]+)\]\((https://www\.imdb\.com/[^)]+)\)(?:\{[^}]*\})?\s*\((\d{4})\)\s*'
        r'🎬\s*([\d.]+)\s*'
        r'\|\s*\[🍅\s*(\d+%)\]\(([^)]+)\)(?:\{[^}]*\})?\s*'
        r'\|\s*\[📖\]\(([^)]+)\)(?:\{[^}]*\})?'
    )

    # Also handle simpler references (just film title without full links)
    simple_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)\s*\((\d{4})\)')

    for match in film_pattern.finditer(cell):
        title = match.group(1).strip()
        imdb_url = match.group(2)
        year = int(match.group(3))
        imdb_rating = match.group(4)
        rt_score = match.group(5)
        rt_url = match.group(6)
        wiki_url = match.group(7)

        film = Film(
            title=title,
            year=year,
            slug=slugify(title),
            imdb_url=imdb_url,
            imdb_rating=imdb_rating,
            rt_url=rt_url,
            rt_score=rt_score,
            wikipedia_url=wiki_url,
            themes=themes.get(title, []),
            discussion_questions=discussions.get(title, [])
        )
        films.append(film)

    # If no full pattern matches found, try simpler pattern
    if not films:
        for match in simple_pattern.finditer(cell):
            title = match.group(1).strip()
            url = match.group(2)
            year = int(match.group(3))

            # Only create if it looks like an IMDB URL
            if 'imdb.com' in url:
                film = Film(
                    title=title,
                    year=year,
                    slug=slugify(title),
                    imdb_url=url,
                    themes=themes.get(title, []),
                    discussion_questions=discussions.get(title, [])
                )
                films.append(film)

    return films


# =============================================================================
# HTML GENERATORS
# =============================================================================

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
               line-height: 1.6; max-width: 900px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #006633; border-bottom: 2px solid #FFCC33; padding-bottom: 10px; }}
        h2 {{ color: #006633; }}
        h3 {{ color: #333; }}
        .metadata {{ background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 20px 0; }}
        .metadata p {{ margin: 5px 0; }}
        .themes {{ background: #e8f4e8; padding: 15px; border-radius: 8px; margin: 20px 0; }}
        .themes ul {{ margin: 10px 0; padding-left: 20px; }}
        .discussion {{ margin: 20px 0; }}
        .discussion-question {{ background: #fff9e6; padding: 15px; border-left: 4px solid #FFCC33;
                               margin: 15px 0; border-radius: 0 8px 8px 0; }}
        .discussion-question h4 {{ color: #006633; margin-top: 0; }}
        .activities {{ background: #e6f3ff; padding: 15px; border-radius: 8px; margin: 20px 0; }}
        .activities ul {{ margin: 10px 0; padding-left: 20px; }}
        a {{ color: #006633; }}
        .spring-break {{ background: #ffe6e6; padding: 30px; border-radius: 8px; text-align: center; }}
        .links {{ margin: 15px 0; }}
        .links a {{ margin-right: 15px; }}
    </style>
</head>
<body>
{content}
</body>
</html>
"""


def generate_overview_html(week: WeekModule, section: CourseSection) -> str:
    """Generate HTML content for a week's overview page."""
    if week.is_spring_break:
        content = f"""
<h1>Week {week.week_number}: {week.module_name}</h1>
<div class="spring-break">
    <h2>🌴 SPRING BREAK 🌴</h2>
    <p><strong>March 9-15, 2026</strong></p>
    <p>No classes this week. Enjoy your break!</p>
    <p>Classes resume the following week.</p>
</div>
"""
    else:
        film_list = ""
        if week.films:
            film_items = "\n".join(
                f"        <li>Watch: <strong>{f.title}</strong> ({f.year})</li>"
                for f in week.films
            )
            film_list = f"\n{film_items}"

        quiz_item = ""
        if week.quiz_number:
            quiz_item = f"\n        <li>Complete: <strong>Quiz {week.quiz_number}</strong></li>"

        discussion_item = ""
        if week.films and any(f.discussion_questions for f in week.films):
            discussion_item = "\n        <li>Prepare: Review discussion questions before class</li>"

        content = f"""
<h1>Week {week.week_number}: {week.module_name}</h1>
<h2>{week.title}</h2>

<div class="metadata">
    <p><strong>Section:</strong> {section.section_number}</p>
    <p><strong>Meeting Time:</strong> {section.meeting_time}</p>
</div>

<div class="activities">
    <h3>This Week's Activities</h3>
    <ul>{film_list}{discussion_item}{quiz_item}
        <li>Engage: Participate in class discussion</li>
    </ul>
</div>
"""

        # Add links to film pages
        if week.films:
            content += "\n<h3>Film Guides</h3>\n<ul>\n"
            for film in week.films:
                content += f'    <li><a href="{film.slug}.html">{film.title} ({film.year})</a></li>\n'
            content += "</ul>\n"

    return HTML_TEMPLATE.format(title=f"Week {week.week_number} Overview", content=content)


def generate_film_html(film: Film) -> str:
    """Generate HTML page with film info and links."""
    # External links
    links_html = '<div class="links">'
    if film.imdb_url:
        rating = f" ({film.imdb_rating}/10)" if film.imdb_rating else ""
        links_html += f'<a href="{html_escape(film.imdb_url)}" target="_blank">🎬 IMDB{rating}</a>'
    if film.rt_url:
        score = f" ({film.rt_score})" if film.rt_score else ""
        links_html += f'<a href="{html_escape(film.rt_url)}" target="_blank">🍅 Rotten Tomatoes{score}</a>'
    if film.wikipedia_url:
        links_html += f'<a href="{html_escape(film.wikipedia_url)}" target="_blank">📖 Wikipedia</a>'
    links_html += '</div>'

    # Themes
    themes_html = ""
    if film.themes:
        theme_items = "\n".join(f"    <li>{html_escape(t)}</li>" for t in film.themes)
        themes_html = f"""
<div class="themes">
    <h2>Psychological Themes</h2>
    <ul>
{theme_items}
    </ul>
</div>
"""

    # Governing areas summary
    if film.discussion_questions:
        areas = list(set(q.governing_area for q in film.discussion_questions))
        areas_text = ", ".join(areas)
        governing_html = f"""
<div class="metadata">
    <h3>Governing Areas of Inquiry</h3>
    <p>This film engages: <strong>{html_escape(areas_text)}</strong></p>
</div>
"""
    else:
        governing_html = ""

    content = f"""
<h1>{html_escape(film.title)} ({film.year})</h1>

{links_html}

{themes_html}

{governing_html}
"""

    return HTML_TEMPLATE.format(title=f"{film.title} ({film.year})", content=content)


def generate_discussion_html(week: WeekModule) -> str:
    """Generate HTML page with discussion questions (read-only)."""
    questions_html = ""

    for film in week.films:
        if not film.discussion_questions:
            continue

        questions_html += f'<h2>{html_escape(film.title)}</h2>\n'

        for i, q in enumerate(film.discussion_questions, 1):
            questions_html += f"""
<div class="discussion-question">
    <h4>{i}. {html_escape(q.governing_area)}</h4>
    <p>{html_escape(q.text)}</p>
</div>
"""

    if not questions_html:
        questions_html = "<p>No discussion questions for this week.</p>"

    content = f"""
<h1>Discussion Questions: Week {week.week_number}</h1>
<p><em>Use these questions to guide your thinking before and during class discussion.</em></p>

<div class="discussion">
{questions_html}
</div>
"""

    return HTML_TEMPLATE.format(title=f"Week {week.week_number} Discussion Questions", content=content)


def generate_readings_html(week: WeekModule) -> str:
    """Generate HTML page with weekly reading references."""
    # For now, create a placeholder that links to the main readings page
    # In the future, this could parse READINGS.qmd for specific themes

    areas = set()
    for film in week.films:
        for q in film.discussion_questions:
            areas.add(q.governing_area)

    areas_list = ""
    if areas:
        items = "\n".join(f"        <li>{html_escape(a)}</li>" for a in sorted(areas))
        areas_list = f"""
<h3>Related Themes</h3>
<ul>
{items}
</ul>
"""

    content = f"""
<h1>Week {week.week_number} Readings</h1>

<div class="metadata">
    <p>Access course readings through our Zotero library:</p>
    <p><a href="https://www.zotero.org/groups/6375337/psyc_-mystery_madness_murder/library" target="_blank">
        📚 PSYC 405 Zotero Library
    </a></p>
</div>

{areas_list}

<p>Focus on readings related to the themes covered in this week's film(s).</p>
"""

    return HTML_TEMPLATE.format(title=f"Week {week.week_number} Readings", content=content)


# =============================================================================
# COMMON CARTRIDGE MANIFEST
# =============================================================================

def create_imsmanifest(section: CourseSection, include_quizzes: bool = False) -> ET.Element:
    """Create IMS Common Cartridge 1.3 manifest."""
    # Namespaces
    nsmap = {
        '': 'http://www.imsglobal.org/xsd/imsccv1p3/imscp_v1p1',
        'lom': 'http://ltsc.ieee.org/xsd/imsccv1p3/LOM/resource',
        'lomimscc': 'http://ltsc.ieee.org/xsd/imsccv1p3/LOM/manifest'
    }

    manifest = ET.Element('manifest')
    manifest.set('xmlns', nsmap[''])
    manifest.set('xmlns:lom', nsmap['lom'])
    manifest.set('xmlns:lomimscc', nsmap['lomimscc'])
    manifest.set('identifier', f'psyc405_{section.section_id}')

    # Metadata
    metadata = ET.SubElement(manifest, 'metadata')
    schema = ET.SubElement(metadata, 'schema')
    schema.text = 'IMS Common Cartridge'
    schemaversion = ET.SubElement(metadata, 'schemaversion')
    schemaversion.text = '1.3.0'

    # LOM metadata for title
    lom = ET.SubElement(metadata, '{%s}lom' % nsmap['lomimscc'])
    general = ET.SubElement(lom, '{%s}general' % nsmap['lomimscc'])
    title_elem = ET.SubElement(general, '{%s}title' % nsmap['lomimscc'])
    string_elem = ET.SubElement(title_elem, '{%s}string' % nsmap['lomimscc'])
    string_elem.text = f"{section.course_title} - Section {section.section_number}"

    # Organizations (module structure)
    organizations = ET.SubElement(manifest, 'organizations')
    organization = ET.SubElement(organizations, 'organization')
    organization.set('identifier', 'org_1')
    organization.set('structure', 'rooted-hierarchy')

    root_item = ET.SubElement(organization, 'item')
    root_item.set('identifier', 'root')

    # Resources
    resources = ET.SubElement(manifest, 'resources')

    # Build modules for each week
    for week in section.weeks:
        week_id = f'week_{week.week_number:02d}'

        # Module item
        module_item = ET.SubElement(root_item, 'item')
        module_item.set('identifier', f'{week_id}_module')
        module_title = ET.SubElement(module_item, 'title')
        module_title.text = f"Week {week.week_number}: {week.module_name}"

        # Overview page
        overview_item = ET.SubElement(module_item, 'item')
        overview_item.set('identifier', f'{week_id}_overview')
        overview_item.set('identifierref', f'res_{week_id}_overview')
        overview_title = ET.SubElement(overview_item, 'title')
        overview_title.text = f"Week {week.week_number} Overview"

        add_resource(resources, f'res_{week_id}_overview', f'week{week.week_number:02d}/overview.html')

        if week.is_spring_break:
            continue

        # Film pages
        for film in week.films:
            film_item = ET.SubElement(module_item, 'item')
            film_item.set('identifier', f'{week_id}_{film.slug}')
            film_item.set('identifierref', f'res_{film.slug}')
            film_title_elem = ET.SubElement(film_item, 'title')
            film_title_elem.text = f"{film.title} ({film.year})"

            add_resource(resources, f'res_{film.slug}', f'week{week.week_number:02d}/{film.slug}.html')

        # Discussion questions page
        if week.films and any(f.discussion_questions for f in week.films):
            disc_item = ET.SubElement(module_item, 'item')
            disc_item.set('identifier', f'{week_id}_discussion')
            disc_item.set('identifierref', f'res_{week_id}_discussion')
            disc_title = ET.SubElement(disc_item, 'title')
            disc_title.text = "Discussion Questions"

            add_resource(resources, f'res_{week_id}_discussion', f'week{week.week_number:02d}/discussion.html')

        # Readings page
        readings_item = ET.SubElement(module_item, 'item')
        readings_item.set('identifier', f'{week_id}_readings')
        readings_item.set('identifierref', f'res_{week_id}_readings')
        readings_title = ET.SubElement(readings_item, 'title')
        readings_title.text = "Readings"

        add_resource(resources, f'res_{week_id}_readings', f'week{week.week_number:02d}/readings.html')

        # Quiz reference
        if week.quiz_number and include_quizzes:
            quiz_item = ET.SubElement(module_item, 'item')
            quiz_item.set('identifier', f'{week_id}_quiz')
            quiz_item.set('identifierref', f'res_quiz_{week.quiz_number:02d}')
            quiz_title = ET.SubElement(quiz_item, 'title')
            quiz_title.text = f"Quiz {week.quiz_number}"

            add_resource(resources, f'res_quiz_{week.quiz_number:02d}',
                        f'quizzes/quiz{week.quiz_number:02d}.xml',
                        resource_type='imsqti_xmlv1p2')

    return manifest


def add_resource(resources: ET.Element, identifier: str, href: str,
                 resource_type: str = 'webcontent') -> None:
    """Add a resource entry to the manifest."""
    resource = ET.SubElement(resources, 'resource')
    resource.set('identifier', identifier)
    resource.set('type', resource_type)
    resource.set('href', href)

    file_elem = ET.SubElement(resource, 'file')
    file_elem.set('href', href)


def prettify_xml(elem: ET.Element) -> str:
    """Return a pretty-printed XML string."""
    rough_string = ET.tostring(elem, encoding='unicode')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent='  ')


# =============================================================================
# PACKAGING
# =============================================================================

def generate_course_files(section: CourseSection, output_dir: Path,
                          include_quizzes: bool = False) -> None:
    """Generate all HTML files and manifest for a course section."""
    section_dir = output_dir / section.section_id

    # Create directory structure
    for week in section.weeks:
        week_dir = section_dir / f'week{week.week_number:02d}'
        week_dir.mkdir(parents=True, exist_ok=True)

        # Generate overview page
        overview_html = generate_overview_html(week, section)
        (week_dir / 'overview.html').write_text(overview_html, encoding='utf-8')
        print(f"    Created week{week.week_number:02d}/overview.html")

        if week.is_spring_break:
            continue

        # Generate film pages
        for film in week.films:
            film_html = generate_film_html(film)
            (week_dir / f'{film.slug}.html').write_text(film_html, encoding='utf-8')
            print(f"    Created week{week.week_number:02d}/{film.slug}.html")

        # Generate discussion page
        if week.films and any(f.discussion_questions for f in week.films):
            discussion_html = generate_discussion_html(week)
            (week_dir / 'discussion.html').write_text(discussion_html, encoding='utf-8')
            print(f"    Created week{week.week_number:02d}/discussion.html")

        # Generate readings page
        readings_html = generate_readings_html(week)
        (week_dir / 'readings.html').write_text(readings_html, encoding='utf-8')
        print(f"    Created week{week.week_number:02d}/readings.html")

    # Copy quiz files if requested
    if include_quizzes:
        quiz_src = output_dir / section.section_id
        quiz_dest = section_dir / 'quizzes'

        # Check if QTI files exist in the section directory already
        existing_quiz_dir = output_dir / section.section_id
        qti_files = list(existing_quiz_dir.glob('quiz*.xml'))

        if qti_files:
            quiz_dest.mkdir(exist_ok=True)
            for qti_file in qti_files:
                shutil.copy(qti_file, quiz_dest / qti_file.name)
                print(f"    Copied {qti_file.name} to quizzes/")

    # Generate manifest
    manifest = create_imsmanifest(section, include_quizzes)
    manifest_xml = prettify_xml(manifest)
    (section_dir / 'imsmanifest.xml').write_text(manifest_xml, encoding='utf-8')
    print(f"    Created imsmanifest.xml")


def create_cartridge_package(section: CourseSection, output_dir: Path) -> Path:
    """Create .imscc ZIP package for Canvas import."""
    section_dir = output_dir / section.section_id
    package_path = output_dir / f'{section.section_id}_course.imscc'

    with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(section_dir):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(section_dir)
                zipf.write(file_path, arcname)

    return package_path


# =============================================================================
# MAIN
# =============================================================================

def find_syllabus_file(section_id: str, base_dir: Path) -> Optional[Path]:
    """Find the syllabus file for a given section ID."""
    # Parse section_id (e.g., "spring2026_001")
    match = re.match(r'(spring|fall)(\d{4})_(\d{3})', section_id)
    if not match:
        return None

    semester = match.group(1).capitalize()
    year = match.group(2)
    section = match.group(3)

    # Build expected filename
    semester_code = 'S' if semester.lower() == 'spring' else 'F'
    filename = f'PSYC405_{semester_code}{year}_{section}.qmd'

    filepath = base_dir / filename
    return filepath if filepath.exists() else None


def convert_section(section_id: str, base_dir: Path, output_dir: Path,
                    include_quizzes: bool = False) -> Optional[CourseSection]:
    """Convert a single course section to Common Cartridge format."""
    syllabus_file = find_syllabus_file(section_id, base_dir)

    if not syllabus_file:
        print(f"Error: Syllabus file not found for section {section_id}")
        return None

    print(f"  Parsing {syllabus_file.name}...")
    section = parse_syllabus(syllabus_file)

    print(f"  Found {len(section.weeks)} weeks, {len(section.all_films)} films")

    print(f"  Generating HTML pages...")
    generate_course_files(section, output_dir, include_quizzes)

    print(f"  Creating .imscc package...")
    package_path = create_cartridge_package(section, output_dir)
    print(f"  Created: {package_path.name}")

    return section


def main():
    parser = argparse.ArgumentParser(
        description='Convert PSYC 405 syllabi to Canvas Common Cartridge format'
    )
    parser.add_argument(
        'section',
        nargs='?',
        help='Section to convert (e.g., spring2026_001)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Convert all available sections'
    )
    parser.add_argument(
        '--include-quizzes',
        action='store_true',
        help='Include QTI quiz files in the package'
    )
    parser.add_argument(
        '--output-dir',
        default='canvas',
        help='Output directory (default: canvas)'
    )

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    base_dir = script_dir.parent
    output_dir = base_dir / args.output_dir

    print("PSYC 405 Syllabus to Canvas Common Cartridge Converter")
    print("======================================================")
    print(f"Base directory: {base_dir}")
    print(f"Output directory: {output_dir}")
    print()

    if args.all:
        # Find all syllabus files
        syllabus_files = list(base_dir.glob('PSYC405_S*_*.qmd'))
        sections = []
        for sf in syllabus_files:
            match = re.search(r'PSYC405_S(\d{4})_(\d{3})\.qmd', sf.name)
            if match:
                sections.append(f"spring{match.group(1)}_{match.group(2)}")
    elif args.section:
        sections = [args.section]
    else:
        parser.print_help()
        sys.exit(1)

    total_sections = 0
    for section_id in sorted(sections):
        print(f"Converting section: {section_id}")
        result = convert_section(section_id, base_dir, output_dir, args.include_quizzes)
        if result:
            total_sections += 1
        print()

    print(f"Conversion complete!")
    print(f"  Sections converted: {total_sections}")
    print(f"  Output location: {output_dir}")
    print()
    print("To import into Canvas:")
    print("  1. Go to your Canvas course")
    print("  2. Navigate to Settings > Import Course Content")
    print("  3. Select 'Common Cartridge 1.x Package'")
    print("  4. Upload the .imscc file (e.g., spring2026_001_course.imscc)")
    print("  5. Select 'All content' or choose specific modules")


if __name__ == '__main__':
    main()
