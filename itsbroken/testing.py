# -*- coding: utf-8 -*-
"""
    testing

    :copyright: © 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: AGPL with Openlabs Exception, see LICENSE for more details.
"""
import time

from openerp.modules.registry import RegistryManager
from openerp.service.web_services import db

from .transaction import Transaction


DB_NAME = 'test_' + str(int(time.time()))
USER = 1
USER_PASSWORD = 'admin'
CONTEXT = {}

# Create a database with the name
DB = db().exp_create_database(
    DB_NAME, demo=False, lang=None, user_password=USER_PASSWORD
)


class Pool(object):
    """
    A proxy object to the current database pool
    """
    def __getattr__(self, name):
        """
        Just act as a proxy for all attributes
        """
        return getattr(RegistryManager.get(DB_NAME), name)


POOL = Pool()

# Load the default context of the admin user
with Transaction().start(DB_NAME, USER) as txn:
    CONTEXT.update(txn.get_context())


def install_module(module):
    """
    Install the given module. An assertion error is raised
    if the module could not be found
    """
    module_obj = POOL.get('ir.module.module')

    with Transaction().start(DB_NAME) as txn:
        module_ids = module_obj.search(
            txn.cursor, USER,
            [('name', '=', module)],
            context=CONTEXT
        )
        assert module_ids, "Module %s not found" % module
        module_obj.button_install(txn.cursor, USER, module_ids)

        # The new osv_memory way of doing this. Someone claimed this was better
        # but this is so fucked up mate. I have no idea why this bloat is the
        # default preference of OpenERP. RIP
        upgrade_wizard = POOL.get('base.module.upgrade')

        # The signature of the upgrade module method is (cr, uid, ids,
        # context=None).
        # ids is not really required (openerp just says its required). So just
        # send None and they will be happy.
        # **FUCK YOU OPENERP**
        upgrade_wizard.upgrade_module(txn.cursor, USER, None)


def drop_database():
    """
    Drop the test database created
    """
    db().exp_drop(DB_NAME)
