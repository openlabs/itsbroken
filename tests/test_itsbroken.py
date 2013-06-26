# -*- coding: utf-8 -*-
"""
    example1

    :copyright: © 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: AGPL, see LICENSE for more details.
"""
import unittest

from itsbroken.transaction import Transaction
from itsbroken.testing import DB_NAME, POOL, USER, CONTEXT, \
    install_module, drop_database


class TestItsBroken(unittest.TestCase):
    """
    Test the itsbroken library by connecting to an instance of
    OpenERP.

    By default OpenERP has the res module and other core modules
    installed, so most of the test uses those modules.
    """
    def setUp(self):
        install_module('product')

    def test_0010_create(self):
        """
        Test by creating a new partner
        """
        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            partner_obj = POOL.get('res.partner')

            values = {
                'name': 'Sharoon Thomas'
            }
            id = partner_obj.create(
                txn.cursor, txn.user, values, txn.context
            )
            partner = partner_obj.browse(txn.cursor, txn.user, id)
            self.assertEqual(partner.name, values['name'])

    def test_0020_no_commit(self):
        """
        Ensure that commits don't happen
        """
        partner_count = None
        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            partner_obj = POOL.get('res.partner')
            partner_count = partner_obj.search(
                txn.cursor, txn.user, [], count=True
            )

            values = {
                'name': 'Sharoon Thomas'
            }
            partner_obj.create(
                txn.cursor, txn.user, values, txn.context
            )
            after_partner_count = partner_obj.search(
                txn.cursor, txn.user, [], count=True
            )
            self.assertEqual(partner_count + 1, after_partner_count)

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            partner_obj = POOL.get('res.partner')
            partner_count_new_txn = partner_obj.search(
                txn.cursor, txn.user, [], count=True
            )
            # Original partner counts should remain the same
            self.assertEqual(partner_count_new_txn, partner_count)

    def test_0030_with_commit(self):
        """
        Making commits and ensuring records are saved
        """
        partner_count = None
        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            partner_obj = POOL.get('res.partner')
            partner_count = partner_obj.search(
                txn.cursor, txn.user, [], count=True
            )

            values = {
                'name': 'Sharoon Thomas'
            }
            partner_obj.create(
                txn.cursor, txn.user, values, txn.context
            )
            txn.cursor.commit()

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            partner_obj = POOL.get('res.partner')
            partner_count_new_txn = partner_obj.search(
                txn.cursor, txn.user, [], count=True
            )
            # The count will be incremented since the previous transaction
            # was actually saved
            self.assertEqual(partner_count_new_txn, partner_count + 1)


def tearDownModule():
    """
    Drop the database at the end of this test module
    Works only with unittest2 (default in python 2.7+)
    """
    drop_database()


def suite():
    _suite = unittest.TestSuite()
    _suite.addTests([
        unittest.TestLoader().loadTestsFromTestCase(TestItsBroken),
    ])
    return _suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
