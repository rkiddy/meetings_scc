
import argparse
import traceback

import requests
from dotenv import dotenv_values
from sqlalchemy import create_engine

cfg = dotenv_values(".env")
engine = create_engine(f"mysql+pymysql://{cfg['USR']}:{cfg['PWD']}@{cfg['HOST']}/{cfg['DB']}")
conn = engine.connect()


def fetch_web(url) -> list:
    resp = requests.get(url).content.decode("utf-8")
    resp = resp.replace('\r', '')
    return resp.split('\n')

def db_exec(sql_engine, sql):
    if sql.strip().lower().startswith('select'):
        return [dict(r) for r in sql_engine.execute(sql).fetchall()]
    else:
        return sql_engine.execute(sql)

def fetch_sjusd_meeting_dates(resp_lines) -> dict:

    meetings = dict()
    in_mtgs = False
    m_id = None

    for line in resp_lines:

        if line == '];ContentPlaceHolder1_MeetingGrid_newGrid.dataBuffer=[':
            in_mtgs = True
            continue

        if in_mtgs and line.find('ContentPlaceHolder1_MeetingGrid_newGrid') >= 0:
            # end of list of meetings
            in_mtgs = False
            continue

        if in_mtgs and line.find('{') >= 0:
            # start of a meeting
            m_id = None
            continue

        if in_mtgs and line.find('}') >= 0:
            meetings[m_id]['address'] = ', '.join(meetings[m_id]['addresses'])
            meetings[m_id].pop('addresses')
            continue

        if in_mtgs and line.find('Master_MeetingID') >= 0:
            m_id = int(line.split(':')[-1].strip().replace(',', ''))
            meetings[m_id] = dict()
            meetings[m_id]['id'] = m_id
            continue

        if in_mtgs and line.find('MM_MeetingTitle') >= 0:
            info = line.split(':')[-1].replace('"', '').strip().replace(',', '')
            meetings[m_id]['name'] = info
            continue

        if in_mtgs and line.find('MM_DateTime') >= 0:
            idx = line.find(':') + 2
            info = line[idx:].replace('"', '').strip().replace(',', '')
            dt, ti = info.split('T')
            meetings[m_id]['meet_time'] = f"{dt} {ti[:5]}"
            continue

        if in_mtgs and line.find('MM_Address') >= 0:
            if 'addresses' not in meetings[m_id]:
                meetings[m_id]['addresses'] = list()
            idx = line.find(':') + 2
            info = line[idx:].replace('"', '').strip().replace(',', '')
            meetings[m_id]['addresses'].append(info)
            continue

        if in_mtgs and line.find('ML_TypeTitle') >= 0:
            # TODO maybe just equal to MM_MeetingTitle
            continue

        if in_mtgs and line.find('MinutesStatus') >= 0:
            # TODO get the minutes and put in resources.
            continue

    return meetings

def find_new_meetings(all_found):

    sql = f"""
        select * from meetings m1, mtg_entities e1
        where m1.entity_pk = e1.pk
            and e1.short_code = 'SJUSD'
    """

    added_mtgs = list()

    in_db = db_exec(engine, sql)
    m_ids_in_db = [int(r['mtg_id']) for r in in_db]

    m_ids_found = list(all_found.keys())

    for m_id in m_ids_found:
        if m_id not in m_ids_in_db:
            added_mtgs.append(all_found[m_id])

    return added_mtgs

def find_updated_meetings(all_found):
    return []

def save_meetings(new_found):

    sql = "select max(pk) as pk from meetings"
    max_pk = db_exec(engine, sql)[0]['pk']

    pk = max_pk

    sql = "select pk from mtg_entities where short_code = 'SJUSD'"
    sjusd_pk = db_exec(engine, sql)[0]['pk']

    for found_mtg in new_found:
        cols = list()
        values = list()

        pk += 1
        cols.append('pk')
        values.append(f"'{pk}'")

        cols.append('entity_pk')
        values.append(f"{sjusd_pk}")

        cols.append('mtg_name')
        values.append(f"'{found_mtg['name']}'")

        cols.append('sub_name')
        values.append(f"'{found_mtg['address']}'")

        cols.append('full_name')
        values.append(f"'{found_mtg['name']} - {found_mtg['address']}'")

        cols.append('mtg_time')
        values.append(f"'{found_mtg['meet_time']}'")

        cols.append('scp_time')
        values.append(f"'{found_mtg['meet_time']}'")

        cols.append('mtg_id')
        values.append(f"'{found_mtg['id']}'")

        cols.append('created')
        values.append("unix_timestamp()")

        sql = f"insert into meetings ({', '.join(cols)}) values ({', '.join(values)})"
        db_exec(engine, sql)

def update_meetings(updated_found):
    pass

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--verbose', '-v', action='store_true')Python tests in test.py
    parser.add_argument('--dry-run', action='store_true')

    args = parser.parse_args()

    verbose = args.verbose
    dry_run = args.dry_run

    try:
        lines = fetch_web('https://simbli.eboardsolutions.com/SB_Meetings/SB_MeetingListing.aspx?S=36030421')
        print(f"lines found in web site: {len(lines)}")

        found = fetch_sjusd_meeting_dates(lines)
        print(f"meetings found: {len(found)}")

        new_mtgs = find_new_meetings(found)
        print(f"new meetings found: {len(new_mtgs)}")

        updated_mtgs = find_updated_meetings(found)

        save_meetings(new_mtgs)
        update_meetings(updated_mtgs)

    except Exception as e:
        traceback.print_exc()

    finally:
        pass
