
from datetime import datetime as dt

from dotenv import dotenv_values
from flask import session
from sqlalchemy import create_engine

cfg = dotenv_values(".env")

engine = create_engine(f"mysql+pymysql://{cfg['USR']}:{cfg['PWD']}@{cfg['HOST']}/{cfg['DB']}")
conn = engine.connect()

def db_exec(sql_engine, sql):
    if sql.strip().startswith('select'):
        return [dict(r) for r in sql_engine.execute(sql).fetchall()]
    else:
        return sql_engine.execute(sql)

def meetings_main(short_code) -> dict:
    context = dict()

    context['code'] = short_code

    if short_code == '':
        sql = "select name, short_code from mtg_entities"
        entities = db_exec(conn, sql)
        context['entities'] = entities
        return context
    else:
        sql = f"select name from mtg_entities where short_code = '{short_code}'"
        context['entity'] = db_exec(conn, sql)[0]['name']

    mtgs_displayed = session.get('mtgs_displayed')
    context['mtgs_displayed'] = mtgs_displayed

    if mtgs_displayed == 'all':
        sql = f"""
            select * from meetings m1, mtg_entities e1
            where m1.entity_pk = e1.pk
                and e1.short_code = '{short_code}'
        """
    else:
        now = dt.now().strftime('%Y-%m-%d 00:00:00')
        sql = f"""
            select * from meetings m1, mtg_entities e1
            where m1.entity_pk = e1.pk
                and e1.short_code = '{short_code}'
                and mtg_time >= '{now}'
        """

    meetings = db_exec(conn, sql)

    for meeting in meetings:
        meeting['created'] = dt.fromtimestamp(int(meeting['created'])).strftime("%Y-%m-%d_%H:%M")
        if meeting['updated'] is not None:
            meeting['updated'] = dt.fromtimestamp(int(meeting['updated'])).strftime("%Y-%m-%d_%H:%M")

    mtgs_by_pk = dict()
    for meeting in meetings:
        mtgs_by_pk[int(meeting['pk'])] = meeting

    # TODO not necessary to limit this fetch to the entity. But when there are more...
    sql = "select meeting_pk, name, url from resources"

    resources = db_exec(conn, sql)

    for resource in resources:
        mpk = int(resource['meeting_pk'])
        if mpk in mtgs_by_pk:
            mtgs_by_pk[mpk][resource['name']] = resource['url']

    context['meetings'] = meetings
    return context
