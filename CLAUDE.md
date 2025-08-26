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