#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import xmlrpclib
import socket
import xlrd
import datetime


class import_account_entries(object):
    def __init__(self, dbname, user, passwd, accounts_file, file_type,
                 account_move_id):
        """método incial"""

        try:
            self.url_template = "http://%s:%s/xmlrpc/%s"
            self.server = "localhost"
            self.port = 8069
            self.dbname = dbname
            self.user_name = user
            self.user_passwd = passwd
            self.accounts_file = accounts_file
            if int(file_type) not in (1, 2, 3):
                raise Exception(u'Tipo defichero incorrecto')
            self.file_type = int(file_type)
            self.account_move_id = int(account_move_id)

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

        move_data = self.read('account.move', self.account_move_id,
                              ['date', 'journal_id', 'period_id'])
        cont = 1
        all_lines = sh.nrows - 1
        print "entries no: ", all_lines
        for rownum in range(1, all_lines):
            record = sh.row_values(rownum)
            try:
                line_vals = {'date': move_data['date'],
                             'period_id': move_data['period_id'][0],
                             'journal_id': move_data['journal_id'][0],
                             'move_id': self.account_move_id,
                             'partner_id': False}
                if self.file_type == 1 and record[2]:  # Saldos
                    account_ids = self.search("account.account",
                                              [('code', '=', record[0])])
                    if not account_ids:
                        raise Exception(u'Cuenta no encontrada %s' % record[0])
                    line_vals.update({
                        'account_id': account_ids[0],
                        'name': record[1]})

                    if record[3]:
                        partner_ids = self.search("res.partner",
                                                  [('ref', '=',
                                                    str(int(record[3])))])
                        if not partner_ids:
                            raise Exception(u'Empresa no encontrado %s' %
                                            str(int(record[3])))
                        else:
                            line_vals['partner_id'] = partner_ids[0]

                    if record[2] < 0:
                        line_vals['debit'] = abs(record[2])
                        line_vals['credit'] = 0.0
                    else:
                        line_vals['credit'] = record[2]
                        line_vals['debit'] = 0.0
                elif self.file_type == 2:  # Efectos proveedores
                    account_ids = self.search("account.account",
                                              [('code', '=', record[9])])
                    if not account_ids:
                        raise Exception(u'Cuenta no encontrada %s' % record[9])

                    supplier_ids = self.search("res.partner",
                                               [('ref', '=', record[11])])
                    if not supplier_ids:
                        print u'Proveedor no encontrado: ', record[11]

                    line_vals.update({
                        'account_id': account_ids[0],
                        'name': record[3] + u" " + record[5] + u" " +
                        record[11],
                        'partner_id': supplier_ids and supplier_ids[0] or
                        False,
                        'date_maturity':
                        datetime.
                        datetime(*xlrd.xldate_as_tuple(record[15],
                                                       cwb.datemode)).
                        strftime("%Y-%m-%d"),
                        })
                    if record[16]:
                        line_vals['currency_id'] = 3
                        line_vals['amount_currency'] = -record[16]
                    if record[14] < 0:
                        line_vals['debit'] = abs(record[14])
                        line_vals['credit'] = 0.0
                    else:
                        line_vals['credit'] = record[14]
                        line_vals['debit'] = 0.0
                elif self.file_type == 3:  # Efectos de clientes
                    account_ids = self.search("account.account",
                                              [('code', '=', record[10])])
                    if not account_ids:
                        raise Exception(u'Cuenta no encontrada %s'
                                        % record[10])

                    customer_ids = self.search("res.partner",
                                               [('ref', '=', record[12])])
                    if not customer_ids:
                        print u'Cliente no encontrado: ', record[12]

                    line_vals.update({
                        'account_id': account_ids[0],
                        'name': record[1] + u" " + record[6] + u" " +
                        record[12],
                        'partner_id': customer_ids and customer_ids[0] or
                        False,
                        'date_maturity':
                        datetime.
                        datetime(*xlrd.xldate_as_tuple(record[16],
                                                       cwb.datemode)).
                        strftime("%Y-%m-%d"),
                        })
                    if record[15] < 0:
                        line_vals['debit'] = abs(record[15])
                        line_vals['credit'] = 0.0
                    else:
                        line_vals['credit'] = record[15]
                        line_vals['debit'] = 0.0
                else:
                    print "%s de %s" % (cont, all_lines)
                    cont += 1
                    continue

                if line_vals:
                    self.create("account.move.line", line_vals)

                print "%s de %s" % (cont, all_lines)
                cont += 1
            except Exception, e:
                print "EXCEPTION: REC: ", (record), e
                print "%s de %s" % (cont, all_lines)
                cont += 1

        return True


if __name__ == "__main__":
    if len(sys.argv) < 7:
        print u"Uso: %s <dbname> <user> <password> <entries.xls> " \
              u"<file_type [(1, Account Balances),(2, Supplier entries),"\
              u"(3, Customer entries)]> <account_move_id>" % sys.argv[0]
    else:
        import_account_entries(sys.argv[1], sys.argv[2], sys.argv[3],
                               sys.argv[4], sys.argv[5], sys.argv[6])
