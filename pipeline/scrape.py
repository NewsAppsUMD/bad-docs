import csv
import os
import time
import datetime
import requests
from bs4 import BeautifulSoup
from _paths import DATA_DIR

list_of_rows = []

# for the current year, use disciplinary
# for any previous year, use disciplinary_{year}

today = datetime.date.today()
years = [year for year in range(2014, today.year+1)]

for year in years:
    time.sleep(1)

    if year == today.year:
        url = 'https://www.mbp.state.md.us/disciplinary.aspx'
    else:
        url = f"https://www.mbp.state.md.us/disciplinary_{year}.aspx"

    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0'})
    html = response.content

    soup = BeautifulSoup(html, features="html.parser")
    table = soup.find('tbody')

    if table is None:
        print(f"Warning: no table found for {year} (status {response.status_code}), skipping")
        continue

    if year > 2016:
        for row in table.find_all('tr'):
            tds = row.find_all('td')
            if len(tds) == 4:
                # 2026+ layout: [link_only, name, type, date]
                link = tds[0].find('a')['href']
                if link.startswith('http'):
                    file_id = link.split('/')[-1].replace('.pdf', '')
                    url_val = link
                else:
                    file_id = link.split('/')[3].replace('.pdf', '')
                    url_val = "https://www.mbp.state.md.us" + link
                name = ' '.join(tds[1].text.split())
                doc_type = tds[2].text.strip()
                date = tds[3].text.strip()
                list_of_rows.append([file_id, url_val, name, doc_type, date, year])
            elif len(tds) == 3:
                list_of_cells = []
                for cell in tds:
                    if cell.find('a'):
                        id = cell.find('a')['href'].split('/')[3].replace('.pdf','')
                        list_of_cells.append(id)
                        list_of_cells.append("https://www.mbp.state.md.us" + cell.find('a')['href'])
                    text = cell.text.strip()
                    list_of_cells.append(text)
                list_of_cells.append(year)
                list_of_rows.append(list_of_cells)
    else:
        for row in table.find_all('tr'):
            list_of_cells = []
            for cell in row.find_all('td'):
                if cell.find('a'):
                    id = cell.find('a')['href'].split('/')[3].replace('.pdf','')
                    link = "https://www.mbp.state.md.us" + cell.find('a')['href']
                    type, name = cell.text.rsplit(' - ', 1)
                    list_of_cells = [id, link, name, type]
                else:
                    list_of_cells.append(cell.text)
                    list_of_cells.append(year)
            list_of_rows.append(list_of_cells)

outfile = open(os.path.join(DATA_DIR, "alerts.csv"), "w")
writer = csv.writer(outfile)
# i am writing a header row
writer.writerow(["file_id", "url", "name", "type", "date","year"])
writer.writerows(list_of_rows)