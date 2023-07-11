from odoo.tests.common import TransactionCase
from odoo.addons.retry_cron_on_exception.models.exceptions import RetryCallbackException
from odoo.exceptions import UserError
from psycopg2.extensions import TransactionRollbackError

class TestIrCron(TransactionCase):
    post_install = True
    at_install = True

    def setUp(self):
        super().setUp()
        self.cron_retry_on_exception = self.env['ir.cron'].create(
            {'name': 'Test', 'retry_on_exception': True, 'retry_on_exception_time': 9,
             'nextcall':'2023-01-01 00:00:00','numbercall':-1,'interval_number':1,'interval_type':'hours',
             'model_id': self.env['ir.model']._get('ir.cron').id})
        self.cron_no_retry_on_exception = self.env['ir.cron'].create({'name':'Test1','retry_on_exception':False,
                                                                    'model_id':self.env['ir.model']._get('ir.cron').id})
        self.transaction_rollback_exception = TransactionRollbackError("Concurrent update")
        self.user_error_exception = UserError("No concurrent error")

    def test_exception_raises_when_there_is_a_TransactionRollbackError_in_handle_callback_exception_and_retry_on_exception_is_True(self):
        with self.assertRaises(RetryCallbackException):
            self.cron_retry_on_exception._handle_callback_exception(self.cron_retry_on_exception.name, 123,
                                                                        self.cron_retry_on_exception.id, self.transaction_rollback_exception)


    def test_exception_no_raises_when_there_is_a_TransactionRollbackError_in_handle_callback_exception_and_retry_on_exception_is_False(self):
        self.cron_no_retry_on_exception._handle_callback_exception(self.cron_no_retry_on_exception.name, 123,
                                                                        self.cron_no_retry_on_exception.id, self.transaction_rollback_exception)

    def test_exception_no_raises_when_there_is_no_a_TransactionRollbackError_in_handle_callback_exception_and_retry_on_exception_is_True(self):
        self.cron_retry_on_exception._handle_callback_exception(self.cron_retry_on_exception.name, 123,
                                                                    self.cron_retry_on_exception.id, self.user_error_exception)


    def test_exception_no_raises_when_there_is_no_a_TransactionRollbackError_in_handle_callback_exception_and_retry_on_exception_is_False(self):
        self.cron_no_retry_on_exception._handle_callback_exception(self.cron_no_retry_on_exception.name, 123,
                                                                    self.cron_no_retry_on_exception.id, self.user_error_exception)
