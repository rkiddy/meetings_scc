import sys

from dotenv import dotenv_values
from flask import Flask, redirect, session
from jinja2 import Environment, PackageLoader

cfg = dotenv_values(".env")

sys.path.append(f"{cfg['APP_HOME']}")
import data

meetings = Flask(__name__)
meetings.config['mtgs_displayed'] = 'current'
meetings.config['SESSION_TYPE'] = 'filesystem'
meetings.secret_key = b'8ec7851e-13be-4039-97ac-ba3046378968'
application = meetings
env = Environment(loader=PackageLoader('meetings', 'pages'))


@meetings.route(f"/{cfg['WWW']}")
@meetings.route(f"/{cfg['WWW']}/<code>")
def meetings_main(code = ''):
    main = env.get_template('meetings.html')
    context = data.meetings_main(code)
    return main.render(**context)


@meetings.route(f"/{cfg['WWW']}/<code>/show_curr_mtgs")
def meetings_set_mtgs_curr(code):
    session['mtgs_displayed'] = 'current'
    return redirect(f"/{cfg['WWW']}/{code}")


@meetings.route(f"/{cfg['WWW']}/<code>/show_all_mtgs")
def meetings_set_mtgs_all(code):
    session['mtgs_displayed'] = 'all'
    return redirect(f"/{cfg['WWW']}/{code}")
