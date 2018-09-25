"""
    Steam API integrations (and web scraping) for retrieving
    information about a Steam app or workshop item.
"""
import requests
from bs4 import BeautifulSoup

from app.util import image_url_to_data_uri

class SteamApiException(Exception):
    pass


class SteamApp:
    """Information about a specific Steam app on the store

    Attributes are pulled directly from the `data` of the appdetails API,
    as well as some custom calculated attributes.

    Useful attributes include:
        - name
        - short_description
        - logo_url
        - movies
        - release_date [.coming_soon, .date]
        - publishers
        - developers
        - controller_support

    :param appid: Steam App ID
    """
    appid: str
    data: dict
    scraped: dict
    _logo_b64: str
    loaded: bool

    def __init__(self, appid: str):
        self.appid = appid
        self.loaded = False
        self.scraped = {
            'reviews': []
        }

    def load_from_api(self):
        """Populate attributes from available Steam APIs"""

        details_api = 'https://store.steampowered.com/api/appdetails/?appids={}&cc=us&l=en&json=1'
        # reviews_api = 'https://store.steampowered.com/appreviews/{}?json=1'
        store_url = 'https://store.steampowered.com/app/{}'

        # TODO: Async this up
        r = requests.get(details_api.format(self.appid))
        details_json = r.json()

        # Make sure the API is bringing back real app data
        if not details_json or not details_json[self.appid]['success']:
            raise SteamApiException('Invalid App ID')

        self.data = details_json[self.appid]['data']

        # Reviews - scraped from the store page since the official API only
        # provides overall review aggregation and not a split for recent vs all
        r = requests.get(store_url.format(self.appid))
        soup = BeautifulSoup(r.content, features='html.parser')

        for subtitle in soup.select('div.subtitle'):
            for caption in subtitle.stripped_strings:
                if caption == 'Recent Reviews:' or caption == 'All Reviews:':
                    summary = subtitle.parent.select('span.game_review_summary')

                    # These next two are horrible selectors, but it's all we got :(
                    count = subtitle.parent.select('span.responsive_hidden')
                    # desc = subtitle.parent.select('span.responsive_reviewdesc')

                    if summary and count:
                        self.scraped['reviews'].append({
                            'type': caption[:-1],
                            'summary': summary[0].get_text(strip=True),
                            'count': count[0].get_text(strip=True)[1:-1]
                        })

        self.loaded = True

    @property
    def price(self) -> str:
        """Calculate a human readable price string.

        Examples: `$19.99`, `Free`, `Coming Soon`
        """
        if self.is_free:
            return 'Free'

        # No price (unreleased game, or pulled)
        if 'price_overview' not in self.data:
            return 'Not Available'

        return '${}'.format(self.price_overview['final'] / 100)

    @property
    def discount(self) -> str:
        """Calculate a human readable discount string.

        Example: `(-50%)`
        Will return an empty string if there is no discount.
        """
        if not self.loaded:
            self.load_from_api()

        if 'price_overview' in self.data:
            discount = self.price_overview['discount_percent']
            if discount:
                return '(-{}%)'.format(discount)

        return ''

    @property
    def categories(self) -> list:
        """Return a list of categories

        Example: ['Single-player', 'Steam Achievements', 'Full controller support']
        """
        if not self.loaded:
            self.load_from_api()

        return [c['description'] for c in self.data['categories']]

    @property
    def genres(self) -> list:
        """Return a list of genres

        Example: ['Survival', 'Sandbox', 'Crafting', 'Open World', 'Indie', 'Multiplayer']
        """
        if not self.loaded:
            self.load_from_api()

        return [g['description'] for g in self.data['genres']]

    @property
    def reviews(self) -> list:
        """Return review summary information

        Example: ['All Reviews: Mixed (10)', 'Recent Reviews: Mixed (5)']

        May exclude 'Recent Reviews' if it's not old enough
        """
        if not self.loaded:
            self.load_from_api()

        return self.scraped['reviews']

    @property
    def is_early_access(self) -> bool:
        """Returns true if this app is still in early access"""
        return 'Early Access' in self.genres

    @property
    def is_unreleased(self) -> bool:
        """Returns true if this app isn't out yet"""
        return self.release_date['coming_soon'] == True

    @property
    def released(self) -> str:
        """Returns the actual release date of the app.

        Examples: `Aug 7, 2018`, `No release date`
        """
        if not self.release_date['date']:
            return 'No release date'

        return self.release_date['date']

    @property
    def logo_base64(self) -> str:
        """Return a base64 encoded version of this app's logo"""
        if not self._logo_b64:
            self._logo_b64 = image_url_to_data_uri(self.header_image)

        return self._logo_b64

    def __getattr__(self, attr):
        """Delegate attribute lookup to keys in our steam API JSON

        :param attr: Attribute to retrieve
        """
        if not self.loaded:
            self.load_from_api()

        if attr in self.data:
            return self.data[attr]

        raise AttributeError('Attribute {} not available from Steam API'.format(attr))


class SteamWorkshopItem:
    """Information about a specific item on the Steam Workshop

    Attributes are primarily pulled from web scraping since there's no API (afaik?)

    :param fileid: Workshop file ID
    """
    itemid: str
    scraped: dict
    loaded: bool

    def __init__(self, itemid: str):
        self.itemid = itemid
        self.loaded = False
        self.scraped = {
            'tags': []
        }

    def load_from_api(self):
        workshop_url = 'https://steamcommunity.com/sharedfiles/filedetails/?id={}'

        r = requests.get(workshop_url.format(self.itemid))
        soup = BeautifulSoup(r.content, features='html.parser')

        # Extract basic info (item name, app name)
        self.scraped['appname'] = soup.select_one('.apphub_AppName').text
        self.scraped['title'] = soup.select_one('.workshopItemTitle').text
        self.scraped['logo'] = soup.select_one('link[rel="image_src"]')['href']

        # Extract tags (variable number of tags and items per workshop item)
        for tag in soup.select('div.workshopTags'):
            self.scraped['tags'].append(tag.text.split(':\xa0'))

        """
        Scraping ratings would be nice, but not very doable right now.
        The star rating is based on an <img> that's embedded that has a certain
        filename (e.g. 4-star_large.png) but no other data on the page.
        """

        self.loaded = True

    @property
    def tags(self) -> list:
        return self.scraped['tags']

    @property
    def appname(self) -> str:
        return self.scraped['appname']

    @property
    def title(self) -> str:
        return self.scraped['title']

    @property
    def logo_url(self) -> str:
        """Image URL to either a logo image or a screenshot"""
        return self.scraped['logo']
