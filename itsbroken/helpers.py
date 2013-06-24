# -*- coding: UTF-8 -*-
'''
OpenERP access library to connect to a single database
and work on it. Ideally suited as a test suite.

:copyright: (c) 2010-2013 by Openlabs Technologies & Consulting (P) Ltd.

:license: AGPL, see LICENSE for more details
'''
from functools import partial
import ConfigParser
import threading
import time
import sys

from .transaction import Transaction, ContextModel

_CONFIG = threading.local()


class OpenERPConfig(object):
    'Openerp configuration class'
    #: config_file is the path to the location where
    #: openerp_server rc is located. Usually located in
    #: your home path, because OpenERP saves it there
    config_file = '~/.openerp_serverrc'

    #: Database to connect to
    database = None

    #: User with which to connect to Defaults to Admin (1)
    user = 1
    password = 'admin'

    #: Autocommit mode, otherwise the commit() method must
    #: be called
    auto_commit = True

    #: Context, if context remains none, the context will be
    #: generated automatically from the user's preferences
    context = None

    #: Language, defaults to en_US
    language = 'en_US'

    #: Parsed Configuration object
    config = None

    #: Version of OpenERP to which the connection has to be made
    version = 5

    def __init__(self, config_file=None, database=None, version=None):
        if config_file is not None:
            self.config_file = config_file
        if database is not None:
            self.database = database
        if version is not None:
            self.version = version
        self.load_config()

    def load_config(self):
        'Read the configuration file'
        self.config = ConfigParser.ConfigParser()
        self.config.readfp(open(self.config_file))

    @property
    def root_path(self):
        'Return the root path'
        return self.config.get('options', 'root_path')

    @property
    def admin_password(self):
        'Return the admin password'
        return self.config.get('options', 'admin_passwd')


def set_config(config_file, database=None, user=1, context=None, version=None):
    "Set the configuration"
    _CONFIG.current = OpenERPConfig(config_file, database, version)
    _CONFIG.current.user = user
    _CONFIG.current.context = context
    Transaction(_CONFIG.current.root_path)


def create_database(db_name, demo=False, lang=None, user_password='admin'):
    'Create a database'
    current = _CONFIG.current
    lang = current.language if lang is None else lang
    transaction = Transaction(current.root_path, current.config_file)
    res = transaction.call_database_service('create', 
        current.admin_password, db_name, demo, lang, user_password)
    # Now wait for the proccess tp be complete
    while True:
        progress, user = transaction.call_database_service(
            'get_progress', current.admin_password, res)
        sys.stdout.write('.')
        if progress == 1.0:
            sys.stdout.write('\n')
            break
        else:
            time.sleep(1)


def setup_database(config_path, dbname, version, demo=True):
    set_config(config_path, version=version)
    create_database(dbname, demo)
    set_config(config_path, dbname, version=version)


def setup_module(modules):
    module_obj = Model('ir.module.module')
    module_ids = module_obj.search_([
        ('name', 'in', modules)])
    module_obj._make_partial_call('button_install', module_ids)
    if _CONFIG.current.version < 6:
        upgrade_wizard = Wizard('module.upgrade')
        upgrade_wizard.create()
        return upgrade_wizard.execute({}, 'start')
    else:
        # The new osv_memory way of doing this. Someone claimed this was better
        # but this is so fucked up mate. I have no idea why this bloat is the
        # default preference of OpenERP. RIP
        upgrade_wizard = Model('base.module.upgrade')

        # The signature of the upgrade module method is (cr, uid, ids, 
        # context=None). Cursor and user is provided by the partial call, while
        # ids is not really required (openerp just says its required). So just
        # send None and they will be happy. FUCK YOU OPENERP
        return upgrade_wizard._make_partial_call('upgrade_module', None)


def drop_database(db_name):
    'Drop the database'
    current = _CONFIG.current
    transaction = Transaction(current.root_path, current.config_file)
    transaction.call_database_service('drop', current.admin_password, db_name)


class Wizard(object):
    'Wizard proxy'
    def __init__(self, name):
        super(Wizard, self).__init__()
        assert name, 'Wizard name cannot be none'
        assert _CONFIG.current.database is not None, 'DB undefined'
        self.name = name
        self.wiz_id = None

    def create(self, datas=None):
        'Calls the create instance of the wizard'
        from netsvc import LocalService
        wizard_service = LocalService('wizard')
        settings = _CONFIG.current

        self.wiz_id = wizard_service.create(
            settings.database, settings.user, settings.password, 
            self.name, datas)
        return self.wiz_id

    def execute(self, datas=None, action='init'):
        'Call execute on wizard'
        assert self.wiz_id is not None, "ID cannot be None"
        if datas is None:
            datas = { }
        from netsvc import LocalService
        wizard_service = LocalService('wizard')
        settings = _CONFIG.current

        return wizard_service.execute(
            settings.database, settings.user, settings.password,
            self.wiz_id, datas, action, settings.context)


class Model(ContextModel):
    'Model proxy object'
    def __init__(self, name):
        super(Model, self).__init__()
        settings = _CONFIG.current
        assert settings.database is not None, 'DB undefined'
        with Transaction().start(settings.database, settings.user):
            assert name in Transaction().pool.obj_list(), 'Invalid Model Name'
            self._poseidon_obj = Transaction().pool.get(name)

    def _make_partial_call(self, name, *args, **kwargs):
        'Makes a partial call'
        settings = _CONFIG.current
        with Transaction().start(
                settings.database, 
                settings.user) as transaction:
            func = partial(
                    getattr(self._poseidon_obj, name),
                    transaction.cursor,
                    transaction.user,
                    context = transaction.context)
            result = func(*args, **kwargs)
            if settings.auto_commit:
                transaction.cursor.commit()
        return result

    def __getattr__(self, name):
        return getattr(self._poseidon_obj, name)

    def find(self, domain):
        'Return a list of record objects matching criteria'
        ids = self.search_(domain)
        return [Record(self, id_) for id_ in ids]


class Record(object):
    '''Proxy to a Record, similar to Browse Record

    :param model: The instance Model to which this belongs
    :param record_id: ID of the record
    '''
    def __init__(self, model, record_id):
        self._p_model = model
        self.id = record_id

    def __getattr__(self, name):
        if name in self._p_model._columns:
            field = self._p_model._columns[name]
        elif name in self._p_model._inherit_fields:
            field = self._p_model._inherit_fields[name][2]

        read_result = self._p_model.read_(self.id, [name])
        if name in read_result:
            value = read_result[name]
        else:
            raise AttributeError

        if not value:
            return False

        if field._type in ('many2one', 'one2one'): 
            return Record(Model(field._obj), value[0])
        elif field._type in ('one2many', 'many2many'):
            return [Record(Model(field._obj), _id) for _id in value]
        elif field._type == 'reference':
            model, record_id = value.split(',')
            return Record(Model(model), record_id)
        return value

    def __repr__(self):
        return u'<Record (%s, %s)>' % (self._p_model._name, self.id)
