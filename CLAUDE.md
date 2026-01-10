# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an academic course repository for PSYC 405: Mystery, Madness & Murder at George Mason University. The repository contains course materials including syllabi, timeline content, and course structure documents, all written in Quarto Markdown (.qmd) format and rendered to multiple output formats (HTML, PDF, DOCX).

## Architecture

### Document Structure
- **Core Documents**: Syllabus files (`PSYC405syllabus.qmd`, `corrected_syllabus.qmd`, `updated_syllabus.qmd`)
- **Course Content**: Timeline (`timeline.qmd`), course structure (`course_structure.qmd`), and case study materials (`Diabolique.qmd`)
- **Data Files**: CSV files containing movie metadata and reviews (`diabolique_1955_metadata.csv`, `diabolique_1955_reviews.csv`)
- **References**: Bibliography file (`references.bib`)

### Output Generation
Documents are rendered from .qmd source files to multiple formats:
- HTML files with Bootstrap-based styling and Quarto JavaScript libraries
- PDF and DOCX versions for distribution
- Associated asset directories (`*_files/`) containing CSS, JavaScript, and other resources

## Common Commands

### Document Rendering
```bash
# Render a single document to all formats
quarto render filename.qmd

# Render to specific format
quarto render filename.qmd --to html
quarto render filename.qmd --to pdf
quarto render filename.qmd --to docx

# Preview document with live reload
quarto preview filename.qmd
```

### Publishing
The repository uses Netlify for publication as configured in `_publish.yml`:
```bash
# Publish to Netlify (if configured)
quarto publish netlify
```

## Working with Course Content

### Document Headers
All .qmd files follow a consistent YAML header structure:
```yaml
---
title: "Document Title"
subtitle: "Optional subtitle"
author: "Patrick E. McKnight"
format:
  html:
    toc: true
    toc_float: true
  pdf: default
  docx: default
---
```

### Content Organization
- Course materials reference a detailed timeline in `README.md` covering historical events from ancient times to the 21st century
- Character profiles include philosophers, psychologists, cognitive scientists, and historical figures
- The course integrates psychological science with real and fictional behavioral analysis

## File Management

### Git Workflow
Current branch status shows modified `_publish.yml` and several untracked corrected syllabus files. When making changes:
- Stage relevant files before committing
- Be mindful of rendered output files (HTML, PDF) which may not need version control

### Asset Management
- Images (like `20130820_123617.jpg`) are referenced directly in .qmd files
- Rendered assets are automatically organized in `*_files/` directories
- Bootstrap and Quarto libraries are included in output directories

## Development Notes

- This is primarily a content repository, not a software project
- No traditional build/test/lint commands - document rendering serves this purpose
- Focus on content accuracy and proper Quarto formatting
- When editing .qmd files, ensure YAML headers remain properly formatted

## Zotero Library Integration

The course maintains a public Zotero library for academic readings that syncs to this repository.

### Zotero Library Details
- **Library URL:** https://www.zotero.org/groups/6375337/psyc_-mystery_madness_murder/library
- **Group ID:** 6375337
- **API Endpoint:** `https://api.zotero.org/groups/6375337/items?format=bibtex&limit=100`

### Syncing Workflow

When the user asks to "sync" or "update" readings from Zotero:

1. **Fetch latest BibTeX:**
   ```
   WebFetch: https://api.zotero.org/groups/6375337/items?format=bibtex&limit=100
   ```

2. **Compare with existing `references.bib`:**
   - Identify NEW entries not already in the file
   - Note any entries that need updating

3. **Update `references.bib`:**
   - Add new entries to appropriate theme sections:
     - BELIEF - Why People Believe Weird Things
     - PURPOSE - Purpose in Life & Well-Being
     - EMOTION - Emotion Regulation
     - MOTIVATION - Social Dominance
     - UNCERTAINTY - Deception Detection
     - MURDER - Psychopathy, Criminal Responsibility, Mens Rea
   - Remove duplicate entries (Zotero sometimes exports with `-1` suffixes)
   - Update the "Last synced" date in the file header

4. **Update `READINGS.qmd`:**
   - Add new readings to the appropriate theme section
   - Include author, year, title, journal, and DOI link
   - Add brief description of the reading's relevance

5. **Render and commit:**
   ```bash
   quarto render READINGS.qmd
   git add references.bib READINGS.qmd
   git commit -m "Sync references.bib with Zotero library - [describe new entries]"
   git push
   ```

### File Locations
- **BibTeX file:** `references.bib`
- **Readings page:** `READINGS.qmd`
- **Rendered output:** `_site/READINGS.html`

