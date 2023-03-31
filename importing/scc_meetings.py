# TODO write flask app here to show the data and configure the fetching.
# TODO separate the 'name - subname' parts into separate columns.
# TODO Why am I getting extra "added" numbers, even though it is not duplicatively adding?
# rrk 2023-02-03

import argparse
import os
import traceback
from datetime import datetime
from pprint import pprint
from time import sleep

from dotenv import dotenv_values
from selenium import webdriver
from selenium.webdriver.common.by import By
from sqlalchemy import create_engine

cfg = dotenv_values(".env")
engine = create_engine(f"mysql+pymysql://{cfg['USR']}:{cfg['PWD']}@{cfg['HOST']}/{cfg['DB']}")
conn = engine.connect()


def get_pk(table_name):
    sql = f"select max(pk) as max from {table_name}"
    pk_row = conn.execute(sql).fetchone()
    if pk_row['max'] is None:
        return 0
    else:
        return int(pk_row['max'])


def get_entity_pk(entity_code):
    sql = f"select pk from mtg_entities where short_code = '{entity_code}'"
    return conn.execute(sql).fetchone()

def date_value(scraped_date) -> datetime:
    # eg MONDAY, JANUARY 9, 2023  12:00 PM
    d = datetime.strptime(scraped_date, "%A, %B %d, %Y %I:%M %p")
    return d

def next_date_value(dt) -> str:
    return dt.strftime("%Y-%m-%d %H:%M")

def scrape_meetings() -> dict:
    """
    Scrape the SCC Meetings list and generate dictionaries to capture
    the meetings found.
    We return objects like this:
    {
        'Youth Task Force - Regular Meeting|WEDNESDAY, SEPTEMBER 13, 2023  5:00 PM': {
            'board': 'Youth Task Force',
            'resources': {
                'Detail_Meeting': 'http://sccgov.iqm2.com/Citizens/Detail_Meeting.aspx?ID=15076'
            },
            'status': 'Scheduled',
            'type': 'Regular Meeting',
            'when': 'WEDNESDAY, SEPTEMBER 13, 2023  5:00 PM'
        }
    }
    The "full name" is made up of the "board" value with the "type" value.
    The meeting's full name and the scrape-time (seen above as the key)
    uniquely identify the meeting.
    :return: dict
    """

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

        mtg_entry['resources'] = dict()
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
                name = 'Detail_Meeting'
                url = link.get_attribute('href')
                mtg_entry['resources'][name] = url

            if link.get_attribute('class') != 'HiddenDocumentLink':
                if link.get_attribute('href').find('FileOpen.aspx') >= 0:
                    name = link.text
                    url = link.get_attribute('href')
                    mtg_entry['resources'][name] = url

            if link.text == 'Video':
                name = link.text
                mtg_entry['resources'][name] = None

        mtg_entries.append(mtg_entry)

    scraped = dict()

    driver.quit()

    for mtg_entry in mtg_entries:
        key = f"{mtg_entry['board']} - {mtg_entry['type']}|{mtg_entry['when']}"
        scraped[key] = mtg_entry

    if verbose:
        print(f"\nscraped meetings:\n")
        pprint(scraped, compact=True)

    return scraped


def fetch_db_meetings() -> dict:
    """
    Fetch known meetings from the database and create a dictionary that
    can be compared to the scraped meetings found.
    We only check for changes to resources and status values. These
    are the only things that should change.
    We return objects like this:
    { 'resources': {
        'Detail_Meeting': 'http://sccgov.iqm2.com/Citizens/Detail_Meeting.aspx?ID=15076'
      },
      'status': 'Scheduled'
    }}
    :return: dict
    """
    sql = """
        select m1.full_name, m1.scp_time, m1.status, r1.name, r1.url
        from meetings m1, resources r1
        where m1.pk = r1.meeting_pk
    """
    rows = [dict(d) for d in conn.execute(sql).fetchall()]

    meetings = dict()

    for row in rows:
        key = f"{row['full_name']}|{row['scp_time']}"
        if key not in meetings:
            meetings[key] = dict()
            meetings[key]['status'] = row['status']
            meetings[key]['resources'] = dict()
            meetings[key]['resources'][row['name']] = row['url']
        else:
            meetings[key]['resources'][row['name']] = row['url']

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
            if scraped[scrape_key]['status'] != fetched[scrape_key]['status']:
                found[scrape_key] = scraped[scrape_key]
                continue
            if scraped[scrape_key]['resources'] != fetched[scrape_key]['resources']:
                found[scrape_key] = scraped[scrape_key]
                continue
    return found


