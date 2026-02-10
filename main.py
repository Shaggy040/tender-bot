{\rtf1\ansi\ansicpg1252\cocoartf2867
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import requests\
from bs4 import BeautifulSoup\
import gspread\
from oauth2client.service_account import ServiceAccountCredentials\
import time\
\
BASE_URL = "https://mumbaiport.gov.in/"\
URL = "https://mumbaiport.gov.in/show_tenders.php?lang=1&depid=1&catid=3"\
\
def connect_sheet():\
    scope = [\
        "https://spreadsheets.google.com/feeds",\
        "https://www.googleapis.com/auth/drive"\
    ]\
\
    creds = ServiceAccountCredentials.from_json_keyfile_name(\
        "credentials.json", scope\
    )\
\
    client = gspread.authorize(creds)\
    return client.open("Mumbai Port Tender Tracker").sheet1\
\
def scrape():\
    print("Checking tenders...")\
    sheet = connect_sheet()\
    existing = sheet.col_values(1)\
\
    headers = \{"User-Agent": "Mozilla/5.0"\}\
    res = requests.get(URL, headers=headers, timeout=30)\
\
    soup = BeautifulSoup(res.text, "html.parser")\
    table = soup.find("table")\
    rows = table.find_all("tr")\
\
    for row in rows[1:]:\
        cols = row.find_all("td")\
        if len(cols) < 7:\
            continue\
\
        tender = cols[1].text.strip()\
        desc = cols[2].text.strip()\
        date = cols[3].text.strip()\
\
        link_tag = cols[6].find("a")\
        if link_tag and link_tag.get("href"):\
            detail_link = BASE_URL + link_tag.get("href")\
        else:\
            detail_link = "No Link"\
\
        if tender not in existing and tender != "":\
            sheet.append_row([tender, desc, date, detail_link])\
            print("Added:", tender)\
\
while True:\
    scrape()\
    time.sleep(3600)\
}