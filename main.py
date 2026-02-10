from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

SHEET_NAME = "Mumbai Port Tenders"

def start_browser():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(options=options)
    return driver


def scrape():
    driver = start_browser()
    driver.get("https://mumbaiport.gov.in/show_tenders.php?lang=1&depid=1&catid=3")
    time.sleep(5)

    rows = driver.find_elements(By.XPATH, "//table//tr")[1:]

    tenders = []

    for row in rows:
        try:
            cols = row.find_elements(By.TAG_NAME, "td")

            tender_no = cols[1].text
            desc = cols[2].text
            date = cols[3].text

            # click info icon
            detail_btn = row.find_element(By.XPATH, ".//img[contains(@src,'info')]")
            driver.execute_script("arguments[0].click();", detail_btn)
            time.sleep(3)

            # download link
            links = driver.find_elements(By.XPATH, "//a[contains(@href,'showfile.php')]")
            file_link = links[0].get_attribute("href") if links else ""

            tenders.append([tender_no, desc, date, file_link])

            # close popup
            driver.find_element(By.XPATH, "//button[contains(text(),'×')]").click()
            time.sleep(1)

        except:
            pass

    driver.quit()
    return tenders


def update_sheet(tenders):
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    import os
    import json

    creds_dict = json.loads(os.environ["GOOGLE_CREDS"])

    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    sheet = client.open(Mumbai Port Tender Tracker).sheet1

    existing = sheet.get_all_values()
    existing_tenders = [row[0] for row in existing[1:]]

    for tender in tenders:
        if tender[0] not in existing_tenders:
            sheet.append_row(tender)
            print("Added:", tender[0])


if __name__ == "__main__":
    data = scrape()
    update_sheet(data)