def insert_meetings(meetings) -> int:

    mtg_pk = get_pk('meetings')
    res_pk = get_pk('resources')

    epk = None

    for scrape in meetings:

        if epk is None:
            epk = get_entity_pk('SCC')

        mtg_pk += 1

        full_name, scp_time = scrape.split('|')
        full_name = full_name.replace("'", "''")
        mtg_name, sub_name = full_name.split(' - ')
        mtg_time = next_date_value(date_value(scp_time))

        sql = f"""insert into meetings
                (pk, entity_pk, full_name, mtg_name, sub_name, mtg_time, scp_time, status, created, updated)
                values (
                {mtg_pk}, {epk},
                '{full_name}', '{mtg_name}', '{sub_name}',
                '{mtg_time}', '{scp_time}',
                '{meetings[scrape]['status']}',
                unix_timestamp(), unix_timestamp())"""
        if verbose:
            print(f"\n{sql}")
        if not dry_run:
            conn.execute(sql)

        for name in meetings[scrape]['resources']:

            res_pk += 1

            url = meetings[scrape]['resources'][name]

            if url is None:
                url = 'NULL'
            else:
                url = f"'{url}'"

            sql = f"""insert into resources
                (pk, meeting_pk, name, url)
                values ({res_pk}, {mtg_pk}, '{name}', {url})"""
            if verbose:
                print(f"\n{sql}")
            if not dry_run:
                conn.execute(sql)

    return len(meetings)


def update_meetings(meetings) -> int:

    res_pk = get_pk('resources')

    for scrape in meetings:
        full_name, scp_time = scrape.split('|')
        full_name = full_name.replace("'", "''")

        sql = f"select pk from meetings where full_name = '{full_name}' and scp_time = '{scp_time}'"
        if verbose:
            print(f"sql: {sql}")
        mtg_pk = conn.execute(sql).fetchone()['pk']

        sql1 = f"""
            update meetings set status = '{meetings[scrape]['status']}', updated = unix_timestamp()
            where full_name = '{full_name}'
        """
        sql2 = f"""
            delete from resources where meeting_pk =
            (select pk from meetings where full_name = '{full_name}' and scp_time = '{scp_time}')
        """
        sql3 = "insert into resources (pk, meeting_pk, name, url) values "
        adds = list()
        for name in meetings[scrape]['resources']:

            res_pk += 1

            url = meetings[scrape]['resources'][name]
            if url is None:
                url = 'NULL'
            else:
                url = f"'{url}'"

            adds.append(f"({res_pk}, {mtg_pk}, '{name}', {url})")

        sql3 = sql3 + ','.join(adds)

        if verbose:
            print(f"\nsql1: {sql1}\nsql2: {sql2}\nsql3: {sql3}")
        if not dry_run:
            conn.execute(sql1)
            conn.execute(sql2)
            conn.execute(sql3)

    return len(meetings)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--verbose', '-v', action='store_true')
    parser.add_argument('--dry-run', action='store_true')

    args = parser.parse_args()

    verbose = args.verbose
    dry_run = args.dry_run

    try:
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

    except Exception as e:
        traceback.print_exc()

    finally:
        if os.path.exists("geckodriver.log"):
            os.remove("geckodriver.log")
