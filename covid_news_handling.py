"""
This module handles the processing of News articles from the News API and the scheduling and
cancellation of updates to the News articles data.

Attributes:
    logger (logging): An instance of the project's logging
    updates (dict): A dictionary used to hold the current News data updates scheduled
    current_articles (dict): A dictionary used to hold the current News articles
    schedule (sched): An instance of the project's sched
    config_data (dict): A dictionary containing all the configurable variables from the config file

"""

import logging
import sched
import time
import json
import requests

logger = logging.getLogger(__name__)
updates = {}
schedule = sched.scheduler()
current_articles = {}
with open('config.json', 'r') as f:
    config_data = json.load(f)


def news_API_request(covid_terms: str = "Covid COVID-19 coronavirus") -> list:
    """
    A function that takes in a string of multiple news term filters and uses this to gather relevant
    news articles from the news API and return the articles as a dictionary

    Args:
        covid_terms (str): A string of words used to filter what articles are gathered

    Returns:
        articles (list): A formatted list of dictionaries containing the gathered news articles
    """
    global config_data
    logger.info("Data requested from News API")
    terms = covid_terms.split()
    terms = " OR ".join(terms)
    api_key = config_data["API Key"]
    complete_url = "https://newsapi.org/v2/everything?q=" + terms + "&" + config_data[
        "News Sorting"] + "&language=" + \
                   config_data["News Language"] + "&apiKey=" + api_key
    response = requests.get(complete_url)
    articles = response.json()
    # Remove unnecessary formatting
    articles = articles["articles"]
    return articles


def update_news(covid_terms: str = "Covid COVID-19 coronavirus") -> list:
    """
    A function that gathers news articles based on the terms given and filters them such that the
    articles returned are not ones that have already been removed.

    Args:
        covid_terms (str): A string of words used to filter what articles are gathered

    Returns:
        current_articles (list): A formatted list of dictionaries containing the gathered articles
    """
    global current_articles
    current_articles = news_API_request(covid_terms)
    # Imports all deleted articles from file and creates an empty list should the file not exist
    try:
        with open('deleted_articles.txt') as del_art_file:
            deleted_articles = del_art_file.read().splitlines()
    except FileNotFoundError:
        deleted_articles = []
    # Removes already deleted articles from the current articles
    for i in range(0, len(deleted_articles)):
        for j in range(0, len(current_articles)):
            try:
                if (current_articles[j]["title"]) == deleted_articles[i]:
                    del current_articles[j]
            except IndexError:
                break

    return current_articles


def schedule_news_updates(update_interval: str, update_name: str) -> None:
    """
    A function used to schedule a News update with the given name at the given date.

    Args:
        update_interval (str): The time for the update to be scheduled to in the form 12:15
        update_name (str): The name of the update to be scheduled

    Returns:
        None
    """
    logger.info("News update " + update_name + " scheduled for " + update_interval)
    global updates
    global schedule
    # Gathers the current time
    current_hour = int(time.gmtime().tm_hour)
    current_minute = int(time.gmtime().tm_min)
    current_second = int(time.gmtime().tm_sec)
    # Converts the time given by update_interval into an integer in seconds
    update_hour = update_interval[0:2]
    update_minute = update_interval[3:]
    update_hour = int(update_hour)
    update_minute = int(update_minute)
    # Calculates the time in seconds until the scheduled time
    timer = ((update_hour - current_hour) * 3600) + (
        (update_minute - current_minute) * 60) - current_second
    if timer < 0:
        timer += 24 * 3600
    updates[update_name] = schedule.enter(timer, 1, update_news,
                                          argument=(config_data["News Terms"],))
    schedule.run(blocking=False)


def get_news_articles() -> list:
    """
    A function used in the main file to access current news articles from this module.

    Args:
        None

    Returns:
        current_articles (list): A list of dictionaries containing current news articles
    """
    global current_articles
    logger.info("News data requested")
    schedule.run(blocking=False)
    try:
        with open('deleted_articles.txt') as del_art_file:
            deleted_articles = del_art_file.read().splitlines()
    except FileNotFoundError:
        deleted_articles = []
    # Removes already deleted articles from the current articles
    for i in range(0, len(deleted_articles)):
        for j in range(0, len(current_articles)):
            try:
                if (current_articles[j]["title"]) == deleted_articles[i]:
                    del current_articles[j]
            except IndexError:
                break

    return current_articles


def cancel_news_update(update_name: str) -> None:
    """
    A function used to cancel a scheduled news data update.

    Args:
        update_name (str): The name of the update to be cancelled

    Returns:
        None
    """
    logger.info("News update %s cancelled", update_name)
    global updates
    global schedule
    schedule.cancel(updates[update_name])
    del updates[update_name]
