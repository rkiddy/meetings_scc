
from datetime import datetime

def date_value(scraped_date):
    # eg Jan 6, 2023 12:15 PM
    d = datetime.strptime(scraped_date, "%b %d, %Y %I:%M %p")
    return d

def next_date_value(dt):
    return dt.strftime("%Y-%m-%d %H:%M")

# TODO use the methods in meetings.py once it is protected by a __main__ check.

def test_date_format():

    assert datetime(2023, 1, 6, 10, 0) == date_value("Jan 6, 2023 10:00 AM")
    assert datetime(2023, 1, 6, 12, 15) == date_value("Jan 6, 2023 12:15 PM")
    assert datetime(2023, 1, 9, 8, 30) == date_value("Jan 9, 2023 8:30 AM")
    assert datetime(2023, 1, 9, 13, 30) == date_value("Jan 9, 2023 1:30 PM")

    assert "2023-01-06 10:00" == next_date_value(datetime(2023, 1, 6, 10, 0))
    assert "2023-01-06 12:15" == next_date_value(datetime(2023, 1, 6, 12, 15))
    assert "2023-01-09 08:30" == next_date_value(datetime(2023, 1, 9, 8, 30))
    assert "2023-01-09 13:30" == next_date_value(datetime(2023, 1, 9, 13, 30))
