"""
This is the main program module from which everything is run. The Flask app is run from here as well
as the logger and scheduler. The module creates a Covid Data Dashboard which is a simple
personalised covid dashboard that displays information about the Covid infection rates in the local
area, as well as nationally, and news stories about Covid. The user is able to schedule updates to
both the displayed Covid Data and the news stories on the dashboard, as well as being able to delete
any news stories they no longer wish to see which will then be replaced with a fresh story.
Updates to news and Covid data can be scheduled separately and can also be set to repeat at a set
time daily.

Attributes:
    logger (logging): The main project logger, initialised at debug level and saved to sys.log
    schedule (sched): The main project scheduler; an instance of sched
    app (Flask): A flask app instance
"""

import logging
import sched
import time
from datetime import datetime, timedelta
from flask import *
from covid_data_handler import *
from covid_news_handling import *

logging.basicConfig(filename='sys.log', encoding='utf-8',
                    format="%(asctime)s %(module)s [%(levelname)s] - %(message)s",
                    level=logging.DEBUG)
logger = logging.getLogger()

app = Flask(__name__)
schedule = sched.scheduler()


@app.route('/')
def root() -> str:
    """
    A simple function to redirect the user to the proper URL should they have visited the base URL

    Args:
        None

    Returns:
        update (str): The main function/string from which almost everything is run
    """
    logger.info("User went to base IP")
    return update()


