import requests
import json
import csv
import time
from datetime import datetime
from typing import Dict, List, Optional
import os

class JSearchJobScraper:
    """
    A job scraper using the JSearch API from RapidAPI
    """
    
    def __init__(self, api_key: str):
        """
        Initialize the scraper with API credentials
        
        Args:
            api_key (str): Your RapidAPI key for JSearch
        """
        self.api_key = api_key
        self.base_url = "https://jsearch.p.rapidapi.com"
        self.headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def search_jobs_max_data(self, 
                           query: str, 
                           page: int = 1,
                           num_pages: int = 10,
                           date_posted: str = "all",
                           country: str = "us",
                           employment_types: str = "FULLTIME",
                           job_requirements: str = None,
                           radius: int = 100,
                           get_job_details: bool = True) -> List[Dict]:
        """
        Search for jobs and get maximum data without cleaning
        
        Args:
            query (str): Job search query
            page (int): Page number to start from
            num_pages (int): Number of pages to scrape
            date_posted (str): Filter by date posted
            country (str): Country code
            employment_types (str): Job types
            job_requirements (str): Requirements filter
            radius (int): Search radius in km
            get_job_details (bool): Whether to fetch detailed job info for each job
            
        Returns:
            List[Dict]: List of raw job postings with maximum data
        """
        
        all_jobs = []
        
        for current_page in range(page, page + num_pages):
            print(f"Scraping page {current_page}...")
            
            # API endpoint for job search
            url = f"{self.base_url}/search"
            
            # Parameters for the API call
            params = {
                "query": query,
                "page": current_page,
                "num_pages": "1",
                "date_posted": date_posted,
                "country": country,
                "employment_types": employment_types,
                "radius": radius
            }
            
            # Add job requirements if specified
            if job_requirements:
                params["job_requirements"] = job_requirements
            
            try:
                response = self.session.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                if data.get("status") == "OK" and data.get("data"):
                    jobs = data["data"]
                    
                    # If get_job_details is True, fetch detailed info for each job
                    if get_job_details:
                        print(f"Getting detailed info for {len(jobs)} jobs...")
                        detailed_jobs = []
                        for i, job in enumerate(jobs):
                            job_id = job.get("job_id")
                            if job_id:
                                print(f"  Getting details for job {i+1}/{len(jobs)}: {job.get('job_title', 'Unknown')}")
                                details = self.get_job_details(job_id)
                                if details:
                                    # Handle both dict and list responses from job details API
                                    if isinstance(details, list) and len(details) > 0:
                                        details = details[0]  # Take first item if it's a list
                                    elif isinstance(details, list) and len(details) == 0:
                                        details = {}  # Empty dict if empty list
                                    
                                    if isinstance(details, dict):
                                        # Merge search result with detailed info
                                        merged_job = {**job, **details}
                                        detailed_jobs.append(self.get_raw_job_data(merged_job))
                                    else:
                                        # If details is not a dict, just use original job data
                                        detailed_jobs.append(self.get_raw_job_data(job))
                                else:
                                    detailed_jobs.append(self.get_raw_job_data(job))
                                # Rate limiting for detail requests
                                time.sleep(0.5)
                            else:
                                detailed_jobs.append(self.get_raw_job_data(job))
                        
                        all_jobs.extend(detailed_jobs)
                    else:
                        # Just add raw search results
                        raw_jobs = [self.get_raw_job_data(job) for job in jobs]
                        all_jobs.extend(raw_jobs)
                    
                    print(f"Added {len(jobs)} jobs from page {current_page}")
                    
                    # Check if there are more pages
                    if len(jobs) == 0:
                        print("No more jobs found. Stopping.")
                        break
                else:
                    print(f"API returned status: {data.get('status')}")
                    print(f"Error: {data.get('error', 'Unknown error')}")
                    break
                    
            except requests.exceptions.RequestException as e:
                print(f"Error fetching page {current_page}: {e}")
                break
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON on page {current_page}: {e}")
                break
            
            # Rate limiting between pages
            time.sleep(1)
        
        return all_jobs
    
    def get_job_details(self, job_id: str) -> Dict:
        """
        Get detailed information about a specific job
        
        Args:
            job_id (str): The job ID from search results
            
        Returns:
            Dict: Detailed job information
        """
        url = f"{self.base_url}/job-details"
        params = {"job_id": job_id}
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("status") == "OK":
                job_data = data.get("data", [])
                
                # Handle both list and dict responses
                if isinstance(job_data, list) and len(job_data) > 0:
                    return job_data[0]  # Return first item if it's a list
                elif isinstance(job_data, dict):
                    return job_data  # Return as-is if it's already a dict
                else:
                    return {}  # Return empty dict if no valid data
            else:
                print(f"Error getting job details: {data.get('error')}")
                return {}
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching job details: {e}")
            return {}
        except json.JSONDecodeError as e:
            print(f"Error parsing job details JSON: {e}")
            return {}
    
    def get_raw_job_data(self, job: Dict) -> Dict:
        """
        Get raw job data without any cleaning - preserves all original fields
        
        Args:
            job (Dict): Raw job data from API
            
        Returns:
            Dict: Raw job data with timestamp added
        """
        # Add scraping timestamp to raw data
        raw_job = job.copy()
        raw_job["scraped_at"] = datetime.now().isoformat()
        return raw_job
    
    def save_raw_data(self, jobs: List[Dict], format: str = "json", filename: str = None):
        """
        Save raw job data in specified format
        
        Args:
            jobs (List[Dict]): List of raw job dictionaries
            format (str): Output format ("json", "csv", "both")
            filename (str): Base filename (optional)
        """
        if not jobs:
            print("No jobs to save.")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = filename or f"raw_jobs_{timestamp}"
        
        if format in ["json", "both"]:
            json_filename = f"{base_filename}.json"
            with open(json_filename, 'w', encoding='utf-8') as jsonfile:
                json.dump(jobs, jsonfile, indent=2, ensure_ascii=False, default=str)
            print(f"Saved {len(jobs)} raw jobs to {json_filename}")
        
        if format in ["csv", "both"]:
            csv_filename = f"{base_filename}.csv"
            
            # Flatten nested dictionaries and lists for CSV
            flattened_jobs = []
            for job in jobs:
                flattened_job = self._flatten_dict(job)
                flattened_jobs.append(flattened_job)
            
            # Get all unique keys
            all_keys = set()
            for job in flattened_jobs:
                all_keys.update(job.keys())
            
            with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=sorted(all_keys))
                writer.writeheader()
                writer.writerows(flattened_jobs)
            
            print(f"Saved {len(jobs)} raw jobs to {csv_filename}")
    
    def _flatten_dict(self, d: Dict, parent_key: str = '', sep: str = '_') -> Dict:
        """
        Flatten nested dictionaries and convert lists to strings
        
        Args:
            d (Dict): Dictionary to flatten
            parent_key (str): Parent key for nested items
            sep (str): Separator for nested keys
            
        Returns:
            Dict: Flattened dictionary
        """
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                # Convert lists to string representation
                items.append((new_key, str(v)))
            else:
                items.append((new_key, v))
        return dict(items)
    
    def filter_jobs(self, jobs: List[Dict], filters: Dict) -> List[Dict]:
        """
        Filter jobs based on criteria
        
        Args:
            jobs (List[Dict]): List of job dictionaries
            filters (Dict): Filter criteria
            
        Returns:
            List[Dict]: Filtered jobs
        """
        filtered_jobs = []
        
        for job in jobs:
            include_job = True
            
            # Filter by salary range
            if filters.get("min_salary") and job.get("salary_min"):
                try:
                    if float(job["salary_min"]) < filters["min_salary"]:
                        include_job = False
                except (ValueError, TypeError):
                    pass
            
            # Filter by location
            if filters.get("location") and job.get("location"):
                if filters["location"].lower() not in job["location"].lower():
                    include_job = False
            
            # Filter by remote work
            if filters.get("remote_only") and not job.get("is_remote"):
                include_job = False
            
            # Filter by company
            if filters.get("company") and job.get("company"):
                if filters["company"].lower() not in job["company"].lower():
                    include_job = False
            
            # Filter by keywords in title
            if filters.get("title_keywords"):
                title = job.get("title", "").lower()
                if not any(keyword.lower() in title for keyword in filters["title_keywords"]):
                    include_job = False
            
            if include_job:
                filtered_jobs.append(job)
        
        return filtered_jobs
    
    def get_job_statistics(self, jobs: List[Dict]) -> Dict:
        """
        Get basic statistics about scraped jobs
        
        Args:
            jobs (List[Dict]): List of job dictionaries
            
        Returns:
            Dict: Job statistics
        """
        if not jobs:
            return {}
        
        stats = {
            "total_jobs": len(jobs),
            "companies": len(set(job.get("company", "") for job in jobs if job.get("company"))),
            "locations": len(set(job.get("location", "") for job in jobs if job.get("location"))),
            "employment_types": {},
            "remote_jobs": sum(1 for job in jobs if job.get("is_remote")),
            "avg_salary": None
        }
        
        # Employment type distribution
        for job in jobs:
            emp_type = job.get("employment_type", "Unknown")
            stats["employment_types"][emp_type] = stats["employment_types"].get(emp_type, 0) + 1
        
        # Calculate average salary
        salaries = []
        for job in jobs:
            if job.get("salary_min") and job.get("salary_max"):
                try:
                    avg_salary = (float(job["salary_min"]) + float(job["salary_max"])) / 2
                    salaries.append(avg_salary)
                except (ValueError, TypeError):
                    pass
        
        if salaries:
            stats["avg_salary"] = sum(salaries) / len(salaries)
        
        return stats


