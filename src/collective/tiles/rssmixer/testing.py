# -*- coding: utf-8 -*-
from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE

# from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.testing import z2

import collective.tiles.rssmixer


class CollectiveTilesRssmixerLayer(PloneSandboxLayer):

    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        self.loadZCML(package=collective.tiles.rssmixer)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'collective.tiles.rssmixer:default')


COLLECTIVE_TILES_RSSMIXER_FIXTURE = CollectiveTilesRssmixerLayer()


COLLECTIVE_TILES_RSSMIXER_INTEGRATION_TESTING = IntegrationTesting(
    bases=(COLLECTIVE_TILES_RSSMIXER_FIXTURE,),
    name='CollectiveTilesRssmixerLayer:IntegrationTesting',
)


COLLECTIVE_TILES_RSSMIXER_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(COLLECTIVE_TILES_RSSMIXER_FIXTURE,),
    name='CollectiveTilesRssmixerLayer:FunctionalTesting',
)


# COLLECTIVE_TILES_RSSMIXER_ACCEPTANCE_TESTING = FunctionalTesting(
#     bases=(
#         COLLECTIVE_TILES_RSSMIXER_FIXTURE,
#         REMOTE_LIBRARY_BUNDLE_FIXTURE,
#         z2.ZSERVER_FIXTURE,
#     ),
#     name='CollectiveTilesRssmixerLayer:AcceptanceTesting',
# )
