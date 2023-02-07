
from dotenv import dotenv_values
from sqlalchemy import create_engine

from datetime import datetime as dt

cfg = dotenv_values(".env")

engine = create_engine(f"mysql+pymysql://{cfg['USR']}:{cfg['PWD']}@{cfg['HOST']}/{cfg['DB']}")
conn = engine.connect()

def meetings_main() -> dict:
    context = dict()

    sql = "select * from meetings order by mtg_time"
    meetings = [dict(d) for d in conn.execute(sql).fetchall()]

    for meeting in meetings:
        meeting['created'] = dt.fromtimestamp(int(meeting['created'])).strftime("%Y-%m-%d_%H:%M")
        if meeting['updated'] is not None:
            meeting['updated'] = dt.fromtimestamp(int(meeting['updated'])).strftime("%Y-%m-%d_%H:%M")

    context['meetings'] = meetings
    return context
