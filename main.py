from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials


SHEET_NAME = "Mumbai Port Tender Tracker"


# ---------- BROWSER ----------
def start_browser():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)
    return driver


# ---------- SCRAPER ----------
def scrape():

    driver = start_browser()
    wait = WebDriverWait(driver, 20)

    driver.get("https://mumbaiport.gov.in/show_tenders.php?lang=1&depid=1&catid=3")

    # wait for table
    wait.until(EC.presence_of_element_located((By.XPATH, "//table")))

    rows = driver.find_elements(By.XPATH, "//table//tr")[1:]

    tenders = []

    for row in rows:
        try:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) < 6:
                continue

            tender_no = cols[1].text.strip()
            desc = cols[2].text.strip()
            date = cols[3].text.strip()

            # click DETAILS button (blue info icon)
            detail_btn = row.find_element(By.XPATH, ".//a[contains(@class,'btn-info')]")
            driver.execute_script("arguments[0].click();", detail_btn)

            # wait for popup PDF link
            wait.until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(@href,'showfile.php')]"))
            )

            links = driver.find_elements(By.XPATH, "//a[contains(@href,'showfile.php')]")
            file_link = links[0].get_attribute("href") if links else ""

            tenders.append([tender_no, desc, date, file_link])

            # close popup
            close_btn = driver.find_element(By.XPATH, "//button[@class='close']")
            driver.execute_script("arguments[0].click();", close_btn)
            time.sleep(1)

        except Exception as e:
            print("Skipped row:", e)

    driver.quit()

    print("Total tenders found:", len(tenders))
    return tenders


# ---------- GOOGLE SHEETS ----------
def update_sheet(tenders):

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds_dict = json.loads(os.environ["GOOGLE_CREDS"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    sheet = client.open(SHEET_NAME).sheet1

    existing = sheet.get_all_values()
    existing_tender_numbers = [row[0] for row in existing[1:]]

    new_count = 0

    for tender in tenders:
        if tender[0] not in existing_tender_numbers:
            sheet.append_row(tender)
            new_count += 1

    print("New tenders added:", new_count)


# ---------- MAIN ----------
if __name__ == "__main__":
    data = scrape()
    update_sheet(data)
