# TODO interpret mods lines to pull out "Agenda", "Agenda Packet", "Cancelled" and so on
# TODO write flask app here to show the data and configure the fetching.
# TODO separate the 'name - subname' parts into separate columns.
# TODO Why am I getting extra "added" numbers, even though it is not duplicatively adding?
# rrk 2023-02-03

import os
from datetime import datetime
from pprint import pprint
from time import sleep

from dotenv import dotenv_values
from selenium import webdriver
from selenium.webdriver.common.by import By
from sqlalchemy import create_engine

verbose = False
dry_run = False

cfg = dotenv_values(".env")
engine = create_engine(f"mysql+pymysql://{cfg['USR']}:{cfg['PWD']}@{cfg['HOST']}/{cfg['DB']}")
conn = engine.connect()


def get_pk(table_name):
    pk_row = conn.execute(f"select max(pk) as max from {table_name}").fetchone()
    if pk_row['max'] is None:
        return 0
    else:
        return int(pk_row['max'])


def date_value(scraped_date) -> datetime:
    # eg MONDAY, JANUARY 9, 2023  12:00 PM
    d = datetime.strptime(scraped_date, "%A, %B %d, %Y %I:%M %p")
    return d


def next_date_value(dt) -> str:
    return dt.strftime("%Y-%m-%d %H:%M")


def scrape_meetings() -> dict:

    agent1 = "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6)"
    agent2 = "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36"
    agent = f"{agent1} {agent2}"

    options = webdriver.FirefoxOptions()
    options.add_argument('--headless')
    options.add_argument("--disable-extensions")
    options.add_argument('--disable-application-cache')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument(agent)

    driver = webdriver.Firefox(options=options)
    driver.get("http://sccgov.iqm2.com/citizens/calendar.aspx")
    sleep(3)

    mtg_entries = list()

    for elt in driver.find_elements(By.CLASS_NAME, 'MeetingRow'):

        mtg_entry = dict()

        mtg_entry['resources'] = list()
        for img in elt.find_elements(By.TAG_NAME, 'IMG'):

            lines = img.get_attribute('title').split('\r')
            mtg_entry['when'] = lines[0]

            for line in lines:
                if line.startswith('Board:'):
                    mtg_entry['board'] = line.split('\t')[-1]
                if line.startswith('Type:'):
                    mtg_entry['type'] = line.split('\t')[-1]
                if line.startswith('Status:'):
                    mtg_entry['status'] = line.split('\t')[-1]

        for link in elt.find_elements(By.TAG_NAME, 'A'):
            if link.get_attribute('href').find('Detail_Meeting') >= 0:
                mtg_resource = dict()
                mtg_resource['name'] = 'Detail_Meeting'
                mtg_resource['url'] = link.get_attribute('href')
                mtg_entry['resources'].append(mtg_resource)

            if link.get_attribute('class') != 'HiddenDocumentLink':
                if link.get_attribute('href').find('FileOpen.aspx') >= 0:
                    mtg_resource = dict()
                    mtg_resource['name'] = link.text
                    mtg_resource['url'] = link.get_attribute('href')
                    mtg_entry['resources'].append(mtg_resource)

            if link.text == 'Video':
                mtg_resource = dict()
                mtg_resource['name'] = link.text
                mtg_entry['resources'].append(mtg_resource)

        mtg_entries.append(mtg_entry)

    scraped = dict()

    driver.quit()

    for mtg_entry in mtg_entries:
        key = f"{mtg_entry['board']} - {mtg_entry['type']}|{mtg_entry['when']}"
        scraped[key] = mtg_entry

    if verbose:
        print(f"\nscraped meetings:\n")
        pprint(mtg_entries, compact=True)

    return scraped


def fetch_db_meetings() -> dict:

    rows = conn.execute("select * from meetings").fetchall()
    meetings = dict()
    for row in rows:
        meetings[f"{row['full_name']}|{row['scp_time']}"] = row['mods']

    if verbose:
        print(f"\nmeetings:\n")
        pprint(meetings, compact=True)

    return meetings


def added_meetings(scraped, fetched) -> dict:
    found = dict()
    for scrape_key in scraped:
        if scrape_key not in fetched:
            found[scrape_key] = scraped[scrape_key]
    return found


def updated_meetings(scraped, fetched) -> dict:
    found = dict()
    for scrape_key in scraped:
        if scrape_key in fetched:
            if scraped[scrape_key] != fetched[scrape_key]:
                found[scrape_key] = scraped[scrape_key]
    return found


def insert_meetings(meetings) -> int:

    mtg_pk = get_pk('meetings')
    res_pk = get_pk('resources')

    for scrape in meetings:

        mtg_pk += 1

        full_name, scp_time = scrape.split('|')
        full_name = full_name.replace("'", "''")
        mtg_name, sub_name = full_name.split(' - ')
        mtg_time = next_date_value(date_value(scp_time))

        sql = f"""insert into meetings
                (pk, full_name, mtg_name, sub_name, mtg_time, scp_time, status, created, updated)
                values (
                {mtg_pk},
                '{full_name}', '{mtg_name}', '{sub_name}',
                '{mtg_time}', '{scp_time}',
                '{meetings[scrape]['status']}',
                unix_timestamp(), unix_timestamp())"""
        if verbose:
            print(f"\n{sql}")
        if not dry_run:
            conn.execute(sql)

        for resource in meetings[scrape]['resources']:

            if 'url' in resource:
                url = f"'{resource['url']}'"
            else:
                url = 'NULL'

            sql = f"""insert into resources
                (pk, meeting_pk, name, url)
                values ({res_pk}, {mtg_pk}, '{resource['name']}', {url})"""
            if verbose:
                print(f"\n{sql}")
            if not dry_run:
                conn.execute(sql)
            res_pk += 1

    return len(scraped_mtgs)


def update_meetings(meetings) -> int:
    for scrape in meetings:
        full_name, scp_time = scrape.split('|')
        full_name = full_name.replace("'", "''")
        mods = meetings[scrape]
        sql = f"""update meetings set mods = '{mods}', updated = unix_timestamp()
            where full_name = '{full_name}' and scp_time = '{scp_time}'"""
        if verbose:
            print(f"\n{sql}")
        if not dry_run:
            conn.execute(sql)
    return len(meetings)


if __name__ == '__main__':

    scraped_mtgs = scrape_meetings()

    fetched_mtgs = fetch_db_meetings()

    print(f"\nmeetings scraped # {len(scraped_mtgs)}, fetched # {len(fetched_mtgs)}")

    addeds = added_meetings(scraped_mtgs, fetched_mtgs)
    added = insert_meetings(addeds)

    updateds = updated_meetings(scraped_mtgs, fetched_mtgs)
    updated = update_meetings(updateds)

    asis = len(fetched_mtgs) - updated

    print(f"\nmeetings unchanged # {asis}, added # {len(addeds)}, updated # {len(updateds)}")
    print("")

    if os.path.exists("geckodriver.log"):
        os.remove("geckodriver.log")
