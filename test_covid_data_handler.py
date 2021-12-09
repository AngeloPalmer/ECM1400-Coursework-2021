"""
This is the test module with test functions to test the functions in covid_data_handler.py

Each function is tested with some test cases and the return type is tested as well.
"""

from covid_data_handler import *


def test_parse_csv_data() -> None:
    """
    This function is used to test the function parse_csv_data.
    """
    data = parse_csv_data('nation_2021-10-28.csv')
    assert len(data) == 639, "Test for length of parsed csv data: failed"
    assert isinstance(data, list), "Test for return type of parse_csv_data: failed"
    assert isinstance(data[1][1], str), "Test for correct data types returned"


def test_process_covid_csv_data() -> None:
    """
    This function is used to test the function covid_csv_data.
    """
    last7days_cases, current_hospital_cases, total_deaths = process_covid_csv_data(
        parse_csv_data('nation_2021-10-28.csv'))
    assert last7days_cases == 240299, "Test for value of last7days_cases: failed"
    assert current_hospital_cases == 7019, "Test for value of current_hospital_cases: failed"
    assert total_deaths == 141544, "Test for value of total_deaths: failed"
    assert isinstance(last7days_cases, int), "Test for return type of last7days_cases: failed"
    assert isinstance(current_hospital_cases,
                      int), "Test for return type of current_hospital_cases: failed"
    assert isinstance(total_deaths, int), "Test for return type of total_deaths: failed"


def test_covid_API_request() -> None:
    """
    This function is used to test the function covid_API_request.
    """
    data = covid_API_request()
    assert covid_API_request("Exeter",
                             "ltla") == covid_API_request(), "Test to show that returned values are the same for default arguments, whether inputted or not: failed"
    assert not (covid_API_request("London",
                                  "ltla") == covid_API_request()), "Test to show that the returned values are not the same for non-default inputted arguments: failed"
    assert isinstance(data, dict), "Test for return type of covid_API_request: failed"


def test_schedule_covid_updates() -> None:
    """
    This function is used to test the function schedule_covid_updates.
    """
    data = schedule_covid_updates("10:10", "update test")
    assert data is None, "Test for return type of schedule_covid_updates: failed"
    assert len(updates) == 1, "Test for addition of update: failed"
    assert not(updates["update test"] is None), "Test for proper addition of update: failed"


def test_get_covid_data() -> None:
    """
    This function is used to test the function get_covid_data.
    """
    data = get_covid_data()
    value = data['2021-12-07'][0]["newCasesByPublishDate"]
    assert isinstance(data, dict), "Test for return type of get_covid_data: failed"
    assert isinstance(value, int), "Test that returned data is in the correct form: failed"


def test_cancel_covid_update() -> None:
    """
    This function is used to test the function cancel_covid_update.
    """
    data = cancel_covid_update("update test")
    assert data is None, "Test for return type of cancel_covid_update: failed"
    assert len(updates) == 0, "Test for cancellation of an update named update test: failed"
