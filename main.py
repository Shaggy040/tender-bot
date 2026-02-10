import requests
from bs4 import BeautifulSoup
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os

SHEET_NAME = "Mumbai Port Tender Tracker"


# -------- SCRAPER (NO BROWSER NOW) --------
def scrape():

    url = "https://mumbaiport.gov.in/show_tenders.php?lang=1&depid=1&catid=3"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    table = soup.find("table")

    rows = table.find_all("tr")[1:]

    tenders = []

    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 6:
            continue

        tender_no = cols[1].text.strip()
        desc = cols[2].text.strip()
        date = cols[3].text.strip()

        # details button
        link_tag = cols[6].find("a")
        pdf_link = ""

        if link_tag:
            detail_page = "https://mumbaiport.gov.in/" + link_tag["href"]

            detail_r = requests.get(detail_page, headers=headers)
            detail_soup = BeautifulSoup(detail_r.text, "html.parser")

            pdf = detail_soup.find("a", href=lambda x: x and "showfile.php" in x)
            if pdf:
                pdf_link = "https://mumbaiport.gov.in/" + pdf["href"]

        tenders.append([tender_no, desc, date, pdf_link])

    print("Total tenders found:", len(tenders))
    return tenders


# -------- GOOGLE SHEET --------
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


# -------- MAIN --------
if __name__ == "__main__":
    data = scrape()
    update_sheet(data)
