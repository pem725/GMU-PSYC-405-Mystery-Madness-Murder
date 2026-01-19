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

### Canvas QTI Export Workflow

Quizzes can be exported to Canvas using the QTI (Question & Test Interoperability) format, which preserves:
- Question text and answer choices
- Correct answer scoring (10 points per question)
- Answer feedback (rationales from answer keys)
- Single attempt setting

#### Directory Structure
```
canvas/
├── spring2026_001/                        # Section 001 QTI files
│   ├── imsmanifest.xml                    # Canvas manifest
│   ├── quiz01.xml                         # Quiz 1 QTI file
│   ├── quiz02.xml
│   └── ...
├── spring2026_002/                        # Section 002 QTI files
│   └── ...
├── spring2026_001_canvas_quizzes.zip      # Ready-to-import ZIP
└── spring2026_002_canvas_quizzes.zip
```

#### Converting Quizzes to Canvas Format

Use the conversion script to generate QTI files:

```bash
# Convert a single section
python scripts/convert_to_canvas_qti.py spring2026_001

# Convert all sections
python scripts/convert_to_canvas_qti.py --all

# Convert all sections AND create ZIP packages for Canvas
python scripts/convert_to_canvas_qti.py --all --zip
```

The script:
1. Reads quiz questions from `quizzes/{section}/quiz*.qmd`
2. Reads correct answers and rationales from `quizzes/answer_keys/{section}_quiz*.md`
3. Generates QTI XML files in `canvas/{section}/`
4. Creates a manifest file for Canvas import
5. Optionally packages everything into a ZIP file

#### Importing to Canvas

1. Go to your Canvas course
2. Navigate to **Settings > Import Course Content**
3. Select **QTI .zip file**
4. Upload the ZIP file (e.g., `spring2026_001_canvas_quizzes.zip`)
5. Select **All quizzes** during import
6. Review imported quizzes in **Quizzes** section

#### Quiz Settings in Canvas

After import, verify these settings for each quiz:
- **Points:** 50 total (10 points × 5 questions)
- **Attempts:** 1
- **Time limit:** None (students can access ahead of time)
- **Availability:** Set due date after in-class discussion
- **Show correct answers:** After due date (answers discussed in class first)

#### Semester Workflow

When preparing quizzes for a new semester:

1. **Create quiz source files** in `quizzes/{semester}{year}_{section}/`
2. **Create answer keys** in `quizzes/answer_keys/`
3. **Run conversion script:**
   ```bash
   python scripts/convert_to_canvas_qti.py --all --zip
   ```
4. **Import to Canvas** using the generated ZIP files
5. **Commit Canvas files** to version control:
   ```bash
   git add canvas/
   git commit -m "Generate Canvas QTI files for {semester}"
   ```

#### Regenerating After Quiz Changes

If you edit quiz questions or answer keys, regenerate the Canvas files:

```bash
# Regenerate specific section
python scripts/convert_to_canvas_qti.py spring2026_001 --zip

# Re-import to Canvas (will create new quizzes, not update existing)
```

**Note:** Canvas imports create NEW quizzes. Delete old versions after re-importing.

### Canvas Course Website (Common Cartridge)

In addition to quizzes, the entire course website can be exported as IMS Common Cartridge packages for Canvas import. This creates 15 weekly modules with film information, discussion questions, and readings.

#### Directory Structure (Course Website)
```
canvas/
├── spring2026_001/
│   ├── imsmanifest.xml              # CC manifest
│   ├── week01/ ... week15/          # Weekly module pages
│   │   ├── overview.html            # Week overview
│   │   ├── {film_title}.html        # Film info page
│   │   ├── discussion.html          # Discussion questions
│   │   └── readings.html            # Weekly readings
│   └── quizzes/                     # If --include-quizzes
├── spring2026_001_course.imscc      # Ready-to-import package
└── spring2026_002_course.imscc
```

#### Converting Syllabus to Canvas Modules

```bash
# Convert single section
python scripts/convert_to_canvas_cc.py spring2026_001

# Convert all sections
python scripts/convert_to_canvas_cc.py --all

# Include quiz QTI files in the package
python scripts/convert_to_canvas_cc.py --all --include-quizzes
```

#### What Gets Generated

Each of the 15 weekly modules contains:
- **Overview page** - Week introduction, module name, activities list
- **Film page(s)** - Title, year, IMDB/RT/Wiki links, psychological themes
- **Discussion page** - 4 read-only discussion questions per film
- **Readings page** - Links to Zotero library for relevant themes

#### Importing Course Website to Canvas