def main():
    """
    Example usage for maximum raw data extraction
    """
    
    # You need to get your API key from RapidAPI
    API_KEY = "ce5365cfe2msh03d28dfd11ac1dbp18f786jsn6aa3521a1f55"
    
    if API_KEY == "YOUR_RAPIDAPI_KEY_HERE":
        print("Please set your RapidAPI key in the API_KEY variable")
        return
    
    # Initialize the scraper
    scraper = JSearchJobScraper(API_KEY)
    
    # Get maximum raw job data
    print("Searching for jobs with maximum data extraction...")
    raw_jobs = scraper.search_jobs_max_data(
        query="Software Engineer",
        num_pages=3,  # Adjust based on your needs
        date_posted="week",
        country="us",
        employment_types="FULLTIME",
        get_job_details=True  # Set to True for maximum data
    )
    
    print(f"\nExtracted {len(raw_jobs)} jobs with full raw data")
    
    # Display sample of available fields
    if raw_jobs:
        print("\nSample of available fields in raw data:")
        sample_job = raw_jobs[0]
        for key in sorted(sample_job.keys())[:20]:  # Show first 20 fields
            print(f"  - {key}: {type(sample_job[key]).__name__}")
        
        if len(sample_job.keys()) > 20:
            print(f"  ... and {len(sample_job.keys()) - 20} more fields")
    
    # Save raw data in both formats
    scraper.save_raw_data(raw_jobs, format="both", filename="maximum_job_data")
    
    print(f"\nTotal fields per job: {len(raw_jobs[0].keys()) if raw_jobs else 0}")
    print("Raw data saved without any cleaning or filtering!")


# Additional utility function for exploring data structure
def explore_job_structure(jobs: List[Dict]):
    """
    Explore the structure of job data to understand available fields
    
    Args:
        jobs (List[Dict]): List of job dictionaries
    """
    if not jobs:
        print("No jobs to explore")
        return
    
    all_fields = set()
    field_types = {}
    
    for job in jobs:
        for key, value in job.items():
            all_fields.add(key)
            if key not in field_types:
                field_types[key] = type(value).__name__
    
    print(f"\nFound {len(all_fields)} unique fields across all jobs:")
    print("-" * 50)
    
    for field in sorted(all_fields):
        print(f"{field:<40} {field_types[field]}")
    
    # Show sample values for some key fields
    sample_job = jobs[0]
    key_fields = ['job_id', 'job_title', 'employer_name', 'job_city', 
                  'job_employment_type', 'job_posted_at_datetime_utc']
    
    print(f"\nSample values from first job:")
    print("-" * 50)
    for field in key_fields:
        if field in sample_job:
            value = sample_job[field]
            if isinstance(value, str) and len(value) > 100:
                value = value[:100] + "..."
            print(f"{field}: {value}")


if __name__ == "__main__":
    main()