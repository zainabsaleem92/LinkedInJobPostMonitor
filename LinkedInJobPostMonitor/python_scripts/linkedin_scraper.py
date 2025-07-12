from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def linkedin_job_scraper(keyword, location=None):
    options = Options()
    # options.add_argument("--headless")  # Run Chrome in headless mode
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        base_url = "https://www.linkedin.com/jobs/search/"
        query = f"?keywords={keyword.replace(' ', '%20')}"
        if location:
            query += f"&location={location.replace(' ', '%20')}"
        url = base_url + query

        driver.get(url)
        time.sleep(5)  # Wait for page load

        # Popup handling: wait and dismiss if it appears
        try:
            print("🔍 Trying to find and dismiss popup...")
            wait = WebDriverWait(driver, 10)
            print("🔍 Trying to find dismiss button by CSS selector...")
            dismiss_button = wait.until(
                EC.element_to_be_clickable((
                    By.CSS_SELECTOR,
                    'button.contextual-sign-in-modal__modal-dismiss[aria-label="Dismiss"]'
                ))
            )
            print("Found dismiss button!")
            driver.save_screenshot("before_clicking_dismiss.png")
            dismiss_button.click()
            print("✅ Popup dismissed.")
            time.sleep(2)
        except Exception as e:
            driver.save_screenshot("popup_not_closed.png")
            print("❌ Popup not found or couldn't be closed:", e)

        # Now scrape job posts
        jobs = driver.find_elements(By.CLASS_NAME, 'job-card-container')
        if not jobs:
            print("No job posts found.")
            return []

        results = []
        for job in jobs:
            title = job.find_element(By.CSS_SELECTOR, 'h3').text
            company = job.find_element(By.CSS_SELECTOR, 'h4').text
            location_text = job.find_element(By.CSS_SELECTOR, '.job-search-card__location').text
            job_link = job.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')

            results.append({
                'title': title,
                'company': company,
                'location': location_text,
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
