#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import xmlrpclib
import socket
import xlrd
import datetime


class import_account_entries(object):
    def __init__(self, dbname, user, passwd, accounts_file, file_type):
        """método incial"""

        try:
            self.url_template = "http://%s:%s/xmlrpc/%s"
            self.server = "localhost"
            self.port = 9069
            self.dbname = dbname
            self.user_name = user
            self.user_passwd = passwd
            self.accounts_file = accounts_file
            if int(file_type) not in (1, 2):
                raise Exception(u'Tipo defichero incorrecto')
            self.file_type = int(file_type)

            #
            # Conectamos con OpenERP
            #
            login_facade = xmlrpclib.ServerProxy(self.url_template %
                                                 (self.server, self.port,
                                                  'common'))
            self.user_id = login_facade.login(self.dbname, self.user_name,
                                              self.user_passwd)
            self.object_facade = xmlrpclib.ServerProxy(self.url_template %
                                                       (self.server, self.port,
                                                        'object'))

            res = self.import_bnk()
            #con exito
            if res:
                print ("All created")
        except Exception, e:
            print ("ERROR: ", (e))
            sys.exit(1)

        #Métodos Xml-rpc

    def exception_handler(self, exception):
        """Manejador de Excepciones"""
        print "HANDLER: ", (exception)
        return True

    def create(self, model, data, context={}):
        """
        Wrapper del metodo create.
        """
        try:
            res = self.object_facade.execute(self.dbname, self.user_id,
                                             self.user_passwd, model, 'create',
                                             data, context)
            return res
        except socket.error, err:
            raise Exception(u'Conexion rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception(u'Error %s en create: %s' % (err.faultCode,
                                                         err.faultString))

    def search(self, model, query, offset=0, limit=False, order=False,
               context={}, count=False, obj=1):
        """
        Wrapper del metodo search.
        """
        try:
            ids = self.object_facade.execute(self.dbname, self.user_id,
                                             self.user_passwd, model, 'search',
                                             query, offset, limit, order,
                                             context, count)
            return ids
        except socket.error, err:
            raise Exception(u'Conexion rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception(u'Error %s en search: %s' % (err.faultCode,
                                                         err.faultString))

    def read(self, model, ids, fields, context={}):
        """
        Wrapper del metodo read.
        """
        try:
            data = self.object_facade.execute(self.dbname, self.user_id,
                                              self.user_passwd, model, 'read',
                                              ids, fields, context)
            return data
        except socket.error, err:
            raise Exception(u'Conexion rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception(u'Error %s en read: %s' % (err.faultCode,
                                                       err.faultString))

    def write(self, model, ids, field_values, context={}):
        """
        Wrapper del metodo write.
        """
        try:
            res = self.object_facade.execute(self.dbname, self.user_id,
                                             self.user_passwd, model, 'write',
                                             ids, field_values, context)
            return res
        except socket.error, err:
            raise Exception(u'Conexion rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception(u'Error %s en write: %s' % (err.faultCode,
                                                        err.faultString))

    def unlink(self, model, ids, context={}):
        """
        Wrapper del metodo unlink.
        """
        try:
            res = self.object_facade.execute(self.dbname, self.user_id,
                                             self.user_passwd, model,
                                             'unlink', ids, context)
            return res
        except socket.error, err:
            raise Exception(u'Conexion rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception(u'Error %s en unlink: %s' % (err.faultCode,
                                                         err.faultString))

    def default_get(self, model, fields_list=[], context={}):
        """
        Wrapper del metodo default_get.
        """
        try:
            res = self.object_facade.execute(self.dbname, self.user_id,
                                             self.user_passwd, model,
                                             'default_get', fields_list,
                                             context)
            return res
        except socket.error, err:
                raise Exception('Conexion rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
                raise Exception('Error %s en default_get: %s' % (err.faultCode,
                                                                 err.
                                                                 faultString))

    def execute(self, model, method, *args, **kw):
        """
        Wrapper del método execute.
        """
        try:
            res = self.object_facade.execute(self.dbname, self.user_id,
                                             self.user_passwd, model, method,
                                             *args, **kw)
            return res
        except socket.error, err:
                raise Exception('Conexión rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
                raise Exception('Error %s en execute: %s' % (err.faultCode,
                                                             err.faultString))

    def exec_workflow(self, model, signal, ids):
        """ejecuta un workflow por xml rpc"""
        try:
            res = self.object_facade.exec_workflow(self.dbname, self.user_id,
                                                   self.user_passwd, model,
                                                   signal, ids)
            return res
        except socket.error, err:
            raise Exception(u'Conexión rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception(u'Error %s en exec_workflow: %s' % (err.faultCode,
                                                                err.
                                                                faultString))

    def import_bnk(self):
        cwb = xlrd.open_workbook(self.accounts_file,
                                 encoding_override="utf-8")
        sh = cwb.sheet_by_index(0)
        cont = 1
        all_lines = sh.nrows - 1
        invoices = {}
        last_invoice_id = False
        counterpart_acc_id = self.search("account.account",
                                         [("code", "=", "11300000")])

        print "entries no: ", all_lines
        history = True
        for rownum in range(1, all_lines):
            record = sh.row_values(rownum)
            if history:
                invoice_ids = self.search("account.invoice", [('number', '=',
                                                               record[0])])
                if invoice_ids:
                    print "%s de %s" % (cont, all_lines)
                    cont += 1
                    continue
                else:
                    history = False
            try:
                if record[0] not in invoices:
                    if record[12]:
                        pterm_ids = self.search("account.payment.term",
                                                [('name', '=', record[12])])
                        if not pterm_ids:
                            raise Exception(u'Plazo de pago no encontrado %s' %
                                            record[12])
                        else:
                            pterm_id = pterm_ids[0]
                    else:
                        pterm_id = False

                    if record[13]:
                        pmode_ids = self.search("payment.mode",
                                                [('name', '=', record[13])])
                        if not pmode_ids:
                            raise Exception(u'Modo de pago no encontrado %s' %
                                            record[13])
                        else:
                            pmode_id = pmode_ids[0]
                    else:
                        pmode_id = False
                    account_id = self.\
                        search("account.account",
                               [('code', '=', record[9])])[0]

                    partner_ids = self.search("res.partner",
                                              [('ref', '=', record[11])])
                    if not partner_ids:
                        raise Exception(u'Empresa no encontrado %s' %
                                        record[11])

                    invoice_date = datetime.\
                        datetime(*xlrd.xldate_as_tuple(record[4],
                                                       cwb.datemode)).\
                        strftime("%Y-%m-%d")

                    period_id = self.execute("account.period", "find",
                                             invoice_date)

                    invoice_vals = {
                        'number': record[0],
                        'invoice_number': record[0],
                        'supplier_invoice_number': record[2] or "",
                        'account_id': account_id,
                        'currency_id': 1,
                        'partner_id': partner_ids[0],
                        'payment_term': pterm_id,
                        'date_invoice': invoice_date,
                        'period_id': period_id[0],
                        'commercial_partner_id': partner_ids[0],
                        'payment_mode_id': pmode_id,
                        'allow_confirm_blocked': True
                    }

                    if pmode_id:
                        pmode_data = self.read("payment.mode", pmode_id,
                                               ["payment_order_type"])
                    if self.file_type == 1:
                        if record[16]:
                            invoice_vals['currency_id'] = 3
                        if record[5] == "Anticipo Proveedor":
                            journal_type = "purchase_refund"
                            inv_type = "in_refund"
                        else:
                            journal_type = "purchase"
                            inv_type = "in_invoice"
                        if pmode_id and \
                                pmode_data["payment_order_type"] == "payment":
                            bank_ids = self.search("res.partner.bank",
                                                   [('partner_id', 'child_of',
                                                     [partner_ids[0]])])
                            if bank_ids:
                                invoice_vals["partner_bank_id"] = bank_ids[0]
                    else:
                        if record[14] < 0:
                            journal_type = "sale_refund"
                            inv_type = "out_refund"
                        else:
                            journal_type = "sale"
                            inv_type = "out_invoice"
                        if pmode_id and \
                                pmode_data["payment_order_type"] == "debit":
                            bank_ids = self.search("res.partner.bank",
                                                   [('partner_id', 'child_of',
                                                     [partner_ids[0]]),
                                                    ('mandate_ids', '!=', [])])
                            if bank_ids:
                                bank_data = self.read("res.partner.bank",
                                                      bank_ids[0],
                                                      ["mandate_ids"])
                                invoice_vals["partner_bank_id"] = bank_ids[0]
                                invoice_vals["mandate_id"] = \
                                    bank_data['mandate_ids'][0]

                    journal_id = self.search("account.journal",
                                             [('type', '=', journal_type)])[0]
                    invoice_vals["journal_id"] = journal_id
                    invoice_vals["type"] = inv_type

                    invoice_id = self.create("account.invoice", invoice_vals)
                    invoices[record[0]] = invoice_id

                    if last_invoice_id:
                        self.execute("account.invoice", "button_reset_taxes",
                                     [last_invoice_id])
                        self.exec_workflow("account.invoice", "invoice_open",
                                           last_invoice_id)
                        self.write("account.invoice", [last_invoice_id],
                                   {'state': 'history'})

                    last_invoice_id = invoice_id
                else:
                    invoice_id = invoices[record[0]]

                due_date = datetime.\
                    datetime(*xlrd.xldate_as_tuple(record[15],
                                                   cwb.datemode)).\
                    strftime("%Y-%m-%d")
                line_vals = {'account_id': counterpart_acc_id[0],
                             'uos_id': 1,
                             'name': record[12] + u" " + due_date,
                             'invoice_id': invoice_id,
                             'price_unit': abs(record[14]),
                             'quantity': 1.0
                             }
                if self.file_type == 1:
                    if record[16]:
                        line_vals['price_unit'] = abs(record[16])
                self.create("account.invoice.line", line_vals)

                print "%s de %s" % (cont, all_lines)
                cont += 1
            except Exception, e:
                print "EXCEPTION: REC: ", (record), e
                print "%s de %s" % (cont, all_lines)
                cont += 1

        return True


if __name__ == "__main__":
    if len(sys.argv) < 6:
        print u"Uso: %s <dbname> <user> <password> <entries.xls> " \
              u"<file_type [(1, Supplier entries),"\
              u"(2, Customer entries)]>" % sys.argv[0]
    else:
        import_account_entries(sys.argv[1], sys.argv[2], sys.argv[3],
                               sys.argv[4], sys.argv[5])
