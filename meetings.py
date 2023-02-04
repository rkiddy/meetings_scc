# TODO put the logic into methods and use a __main__ check to allow testing
# TODO interpret mods lines to pull out "Agenda", "Agenda Packet", "Cancelled" and so on
# TODO write flask app here to show the data and configure the fetching.
# rrk 2023-02-03

from datetime import datetime
from time import sleep

from dotenv import dotenv_values
from selenium import webdriver
from selenium.webdriver.common.by import By
from sqlalchemy import create_engine, inspect

verbose = False

def date_value(scraped_date):
    # eg Jan 6, 2023 12:15 PM
    d = datetime.strptime(scraped_date, "%b %d, %Y %I:%M %p")
    return d

def next_date_value(dt):
    return dt.strftime("%Y-%m-%d %H:%M")

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
idx=0
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

cfg = dotenv_values(".env")

engine = create_engine(f"mysql+pymysql://{cfg['USR']}:{cfg['PWD']}@{cfg['HOST']}/{cfg['DB']}")
conn = engine.connect()
inspector = inspect(engine)

rows = conn.execute("select * from meetings").fetchall()
meetings = dict()
for row in rows:
    meetings[f"{row['mtg_name']}|{row['mtg_time']}"] = row['mods']

if len(rows) > 0:
    next_pk = sorted([d['pk'] for d in rows])[-1] + 1
else:
    next_pk = 1

to_add = list()
to_update = list()

added = 0
updated = 0
asis = 0

for scrape in scraped:
    if scrape in meetings:
        # meeting exists but might need update
        if scraped[scrape] != meetings[scrape]:
            parts = scrape.split('|')
            to_update.append({
                'name': parts[0].replace("'", "''"),
                'when': next_date_value(date_value(parts[1])),
                'mods': scraped[scrape]
            })
        else:
            asis += 1
    else:
        # meeting not stored
        parts = scrape.split('|')
        to_add.append({
            'name': parts[0].replace("'", "''"),
            'when': next_date_value(date_value(parts[1])),
            'mods': scraped[scrape]
        })

for add in to_add:
    sql = f"""insert into meetings (pk, mtg_name, mtg_time, mods) values (
            {next_pk}, '{add['name']}', 
            '{add['when']}', '{add['mods']}')"""
    if verbose:
        print(f"\n{sql}")
    conn.execute(sql)
    next_pk += 1
    added += 1

for update in to_update:
    sql = f"""update meetings set mods = '{update['mods']}
        where mtg_name = '{update['name']}' and
        mtg_time = '{update['when']}'"""
    if verbose:
        print(f"\n{sql}")
    conn.execute(sql)
    updated += 1

print("")
print(f"meetings unchanged # {asis}, added # {added}, updated # {updated}")
print("")
