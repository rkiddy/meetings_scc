
import unittest
from datetime import datetime
from unittest.mock import Mock

import meetings as m

class TestMeetingsImport(unittest.TestCase):

    def test_date_value(self):
        assert datetime(2023, 1, 6, 10, 0) == m.date_value("FRIDAY, JANUARY 6, 2023 10:00 AM")
        assert datetime(2023, 1, 6, 12, 15) == m.date_value("FRIDAY, JANUARY 6, 2023 12:15 PM")
        assert datetime(2023, 1, 9, 8, 30) == m.date_value("MONDAY, JANUARY 9, 2023 8:30 AM")
        assert datetime(2023, 1, 9, 13, 30) == m.date_value("MONDAY, JANUARY 9, 2023 1:30 PM")

        assert "2023-01-06 10:00" == m.next_date_value(datetime(2023, 1, 6, 10, 0))
        assert "2023-01-06 12:15" == m.next_date_value(datetime(2023, 1, 6, 12, 15))
        assert "2023-01-09 08:30" == m.next_date_value(datetime(2023, 1, 9, 8, 30))
        assert "2023-01-09 13:30" == m.next_date_value(datetime(2023, 1, 9, 13, 30))

    def test_another(self):
        # now that I have figured out the mocking (again), I need to test.
        pass

if __name__ == '__main__':
    unittest.main()
