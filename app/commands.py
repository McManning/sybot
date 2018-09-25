
import re
import functools
import random
import requests

import Murmur

from app.steam import SteamApp, SteamWorkshopItem
from app.util import get_url_title, image_url_to_data_uri, strip_html

command_subscribers = []

class TextMessage(Murmur.TextMessage):
    """Wrapper for Murmur TextMessages to add additional message context

    :param server: Server this message is sent to.
    :param user: User that sent this message. None implies a system message
    :param sessions: Sessions (connected users) who were sent this message.
    :param channels: Channels who were sent this message.
    :param trees: Trees of channels who were sent this message.
    :param text: The contents of the message.
    :param match: Re match groups if the message was mapped to a command
    """
    def __init__(
        self,
        user=None,
        server=None,
        sessions=None,
        channels=None,
        trees=None,
        text='',
        match=None
    ):
        super().__init__(sessions, channels, trees, text)
        self.user = user
        self.server = server
        self.match = match

class TextResponse:
    """Prepared message to an individual, channel, or server

    :param message: the message to send (text or HTML)
    :param server:  the target Murmur server. Defaults to all servers
    :param channel: the target channel for the message. If unspecified,
                    all channels on `server` will receive the message.
    :param user:    the target user for a direct message. Will be ignored
                    if `channel` is specified.
    """
    def __init__(
        self,
        message: str,
        server: Murmur.Server = None,
        channel: Murmur.Channel = None,
        user: Murmur.User = None
    ):
        self.message = message
        self.server = server
        self.channel = channel
        self.user = user

    # def send(self):
    #     """Send the prepared message to Murmur"""

    #     servers = []
    #     if self.server:
    #         servers.append(self.server)
    #     else:
    #         servers = meta.getBootedServers()

    #     for server in servers:


def publish(
    server: Murmur.Server,
    user: Murmur.User,
    msg: Murmur.TextMessage
):
    """Publish a text message to all commands matching the message pattern

    :param server: Originating server instance
    :param user: User that sent the message
    :param msg: The message that was sent
    """
    # Wrap original message in a more context aware TextMessage
    wrapped = TextMessage(
        user,
        server,
        msg.sessions,
        msg.channels,
        msg.trees,
        msg.text
    )

    for command in command_subscribers:
        match = command['prog'].search(msg.text)
        if match:
            command['func'](wrapped, **match.groupdict())
            return


def subscribe(
    pattern: str,
    usage: str,
    func: callable
):
    # Make sure it's not already registered before registering
    # (can happen during werkzeug lazy reloads)
    for command in command_subscribers:
        if command['func'] == func:
            return

    command_subscribers.append({
        'prog': re.compile(pattern, re.IGNORECASE),
        'usage': usage,
        'func': func
    })


def command(pattern: str, usage: str = None):
    """Decorator for command subscriber methods"""
    def decorator(func):
        subscribe(pattern, usage, func)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


@command('^(hi|hello)$')
def hello(msg: TextMessage):
    """Test command to ensure the bot is running properly

    :param msg: TextMessage that triggered this command response
    """
    phrases = [
        'Hello',
        'Hi',
        'What up',
        'Sup',
        'Fuck you'
    ]

    text = random.choice(phrases)

    # Reply to the same channel(s) the message was sent to
    for channel in msg.channels:
        msg.server.sendMessageChannel(channel, False, text)


@command('^!h(e|a)lp', usage='!help - Prints this help message')
def usage(msg: TextMessage):
    """List commands available for the user

    This will only list out commands that have `usage` set.
    All others are treated as implicit commands.

    :param msg: TextMessage that triggered this command response
    """
    html = 'Available commands:<ul>'
    for command in command_subscribers:
        if command['usage']:
            html += '<li>' + command['usage'] + '</li>'

    html += '</ul>';

    # Reply directly to the user that sent the message
    msg.server.sendMessage(msg.user.session, html)


@command('^!pickone', usage='!pickone - Select one item from a list at random. Eg: !pickone Gfro, Phantom, Mark')
def pick_one(msg: TextMessage):
    """Select an item from a user provided list at random

    :param msg: TextMessage that triggered this command response
    """
    phrases = [
        'Hmm... I pick {}',
        'Let\'s go with {}',
        'How about {}?',
        '{} sounds good',
        'I don\'t like it, but {} is still the best option there'
    ]

    choice = random.choice(msg.text[8:].split(',')).strip()
    text = random.choice(phrases).format(choice)

    # Reply to the same channel(s) the message was sent to
    for channel in msg.channels:
        msg.server.sendMessageChannel(channel, False, text)


@command('^!(?P<dice>\d+)d(?P<sides>\d+)', usage='!#d# - Roll dice. Eg: !2d6 will roll 2 six-sided dice')
def roll(msg: TextMessage, dice: str, sides: str):
    """Dice roller for an arbitrary number of dice and sides

    :param msg: TextMessage that triggered this command response
    :param dice: Number of dice rolled
    :param sides: Number of sides per dice rolled
    """
    dice = int(dice)
    sides = int(sides)

    if sides < 1:
        text = 'How Can Dice Be Real If Their Sides Are Not?'
    elif dice < 1:
        text = 'How Can Sides Be Real If Dice Are Not?'
    elif dice > 5:
        text = 'I don\'t have that many dice.'
    else:
        rolls = [str(random.randint(1, sides)) for x in range(dice)]
        text = '{} rolled {}'.format(msg.user.name, ', '.join(rolls))

    for channel in msg.channels:
        msg.server.sendMessageChannel(channel, False, text)


