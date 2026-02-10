import os
import json
import time
import gspread

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from google.oauth2.service_account import Credentials


SHEET_NAME = "Mumbai Port Tender Tracker"
URL = "https://mumbaiport.gov.in/show_tenders.php?lang=1&depid=1&catid=3"


# ---------------- GOOGLE SHEET ----------------
def update_sheet(tenders):

    creds_dict = json.loads(os.environ["GOOGLE_CREDS"])

    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ],
    )

    client = gspread.authorize(creds)
    sheet = client.open(SHEET_NAME).sheet1

    existing = sheet.get_all_values()
    existing_numbers = [r[0] for r in existing[1:]]

    added = 0

    for t in tenders:
        if t[0] not in existing_numbers:
            sheet.append_row(t)
            added += 1

    print("New tenders added:", added)


# ---------------- SCRAPER ----------------
def scrape():

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 20)

    driver.get(URL)

    wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))

    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")

    tenders = []

    for i in range(len(rows)):
        try:
            rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
            row = rows[i]

            cols = row.find_elements(By.TAG_NAME, "td")

            tender_no = cols[1].text
            description = cols[2].text
            date = cols[3].text

            # click blue info button
            info_btn = cols[-1].find_element(By.TAG_NAME, "a")
            driver.execute_script("arguments[0].click();", info_btn)

            # wait popup
            wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "modal-content")))

            time.sleep(1)

            # find pdf icon inside popup
            pdf_link = driver.find_element(By.CSS_SELECTOR, "a[href*='showfile.php']").get_attribute("href")

            tenders.append([tender_no, description, date, pdf_link])

            print("Found:", tender_no)

            # close popup
            close_btn = driver.find_element(By.CSS_SELECTOR, ".modal-header button")
            driver.execute_script("arguments[0].click();", close_btn)

            time.sleep(1)

        except Exception as e:
            print("Skipping row:", e)

    driver.quit()

    print("Total tenders found:", len(tenders))
    return tenders


# ---------------- MAIN ----------------
if __name__ == "__main__":
    data = scrape()
    update_sheet(data)
