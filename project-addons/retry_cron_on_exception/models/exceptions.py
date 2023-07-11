from odoo import exceptions

class RetryCallbackException(exceptions.except_orm):
    def __init__(self, msg, time):
        super(RetryCallbackException, self).__init__(msg, value='')
        self.time = time
