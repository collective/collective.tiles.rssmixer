.. This README is meant for consumption by humans and pypi. Pypi can render rst files so please do not use Sphinx features.
   If you want to learn more about writing documentation, please check out: http://docs.plone.org/about/documentation_styleguide.html
   This text does not appear on pypi or github. It is a comment.

=========================
collective.tiles.rssmixer
=========================

This product provides a tile that can fetch RSS feeds from multiple sources and show them together.

Usage
-----

The tile has a set of parameters that allows to configure source feeds and how to render them.
You can set a list of RSS feed urls. Results will be mixed and sorted by date.

Translations
------------

This product has been translated into

- Italian


Installation
------------

Install collective.tiles.rssmixer by adding it to your buildout::

    [buildout]

    ...

    eggs =
        collective.tiles.rssmixer


and then running ``bin/buildout``


Contribute
----------

- Issue Tracker: https://github.com/collective/collective.tiles.rssmixer/issues
- Source Code: https://github.com/collective/collective.tiles.rssmixer


Support
-------

If you are having issues, please let us know.
We have a mailing list located at: project@example.com


License
-------

The project is licensed under the GPLv2.
