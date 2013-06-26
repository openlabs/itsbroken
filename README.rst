"Untested code is broken code"
==============================

It's broken helps you to write unit tests for broken OpenERP modules since
OpenERP does not have much in testing capabilities. If you find strange
resemblance to `Tryton <http://tryton.org>`_ test cases, do not be
confused, this work is inspired by Tryton testing.

Master
------

.. image:: https://travis-ci.org/openlabs/itsbroken.png?branch=master

Develop
-------

.. image:: https://travis-ci.org/openlabs/itsbroken.png?branch=develop

License tl;dr;
--------------

If you intend to publish modules that you use, this program comes with an
AGPL license.

If you wish to use this program in a module which you don't intend to make
public, you should have met the following conditions:

  * You have tweeted atleast once with the #sorryopenerp tag 
    (Frequent bugs in Open ERP will push you in the right 
    direction)
  * You have visited the `Tryton website <http://tryton.org>`_ atleast once.
  * You believe that code without test is broken code (like 
    Hollywood is incomplete without Julia Roberts)
  * You do not use OpenERP or any modules with the "OpenERP 
    AGPL + Private Use License"

The detailed version of the license can be see in the LICENSE file.

Why this license mess ?
~~~~~~~~~~~~~~~~~~~~~~~

While we are 100% committed to Open Source (see also our FAQ), we understand 
that end-users may sometimes require to use private software. To address this
need, OpenERP Enterprise comes with a special additional permission, granted
to each subscriber of OpenERP Enterprise, but exclusively in the context of
private use. We think this is stupid exploitation of work by a greedy
company. 

Example usage
-------------

.. code-block:: python

    import unittest

    from itsbroken.transaction import Transaction
    from itsbroken.testing import DB_NAME, POOL, USER, CONTEXT, \
        install_module, drop_database


    class TestItsBroken(unittest.TestCase):
        """
        Test the itsbroken library by connecting to an instance of
        OpenERP.

        By defualt OpenERP has the partner module and other core modules
        installed, so most of the test uses those modules.
        """
        def setUp(self):
            install_module('product')

        def test_0010_create(self):
            """
            Test by creating a new product
            """
            with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
                product_obj = POOL.get('product.product')

                values = {
                    'name': 'Sharoon Thomas'
                }
                id = product_obj.create(
                    txn.cursor, txn.user, values, txn.context
                )
                product = product_obj.browse(txn.cursor, txn.user, id)
                self.assertEqual(product.name, values['name'])


    if __name__ == '__main__':
        unittest.main()


More examples
-------------

Tests of this module itself is a good example of how to use itsbroken for
testing. See `tests/test_itsbroken.py <https://github.com/openlabs/itsbroken/blob/develop/tests/test_itsbroken.py>`_.
