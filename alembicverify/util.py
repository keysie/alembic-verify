# -*- coding: utf-8 -*-
from collections import namedtuple
from uuid import uuid4
import json

from alembic import command
from alembic.config import Config
from alembic.environment import EnvironmentContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, create_engine
from sqlalchemy_utils import create_database, drop_database, database_exists

from alembicverify.testing.models import Base
from test import assert_items_equal


TablesInfo = namedtuple(
    'TablesInfo', ['left', 'right', 'left_only', 'right_only', 'common'])
"""Represent information about the tables in a comparison between two
databases.  It's meant for internal use. """


DiffResult = namedtuple(
    'DiffResult', ['left_only', 'right_only', 'common', 'diff'])
"""Represent information about table properties in a comparison between
tables from two databases.  It's meant for internal use. """


class InspectorFactory(object):

    """Create a :func:`sqlalchemy.inspect` instance for a given URI. """

    @classmethod
    def from_uri(cls, uri):
        engine = create_engine(uri)
        inspector = inspect(engine)
        return inspector


class CompareResult(object):

    """Represent the result of a comparison.

    It tells if the comparison was a match, and it allows the user to
    dump both the `info` and `errors` dicts to a file in JSON format,
    so that they can be inspected.
    """

    def __init__(self, info, errors):
        self.info = info
        self.errors = errors

    @property
    def is_match(self):
        """Tell if comparison was a match. """
        return not self.errors

    def dump_info(self, filename='info_dump.json'):
        """Dump `info` dict to a file. """
        return self._dump(self.info, filename)

    def dump_errors(self, filename='errors_dump.json'):
        """Dump `errors` dict to a file. """
        return self._dump(self.errors, filename)

    def _dump(self, data_to_dump, filename):
        data = self._dump_data(data_to_dump)
        if filename is not None:
            self._write_data_to_file(data, filename)
        return data

    def _dump_data(self, data):
        return json.dumps(data, indent=4, sort_keys=True)

    def _write_data_to_file(self, data, filename):
        with open(filename, 'w') as stream:
            stream.write(data)


def new_db(uri):
    """Drop the database at ``uri`` and create a brand new one. """
    safe_destroy_database(uri)
    create_database(uri)


def safe_destroy_database(uri):
    """Safely destroy the database at ``uri``. """
    if database_exists(uri):
        drop_database(uri)


def get_temporary_uri(uri):
    """Create a temporary URI given another one.

    For example, given this uri:
    "mysql+mysqlconnector://root:@localhost/alembicverify"

    a call to ``get_temporary_uri(uri)`` could return something like this:
    "mysql+mysqlconnector://root:@localhost/test_db_000da...898fe"

    where the last part of the name is taken from a unique ID in hex
    format.
    """
    base, _ = uri.rsplit('/', 1)
    uri = '{}/test_db_{}'.format(base, uuid4().hex)
    return uri


def make_alembic_config(uri, folder):
    """Create a configured :class:`alembic.config.Config` object. """
    config = Config()
    config.set_main_option("script_location", folder)
    config.set_main_option("sqlalchemy.url", uri)
    return config


def prepare_schema_from_migrations(uri, config, revision="head"):
    """Applies migrations to a database.

    :param string uri: The URI for the database.
    :param config: A :class:`alembic.config.Config` instance.
    :param revision: The revision we want to feed to the
        ``command.upgrade`` call. Normally it's either "head" or "+1".
    """
    engine = create_engine(uri)
    script = ScriptDirectory.from_config(config)
    command.upgrade(config, revision)
    return engine, script


def prepare_schema_from_models(uri):
    """Creates the database schema from the ``SQLAlchemy`` models. """
    engine = create_engine(uri)
    Base.metadata.create_all(engine)


def get_current_revision(config, engine, script):
    """Inspection helper. Get the current revision of a set of migrations. """
    return _get_revision(config, engine, script)


def get_head_revision(config, engine, script):
    """Inspection helper. Get the head revision of a set of migrations. """
    return _get_revision(config, engine, script, revision_type='head')


def _get_revision(config, engine, script, revision_type='current'):
    with engine.connect() as conn:
        with EnvironmentContext(config, script) as env_context:
            env_context.configure(conn, version_table="alembic_version")
            if revision_type == 'head':
                revision = env_context.get_head_revision()
            else:
                migration_context = env_context.get_context()
                revision = migration_context.get_current_revision()
    return revision


def walk_dict(d, path):
    """Walks a dict given a path of keys.

    For example, if we have a dict like this::

        d = {
            'a': {
                'B': {
                    1: ['hello', 'world'],
                    2: ['hello', 'again'],
                }
            }
        }

    Then ``walk_dict(d, ['a', 'B', 1])`` would return
    ``['hello', 'world']``.
    """
    if not path:
        return d
    return walk_dict(d[path[0]], path[1:])
