"""Alerts me of anything important when a script is running."""

from slack import WebClient


SLACK_BOT_TOKEN = 'xoxb-1508191575730-1493530643479-RU5rrOo3VoBGg3jsu9ShmCI1'


def slack_message(message):
    """Sends a bot message to my #stream-scape slack channel.

    Parameters
    ----------
    message : str
        Message sent to slack.
    """
    client = WebClient(SLACK_BOT_TOKEN)
    client.chat_postMessage(channel='#stream-scape', text=message, icon_emoji=':robot_face:')
    print(message)


if __name__ == '__main__':
    slack_message('Hello, World!')
