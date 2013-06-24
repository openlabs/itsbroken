# -*- coding: UTF-8 -*-
'''
    openlabs_toolkit.openerp.transaction

    Transactionalisation of cursor, user and context

    :copyright: (c) 2010-2011 by Openlabs Technologies & Consulting (P) Ltd.
    :license: AGPL, see LICENSE for more details
'''
import sys
from functools import partial
from threading import local


class Singleton(type):
    '''
    Metaclass for singleton pattern

    :copyright: Tryton Project
    '''
    def __init__(mcs, name, bases, dict_):
        super(Singleton, mcs).__init__(name, bases, dict_)
        mcs.instance = None

    def __call__(mcs, *args, **kwargs):
        if mcs.instance is None:
            mcs.instance = super(Singleton, mcs).__call__(*args, **kwargs)
        return mcs.instance


class Transaction(local):
    'A simple transaction'
    __metaclass__ = Singleton

    database = None
    pool = None
    cursor = None
    user = None
    context = None

    def __init__(self, root_path, config_file=None):
        'Add openerp path to the system path and import the modules'
        if root_path not in sys.path:
            sys.path.append(root_path)
        # pylint: disable-msg=F0401
        # pylint: disable-msg=W0612

        # Required before tools is imported to avoid cyclic dependency when
        # the tools module is imported
        import netsvc
        import tools
        if config_file is not None:
            from tools import config
            config.rcfile = config_file
            config.load()

        import pooler
        import osv
        import workflow
        import report

        # Load addons after the config is reloaded as the base module is looked
        # up based on the root path which is probably correct only after this
        # config file is loaded
        import addons

        from service.web_services import objects_proxy
        from service.web_services import common
        from service.web_services import db
        from netsvc import OpenERPDispatcher
        self.objects_proxy_service = objects_proxy()
        self.common_service = common()
        self.db_service = db()
        self.dispatcher = OpenERPDispatcher()

        # pylint: enable-msg=F0401
        # pylint: enable-msg=W0612

    def start(self, database_name, user, context=None):
        'Start Transaction'
        # pylint: disable-msg=F0401
        import pooler
        # pylint: enable-msg=F0401

        self._assert_stopped()

        self.database, self.pool = pooler.get_db_and_pool(database_name)
        self.cursor = self.database.cursor()
        self.user = user
        self.context = context if context is not None else self.get_context()
        return self

    def stop(self):
        'End the transaction'
        self.cursor.close()
        self.cursor = None
        self.user = None
        self.context = None
        self.database = None
        self.pool = None

    def get_context(self):
        'Loads the context of the current user'
        assert self.user is not None

        user_obj = self.pool.get('res.users')
        return user_obj.context_get(self.cursor, self.user)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.stop()

    def _assert_started(self):
        'Asserts if transaction is started'
        assert self.database is not None
        assert self.cursor is not None
        assert self.pool is not None
        assert self.user is not None
        assert self.context is not None

    def _assert_stopped(self):
        'Assert that there is no active transaction'
        assert self.database is None
        assert self.cursor is None
        assert self.pool is None
        assert self.user is None
        assert self.context is None

    def call_object_service(self, service_name, *args):
        'Proxy for Object Service'
        return getattr(self.objects_proxy_service, service_name)(*args)

    def call_common_service(self, service_name, *args):
        'Proxy for Common service'
        return getattr(self.common_service, service_name)(*args)

    def call_database_service(self, service_name, *args):
        'Proxy for Database Service'
        from .poseidon import _CONFIG
        if _CONFIG.current.version >= 6:
            # In version 6 all the database methods have the exp_ prefix for
            # all methods for some strange reason.
            service_name = 'exp_%s' % service_name

            # Interesting to see methods dont need password anymore assuming
            # everybody goes through the dispatcher
            args = args[1:]
        return getattr(self.db_service, service_name)(*args)

    def dispatch(self, service_name, method, params):
        'Generic dispatcher implementation'
        return self.dispatcher.dispatch(service_name, method, params)

    def get_partial(self, func):
        'Returns the partial function for func'
        return partial(
            func, self.cursor, self.user, context=self.context)

    def call_partial(self, func, *args, **kwargs):
        'Makes a partial call to the func'
        self._assert_started()
        return self.get_partial(func)(*args, **kwargs)


class ContextModel(object):
    '''A helper class which when mixed as the nearest ancestor in
    a multiple inheritance pattern allows the contextualisation of
    cursor user and context.

    This only works for known/standard ORM Methods
    '''

    def _make_partial_call(self, name, *args, **kwargs):
        'Makes a partial call'
        func = partial(getattr(self, name),
                Transaction().cursor, Transaction().user,
                context = Transaction().context)
        return func(*args, **kwargs)

    def create_(self, values, *args, **kwargs):
        'Creates a new record'
        return self._make_partial_call('create', values, *args, **kwargs)

    def search_(self, args, offset=0, limit=None, order=None, count=False):
        'Alternate implementation of search'
        return self._make_partial_call(
            'search', args, offset, limit, order, count=count)

    def read_(self, ids, fields_to_read=None, *args, **kwargs):
        'Proxy of Read'
        return self._make_partial_call('read', ids, fields_to_read, 
            *args, **kwargs)

    def write_(self, ids, values, *args, **kwargs):
        'Proxy of write'
        return self._make_partial_call('write', ids, values, *args, **kwargs)

    def unlink_(self, ids, *args, **kwargs):
        'Proxy of Unlink'
        return self._make_partial_call('unlink', ids, *args, **kwargs)

    def copy_(self, id, default=None, *args, **kwargs):
        'Proxy of Copy'
        return self._make_partial_call('copy', id, default, *args, **kwargs)

    def browse_(self, ids, *args, **kwargs):
        'Proxy of Browse'
        return self._make_partial_call('browse', ids, *args, **kwargs)

    def search_count_(self, domain, *args, **kwargs):
        'Proxy of Search Count'
        return self._make_partial_call('search_count', domain, *args, **kwargs)

    def name_get_(self, ids, *args, **kwargs):
        'Proxy of name_get'
        return self._make_partial_call('name_get', ids, *args, **kwargs)
