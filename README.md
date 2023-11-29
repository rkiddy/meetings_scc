# meetings_scc

Scrape data from the Meetings page of Santa Clara County for the purpose of notifications.

To run:

     % mysql
     mysql> create database meetings;
     mysql> quit
     % cat data.sql | mysql meetings
     % virtualenv .venv
     % source .venv/bin/activate
     % pip install -r requirements.txt
     % pytest test.py
     % cat - > .env <<EOF
     USR=<you>
     PWD=<your>
     HOST=localhost
     DB=<your>
     EOF
     % python3 meetings.py

As of now, the data being stored looks like this:

           pk: 3
     mtg_name: Assessment Appeals - Hearing
     mtg_time: 2023-01-04 09:00
         mods: Agenda
     ******
           pk: 4
     mtg_name: Metropolitan City of Florence, Italy Sister-County Commission - Regular Meeting
     mtg_time: 2023-01-05 19:00
         mods: Agenda   Agenda Packet         Video
     ******
           pk: 5
     mtg_name: Behavioral Health Board - Access Committee
     mtg_time: 2023-01-06 10:00
         mods: Agenda   Agenda Packet         Video
     ******
           pk: 6
     mtg_name: Domestic Violence Council - Regular Meeting
     mtg_time: 2023-01-06 12:15
         mods: Cancelled
