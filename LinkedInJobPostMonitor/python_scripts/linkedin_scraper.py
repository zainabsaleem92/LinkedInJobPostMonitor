from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time

def linkedin_job_scraper(keyword, location=None):
    options = Options()
    options.add_argument("--headless")  # Run Chrome in headless mode
    service = Service('./chromedriver')  # Path to your chromedriver

    driver = webdriver.Chrome(service=service, options=options)
    try:
        # Build LinkedIn jobs URL
        base_url = "https://www.linkedin.com/jobs/search/"
        query = f"?keywords={keyword.replace(' ', '%20')}"
        if location:
            query += f"&location={location.replace(' ', '%20')}"
        url = base_url + query

        driver.get(url)
        time.sleep(5)  # Wait for page load

        jobs = driver.find_elements(By.CLASS_NAME, 'job-card-container')
        results = []
        for job in jobs:
            title = job.find_element(By.CSS_SELECTOR, 'h3').text
            company = job.find_element(By.CSS_SELECTOR, 'h4').text
            location = job.find_element(By.CSS_SELECTOR, '.job-search-card__location').text
            job_link = job.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')

            results.append({
                'title': title,
                'company': company,
                'location': location,
                'url': job_link
            })

        return results

    finally:
        driver.quit()

if __name__ == "__main__":
    keyword = "Data Scientist"
    location = "United States"
    job_posts = linkedin_job_scraper(keyword, location)
    for idx, job in enumerate(job_posts):
        print(f"{idx+1}. {job['title']} at {job['company']} - {job['location']}")
        print(f"   Link: {job['url']}\n")
