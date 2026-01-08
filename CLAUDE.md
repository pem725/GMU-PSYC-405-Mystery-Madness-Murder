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