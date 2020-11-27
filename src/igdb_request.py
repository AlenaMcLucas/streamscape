"""Makes POST requests to IGDB, parses responses, and cleans the data."""

import requests
import json
import datetime
import sys

from igdb.wrapper import IGDBWrapper   # from igdb-api-v4

from notifications import slack_message
import util


CLIENT_ID, CLIENT_SECRET = util.parse_igdb_ids()
access_token = ''


def unix_to_datetime(unix):
    """Converts a UNIX time stamp to a datetime object.

    Parameters
    ----------
    unix : int

    Returns
    -------
    datetime
    """
    return datetime.datetime.fromtimestamp(unix).strftime('%Y-%m-%d %H:%M:%S')


def generate_token():
    """Generate IGDB token to call API.

    Returns
    -------
    access_token : str
        IGDB access token to make post requests with.
    """
    token_url = 'https://id.twitch.tv/oauth2/token'
    token_params = {'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET, 'grant_type': 'client_credentials'}

    try:
        response = requests.post(token_url, data=token_params)
        # correct response   ->   {"access_token":"STRING","expires_in":int,"token_type":"bearer"}
    except requests.HTTPError:
        slack_message('IGDB API connection error.')
        sys.exit()

    return response.json()['access_token']


def fill_missing_fields(res):
    """Fill missing fields that the API response didn't contain to prepare it to be published to a relational database.

    Parameters
    ----------
    res : dict
        API response from IGDB.

    Returns
    -------
    dict
        Video game data with 11 values.
    """
    empty_states = {'first_release_date': None, 'game_modes': [], 'genres': [], 'involved_companies': [],
                    'multiplayer_modes': [], 'platforms': [], 'summary': None, 'keywords': [], 'themes': []}

    for states in empty_states.items():
        if res.get(states[0]) is None:
            res[states[0]] = states[1]

    return res


def get_video_game(title='Dogou Souken'):
    """Get video game data and clean up API response from IGDB.

    Parameters
    ----------
    title : str

    Returns
    -------
    json_response : dict
    """
    wrapper = IGDBWrapper(CLIENT_ID, access_token)
    base_query = 'fields id, first_release_date, game_modes, genres, involved_companies, multiplayer_modes, platforms, summary, keywords, themes;'
    where = f' where name="{title}";'
    byte_array = wrapper.api_request('games', base_query + where)

    default_bad_response = fill_missing_fields({'name': title, 'id': None})

    # check for presence of data
    try:
        json_response = json.loads(byte_array.decode('utf8').replace("'", '"'))[0]
    except IndexError:
        slack_message(f'{title} did not return any results from IGDB.')
        return default_bad_response

    # ensure we retrieved a game with an id
    if json_response.get('id') is None:
        slack_message(f'{title} did not return an ID from IGDB.')
        return default_bad_response

    json_response['name'] = title

    # convert to datetime if date was retrieved
    if json_response.get('first_release_date') is not None:
        json_response['first_release_date'] = unix_to_datetime(json_response['first_release_date'])

    return fill_missing_fields(json_response)


# game_modes, genres, involved_companies, multiplayer_modes, platforms, keywords, themes


if __name__ == '__main__':
    access_token = generate_token()
    print(get_video_game())