@app.route("/index")
def update() -> str:
    """
    The main function which is executed at least every 60 seconds by the html template which is then
    re-rendered by this function. From here URL arguments are taken in and processed appropriately;
    any necessary functions from the other two modules are run and their outputs are handled
    accordingly. Further the maintenance of necessary data structures such as a list of scheduled
    updates and the contents of the dashboard toasts is also largely handled here.

    Args:
        None

    Returns:
        render_template (str): A function/string that renders the flask dashboard template with all
            its parameters/arguments filled with the relevant data
    """
    schedule.run(blocking=False)
    global news_articles
    global covid_data
    global update_name
    # Gathers the current (but not necessarily up to date) data from the covid_data_handler and
    # covid_news_handling modules
    covid_data = get_covid_data()
    current_articles = get_news_articles()
    # Updates the displayed news articles
    news_articles = []
    for i in range(0, 3):
        try:
            news_articles.append({"title": current_articles[i]["title"], "content": (
                current_articles[i]["description"] + "\n" + "Article from: " + current_articles[i][
                    "url"])})
        except IndexError:
            logger.warning("No articles left to load")
            break
    # Calculates the relevant Covid data
    hospital_cases = covid_data[two_days_ago][1]["hospitalCases"]
    deaths_total = covid_data[two_days_ago][1]["cumDeaths60DaysByDeathDate"]

    local_7day_infections = 0
    national_7day_infections = 0
    for i in range(0, 7):
        local_7day_infections += covid_data[str(datetime.now().date() - timedelta(2 + i))][0][
            "newCasesByPublishDate"]
        national_7day_infections += covid_data[str(datetime.now().date() - timedelta(2 + i))][1][
            "newCasesByPublishDate"]
    # Checks to see if the current update title has been already used and prevents a new update
    # being scheduled if so
    update_name = request.args.get("two")
    for i in range(0, len(updates)):
        if not update_name:
            break
        if updates[i]["title"] == ((update_name + " - Covid") or (update_name + " - News")):
            logger.warning("Duplicate update name used: %s", update_name)
            return render_template('index.html', title='Covid Daily Update App', location=location,
                                   nation_location=nation_location,
                                   hospital_cases="Hospital Cases: " + str(hospital_cases),
                                   deaths_total="Total Deaths: " + str(deaths_total),
                                   news_articles=news_articles,
                                   updates=updates,
                                   local_7day_infections=local_7day_infections,
                                   national_7day_infections=national_7day_infections,
                                   favicon="./static/images/favicon.ico",
                                   image="covid.png")

    repeat_update = request.args.get("repeat")
    # Checks to see if an update has been scheduled without a time, if so the time is set to the
    # current time, effectively scheduling an immediate update
    update_time = request.args.get("update")
    if (not update_time) and update_name:
        logger.warning("No time inserted, current time being used to schedule immediate update")
        update_time = str(time.gmtime().tm_hour) + ":" + str(time.gmtime().tm_min)
    # If an article is removed, the article is added to the file of removed articles and new
    # articles are added to a maximum of 3. Furthermore, if said file doesn't exist it's created
    remove_news = request.args.get('notif')
    if remove_news:
        try:
            logger.info("Filtering out already deleted articles")
            with open('deleted_articles.txt') as del_art_file:
                deleted_articles = del_art_file.read().splitlines()
                if remove_news not in deleted_articles:
                    deleted_articles.append(remove_news)
        except FileNotFoundError:
            logger.warning(
                "No deleted_articles file found: current article will be used to create said file")
            deleted_articles = [remove_news]
        with open('deleted_articles.txt', 'w') as outfile:
            for article in deleted_articles:
                outfile.write(article + "\n")
        for i in range(0, 3):
            try:
                if (news_articles[i]["title"]) == remove_news:
                    del news_articles[i]
            except IndexError:
                logger.error("Suppressed error in removing filtered articles")
                break
        articles = get_news_articles()
        for i in range(len(news_articles), 3):
            try:
                news_articles.append({"title": articles[i]["title"],
                                      "content": (articles[i][
                                                      "description"]) + "\n" + "Article from: " +
                                                 current_articles[i]["url"]})
            except IndexError:
                logger.warning("No articles left to load")
                break
    # Scheduling a Covid data update and an automatic removal of the relevant toast once the update
    # arrives
    covid_toggle = request.args.get("covid-data")
    if covid_toggle:
        message = "Update of Covid data at: "
        if repeat_update:
            message = "Repeating update of Covid data at: "
        schedule_covid_updates(update_time, update_name + " - Covid")
        updates.append({"title": update_name + " - Covid", "content": message + update_time})
        current_hour = int(time.gmtime().tm_hour)
        current_minute = int(time.gmtime().tm_min)
        current_second = int(time.gmtime().tm_sec)
        update_hour = update_time[0:2]
        update_minute = update_time[3:]
        update_hour = int(update_hour)
        update_minute = int(update_minute)
        timer = ((update_hour - current_hour) * 3600) + (
            (update_minute - current_minute) * 60) - current_second
        toast_updates[update_name + " - Covid"] = schedule.enter(timer, 1, remove_update_toast,
                                                                 argument=(update_name + " - Covid",
                                                                           update_time))
        schedule.run(blocking=False)
    # Scheduling a News article update and an automatic removal of the relevant toast once the
    # update arrives
    news_toggle = request.args.get("news")
    if news_toggle:
        message = "Update of News data at: "
        if repeat_update:
            message = "Repeating update of News data at: "
        schedule_news_updates(update_time, update_name + " - News")
        updates.append({"title": update_name + " - News", "content": message + update_time})
        current_hour = int(time.gmtime().tm_hour)
        current_minute = int(time.gmtime().tm_min)
        current_second = int(time.gmtime().tm_sec)
        update_hour = update_time[0:2]
        update_minute = update_time[3:]
        update_hour = int(update_hour)
        update_minute = int(update_minute)
        timer = ((update_hour - current_hour) * 3600) + (
            (update_minute - current_minute) * 60) - current_second
        toast_updates[update_name + " - News"] = schedule.enter(timer, 1, remove_update_toast,
                                                                argument=(update_name + " - News",
                                                                          update_time))
        schedule.run(blocking=False)
    # Cancellation of the relevant update by reading the contents of the toast. Also cancels the
    # automatic removal of said toast given that it'll no longer exist
    remove_schedule = request.args.get("update_item")
    if remove_schedule:
        logger.info("Removal of toast titled: %s", remove_schedule)
        for i in range(0, len(updates)):
            try:
                if updates[i]["title"] == remove_schedule:
                    update_content = updates[i]["content"].split()
                    if (update_content[2] == "Covid") or (update_content[3] == "Covid"):
                        cancel_covid_update(remove_schedule)
                        schedule.cancel(toast_updates[remove_schedule])
                    else:
                        cancel_news_update(remove_schedule)
                        schedule.cancel(toast_updates[remove_schedule])
                    del updates[i]
            except IndexError:
                break

    return render_template('index.html', title='Covid Daily Update App', location=location,
                           nation_location=nation_location,
                           hospital_cases="Hospital Cases: " + str(hospital_cases),
                           deaths_total="Total Deaths: " + str(deaths_total),
                           news_articles=news_articles,
                           updates=updates,
                           local_7day_infections=local_7day_infections,
                           national_7day_infections=national_7day_infections,
                           favicon="./static/images/favicon.ico",
                           image="covid.png")


