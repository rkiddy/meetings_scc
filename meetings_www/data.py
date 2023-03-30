
from datetime import datetime as dt

from dotenv import dotenv_values
from flask import session
from sqlalchemy import create_engine

cfg = dotenv_values(".env")

engine = create_engine(f"mysql+pymysql://{cfg['USR']}:{cfg['PWD']}@{cfg['HOST']}/{cfg['DB']}")
conn = engine.connect()

def meetings_main() -> dict:
    context = dict()

    mtgs_displayed = session.get('mtgs_displayed')
    context['mtgs_displayed'] = mtgs_displayed

    if mtgs_displayed == 'all':
        sql = "select * from meetings"
    else:
        now = dt.now().strftime('%Y-%m-%d 00:00:00')
        sql = f"select * from meetings where mtg_time >= '{now}'"

    meetings = [dict(d) for d in conn.execute(sql).fetchall()]

    for meeting in meetings:
        meeting['created'] = dt.fromtimestamp(int(meeting['created'])).strftime("%Y-%m-%d_%H:%M")
        if meeting['updated'] is not None:
            meeting['updated'] = dt.fromtimestamp(int(meeting['updated'])).strftime("%Y-%m-%d_%H:%M")

    mtgs_by_pk = dict()
    for meeting in meetings:
        mtgs_by_pk[int(meeting['pk'])] = meeting

    sql = "select meeting_pk, name, url from resources"

    resources = [dict(d) for d in conn.execute(sql).fetchall()]

    for resource in resources:
        mpk = int(resource['meeting_pk'])
        if mpk in mtgs_by_pk:
            mtgs_by_pk[mpk][resource['name']] = resource['url']

    context['meetings'] = meetings
    return context
