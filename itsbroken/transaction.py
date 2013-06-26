# -*- coding: UTF-8 -*-
'''

    Transactionalisation of cursor, user and context

    :copyright: (c) 2010-2013 by Openlabs Technologies & Consulting (P) Ltd.
    :license: AGPL with Openlabs Exception, see LICENSE for more details
'''
from threading import local

from openerp.modules.registry import RegistryManager


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

    def __init__(self):
        'Add openerp path to the system path and import the modules'
        pass

    def start(self, database_name, user=1, context=None):
        '''
        Start Transaction

        :param database_name: Name of the database
        :param user: ID of the user. It is used to build the context
                     if not specified and made available in the context
                     at all times.
        :param context: A dictionary that should be used as context when
                        making calls
        '''
        self._assert_stopped()

        self.pool = RegistryManager.get(database_name)
        self.cursor = self.pool.db.cursor()
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

    def _assert_stopped(self):
        'Assert that there is no active transaction'
        assert self.database is None
        assert self.cursor is None
        assert self.pool is None
        assert self.user is None
        assert self.context is None
