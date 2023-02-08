
from dotenv import dotenv_values
from sqlalchemy import create_engine

from flask import session

from datetime import datetime as dt

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

    context['meetings'] = meetings
    return context
