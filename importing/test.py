
import unittest
from datetime import datetime
from unittest.mock import Mock

import scc_meetings as scc_m
import sjusd_meetings as sjusd_m


class TestMeetingsImport(unittest.TestCase):

    # found_in_db = [
    #     {
    #         'mtg_name': 'Regular Session Board Meeting',
    #         'sub_name': 'Closed Session 5:00 PM, Board Room 855 Lenzen Avenue, (District Administration Building)',
    #         'full_name': 'Regular Session Board Meeting - Closed Session 5:00 PM, Board Room 855 Lenzen Avenue, (District Administration Building)',
    #         'mtg_time': '2023-03-23 18:00',
    #         'scp_time': '2023-03-23 18:00'
    #     }, {
    #         'mtg_name': 'Regular Session Board Meeting',
    #         'sub_name': 'Closed Session 5:00 PM, Board Room 855 Lenzen Avenue, (District Administration Building)',
    #         'full_name': 'Regular Session Board Meeting - Closed Session 5:00 PM, Board Room 855 Lenzen Avenue, (District Administration Building)',
    #         'mtg_time': '2023-03-09 18:00',
    #         'scp_time': '2023-03-09 18:00'
    #     }, {
    #         'mtg_name': 'Regular Session Board Meeting',
    #         'sub_name': 'Closed Session 5:00 PM, Board Room 855 Lenzen Avenue, (District Administration Building)',
    #         'full_name': 'Regular Session Board Meeting - Closed Session 5:00 PM, Board Room 855 Lenzen Avenue, (District Administration Building)',
    #         'mtg_time': '2023-02-16 18:00',
    #         'scp_time': '2023-02-16 18:00'
    #     }, {
    #         'mtg_name': 'Regular Session Board Meeting',
    #         'sub_name': 'Closed Session 5:00 PM, Board Room 855 Lenzen Avenue, (District Administration Building)',
    #         'full_name': 'Regular Session Board Meeting - Closed Session 5:00 PM, Board Room 855 Lenzen Avenue, (District Administration Building)',
    #         'mtg_time': '2023-02-02 18:00',
    #         'scp_time': '2023-02-02 18:00'
    #     }
    # ]

    def test_date_value(self):
        assert datetime(2023, 1, 6, 10, 0) == scc_m.date_value("FRIDAY, JANUARY 6, 2023 10:00 AM")
        assert datetime(2023, 1, 6, 12, 15) == scc_m.date_value("FRIDAY, JANUARY 6, 2023 12:15 PM")
        assert datetime(2023, 1, 9, 8, 30) == scc_m.date_value("MONDAY, JANUARY 9, 2023 8:30 AM")
        assert datetime(2023, 1, 9, 13, 30) == scc_m.date_value("MONDAY, JANUARY 9, 2023 1:30 PM")

        assert "2023-01-06 10:00" == scc_m.next_date_value(datetime(2023, 1, 6, 10, 0))
        assert "2023-01-06 12:15" == scc_m.next_date_value(datetime(2023, 1, 6, 12, 15))
        assert "2023-01-09 08:30" == scc_m.next_date_value(datetime(2023, 1, 9, 8, 30))
        assert "2023-01-09 13:30" == scc_m.next_date_value(datetime(2023, 1, 9, 13, 30))

    def test_fetch_sjusd_meeting_dates(self):
        mock = Mock()
        sjusd_m.fetch_web = mock
        sjusd_m.fetch_web.return_value = [line.strip() for line in open('tests/sjusd_sample.txt').readlines()]

        lines = sjusd_m.fetch_web("")

        expected = {
            19058: {
                'id': 19058,
                'name': 'Regular Session Board Meeting',
                'meet_time': '2023-03-23 18:00',
                'address': 'Closed Session 5:00 PM, Board Room 855 Lenzen Avenue, (District Administration Building)'
            },
            19057: {
                'id': 19057,
                'name': 'Regular Session Board Meeting',
                'meet_time': '2023-03-09 18:00',
                'address': 'Closed Session 5:00 PM, Board Room 855 Lenzen Avenue, (District Administration Building)'
            },
            18720: {
                'id': 18720,
                'name': 'Regular Session Board Meeting',
                'meet_time': '2023-02-16 18:00',
                'address': 'Closed Session 5:00 PM, Board Room 855 Lenzen Avenue, (District Administration Building)'
            },
            18426: {
                'id': 18426,
                'name': 'Regular Session Board Meeting',
                'meet_time': '2023-02-02 18:00',
                'address': 'Closed Session 5:00 PM, Board Room 855 Lenzen Avenue, (District Administration Building)'
            }
        }

        self.assertEqual(
            sjusd_m.fetch_sjusd_meeting_dates(lines),
            expected)

    def test_find_new_meetings(self):

        found_in_db = [
            {
                'mtg_name': 'Regular Session Board Meeting',
                'sub_name': 'Closed Session 5:00 PM, Board Room 855 Lenzen Avenue, (District Administration Building)',
                'full_name': 'Regular Session Board Meeting - Closed Session 5:00 PM, Board Room 855 Lenzen Avenue, (District Administration Building)',
                'mtg_time': '2023-02-16 18:00',
                'scp_time': '2023-02-16 18:00',
                'mtg_id': '18720'
            }, {
                'mtg_name': 'Regular Session Board Meeting',
                'sub_name': 'Closed Session 5:00 PM, Board Room 855 Lenzen Avenue, (District Administration Building)',
                'full_name': 'Regular Session Board Meeting - Closed Session 5:00 PM, Board Room 855 Lenzen Avenue, (District Administration Building)',
                'mtg_time': '2023-02-02 18:00',
                'scp_time': '2023-02-02 18:00',
                'mtg_id': '18426'
            }
        ]

        mock = Mock()
        sjusd_m.db_exec = mock
        sjusd_m.db_exec.return_value = found_in_db

        found_in_web = {
            19058: {
                'id': 19058,
                'name': 'Regular Session Board Meeting',
                'meet_time': '2023-03-23 18:00',
                'address': 'Closed Session 5:00 PM, Board Room 855 Lenzen Avenue, (District Administration Building)'
            },
            19057: {
                'id': 19057,
                'name': 'Regular Session Board Meeting',
                'meet_time': '2023-03-09 18:00',
                'address': 'Closed Session 5:00 PM, Board Room 855 Lenzen Avenue, (District Administration Building)'
            },
            18720: {
                'id': 18720,
                'name': 'Regular Session Board Meeting',
                'meet_time': '2023-02-16 18:00',
                'address': 'Closed Session 5:00 PM, Board Room 855 Lenzen Avenue, (District Administration Building)'
            },
            18426: {
                'id': 18426,
                'name': 'Regular Session Board Meeting',
                'meet_time': '2023-02-02 18:00',
                'address': 'Closed Session 5:00 PM, Board Room 855 Lenzen Avenue, (District Administration Building)'
            }
        }

        expected = [
            {
                'id': 19058,
                'name': 'Regular Session Board Meeting',
                'meet_time': '2023-03-23 18:00',
                'address': 'Closed Session 5:00 PM, Board Room 855 Lenzen Avenue, (District Administration Building)'
            },{
                'id': 19057,
                'name': 'Regular Session Board Meeting',
                'meet_time': '2023-03-09 18:00',
                'address': 'Closed Session 5:00 PM, Board Room 855 Lenzen Avenue, (District Administration Building)'
            }
        ]

        self.assertEqual(
            sjusd_m.find_new_meetings(found_in_web),
            expected)


if __name__ == '__main__':
    unittest.main()
