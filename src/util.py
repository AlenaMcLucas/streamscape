"""Miscellaneous project utilities."""


def read_text_file(text_file):
    """Reads a text file in the /tokens folder that needs to be parsed.

    Parameters
    ----------
    text_file : str
        text file, with the root directory being src/tokens/

    Returns
    -------
    file object
        text file to be read
    """
    return open(f"tokens/{text_file}", "r")


def parse_slack_token():
    """Parse slack bot token from read file.

    Returns
    -------
    str
        slack bot token
    """
    slack_file = read_text_file('slack-bot.txt')
    return slack_file.readline()


def parse_igdb_ids():
    """Parse IGDB client information.

    Returns
    -------
    list of str
        [client_id, client_secret] to make API calls
    """
    igdb_file = read_text_file('igdb-api.txt')
    client_id = igdb_file.readline()[:-1]
    client_secret = igdb_file.readline()
    return [client_id, client_secret]
