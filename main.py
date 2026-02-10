import requests
from bs4 import BeautifulSoup
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import os
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

URL = "https://mumbaiport.gov.in/show_tenders.php?lang=1&depid=1&catid=3"

def connect_sheet():
    creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS"])
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]

    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open("Mumbai Port Tender Tracker").sheet1

def get_existing(sheet):
    try:
        return set(sheet.col_values(1)[1:])
    except:
        return set()

def scrape():
    sheet = connect_sheet()
    existing = get_existing(sheet)

    headers = {"User-Agent":"Mozilla/5.0"}
    res = requests.get(URL, headers=headers, verify=False)
    soup = BeautifulSoup(res.text, "html.parser")

    rows = soup.find_all("tr")[1:]

    for r in rows:
        cols = r.find_all("td")
        if len(cols) < 6:
            continue

        tender_no = cols[1].text.strip()
        desc = cols[2].text.strip()
        date = cols[3].text.strip()

        if tender_no in existing:
            continue

        # extract onclick
        detail_btn = cols[-1].find("a")
        onclick = detail_btn.get("onclick","")

        # get internal id
        import re
        match = re.search(r'\((.*?)\)', onclick)
        detail_link = ""

        if match:
            args = match.group(1).split(",")
            tender_id = args[0].strip()
            year = args[1].strip()

            detail_link = f"https://mumbaiport.gov.in/TenderDetail_CE.php?TenderID={tender_id}&TenderYear={year}"

        sheet.append_row([tender_no, desc, date, detail_link])
        print("Added:", tender_no)

def loop():
    while True:
        try:
            print("Checking tenders...")
            scrape()
        except Exception as e:
            print("Error:", e)
        time.sleep(3600)

loop()