1. Go to Canvas course → **Settings** → **Import Course Content**
2. Select **Common Cartridge 1.x Package**
3. Upload the `.imscc` file (e.g., `spring2026_001_course.imscc`)
4. Select **All content** or choose specific modules
5. Modules appear under **Modules** tab with proper hierarchy

#### Combined Workflow (Quizzes + Course Website)

For a complete Canvas course setup:

```bash
# 1. Generate QTI quizzes
python scripts/convert_to_canvas_qti.py --all --zip

# 2. Generate course website with quizzes included
python scripts/convert_to_canvas_cc.py --all --include-quizzes

# 3. Import to Canvas:
#    - First: Import spring2026_001_course.imscc (modules + quizzes)
#    - Or: Import quizzes separately, then course website
```

## Teaching Notes Workflow

The course maintains confidential teaching notes for instructor use only. These files are tracked in git but NOT published to the website or Canvas.

### Directory Structure

```
teaching_notes/
├── README.md                          # Confidentiality notice
├── TEACHING_NOTES_S2026_001.md        # Section 001 teaching notes
└── TEACHING_NOTES_S2026_002.md        # Section 002 teaching notes
```

### File Naming Convention
Format: `TEACHING_NOTES_{semester}{year}_{section}.md`
- Examples: `TEACHING_NOTES_S2026_001.md`, `TEACHING_NOTES_F2026_002.md`

### What's Included in Teaching Notes

Each teaching notes file contains:

1. **Quick Reference Schedule** - All class dates mapped to weeks, films, and quizzes
2. **Class-by-Class Notes** with:
   - Exact dates and times
   - Topics to cover with time allocations
   - Film viewing segments (where to start/stop each class)
   - Discussion prompts
3. **Quiz Concepts (MUST COVER)** - Critical material that must be discussed before each quiz:
   - Specific researchers and concepts
   - How concepts connect to film content
   - Marked as "ESSENTIAL" when required for quiz questions
4. **Key Readings Reference** - Quick lookup table of authors, concepts, and relevant films
5. **Instructor Reminders** - Quiz logistics, engagement tracking, common student questions

### Privacy Mechanism

Teaching notes are excluded from website publication because:
- `_quarto.yml` uses an explicit `render:` list (whitelist approach)
- `teaching_notes/` is NOT in that list
- Only explicitly listed files are rendered to `_site/`

To verify exclusion: Run `quarto render` and confirm no files appear in `_site/teaching_notes/`

### Creating Teaching Notes for a New Semester

When preparing teaching notes for a new semester:

1. **Calculate class dates:**
   - Identify first/last day from academic calendar
   - Map M/W or T/Th schedule to 28 class sessions
   - Account for spring/fall break

2. **Extract quiz concepts from answer keys:**
   - Read each `quizzes/answer_keys/{section}_quiz*.md`
   - Identify key researchers and concepts
   - Note which concepts are ESSENTIAL for quiz questions

3. **Create teaching notes file:**
   ```bash
   # Create from template or previous semester
   cp teaching_notes/TEACHING_NOTES_S2026_001.md teaching_notes/TEACHING_NOTES_{new_semester}_001.md
   ```

4. **Update content:**
   - Replace all dates with new semester dates
   - Update film schedule if films have changed
   - Update quiz concepts if questions have changed
   - Add content warnings for films with sensitive material

5. **Commit (but NOT to website):**
   ```bash
   git add teaching_notes/
   git commit -m "Add teaching notes for {semester}"
   git push
   ```

### Using Teaching Notes During the Semester

**Before each class:**
1. Review the relevant class session notes
2. Check which quiz concepts need to be covered (marked MUST COVER)
3. Prepare discussion questions
4. Queue film to correct timestamp

**Quiz administration:**
- Announce quiz availability randomly during class
- Typical window: Announce Tuesday, close Friday
- Remind students: Best 10 of 14 quizzes count

**Engagement tracking:**
- Note students who participate
- Follow up with quiet students via Canvas
- Engagement = 20% of grade

## Quiz Performance Analytics Workflow

The course uses an automated system to analyze quiz performance data and identify questions needing revision.

### Directory Structure

```
quiz_analytics/
├── scripts/
│   ├── fetch_canvas_data.py         # Pull data from Canvas API
│   ├── analyze_quiz_performance.py  # Calculate item statistics
│   ├── generate_reports.py          # Create Markdown + HTML reports
│   └── import_survey.py             # Process student feedback
├── data/                            # Gitignored - local only
│   ├── raw/                         # Canvas API exports
│   ├── surveys/                     # Student feedback
│   └── processed/                   # Analysis results
├── reports/                         # Generated reports
│   ├── {section}/                   # Per-quiz Markdown reports
│   ├── dashboards/                  # Interactive HTML dashboards
│   └── flagged_questions/           # Summary of issues
├── config.yaml                      # Thresholds and settings
└── README.md                        # Quick reference
```

