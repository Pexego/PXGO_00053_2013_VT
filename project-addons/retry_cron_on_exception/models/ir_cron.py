from odoo import api, fields, models
from dateutil.relativedelta import relativedelta
from psycopg2.extensions import TransactionRollbackError
from odoo.addons.retry_cron_on_exception.models.exceptions import RetryCallbackException

class IrCron(models.Model):
    _inherit = "ir.cron"

    retry_on_exception = fields.Boolean(help="If This field is checked, the cron will be retried if it fails")
    retry_on_exception_time = fields.Integer(default=0, help="This field represents the time in minutes that the cron will be retried if it fails")
    current_retry = fields.Integer(string='Current try', default=0, help="The current retry of this cron")
    max_retries = fields.Integer(
        string='Max. retries',
        help="The cron will fail if the number of tries reach the "
             "max. retries.\n"
             "Retries are infinite when 0.",
    )

    @api.model
    def _callback(self, cron_name, server_action_id, job_id):
        cron = self.env['ir.cron'].sudo().browse(job_id)
        if cron.retry_on_exception and cron.interval_type in ('end_month_w', 'end_month'):
            return super(IrCron, self.with_context({'force_time': cron.nextcall}))._callback(cron_name, server_action_id, job_id)
        return super(IrCron, self)._callback(cron_name, server_action_id, job_id)

    @classmethod
    def _process_job(cls, job_cr, job, cron_cr):
        """ The original function is inherited to add the possibility to retry a cron if there is a RetryCallbackException.
            :param job_cr: cursor to use to execute the job, safe to commit/rollback
            :param job: job to be run (as a dictionary).
            :param cron_cr: cursor holding lock on the cron job row, to use to update the next exec date,
                   must not be committed/rolled back!
        """
        nextcall = fields.Datetime.from_string(job['nextcall'])
        try:
            super()._process_job(job_cr,job,cron_cr)
            cron_cr.execute(
                f"UPDATE ir_cron SET current_retry=0 WHERE id={job['id']}")
            cron_cr.commit()
        except RetryCallbackException as e:
            cron_cr.execute(
                f"UPDATE ir_cron SET nextcall='{nextcall + relativedelta(minutes=e.time)}', current_retry={job['current_retry'] + 1} WHERE id={job['id']}")
            cron_cr.commit()

    @api.model
    def _handle_callback_exception(self, cron_name, server_action_id, job_id, job_exception):
        """
            The original function is inherited to add the possibility of retrying a cron if an exception has occurred.
            If the cron has checked the field retry_on_exception, and it is a concurrency exception we throw an
            RetryCallbackException (only if the current_retry < max retires or max_retries==0)
            that will be caught in another function in order to retry the cron
        :param cron_name: Name of the cron (string)
        :param server_action_id: Id of the action executed
        :param job_id: Id of the ir.cron
        :param job_exception: Exception raised
        """
        super(IrCron, self)._handle_callback_exception(cron_name,
                                                       server_action_id,
                                                       job_id,
                                                       job_exception)
        my_cron = self.env['ir.cron'].browse(job_id)
        if my_cron.retry_on_exception and (not my_cron.max_retries or my_cron.current_retry < my_cron.max_retries) \
            and isinstance(job_exception, TransactionRollbackError):
            raise RetryCallbackException(job_exception, my_cron.retry_on_exception_time)
