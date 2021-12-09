"""
This is the test module with test functions to test the functions in covid_news_handling.py

Each function is tested with some test cases and the return type is tested as well.
"""

from covid_news_handling import *


def test_news_API_request() -> None:
    """
    This function is used to test the function news_API_request.
    """
    data = news_API_request()
    assert news_API_request(
        "Covid COVID-19 coronavirus") == news_API_request(), "Test to show that returned values are the same for default arguments, whether inputted or not: failed"
    assert not (news_API_request(
        "Tesla") == news_API_request()), "Test to show that the returned values are not the same for non-default inputted arguments: failed"
    assert isinstance(data, list), "Test for return type of news_API_request: failed"

def test_update_news() -> None:
    """
    This function is used to test the function update_news
    """
    data = update_news()
    assert update_news(
        "Covid COVID-19 coronavirus") == update_news(), "Test to show that returned values are the same for default arguments, whether inputted or not: failed"
    assert not (update_news(
        "Tesla") == update_news()), "Test to show that the returned values are not the same for non-default inputted arguments: failed"
    assert isinstance(data, list), "Test for return type of news_API_request: failed"


def test_schedule_news_updates() -> None:
    """
    This function is used to test the function schedule_news_updates.
    """
    data = schedule_news_updates("10:10", "update test")
    assert data is None, "Test for return type of schedule_news_updates: failed"
    assert len(updates) == 1, "Test for addition of update: failed"
    assert not (updates["update test"] is None), "Test for proper addition of update: failed"


def test_get_news_articles() -> None:
    """
    This function is used to test the function get_covid_data.
    """
    data = get_news_articles()
    value = data[0]["title"]
    assert isinstance(data, list), "Test for return type of get_covid_data: failed"
    assert isinstance(value, str), "Test that returned data is in the correct form: failed"


def test_cancel_news_update() -> None:
    """
    This function is used to test the function cancel_covid_update.
    """
    data = cancel_news_update("update test")
    assert data is None, "Test for return type of cancel_news_update: failed"
    assert len(updates) == 0, "Test for cancellation of an update named update test: failed"
