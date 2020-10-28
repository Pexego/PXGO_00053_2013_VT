from odoo import models, api, fields


class MailThread(models.AbstractModel):

    _inherit = 'mail.thread'

    @api.model
    def create(self, values):
        """Eliminamos el log de documento creado y cambios en campos"""
        return super(MailThread, self.
                     with_context({'mail_create_nolog': True,
                                   'mail_notrack': True})).create(values)

    @api.multi
    def write(self, values):
        """Eliminamos el log de cambios en campos"""
        return super(MailThread, self.
                     with_context({'mail_notrack': True})).write(values)


class Followers(models.Model):
    _inherit = 'mail.followers'

    res_model = fields.Char(index=False)
    channel_id = fields.Many2one(index=False)
    partner_id = fields.Many2one(index=False)


class Message(models.Model):
    _inherit = 'mail.message'

    message_id = fields.Char(index=False)
    model = fields.Char(index=False)
    subtype_id = fields.Many2one(index=False)
    mail_activity_type_id = fields.Many2one(index=False)
    author_id = fields.Many2one(index=False)


class Notification(models.Model):
    _inherit = 'mail.notification'

    is_read = fields.Boolean(index=False)
    is_email = fields.Boolean(index=False)
    email_status = fields.Selection(index=False)


class MailMail(models.Model):

    _inherit = "mail.mail"

    fetchmail_server_id = fields.Many2one(index=False)


class Invite(models.TransientModel):
    _inherit = 'mail.wizard.invite'

    res_model = fields.Char(index=False)
    res_id = fields.Integer(index=False)
