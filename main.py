import time
import json
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

URL = "https://mumbaiport.gov.in/show_tenders.php?lang=1&depid=1&catid=3"

# ---------------- GOOGLE SHEET ----------------
def connect_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open("Mumbai Port Tender Tracker").sheet1

# ---------------- BROWSER ----------------
def start_browser():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    return webdriver.Chrome(options=chrome_options)

# ---------------- SCRAPER ----------------
def scrape():
    print("Opening browser...")
    driver = start_browser()
    driver.get(URL)
    time.sleep(5)

    sheet = connect_sheet()

    rows = driver.find_elements(By.XPATH, "//table//tr")[1:]

    for i, row in enumerate(rows):
        try:
            tender_no = row.find_element(By.XPATH, "./td[2]").text
            description = row.find_element(By.XPATH, "./td[3]").text
            date = row.find_element(By.XPATH, "./td[4]").text

            # click info button
            info_button = row.find_element(By.XPATH, ".//td[last()]//a")
            driver.execute_script("arguments[0].click();", info_button)
            time.sleep(3)

            # click document icon
            doc_icon = driver.find_element(By.XPATH, "//img[contains(@src,'pdf')]")
            driver.execute_script("arguments[0].click();", doc_icon)
            time.sleep(4)

            # capture PDF link
            handles = driver.window_handles
            driver.switch_to.window(handles[-1])
            pdf_link = driver.current_url
            driver.close()
            driver.switch_to.window(handles[0])

            # write to sheet
            sheet.append_row([tender_no, description, date, pdf_link])
            print("Saved:", tender_no)

            # close popup
            close = driver.find_element(By.XPATH, "//div[contains(@class,'ui-dialog-titlebar-close')]")
            driver.execute_script("arguments[0].click();", close)

            time.sleep(2)

        except Exception as e:
            print("Skip row:", e)

    driver.quit()

if __name__ == "__main__":
    scrape()
