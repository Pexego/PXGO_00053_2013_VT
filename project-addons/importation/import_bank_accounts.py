#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import xmlrpclib
import socket
import xlrd
import datetime


class import_banks(object):
    def __init__(self, dbname, user, passwd, accounts_file,
                 payment_mode_id_mandate=False):
        """método incial"""

        try:
            self.url_template = "http://%s:%s/xmlrpc/%s"
            self.server = "localhost"
            self.port = 9069
            self.dbname = dbname
            self.user_name = user
            self.user_passwd = passwd
            self.accounts_file = accounts_file
            self.payment_mode_id_mandate = payment_mode_id_mandate

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
        print "banks no: ", all_lines
        for rownum in range(1, all_lines):
            record = sh.row_values(rownum)
            try:
                partner_ids = self.search("res.partner",
                                          [('ref', '=', str(int(record[2])))])
                if partner_ids:
                    partner_bank_ids = self.\
                        search("res.partner.bank",
                               [('partner_id', '=', partner_ids[0]),
                                ('acc_number', '=', record[4])])
                    if not partner_bank_ids:
                        bank_ids = self.search("res.bank",
                                               [('code', '=',
                                                 record[4][4:8])])
                        country_ids = self.search("res.country",
                                                  [('code', '=',
                                                    record[4][:2])])
                        bank_vals = {
                            'partner_id': partner_ids[0],
                            'state': 'iban',
                            'acc_number': record[4],
                            'bank': bank_ids and bank_ids[0] or False,
                            'bank_name': record[3],
                            'bank_bic': record[5],
                            'acc_country_id': country_ids and country_ids[0] or
                            False
                        }
                        bank_id = self.create("res.partner.bank", bank_vals)
                    else:
                        bank_id = partner_bank_ids[0]
                    if self.payment_mode_id_mandate:
                        self.create("account.banking.mandate",
                                    {'type': 'recurrent',
                                     'recurrent_sequence_type': 'recurring',
                                     'signature_date':
                                     datetime.
                                     datetime(*xlrd.
                                              xldate_as_tuple(record[12],
                                                              cwb.datemode)).
                                     strftime("%Y-%m-%d"),
                                     'state': 'valid',
                                     'scheme': record[7],
                                     'partner_bank_id': bank_id})
                print "%s de %s" % (cont, all_lines)
                cont += 1
            except Exception, e:
                print "EXCEPTION: REC: %" % (record), e

        return True


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print u"Uso: %s <dbname> <user> <password> <accounts.xls> " \
              u"<payment_mode_id_mandate (optional)>" % sys.argv[0]
    else:
        import_banks(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4],
                     len(sys.argv) == 6 and sys.argv[5] or False)