def remove_update_toast(update_name: str, update_time: str) -> None:
    """
    A function that removes a toast with a specific name at a specific time (the same time as the
    toast's update time). By checking whether the toast represents a repeating update it is able to
    enact this repeating update; if not it simply removes the toast and the relevant scheduled
    update for the removal of said toast.

    Args:
        update_name (str): The name of the toast to be removed
        update_name (str): The time for the toast to be removed

    Returns:
        None
    """
    logger.info("Removal of toast titled " + update_name + " scheduled for " + update_time)
    for element in updates:
        if element["title"] == update_name:
            update_content = element["content"].split()
            # Reads content of toast; if it is a repeating toast it doesn't delete the toast and
            # schedules a new update of the relevant type as well as a new removal of the toast to
            # allow the cycle to repeat itself
            if update_content[0] == "Repeating":
                if update_content[3] == "Covid":
                    schedule_covid_updates(update_time, update_name)
                    current_hour = int(time.gmtime().tm_hour)
                    current_minute = int(time.gmtime().tm_min)
                    current_second = int(time.gmtime().tm_sec)
                    update_hour = update_time[0:2]
                    update_minute = update_time[3:]
                    update_hour = int(update_hour)
                    update_minute = int(update_minute)
                    timer = ((update_hour - current_hour + 24) * 3600) + (
                        (update_minute - current_minute) * 60) - current_second
                    toast_updates[update_name] = schedule.enter(timer, 1, remove_update_toast,
                                                                argument=(update_name + " - Covid",
                                                                          update_time))
                    schedule.run(blocking=False)
                    break
                else:
                    schedule_news_updates(update_time, update_name)
                    current_hour = int(time.gmtime().tm_hour)
                    current_minute = int(time.gmtime().tm_min)
                    current_second = int(time.gmtime().tm_sec)
                    update_hour = update_time[0:2]
                    update_minute = update_time[3:]
                    update_hour = int(update_hour)
                    update_minute = int(update_minute)
                    timer = ((update_hour - current_hour + 24) * 3600) + (
                        (update_minute - current_minute) * 60) - current_second
                    toast_updates[update_name] = schedule.enter(timer, 1, remove_update_toast,
                                                                argument=(update_name + " - News",
                                                                          update_time))
                    schedule.run(blocking=False)
                    break

            updates.remove(element)


if __name__ == '__main__':
    global covid_data
    logger.info("App starting")
    # Gathering the initial Covid data
    covid_data = covid_API_request(config_data["Location"], config_data["Location Type"])
    try:
        today = str(datetime.now().date())
        two_days_ago = str(datetime.now().date() - timedelta(2))
        location = covid_data[today][0]["areaName"]
    except KeyError:
        logger.error(
            "No data available at current date, initial data gathered will be of the previous day")
        # For when today's data isn't available: e.g. near midnight
        today = str(datetime.now().date() - timedelta(1))
        two_days_ago = str(datetime.now().date() - timedelta(3))
        location = covid_data[today][0]["areaName"]
    # Calculation of the relevant Covid data
    nation_location = covid_data[today][1]["areaName"]
    hospital_cases = covid_data[two_days_ago][1]["hospitalCases"]
    deaths_total = covid_data[two_days_ago][1]["cumDeaths60DaysByDeathDate"]

    local_7day_infections = 0
    national_7day_infections = 0
    for i in range(0, 7):
        local_7day_infections += covid_data[str(datetime.now().date() - timedelta(2 + i))][0][
            "newCasesByPublishDate"]
        national_7day_infections += covid_data[str(datetime.now().date() - timedelta(2 + i))][1][
            "newCasesByPublishDate"]
    # Gathering the initial News articles
    current_articles = update_news(config_data["News Terms"])
    news_articles = []
    for i in range(0, 3):
        logger.info("Loading initial articles")
        try:
            news_articles.append({"title": current_articles[i]["title"], "content": (
                current_articles[i]["description"] + "\n" + "Article from: " + current_articles[i][
                    "url"])})
        except IndexError:
            logger.warning("No articles left to load")
            break
    # Creating the empty update list and toast update dictionary
    updates = []
    toast_updates = {}
    app.run()