### Adding New Theme Sections

If new readings don't fit existing themes, create a new section in both files:
1. Add `% ====... THEME_NAME ...====` section header in `references.bib`
2. Add corresponding `### THEME_NAME:` section in `READINGS.qmd`

## Quiz Generation Workflow

The course uses weekly quizzes that integrate film content with psychological science from the Zotero library.

### Quiz Directory Structure

Quizzes are organized by semester, year, and section:
```
quizzes/
├── spring2026_001/          # Spring 2026, Section 001
│   ├── quiz01_intro.qmd
│   ├── quiz02_shutter_island.qmd
│   └── ...
├── spring2026_002/          # Spring 2026, Section 002
│   ├── quiz01_intro.qmd
│   ├── quiz02_machinist.qmd
│   └── ...
└── ANSWER_KEY_CONFIDENTIAL.md  # NEVER COMMIT - gitignored
```

### Directory Naming Convention
Format: `{semester}{year}_{section}`
- Examples: `spring2026_001`, `fall2026_001`, `spring2027_002`

### Generating New Quizzes

When creating quizzes for a new semester:

1. **Create directory structure:**
   ```bash
   mkdir -p quizzes/{semester}{year}_{section}
   ```

2. **Generate quiz files:**
   - 14 quizzes per section (one per week)
   - 5 questions per quiz
   - Questions must integrate BOTH film content AND psychological science
   - Each question requires knowledge of the movie AND Zotero readings
   - Make questions difficult - no simple recall

3. **Quiz file format:**
   ```markdown
   ---
   title: "Quiz N: Topic"
   subtitle: "PSYC 405 - Section XXX"
   format:
     html:
       toc: false
   ---

   ## Question 1
   Question text here...

   A. Answer choice A
   B. Answer choice B
   C. Answer choice C
   D. Answer choice D
   E. Answer choice E
   ```

4. **Create answer key (LOCAL ONLY):**

   **Directory Structure:**
   ```
   quizzes/answer_keys/                    # gitignored - NEVER commit
   ├── ANSWER_KEY_INDEX.md                 # Quick reference with all answers
   ├── spring2026_001_quiz01.md            # Section 001 quizzes
   ├── spring2026_001_quiz02.md
   ├── ...
   ├── spring2026_002_quiz01.md            # Section 002 quizzes
   ├── spring2026_002_quiz02.md
   └── ...
   ```

   **File Naming Convention:** `{semester}{year}_{section}_quiz{number}.md`
   - Examples: `spring2026_001_quiz01.md`, `fall2027_002_quiz14.md`

   **Required elements for EACH question:**

   ```markdown
   ### Question N

   **Question:** [Full question text exactly as it appears in the quiz]

   **Answer Choices:**
   - A) [Option A text]
   - B) [Option B text] ✓  (mark correct with ✓)
   - C) [Option C text]
   - D) [Option D text]

   **Correct Answer: [Letter]**

   **Rationale for Correct Answer:**
   [Explain WHY this answer is correct. Cite specific research,
   explain the psychological mechanism, and connect to course concepts.]

   **Distractor Analysis:**
   - **A** ([brief label]) - [Why this wrong answer is appealing but incorrect]
   - **C** ([brief label]) - [Why this wrong answer is appealing but incorrect]
   - **D** ([brief label]) - [Why this wrong answer is appealing but incorrect]

   **Course Connection:**
   - **Film:** [Which film(s) the question relates to and specific scenes/characters]
   - **Readings:** [Which Zotero readings inform the question - cite author(s) and year]
   - **Integration:** [How the question requires combining BOTH film AND reading knowledge]
   ```

   This format ensures:
   - Instructors can discuss any question in class with full context
   - The rationale explains not just WHAT is correct but WHY
   - Students who ask about questions can receive meaningful explanations
   - Question quality can be evaluated for future revisions
   - Portable via USB or cloud storage (all links are relative within directory)

5. **Update configuration files:**
   - Add quiz directory to `_quarto.yml` render list
   - Update `QUIZZES.qmd` with links to new quizzes
   - Update syllabus with quiz links

6. **Link quizzes in syllabus:**
   - Each week's assessment should link directly to the quiz
   - Format: `[Quiz N](quizzes/{semester}{year}_{section}/quizNN_topic.html)`

### Quiz Content Guidelines

