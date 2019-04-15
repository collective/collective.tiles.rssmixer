# -*- coding: utf-8 -*-
from collective.tiles.rssmixer.testing import (  # noqa
    COLLECTIVE_TILES_RSSMIXER_FUNCTIONAL_TESTING,  # noqa
)  # noqa
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import TEST_USER_PASSWORD
from plone.testing.z2 import Browser
from unittest import TestCase
from six.moves.urllib.parse import urlencode

import collective.tiles.rssmixer.tests as test_dir
import os


class RSSTileTest(TestCase):
    layer = COLLECTIVE_TILES_RSSMIXER_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.portalURL = self.portal.absolute_url()

        self.browser = Browser(self.layer['app'])
        self.browser.handleErrors = False
        self.browser.addHeader(
            'Authorization',
            'Basic {0}:{1}'.format(TEST_USER_NAME, TEST_USER_PASSWORD),
        )

        self.unprivileged_browser = Browser(self.layer['app'])
        setRoles(self.portal, TEST_USER_ID, ['Manager'])

        dirname = os.path.dirname(test_dir.__file__)
        self.foo = 'file://{0}'.format(os.path.join(dirname, 'RSS-foo.xml'))
        self.bar = 'file://{0}'.format(os.path.join(dirname, 'RSS-bar.xml'))

    def test_rss_tile(self):
        """This tile shows the first five items in a RSS feed.

        """
        # Use the RSS stored in the test directory, this way we don't have an
        # external dependency.

        query = {'urls': [self.foo, '']}
        url = '{0}/@@collective.tiles.rssmixer/unique?{1}'.format(
            self.portalURL, urlencode(query, doseq=True)
        )
        self.unprivileged_browser.open(url)

        self.assertIn('rss-mixer-tile', self.unprivileged_browser.contents)

        self.assertIn(
            '<a href="http://localhost:55440/plone/foo-one" title="Doc one">',
            self.unprivileged_browser.contents,
        )

    def test_mixed_rss_tile(self):
        """This tile shows the first five items in a RSS feed.

        """
        query = {
            'urls': ['foo|{0}'.format(self.foo), 'bar|{0}'.format(self.bar)],
            'show_source': True,
        }
        url = '{0}/@@collective.tiles.rssmixer/unique?{1}'.format(
            self.portalURL, urlencode(query, doseq=True)
        )
        self.unprivileged_browser.open(url)
        self.assertIn(
            '<span class="feed-source">bar</span>',
            self.unprivileged_browser.contents,
        )
        self.assertIn(
            '<span class="feed-source">foo</span>',
            self.unprivileged_browser.contents,
        )
