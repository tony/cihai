# -*- coding: utf8 - *-
"""Cihai core functionality."""
from __future__ import absolute_import, print_function, unicode_literals

import logging
import os

import kaptan
from appdirs import AppDirs
from sqlalchemy import MetaData, create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session

from cihai import bootstrap, exc, extend
from cihai.config import expand_config
from cihai.constants import DEFAULT_CONFIG
from cihai.utils import import_string, merge_dict

from ._compat import string_types

log = logging.getLogger(__name__)


class Database(object):
    def __init__(self, config):
        self.engine = create_engine(config['database']['url'])

        self.metadata = MetaData()
        self.metadata.bind = self.engine
        self.reflect_db()

        self.session = Session(self.engine)

    def reflect_db(self):
        """
        No-op to reflect db info.

        This is available as a method so the database can be reflected
        outside initialization (such bootstrapping unihan during CLI usage).
        """
        self.metadata.reflect(views=True, extend_existing=True)
        self.base = automap_base(metadata=self.metadata)
        self.base.prepare()

    @property
    def is_bootstrapped(self):
        """Return True if UNIHAN and database is set up.

        Returns
        -------
        bool :
            True if Unihan application fixture data installed.
        """
        return bootstrap.is_bootstrapped(self.metadata)

    #: :class:`sqlalchemy.engine.Engine` instance.
    engine = None

    #: :class:`sqlalchemy.schema.MetaData` instance.
    metadata = None

    #: :class:`sqlalchemy.orm.session.Session` instance.
    session = None

    #: :class:`sqlalchemy.ext.automap.AutomapBase` instance.
    base = None


class Cihai(object):
    """
    Central application object.

    Notes
    -----

    Inspired by the early pypa/warehouse applicaton object [1]_.

    **Configuration templates**

    The ``config`` :py:class:`dict` parameter supports a basic template system
    for replacing :term:`XDG Base Directory` directory variables, tildes
    and environmentas variables. This is done by passing the option dict
    through :func:`cihai.conf.expand_config` during initialization.

    Examples
    --------

    **Invocation from Python**

    Cihai must be bootstrapped with data from the UNIHAN [2]_ database.

    :attr:`~cihai.core.Cihai.is_bootstrapped` can check if the system has the
    database installed. It checks against the application's configuration
    settings.

    To bootstrap the cihai environment programatically, create the Cihai
    object and pass its :attr:`~cihai.core.Cihai.metadata`:

    .. code-block:: python

        from cihai.core import Cihai
        from cihai.bootstrap import bootstrap_unihan

        c = Cihai()
        if not c.is_bootstrapped:  # download and install Unihan to db
            bootstrap_unihan(c.metadata)
            c.reflect_db()         # automap new table created during bootstrap

        query = c.lookup_char('好')
        glyph = query.first()
        print(glyph.kDefinition)

        query = c.reverse_char('good')
        print(', '.join([glyph_.char for glyph_ in query]))

    References
    ----------

    .. [1] UNICODE HAN DATABASE (UNIHAN) documentation.
       https://www.unicode.org/reports/tr38/. Accessed March 31st, 2018.
    .. [2] PyPA Warehouse on GitHub. https://github.com/pypa/warehouse.
       Accessed sometime in 2013.
    """

    #: configuration dictionary.
    config = None

    #: :py:class:`dict` of default config, can be monkey-patched during tests
    default_config = DEFAULT_CONFIG

    def __init__(self, config={}):
        # Merge custom configuration settings on top of defaults
        self.config = merge_dict(self.default_config, config)

        #: XDG App directory locations
        dirs = AppDirs("cihai", "cihai team")  # appname  # app author

        #: Expand template variables
        expand_config(self.config, dirs)

        if not os.path.exists(dirs.user_data_dir):
            os.makedirs(dirs.user_data_dir)

        self.sql = Database(self.config)

    def add_dataset(self, _cls, namespace):
        if isinstance(_cls, string_types):
            _cls = import_string(_cls)

        setattr(self, namespace, _cls())
        dataset = getattr(self, namespace)

        if isinstance(dataset, extend.SQLAlchemyMixin):
            dataset.sql = self.sql

        if hasattr(dataset, 'bootstrap') and callable(dataset.bootstrap):
            dataset.bootstrap()

    @classmethod
    def from_file(cls, config_path=None, *args, **kwargs):
        """
        Create a Cihai instance from a JSON or YAML config.

        Parameters
        ----------
        config_path : str, optional
            path to custom config file

        Returns
        -------
        :class:`Cihai` :
            application object
        """

        config_reader = kaptan.Kaptan()

        config = {}

        if config_path:
            if not os.path.exists(config_path):
                raise exc.CihaiException(
                    '{0} does not exist.'.format(os.path.abspath(config_path))
                )
            if not any(
                config_path.endswith(ext) for ext in ('json', 'yml', 'yaml', 'ini')
            ):
                raise exc.CihaiException(
                    '{0} does not have a yaml,yml,json,ini extend.'.format(
                        os.path.abspath(config_path)
                    )
                )
            else:
                custom_config = config_reader.import_config(config_path).get()
                config = merge_dict(config, custom_config)

        return cls(config)