### Metrics Calculated

| Metric | Description | Flag Threshold |
|--------|-------------|----------------|
| **Difficulty (p)** | % of students correct | <30% or >90% |
| **Discrimination (D)** | Top 27% - Bottom 27% | D < 0.20 |
| **Point-Biserial r** | Correlation with final grade | r < 0.15 |
| **Distractor Analysis** | Wrong answer selection rates | <5% or >50% |

### End-of-Semester Workflow

```bash
# 1. Set Canvas API token
export CANVAS_TOKEN="your_token_here"

# 2. Fetch all quiz data
python quiz_analytics/scripts/fetch_canvas_data.py spring2026_001

# 3. Run full analysis and generate reports
python quiz_analytics/scripts/analyze_quiz_performance.py spring2026_001 --full

# 4. (After survey closes) Import student feedback
python quiz_analytics/scripts/import_survey.py spring2026_001 survey_export.csv --regenerate
```

### Output Files

- **Per-quiz reports:** `reports/{section}/quiz_*_analysis.md`
  - Detailed item statistics for each question
  - Distractor analysis tables
  - Flags with specific recommendations

- **Flagged questions summary:** `reports/flagged_questions/{section}_flagged.md`
  - Critical issues requiring immediate revision
  - Warnings for next semester review
  - Excellent questions to use as models

- **Interactive dashboard:** `reports/dashboards/{section}_dashboard.html`
  - Plotly charts for visual analysis
  - Difficulty vs. discrimination scatter plot
  - Quiz-by-quiz score trends

### Student Survey Integration

At semester end, create a Canvas survey with these questions:
1. "Rate the overall clarity of quiz questions" (1-5 scale)
2. "Which quiz questions did you find confusing?" (open text)
3. "Which quiz questions seemed unfair?" (open text)
4. "Any suggestions for improving quizzes?" (open text)

Export responses as CSV and import with the survey script.

### Configuration

Edit `quiz_analytics/config.yaml` to adjust:
- Difficulty/discrimination thresholds
- Course IDs for each section
- Grouping method (top/bottom 27%, thirds, median)

### Privacy

- Raw data stored locally only (gitignored)
- All student IDs anonymized (student_001, student_002, etc.)
- Only aggregated reports tracked in git

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

## GMU Syllabus Compliance

