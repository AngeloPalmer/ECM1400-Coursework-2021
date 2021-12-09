"""
This module handles the processing of Covid data in various forms from either files or the UK
government Covid API and the scheduling and cancellation of updates to said Covid data.

Attributes:
    logger (logging): An instance of the project's logging
    updates (dict): A dictionary used to hold the current Covid data updates scheduled
    covid_data (dict): A dictionary used to hold the current Covid data
    schedule (sched): An instance of the project's sched
    config_data (dict): A dictionary containing all the configurable variables from the config file

"""

import logging
import csv
import sched
import time
import json
from uk_covid19 import Cov19API

# Initialises the logger and scheduler, and creates the updates and covid_data dictionaries
logger = logging.getLogger(__name__)
updates = {}
covid_data = {}
schedule = sched.scheduler()

# Opens the configuration file
with open('config.json', 'r') as f:
    config_data = json.load(f)


# -- These functions are never used but were a necessary project requirement

def parse_csv_data(csv_filename: str) -> list:
    """
    A function that takes in a string and opens a csv file named the value of the string.
    The function then converts this data into a list and returns said list.

    Args:
        csv_filename (str): A string representing the name of the csv file to be opened

    Returns:
        covid_data_list: A list containing the data extracted from the csv file
    """
    with open(csv_filename, newline="") as file:
        reader = csv.reader(file)
        covid_data_list = list(reader)
    return covid_data_list


def process_covid_csv_data(covid_csv_data: list) -> tuple:
    """
    A function that takes in a list of data and processes it to return current hospital cases,
    total deaths and cases in the last 7 days.

    Args:
        covid_csv_data (list): A list containing Covid data

    Returns:
        current_hospital_cases (int): The number of current Covid hospital cases
        total_deaths (int): The cumulative deaths due to Covid infection
        last7days_cases (int): The number of Covid cases in the past 7 days
    """
    current_hospital_cases = covid_csv_data[1][5]
    total_deaths = covid_csv_data[14][4]
    last7days_cases = 0
    for i in range(3, 10):
        last7days_cases += int(covid_csv_data[i][6])
    return int(last7days_cases), int(current_hospital_cases), int(total_deaths)


# --

def covid_API_request(location: str = "Exeter", location_type: str = "ltla") -> dict:
    """
    A function that takes in a location and gathers a set of Covid data from the UK government's
    Covid API relevant to that location and the wider nation. It then returns said data after having
    processed it.

    Args:
        location (str): The local location; defaults to Exeter
        location_type (str): The local location's area classification; defaults to ltla

    Returns:
        covid_data (dict): A dictionary containing up to date Covid data
    """
    global config_data
    global covid_data
    logger.info("Data requested from Covid API")
    # Sets up the filters for the local and national covid data for the API
    local_structure = {
        "areaName": "areaName",
        "date": "date",
        config_data["Local Cases Metric"]: config_data["Local Cases Metric"],
    }
    national_structure = {
        "areaName": "areaName",
        "date": "date",
        config_data["Total Deaths Metric"]: config_data["Total Deaths Metric"],
        "newCasesByPublishDate": "newCasesByPublishDate",
        "hospitalCases": "hospitalCases"
    }
    area_type = "areaType=" + location_type
    area_name = "areaName=" + location
    filter_list = [area_type, area_name]
    # Requests the covid data from the covid API, strips them of unnecessary structures
    local_api = Cov19API(filters=filter_list, structure=local_structure)
    death_api = Cov19API(filters=["areaType=nation", "areaName=" + config_data["Nation"]],
                         structure=national_structure)
    local_data = local_api.get_json()
    national_data = death_api.get_json()
    # Strip unnecessary formatting
    local_data = local_data["data"]
    national_data = national_data["data"]
    # Merges the local and national data
    covid_data = {}
    for i in range(0, len(local_data)):
        covid_data[local_data[i]["date"]] = [local_data[i], national_data[i]]

    return covid_data


def schedule_covid_updates(update_interval: str, update_name: str) -> None:
    """
    A function used to schedule a Covid update with the given name at the given date.

    Args:
        update_interval (str): The time for the update to be scheduled to in the form 12:15
        update_name (str): The name of the update to be scheduled

    Returns:
        None
    """
    logger.info("Covid update " + update_name + " scheduled for " + update_interval)
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
    updates[update_name] = schedule.enter(timer, 1, covid_API_request,
                                          argument=(
                                              config_data["Location"],
                                              config_data["Location Type"],))
    schedule.run(blocking=False)


def get_covid_data() -> dict:
    """
    A function used in the main file to access current Covid data from this module.

    Args:
        None

    Returns:
        covid_data (dict): A dictionary containing current Covid data
    """
    global covid_data
    logger.info("Covid data requested")
    schedule.run(blocking=False)
    return covid_data


def cancel_covid_update(update_name: str) -> None:
    """
    A function used to cancel a scheduled Covid data update.

    Args:
        update_name (str): The name of the update to be cancelled

    Returns:
        None
    """
    logger.info("Covid update %s cancelled", update_name)
    global updates
    global schedule
    schedule.cancel(updates[update_name])
    del updates[update_name]

print(parse_csv_data('nation_2021-10-28.csv'))