# Les Diabolique (1955)

**Author:** Patrick E. McKnight

## Movie Data Scraper Tool

This document contains a Python-based movie scraper tool designed to collect ratings and reviews for "Les Diaboliques" (1955) from multiple sources including Letterboxd and The Movie Database (TMDB).

### Features

The MovieScraper class provides the following functionality:

- **Letterboxd Integration**: Scrapes movie ratings and user reviews from Letterboxd
- **TMDB API Integration**: Retrieves official movie data, ratings, and reviews via TMDB API
- **Data Export**: Exports collected data to CSV files for analysis

### Usage

The scraper requires:
- A TMDB API key (free registration at https://www.themoviedb.org/)
- Python libraries: `requests`, `beautifulsoup4`, `pandas`

### Data Collection

The tool collects:
- **Ratings**: Overall ratings from both platforms
- **Reviews**: User reviews with timestamps
- **Metadata**: Vote counts, popularity scores, and other film metrics

### Export Format

Data is exported to two CSV files:
- `diabolique_1955_reviews.csv`: Contains all collected reviews
- `diabolique_1955_metadata.csv`: Contains aggregated movie metadata

### Technical Implementation

The scraper uses:
- Web scraping with BeautifulSoup for Letterboxd data
- REST API calls for TMDB data
- Pandas for data manipulation and export
- Error handling for robust data collection

### Course Application

This tool serves as a practical example of data collection methods for analyzing film reception and public perception, supporting the course's focus on understanding how media influences beliefs and perceptions.