All syllabi must comply with [GMU Catalog Policy AP.2.5](https://catalog.gmu.edu/policies/academic/course-information/) and include the [GMU Common Course Policies](https://stearnscenter.gmu.edu/home/gmu-common-course-policies/).

### Required Elements (per AP.2.5)

Every syllabus must include:

1. **Course Number and Title**
2. **Course Overview** - expanded description; note Mason Core/WI/RS designations
3. **Learning Outcomes** - expected student competencies
4. **Instructor Information** - name and contact details
5. **Meeting Times and Modality**
6. **Grading Policies:**
   - Numerical grade scale (A = 90-100%, B = 80-89%, etc.)
   - Grade weights (how assignments count toward final grade)
   - Late work and other policies affecting grades
7. **AI Tools Statement** (required since August 2025)

### Common Policy Addendum (Four Required Policies)

The following four policies must be included either in full OR via link to the [GMU Common Course Policies page](https://stearnscenter.gmu.edu/home/gmu-common-course-policies/):

1. **Academic Standards** (replaced "Academic Integrity/Honor Code" in Fall 2024)
   - Three principles: Honesty, Acknowledgement, Uniqueness of Work
   - Link: [academicstandards.gmu.edu](https://academicstandards.gmu.edu)

2. **Disability Services**
   - Updated contact: SUB I Suite 2500, ds@gmu.edu, (703) 993-2474
   - Link: [ds.gmu.edu](https://ds.gmu.edu)

3. **FERPA and GMU Email**
   - Student rights regarding education records
   - Requirement to use @gmu.edu email

4. **Title IX and Sexual Misconduct**
   - Faculty reporting requirements
   - Title IX Coordinator: TitleIX@gmu.edu, (703) 993-8730
   - Confidential resources: SSAC, CAPS, Student Health

### AI Tools Policy Guidelines

The instructor's perspective on AI:

> "AI is a remarkable tool that is widely misunderstood and, unfortunately, often abused. I encourage you to use AI wisely and openly."

**Policy structure:**
- **Permitted uses:** Brainstorming, grammar checking, concept exploration
- **Prohibited uses:** Generating quiz answers, summarizing unwatched films, replacing critical analysis
- **Disclosure requirement:** Students must disclose AI use openly; no penalty for honest disclosure

### Syllabus Template Location

Current syllabi following this format:
- `PSYC405_S2026_001.qmd` - Section 001
- `PSYC405_S2026_002.qmd` - Section 002

### Compliance Verification

When creating or updating syllabi, verify against this checklist:

- [ ] Course number, title, and Mason Core designation
- [ ] Instructor contact information
- [ ] Meeting times and location
- [ ] Learning outcomes
- [ ] Numerical grade scale (percentages)
- [ ] Grade weights with computation details
- [ ] Late work policy
- [ ] AI Tools Policy statement
- [ ] Academic Standards section (not "Honor Code")
- [ ] Disability Services (ds.gmu.edu, not ods.gmu.edu)
- [ ] FERPA statement
- [ ] Title IX statement with confidential resources
- [ ] Link to GMU Common Course Policies

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
- Nuremberg (2025) uses tt29567915

**Common Issues:**
- RT URLs: Use format `/m/{slug}` or `/m/{numeric-id}-{slug}` depending on availability
- Multiple films with same title: Always verify IMDB ID matches the correct year/production

### 4. Quiz Quality Assurance
- Review quiz questions each semester for continued relevance
- Update questions based on new psychological research
- Retire questions that become common knowledge
- Develop new questions as films are rotated

### 5. Canvas Integration Improvements
- ✅ **COMPLETED:** Automated QTI generation via `scripts/convert_to_canvas_qti.py`
- ✅ **COMPLETED:** ZIP packaging for easy Canvas import
- ✅ **COMPLETED:** Quiz performance tracking via `quiz_analytics/` (see workflow below)
- Future: Consider Canvas API integration for direct quiz creation (if needed)

### 6. Syllabus Streamlining (Future Semesters)
- **Goal:** Shorten syllabi by linking to policies instead of including full text
- **Current approach:** Both full policy text AND link to GMU Common Course Policies
- **Future approach:** Replace full text with concise link-only references
- **Example transformation:**
  ```markdown
  # Current (verbose)
  ::: {.callout-warning icon="shield-check"}
  ## Academic Standards
  [Full policy text here...]
  :::

  # Future (streamlined)
  See [GMU Academic Standards](https://academicstandards.gmu.edu){target="_blank"} for university policy.
  ```
- **Benefits:**
  - Shorter, more readable syllabi
  - Always links to current policy (no outdated language)
  - Reduces maintenance burden when policies change
- **Retain full text for:** AI Tools Policy (course-specific)

### 7. Semester Changeover Checklist
When preparing syllabi for a new semester:
1. Update semester dates in YAML header and Important Dates table
2. Update film schedule if films are being rotated
3. Verify all movie links still resolve (IMDB, RT, Wikipedia)
4. Sync Zotero library and update readings if needed
5. Create new quiz directory: `quizzes/{semester}{year}_{section}/`
6. Generate new quizzes integrating updated films and readings
7. Create answer keys in `quizzes/answer_keys/`
8. **Convert quizzes to Canvas format:**
   ```bash
   python scripts/convert_to_canvas_qti.py --all --zip
   ```
9. **Generate Canvas course website:**
   ```bash
   python scripts/convert_to_canvas_cc.py --all --include-quizzes
   ```
10. Import `.imscc` and quiz ZIP files to Canvas
11. **Create teaching notes for both sections:**
    - Calculate all class dates (28 sessions per section)
    - Extract quiz concepts from answer keys
    - Create `teaching_notes/TEACHING_NOTES_{semester}_{section}.md`
12. Verify GMU policy links still work
13. Render and test all pages locally before pushing
14. Update `_quarto.yml` navigation if pages changed
15. Commit all changes including teaching notes (not published to website)

### 8. End-of-Semester Analytics Checklist
After final grades are submitted:
1. **Fetch quiz data from Canvas:**
   ```bash
   export CANVAS_TOKEN="your_token"
   python quiz_analytics/scripts/fetch_canvas_data.py spring2026_001
   python quiz_analytics/scripts/fetch_canvas_data.py spring2026_002
   ```
2. **Run performance analysis:**
   ```bash
   python quiz_analytics/scripts/analyze_quiz_performance.py --all --full
   ```
3. **Create and distribute student survey** via Canvas
4. **Import survey responses:**
   ```bash
   python quiz_analytics/scripts/import_survey.py spring2026_001 survey.csv --regenerate
   ```
5. **Review flagged questions** in `quiz_analytics/reports/flagged_questions/`
6. **Open dashboard** in browser: `quiz_analytics/reports/dashboards/*_dashboard.html`
7. **Update answer keys** with notes on questions to revise
8. **Archive analytics** for semester comparison