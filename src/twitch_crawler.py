"""Scrapes data from Twitch."""

import time
import json

from selenium import webdriver
from bs4 import BeautifulSoup
from google.cloud import pubsub_v1


PAUSE_TIME = 3   # Allow 3 seconds for the web page to load
PROJECT_ID = "pol-pipe"   # GCP project id
driver = webdriver.Chrome(executable_path=r"/Users/alenamclucas/Documents/WebDriver/chromedriver")


def publish(messages, topic_id):
    """Publish data to my specific Google Pub/Sub topic.

    Parameters
    ----------
    messages : ?
    topic_id : ?
    """
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(PROJECT_ID, topic_id)
    for message in messages:
        future = publisher.publish(topic_path, data=message.encode('utf-8'))


def parse_viewers(view):
    """Parses viewer count when it's abbreviated.

    Parameters
    ----------
    view : str
        String representation of viewer count.

    Returns
    -------
    int
        Parsed viewer count.
    """
    if 'K' in view:
        view = int(float(view[:-9]) * 1000)
    elif 'M' in view:
        view = int(float(view[:-9]) * 1000000)
    elif view == '1 viewer':
        view = 1
    else:
        view = int(view[:-8])

    return view


def parse_stream_rank(stream_rank):
    """Parse string rank from scraped data."""
    return int(stream_rank[7:-1]) + 1


def parse_trending_tags(tag_string):
    """Parse trending tags from scraped string.

    Parameters
    ----------
    tag_string : str
        Contains trending tag along with other html.

    Returns
    -------
    str
        Trending tag.
    """
    start = tag_string.find('>') + 1
    end = tag_string[start:].find('<')
    return tag_string[start:start + end]


def scrape_categories(scroll_number_cat=15):
    """Scrape the categories page from high to low viewer count.

    Parameters
    ----------
    scroll_number_cat : int
        Number of scrolls down to perform before scraping the page.

    Returns
    -------
    dict
        Game data including: name is key, values are dictionary of rank (int), primary_tags (list), and uri (str).
    """
    # go to the URL
    driver.get("https://www.twitch.tv/directory?sort=VIEWER_COUNT")
    time.sleep(PAUSE_TIME)

    # scroll down scroll_number_cat times
    for i in range(1, scroll_number_cat):
        driver.execute_script("document.getElementsByClassName('simplebar-scroll-content')[1].scrollTo(1,50000)")
        time.sleep(PAUSE_TIME)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    games = {}

    # parse individual categories
    for card in soup.find_all('div', 'tw-box-art-card'):
        title = card.find('h3').string
        rank = int(card['data-a-target'][5:]) + 1
        tags = {t.string for t in card.find_all('button')}
        uri = card.find('p', 'tw-c-text-alt-2').find('a')['href']

        # bottom_link = card.find('p', 'tw-c-text-alt-2').find('a')
        # viewers = parse_viewers(bottom_link.string)
        # uri = bottom_link['href']

        games[title] = {'rank': rank, 'primary_tags': list(tags), 'uri': uri}   # 'viewers': viewers,

    return games


def scrape_games(top_games_cat, scroll_number_game):
    """Scrape each games page from high to low viewer count.

    Parameters
    ----------
    top_games_cat : dict
        One category/games from scrape_categories().
    scroll_number_game : int
        Number of scrolls down to perform before scraping the page.

    Returns
    -------
    dict
        Name is key, adds additional data points to values: viewers (int), followers (int), secondary_tags (list), trending_tags (list), and streams (dict); streams have username as key, values are dict of: stream_tags (list), stream_viewers (int), stream_rank (int).
    """
    for game, stats in top_games_cat.items():
        # go to the URL
        driver.get(f"https://www.twitch.tv{stats['uri']}?sort=VIEWER_COUNT")
        time.sleep(PAUSE_TIME)

        # scroll down scroll_number_game times
        for i in range(1, scroll_number_game):
            driver.execute_script("document.getElementsByClassName('simplebar-scroll-content')[1].scrollTo(1,50000)")
            time.sleep(PAUSE_TIME)

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # parse game-specific data
        header = soup.find('div', 'tw-flex tw-flex-column tw-justify-content-center')
        vf_bool = False

        for t in header.find_all('p', 'tw-c-text-alt'):
            if not vf_bool:
                top_games_cat[game]['viewers'] = int(t['title'][:-8].replace(',', ''))
                vf_bool = True
            else:
                top_games_cat[game]['followers'] = int(t['title'][:-10].replace(',', ''))

        secondary_tags = {tag['data-a-target'] for tag in header.find_all('a', 'tw-border-radius-rounded tw-inline-flex tw-interactive tw-semibold tw-tag')}
        secondary_tags.difference_update(stats['primary_tags'])
        top_games_cat[game]['secondary_tags'] = list(secondary_tags)

        trending = soup.find('div', 'tw-align-items-center tw-flex tw-flex-wrap')
        trending_tags = {parse_trending_tags(str(t)) for t in trending.find_all('div', 'tw-align-items-center tw-border-radius-rounded tw-flex tw-font-size-6 tw-semibold')}
        top_games_cat[game]['trending_tags'] = list(trending_tags)

        # parse stream-specific data
        stream_data = {}
        for stream in soup.find_all('div', 'tw-mg-b-2 tw-relative'):
            username = stream.find('div', 'tw-media-card-meta__links').find('a').string
            stream_tags = {t.string for t in stream.find_all('div', 'tw-tag__content')}
            stream_viewers = parse_viewers(stream.find('div', 'tw-media-card-stat').find('p').string)
            stream_rank = parse_stream_rank(stream.parent['style'])

            stream_data[username] = {'stream_tags': list(stream_tags), 'stream_viewers': stream_viewers, 'stream_rank': stream_rank}

        top_games_cat[game]['streams'] = stream_data

    return top_games_cat


def quit_driver():
    """Quit web driver."""
    driver.quit()
