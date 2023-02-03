# meetings_scc

Scrape data from the Meetings page of Santa Clara County for the purpose of notifications.

To run:

     % virtualenv .venv
     % source .venv/bin/activate
     % pip install -r requirements.txt (when this is properly created)
     EOF
     % pytest test.py
     % cat - > .env <<EOF
     USR=<you>
     PWD=<your>
     HOST=localhost
     DB=<your>
     EOF
     % python3 meetings.py

