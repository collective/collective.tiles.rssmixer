# -*- coding: utf-8 -*-
from DateTime import DateTime
from collective.tiles.rssmixer import _
from plone.supermodel.model import Schema
from plone.tiles.tile import Tile
from zope import schema
from zope.component import getMultiAdapter
from zope.interface import implementer
from zope.interface import Interface
from requests.exceptions import Timeout

import feedparser
import logging
import requests
import time


logger = logging.getLogger(__name__)
# Accept these bozo_exceptions encountered by feedparser when parsing
# the feed:
ACCEPTED_FEEDPARSER_EXCEPTIONS = (feedparser.CharacterEncodingOverride,)


# store the feeds here (which means in RAM)
FEED_DATA = {}  # url: ({date, title, url, itemlist})


class IRSSMixerTile(Schema):
    """RSS tile schema interface."""

    title = schema.TextLine(
        title=_(u"Title"),
        description=_(
            u"Title of the portlet. If omitted, the title of the "
            u"feed will be used."
        ),
        required=False,
        default=u'',
    )

    count = schema.Int(
        title=_(u"Number of items to display"),
        description=_(u"How many items to list."),
        required=True,
        default=5,
    )

    urls = schema.List(
        title=_(u'List of RSS feeds'),
        description=_(
            u"Enter a list of RSS feeds (one per line) in the following shape:"
            u" source name|url."
        ),
        value_type=schema.TextLine(),
        required=True,
        missing_value=[],
    )

    timeout = schema.Int(
        title=_(u"Feed reload timeout"),
        description=_(
            u"Time in minutes after which the feed should be " u"reloaded."
        ),
        required=True,
        default=100,
    )
    show_dates = schema.Bool(
        title=_(u"Show dates"),
        description=_(
            u"If enabled, last update date for a feed will be shown."
        ),
        required=True,
        default=True,
    )

    show_source = schema.Bool(
        title=_(u"Show source name"),
        description=_(u"If enabled, feed source name will be shown."),
        required=True,
        default=True,
    )
    css_class = schema.TextLine(
        title=_('collection_tile_css_class', u'CSS class'),
        description=_(
            'collection_tile_css_class_help',
            u'Insert a list of additional css classes for this tile.',
        ),
        required=False,
        default=u'',
    )


class RSSMixerTile(Tile):
    """The RSS tile displays a configured RSS feed."""

    def __call__(self):
        self.context_state = getMultiAdapter(
            (self.context, self.request), name=u'plone_context_state'
        )
        self.update()
        return self.index()

    def deferred_update(self):
        """refresh data for serving via KSS"""
        for feed in self._getFeeds():
            feed.update()

    def update(self):
        """update data before rendering. We can not wait for KSS since users
        may not be using KSS."""
        self.deferred_update()

    def _getFeeds(self):
        """Return all feeds"""
        feeds = []  # a list of feed objects

        for feed_data in self.data.get('urls', []):
            source, url = feed_data.split('|')
            feed = FEED_DATA.get(url, None)
            if feed is None:
                # create it
                feed = FEED_DATA[url] = RSSMixerFeed(
                    url=url,
                    source=source,
                    timeout=self.data.get('timeout', 100),
                )
            feeds.append(feed)
        return feeds

    @property
    def feedurl(self):
        """return url of feed for portlet"""
        return self._getFeed().url

    @property
    def siteurl(self):
        """return url of site for portlet"""
        return self._getFeed().siteurl

    @property
    def feedlink(self):
        """return rss url of feed for portlet"""
        return self.data.get('url').replace("http://", "feed://")

    @property
    def title(self):
        """return title of feed for portlet"""
        return self.data.get('title', '') or self._getFeed().title

    @property
    def feedAvailable(self):
        """checks if the feed data is available"""
        return self._getFeed().ok

    def sortingForData(
        self, number_of_sources, number_of_items_to_display, feeds
    ):
        """Sort feed items by date"""

        itemsWithDate = []
        itemsWithoutDate = []

        for feed in feeds:
            for item in feed.items:
                if 'updated' in item:
                    itemsWithDate.append(item)
                else:
                    itemsWithoutDate.append(item)

        decorated = [(item['updated'], item) for item in itemsWithDate]
        decorated.sort(reverse=True)
        sortedItems = [item for (key, item) in decorated]
        sortedItems[len(sortedItems) :] = itemsWithoutDate
        return sortedItems[:number_of_items_to_display]

    @property
    def items(self):
        """View feeds sorted by date"""
        feeds = self._getFeeds()
        number_of_items_to_display = self.data.get('count')
        number_of_sources = len(self.data.get('urls', []))
        return self.sortingForData(
            number_of_sources, number_of_items_to_display, feeds
        )

    @property
    def enabled(self):
        return self._getFeed().ok


