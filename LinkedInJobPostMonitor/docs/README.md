# LinkedIn Job Post Monitor

## Overview

This project monitors LinkedIn job postings based on keywords and locations to generate actionable leads for B2B sales and recruitment. It scrapes job postings, enriches company data, scores leads, and automates the workflow for continuous monitoring.

## Features

- Scrapes LinkedIn job posts with job title, company name, location, and job URL.
- Enriches company data (planned for future modules).
- Scores and ranks leads based on hiring signals.
- Exports leads to CSV or Google Sheets.
- Automates the entire process using n8n workflows.
- Utilizes Databricks for data cleaning, enrichment, and lead scoring.

## Tech Stack

- Python (Selenium for scraping, Pandas for data processing)
- n8n (workflow automation)
- Databricks (data engineering and lead scoring)
- Google Sheets API (for data export)

## Getting Started

### Prerequisites

- Python 3.7 or higher
- Google Chrome and matching ChromeDriver
- n8n account (optional, for automation)
- Databricks workspace (optional, for data processing)

### Setup

1. Clone this repository:

```bash
git clone https://github.com/yourusername/LinkedInJobPostMonitor.git
cd LinkedInJobPostMonitor
```