- **Integration requirement:** Every question must require knowledge of BOTH the film AND the psychological science
- **Distractor quality:** Wrong answers should represent common misconceptions
- **Difficulty level:** High - students must watch actively AND read the literature
- **Source materials:**
  - Films listed in the syllabus
  - Readings from Zotero library (https://www.zotero.org/groups/6375337/psyc_-mystery_madness_murder/library)

### Canvas Integration

Quizzes are also uploaded to Canvas for grading. The Markdown format allows easy copy/paste to Canvas quiz builder.

## Movie Metadata Standards

### Required Information for Each Film

When adding films to syllabi, include:
- **IMDB link and rating:** Film title links to IMDB, followed by 🎬 emoji and rating
- **Rotten Tomatoes link and score:** 🍅 emoji with percentage linking to RT page
- **Wikipedia link:** 📖 emoji linking to Wikipedia article
- **Release year:** Include in parentheses after title
- **CRITICAL:** ALL external links must include `{target="_blank"}` to open in new tabs

### Emoji Legend
| Emoji | Source | Usage |
|-------|--------|-------|
| 🎬 | IMDB | Placed before rating (e.g., 🎬 8.2) |
| 🍅 | Rotten Tomatoes | Linked with percentage (e.g., [🍅 69%](url)) |
| 📖 | Wikipedia | Linked standalone (e.g., [📖](url)) |

### Example Format (Schedule Tables)
```markdown
[Shutter Island](https://www.imdb.com/title/tt1130884/){target="_blank"} (2010) 🎬 8.2 \| [🍅 69%](https://www.rottentomatoes.com/m/1198124-shutter_island){target="_blank"} \| [📖](https://en.wikipedia.org/wiki/Shutter_Island_(film)){target="_blank"}
```

### Example Format (Film Resources Section)
```markdown
**Links:** [🎬 IMDB](https://www.imdb.com/title/tt1130884/){target="_blank"} (8.2/10) | [🍅 Rotten Tomatoes](https://www.rottentomatoes.com/m/1198124-shutter_island){target="_blank"} (69%) | [📖 Wikipedia](https://en.wikipedia.org/wiki/Shutter_Island_(film)){target="_blank"}
```

### Link Standards

**ALL links must open in new tabs.** This applies to:
- Quiz links in schedule tables
- Movie links (IMDB, Rotten Tomatoes, Wikipedia)
- External resource links
- Zotero library links

Format: `[Link Text](URL){target="_blank"}`

## Website Information

- **Live Site:** https://gmu-psyc405.netlify.app/
- **Hosting:** Netlify (auto-deploys on push to main)
- **Navigation:** Configured in `_quarto.yml`

### Key Pages
- Home: `index.qmd`
- Current Syllabi: `PSYC405_S2026_001.qmd`, `PSYC405_S2026_002.qmd`
- Previous Syllabi: `updated_syllabus.qmd`, `PSYC405syllabus.qmd`
- Film History: `FILM_HISTORY.qmd`
- Readings: `READINGS.qmd`
- Past Reviews: `PAST_REVIEWS.qmd`

### External Link Convention
All external links should include `{target="_blank"}` to open in new tabs:
```markdown
[Link Text](https://example.com){target="_blank"}
```

## Future TODOs (Workflow Improvements)

### 1. Movie Suggestions
- Develop a system to suggest new films based on psychological themes
- Track which psychological concepts are underrepresented in current film selection
- Consider student feedback when selecting new films
- Maintain diversity across genres, decades, and psychological domains

### 2. Zotero Library Sync
- Sync with Zotero library at the start of each semester
- Identify new readings that could enhance quiz content
- Expand readings to cover emerging psychological science
- Ensure all quiz questions have supporting literature
- Command: `WebFetch: https://api.zotero.org/groups/6375337/items?format=bibtex&limit=100`

### 3. Movie Link Verification
- Periodically verify all IMDB, Rotten Tomatoes, and Wikipedia links
- Update ratings as they change over time
- Replace broken links promptly
- Consider adding additional sources (Letterboxd, Metacritic)

**Last Verified:** January 2026
- All IMDB links verified working
- Rotten Tomatoes links updated to use numeric IDs (more stable than slug-based URLs)
- Nuremberg links corrected to reference 2000 TV miniseries (tt0208629) instead of 2025 film

**Common Issues:**
- RT URLs: Use format `/m/{numeric-id}-{slug}` for stability (e.g., `/m/1102961-nuremberg`)
- Multiple films with same title: Always verify IMDB ID matches the correct year/production

### 4. Quiz Quality Assurance
- Review quiz questions each semester for continued relevance
- Update questions based on new psychological research
- Retire questions that become common knowledge
- Develop new questions as films are rotated

### 5. Canvas Integration Improvements
- Streamline quiz import to Canvas
- Consider developing automated Canvas quiz generation
- Track quiz performance data to improve question quality