class IRSSMixerFeed(Interface):
    def __init__(url, source, timeout):
        """Initialize the feed with the given url. will not automatically load
        it timeout defines the time between updates in minutes.
        """

    def loaded():
        """Return if this feed is in a loaded state."""

    def title():
        """Return the title of the feed."""

    def items():
        """Return the items of the feed."""

    def feed_link():
        """Return the url of this feed in feed:// format."""

    def site_url():
        """Return the URL of the site."""

    def last_update_time_in_minutes():
        """Return the time this feed was last updated in minutes since epoch.
        """

    def last_update_time():
        """Return the time the feed was last updated as DateTime object."""

    def needs_update():
        """return if this feed needs to be updated."""

    def update():
        """Update this feed. will automatically check failure state etc.
        returns True or False whether it succeeded or not.
        """

    def update_failed():
        """Return if the last update failed or not."""

    def ok():
        """Is this feed ok to display?"""


@implementer(IRSSMixerFeed)
class RSSMixerFeed(object):
    """An RSS feed."""

    # TODO: discuss whether we want an increasing update time here, probably
    # not though
    # time in minutes after which we retry to load it after a failure
    FAILURE_DELAY = 10

    def __init__(self, url, source, timeout):
        self.url = url
        self.timeout = timeout
        self.source = source
        self._items = []
        self._title = ""
        self._siteurl = ""
        self._loaded = False  # is the feed loaded
        self._failed = False  # does it fail at the last update?
        self._last_update_time_in_minutes = 0  # when was the feed updated?
        self._last_update_time = None  # time as DateTime or Nonw

    @property
    def last_update_time_in_minutes(self):
        """Return the time the last update was done in minutes."""
        return self._last_update_time_in_minutes

    @property
    def last_update_time(self):
        """Return the time the last update was done in minutes."""
        return self._last_update_time

    @property
    def update_failed(self):
        return self._failed

    @property
    def ok(self):
        return not self._failed and self._loaded

    @property
    def loaded(self):
        """Return whether this feed is loaded or not."""
        return self._loaded

    @property
    def needs_update(self):
        """Check if this feed needs updating."""
        now = time.time() / 6
        return (self.last_update_time_in_minutes + self.timeout) < now

    def update(self):
        """Update this feed."""
        now = time.time() / 60  # time in minutes

        # check for failure and retry
        if self.update_failed:
            if (self.last_update_time_in_minutes + self.FAILURE_DELAY) < now:
                return self._retrieveFeed()
            else:
                return False

        # check for regular update
        if self.needs_update:
            return self._retrieveFeed()

        return self.ok

    def _getFeedFromUrl(self, url):
        """
        Use requests to retrieve an rss feed.
        In this way, we can manage timeouts.
        """
        try:
            res = requests.get(url, timeout=5)
        except Timeout as e:
            logger.exception(e)
            return ''
        if not res.ok or res.status_code != 200:
            logger.error(
                'Unable to retrieve RSS feed from "{0}": {1} - {2}'
            ).format(url, res.status_code, res.reason)
            return ''
        return res.text

    def _retrieveFeed(self):
        """Do the actual work and try to retrieve the feed."""
        url = self.url
        if url != '':
            self._last_update_time_in_minutes = time.time() / 60
            self._last_update_time = DateTime()
            feed_str = self._getFeedFromUrl(url)
            if not feed_str:
                self._loaded = True  # we tried at least but have a failed load
                self._failed = True
                return False
            d = feedparser.parse(feed_str)
            if d.bozo == 1 and not isinstance(
                d.get('bozo_exception'), ACCEPTED_FEEDPARSER_EXCEPTIONS
            ):
                self._loaded = True  # we tried at least but have a failed load
                self._failed = True
                return False
            self._title = d.feed.title
            self._siteurl = d.feed.link
            self._items = []

            for item in d['items']:
                try:
                    link = item.links[0]['href']
                    itemdict = {
                        'title': item.title,
                        'url': link,
                        'summary': item.get('description', ''),
                        'source': self.source,
                    }
                    if hasattr(item, "updated"):
                        itemdict['updated'] = DateTime(item.updated)
                except AttributeError:
                    continue
                self._items.append(itemdict)
            self._loaded = True
            self._failed = False
            return True

        self._loaded = True
        self._failed = True  # no url set means failed
        # no url set, although that actually should not really happen
        return False

    @property
    def items(self):
        return self._items

    # convenience methods for displaying

    @property
    def feed_link(self):
        """Return rss url of feed for portlet."""
        return self.url.replace("http://", "feed://")

    @property
    def title(self):
        """Return title of feed for portlet."""
        return self._title

    @property
    def siteurl(self):
        """Return the link to the site the RSS feed points to."""
        return self._siteurl
