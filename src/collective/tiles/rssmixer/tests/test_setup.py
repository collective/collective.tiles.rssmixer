# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from collective.tiles.rssmixer.testing import COLLECTIVE_TILES_RSSMIXER_INTEGRATION_TESTING  # noqa

import unittest


class TestSetup(unittest.TestCase):
    """Test that collective.tiles.rssmixer is properly installed."""

    layer = COLLECTIVE_TILES_RSSMIXER_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')

    def test_product_installed(self):
        """Test if collective.tiles.rssmixer is installed."""
        self.assertTrue(self.installer.isProductInstalled(
            'collective.tiles.rssmixer'))

    def test_browserlayer(self):
        """Test that ICollectiveTilesRssmixerLayer is registered."""
        from collective.tiles.rssmixer.interfaces import (
            ICollectiveTilesRssmixerLayer)
        from plone.browserlayer import utils
        self.assertIn(
            ICollectiveTilesRssmixerLayer,
            utils.registered_layers())


class TestUninstall(unittest.TestCase):

    layer = COLLECTIVE_TILES_RSSMIXER_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')
        roles_before = api.user.get_roles(TEST_USER_ID)
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.installer.uninstallProducts(['collective.tiles.rssmixer'])
        setRoles(self.portal, TEST_USER_ID, roles_before)

    def test_product_uninstalled(self):
        """Test if collective.tiles.rssmixer is cleanly uninstalled."""
        self.assertFalse(self.installer.isProductInstalled(
            'collective.tiles.rssmixer'))

    def test_browserlayer_removed(self):
        """Test that ICollectiveTilesRssmixerLayer is removed."""
        from collective.tiles.rssmixer.interfaces import \
            ICollectiveTilesRssmixerLayer
        from plone.browserlayer import utils
        self.assertNotIn(
            ICollectiveTilesRssmixerLayer,
            utils.registered_layers())