@command(r'(?:youtube(?:-nocookie)?\.com/(?:[^/]+/.+/|(?:v|e(?:mbed)?)/|.*[?&]v=)|youtu\.be/)(?P<id>[^\"&?/ ]{11})')
def youtube(msg: TextMessage, id: str):
    """YouTube links display the title of the video linked.

    Regex sourced from https://stackoverflow.com/a/6382259

    :param msg: TextMessage that triggered this command response
    :param id: YouTube video ID
    """
    page_url = 'https://www.youtube.com/watch?v={}'
    thumbnail_url = 'https://img.youtube.com/vi/{}/mqdefault.jpg'

    # Other options:
    # https://img.youtube.com/vi/I_nkflrpp90/default.jpg - 120x90
    # https://img.youtube.com/vi/I_nkflrpp90/mqdefault.jpg - 320x180
    # https://img.youtube.com/vi/I_nkflrpp90/hqdefault.jpg - 480x360

    title = get_url_title(page_url.format(id))
    thumbnail = image_url_to_data_uri(thumbnail_url.format(id))
    # thumbnail = None

    # Extract the original youtube URL from the message.
    # We don't want whatever else is in their message, just the full
    # url associated with the ID. This is to make a large clickable
    # link that maintains whatever other context they posted with the
    # url (timestamp, playlist, etc)
    # original_url = re.search('[^\s"\']+' + re.escape(id) + '[^\s"\']+', msg.text).group()

    original_url = strip_html(msg.text)

    # List who posted it, the title, and a linked thumbnail
    html = '{} posted a link to <b>{}</b><br/><a href="{}"><img src="{}"/></a>'.format(
        msg.user.name,
        title[:-10], # Title without the ` - YouTube` suffix
        original_url,
        thumbnail
    )

    for channel in msg.channels:
        msg.server.sendMessageChannel(channel, False, html)


@command('https?://(?:www\.)?veoh.com/watch/yapi-(?P<id>[^\s]+)\"')
def veoh(msg: TextMessage, id: str):
    """Handle YouTube links that are just rehosted on Veoh

    This method simply transforms the veoh url to a youtube one
    and delegates over to `youtube()`

    :param msg: TextMessage that triggered this command response
    :param id: YouTube video ID
    """
    youtube(msg, id)


@command('(?P<url>https?://(?:www\.)?vimeo[^\s]+)\"')
def vimeo(msg: TextMessage, url: str):
    """Vimeo links display the title of the video linked

    :param msg: TextMessage that triggered this command response
    :param url: Vimeo URL to read
    """
    title = get_url_title(page_url.format(id))

    text = '{} posted a link to <b>{}</b>'.format(
        msg.user.name,
        title[:-9] # Title without the `on Vimeo` suffix
    )

    for channel in msg.channels:
        msg.server.sendMessageChannel(channel, False, text)

@command(r'https?://store.steampowered.com/app/(?P<appid>[\d]+)')
def steam_store(msg: TextMessage, appid: str):
    """Steam store links that display information about an app

    :param msg: TextMessage that triggered this command response
    :param appid: Steam App ID
    """
    app = SteamApp(appid)

    # Compile final presentation for this steam app
    html = '{name} posted a link to <b>{app}</b><br/>{short_description}'.format(
        name=msg.user.name,
        app=app.name,
        short_description=app.short_description
    )

    # Additional context-aware information about the app.

    if app.is_early_access:
        if app.is_unreleased:
            html += '<br/><b>Unreleased Early Access Meme</b>'
        else:
            html += '<br/><b>Early Access Meme</b>'
    else:
        # It's not a meme
        if app.is_unreleased:
            html += '<br/><b>Unreleased:</b> Comes out {}'.format(app.release_date['date'])

    # Released app - check for aggregate reviews
    if not app.is_unreleased:
        if app.reviews:
            html += '<br/>' + '<br/>'.join([
                '<b>{type}:</b> {summary} ({count})'.format(**x) for x in app.reviews
            ])
        else:
            html += '<br/>Not enough reviews'

    # Pricing/discount information
    html += '<br/><b>Price:</b> {price} {discount}'.format(
        price=app.price,
        discount=app.discount
    )

    # Respond to the channel the link was posted in
    for channel in msg.channels:
        msg.server.sendMessageChannel(channel, False, html)


@command(r'https?://steamcommunity.com/(sharedfiles|workshop)/filedetails/.*\?id=(?P<itemid>[\d]+).*')
def steam_worshop(msg: TextMessage, itemid: str):
    """Steam workshop links that display information about an item

    :param msg: TextMessage that triggered this command response
    :param itemid: Workshop item ID
    """
    item = SteamWorkshopItem(itemid)
    item.load_from_api()

    # Compile final presentation for this item
    html = '{name} posted a link to <b>{title}</b> for {app}'.format(
        name=msg.user.name,
        title=item.title,
        app=item.appname
    )

    # Tag list (different per item and workshop app)
    for tag in item.tags:
        html += '<br/><b>{}:</b> {}'.format(tag[0], tag[1])

    # Respond to the channel the link was posted in
    for channel in msg.channels:
        msg.server.sendMessageChannel(channel, False, html)
