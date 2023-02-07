import sys

from dotenv import dotenv_values
from flask import Flask
from jinja2 import Environment, PackageLoader

cfg = dotenv_values(".env")

sys.path.append(f"{cfg['APP_HOME']}")
import data

meetings = Flask(__name__)
application = meetings
env = Environment(loader=PackageLoader('meetings', 'pages'))


@meetings.route(f"/{cfg['WWW']}")
@meetings.route(f"/{cfg['WWW']}/")
def contracts_main():
    main = env.get_template('meetings.html')
    context = data.meetings_main()
    return main.render(**context)
