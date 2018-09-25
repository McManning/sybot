
import zlib
from PIL import Image
from io import BytesIO

import base64
import re
import requests
# from bs4 import BeautifulSoup

def image_url_to_data_uri(url: str) -> str:
    """Returns a base 64 data URI version of the source URL image

    :param url: Source URL
    """
    r = requests.get(url)

    # TODO: Automatic image compression for images that will be too large to send.
    # Probably use PIL to resize the source image and then b64 that.

    uri = 'data:{};base64,{}'.format(
        r.headers['Content-Type'],
        base64.b64encode(r.content).decode('utf-8') # str(base64.b64encode(r.content).decode("utf-8")))
    )

    return uri

def get_url_title(url: str) -> str:
    """Extract the <title> element from a page and return

    :param url: URL to grab HTML from
    """
    r = requests.get(url)

    # Soup is slow - especially for insane DOMs like YouTube.
    # soup = BeautifulSoup(r.content, features='html.parser')

    # titles = soup.find_all('title')
    # if titles:
    #     return titles[0].get_text(strip=True)

    match = re.search("<title>(?P<title>.*)</title>", r.text, re.IGNORECASE)
    if match:
        return match.group('title')

    return 'No Title'

def texture_to_data_uri(texture) -> str:
    """Convert a Murmur Texture to a data uri encoded PNG"""

    if len(texture) < 1:
        return None

    # Murmur gives us the *original* image data, so we want
    # to try to decode that, crush it to an avatar size, and encode
    image = Image.open(BytesIO(texture))
    image.thumbnail((128, 128), Image.ANTIALIAS)

    # Convert image to PNG string
    buffered = BytesIO()
    image.save(buffered, format='PNG')

    encoded = base64.b64encode(buffered.getvalue())
    return 'data:image/png;base64,' + encoded.decode('utf-8')

def strip_html(html: str) -> str:
    """Strip out tags from an HTML string

    :param html: content to strip
    """
    return re.sub('<[^<]+?>', '', html)
