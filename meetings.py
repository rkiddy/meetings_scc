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


def date_value(scraped_date):
    # eg Jan 6, 2023 12:15 PM
    d = datetime.strptime(scraped_date, "%b %d, %Y %I:%M %p")
    return d


def next_date_value(dt):
    return dt.strftime("%Y-%m-%d %H:%M")


def scrape_meetings():

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
        mtg_entries.append(elt.text)
    driver.quit()

    scraped = dict()
    for entry in mtg_entries:
        lines = entry.split('\n')
        when = lines[0].strip()
        name = lines[-1].strip()
        if len(lines) == 3:
            mods = lines[1].strip()
        else:
            mods = ''
        scraped[f"{name}|{when}"] = mods

    if verbose:
        print(f"\nscraped:\n")
        pprint(scraped, compact=True)

    return scraped


def fetch_db_meetings():

    rows = conn.execute("select * from meetings").fetchall()
    meetings = dict()
    for row in rows:
        meetings[f"{row['mtg_name']}|{row['scp_time']}"] = row['mods']

    if verbose:
        print(f"\nmeetings:\n")
        pprint(meetings, compact=True)

    return meetings


def added_meetings(scraped, fetched):
    found = dict()
    for scrape_key in scraped:
        if scrape_key not in fetched:
            found[scrape_key] = scraped[scrape_key]
    return found


def updated_meetings(scraped, fetched):
    found = dict()
    for scrape_key in scraped:
        if scrape_key in fetched:
            if scraped[scrape_key] != fetched[scrape_key]:
                found[scrape_key] = scraped[scrape_key]
    return found


def insert_meetings(meetings):

    pk_row = conn.execute("select max(pk) as max from meetings").fetchone()
    if pk_row['max'] is None:
        pk = 0
    else:
        pk = int(pk_row['max'])

    for scrape in meetings:
        mtg_name, scp_time = scrape.split("|")
        mtg_name = mtg_name.replace("'", "''")
        mtg_time = next_date_value(date_value(scp_time))
        mods = meetings[scrape]
        pk += 1
        sql = f"""insert into meetings
                (pk, mtg_name, mtg_time, scp_time, mods, created) values (
                {pk},
                '{mtg_name}',
                '{mtg_time}',
                '{scp_time}',
                '{mods}',
                unix_timestamp())"""
        if verbose:
            print(f"\n{sql}")
        if not dry_run:
            conn.execute(sql)

    return len(scraped_mtgs)


def update_meetings(meetings):
    for scrape in meetings:
        mtg_name, scp_time = scrape.split("|")
        mtg_name = mtg_name.replace("'", "''")
        mods = meetings[scrape]
        sql = f"""update meetings set mods = '{mods}', updated = unix_timestamp()
            where mtg_name = '{mtg_name}' and scp_time = '{scp_time}'"""
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
