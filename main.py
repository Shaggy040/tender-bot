import requests
from bs4 import BeautifulSoup
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import os
import json

BASE_URL = "https://mumbaiport.gov.in/"
URL = "https://mumbaiport.gov.in/show_tenders.php?lang=1&depid=1&catid=3"

def connect_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

    client = gspread.authorize(creds)
    return client.open("Mumbai Port Tender Tracker").sheet1

def scrape():
    print("Checking tenders...")
    sheet = connect_sheet()
    existing = sheet.col_values(1)

    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(URL, headers=headers, timeout=30)

    soup = BeautifulSoup(res.text, "html.parser")
    table = soup.find("table")
    rows = table.find_all("tr")

    for row in rows[1:]:
        cols = row.find_all("td")
        if len(cols) < 7:
            continue

        tender = cols[1].text.strip()
        desc = cols[2].text.strip()
        date = cols[3].text.strip()

        link_tag = cols[6].find("a")
        if link_tag and link_tag.get("href"):
            detail_link = BASE_URL + link_tag.get("href")
        else:
            detail_link = "No Link"

        if tender not in existing and tender != "":
            sheet.append_row([tender, desc, date, detail_link])
            print("Added:", tender)

while True:
    scrape()
    time.sleep(3600)
