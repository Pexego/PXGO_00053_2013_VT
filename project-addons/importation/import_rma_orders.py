#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import xmlrpclib
import socket
import xlrd

class import_rma_order(object):
    def __init__(self, dbname, user, passwd, rmas_file):
        """método incial"""

        try:
            self.url_template = "http://%s:%s/xmlrpc/%s"
            self.server = "localhost"
            self.port = 9069
            self.dbname = dbname
            self.user_name = user
            self.user_passwd = passwd
            self.rmas_file = rmas_file

            #
            # Conectamos con OpenERP
            #
            login_facade = xmlrpclib.ServerProxy(self.url_template % (self.server, self.port, 'common'))
            self.user_id = login_facade.login(self.dbname, self.user_name, self.user_passwd)
            self.object_facade = xmlrpclib.ServerProxy(self.url_template % (self.server, self.port, 'object'))

            res = self.import_orders()
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
            res = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                                            model, 'create', data, context)
            return res
        except socket.error, err:
            raise Exception(u'Conexion rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception(u'Error %s en create: %s' % (err.faultCode, err.faultString))


    def search(self, model, query, offset=0, limit=False, order=False, context={}, count=False, obj=1):
        """
        Wrapper del metodo search.
        """
        try:
            ids = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                    model, 'search', query, offset, limit, order, context, count)
            return ids
        except socket.error, err:
                raise Exception(u'Conexion rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
                raise Exception(u'Error %s en search: %s' % (err.faultCode, err.faultString))


    def read(self, model, ids, fields, context={}):
        """
        Wrapper del metodo read.
        """
        try:
            data = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                            model, 'read', ids, fields, context)
            return data
        except socket.error, err:
                raise Exception(u'Conexion rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
                raise Exception(u'Error %s en read: %s' % (err.faultCode, err.faultString))


    def write(self, model, ids, field_values,context={}):
        """
        Wrapper del metodo write.
        """
        try:
            res = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                                    model, 'write', ids, field_values, context)
            return res
        except socket.error, err:
                raise Exception(u'Conexion rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
                raise Exception(u'Error %s en write: %s' % (err.faultCode, err.faultString))


    def unlink(self, model, ids, context={}):
        """
        Wrapper del metodo unlink.
        """
        try:
            res = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                                    model, 'unlink', ids, context)
            return res
        except socket.error, err:
                raise Exception(u'Conexion rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
                    raise Exception(u'Error %s en unlink: %s' % (err.faultCode, err.faultString))

    def default_get(self, model, fields_list=[], context={}):
        """
        Wrapper del metodo default_get.
        """
        try:
            res = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                        model, 'default_get', fields_list, context)
            return res
        except socket.error, err:
                raise Exception('Conexion rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
                raise Exception('Error %s en default_get: %s' % (err.faultCode, err.faultString))

    def execute(self, model, method, *args, **kw):
        """
        Wrapper del método execute.
        """
        try:
            res = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                                                model, method, *args, **kw)
            return res
        except socket.error, err:
                raise Exception('Conexión rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
                raise Exception('Error %s en execute: %s' % (err.faultCode, err.faultString))

    def exec_workflow(self, model, signal, ids):
        """ejecuta un workflow por xml rpc"""
        try:
            res = self.object_facade.exec_workflow(self.dbname, self.user_id, self.user_passwd, model, signal, ids)
            return res
        except socket.error, err:
            raise Exception(u'Conexión rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception(u'Error %s en exec_workflow: %s' % (err.faultCode, err.faultString))


    def import_orders(self):
        cwb = xlrd.open_workbook(self.rmas_file, encoding_override="utf-8")
        sh = cwb.sheet_by_index(0)

        cont = 1
        all_lines = sh.nrows - 1
        print "lines no: ", all_lines
        context = {'lang': 'es_ES'}
        last_number = False
        for rownum in range(1, all_lines):
            record = sh.row_values(rownum)
            if not last_number:
                last_number = str(int(record[0]))
            try:
                rma_ids = self.search("crm.claim", [('number', '=', str(int(record[0])))])
                if not rma_ids:
                    last_number = str(int(record[0]))
                    partner_ids = self.search("res.partner", [('name', 'ilike', record[5]),('is_company', '=', True),('customer', '=', True)], context=context)

                    if record[4]:
                        user_ids = self.search("res.users", [('name', 'ilike', record[4])], context=context)
                    else:
                        user_ids = []
                    sat_user_ids = self.search("res.users", [('name', '=', "sat")])
                    comercial_ids = self.search("res.users", [('name', 'ilike', record[7])], context=context)

                    vals = {
                        'number': str(int(record[0])),
                        'date': record[1],
                        'priority': record[2] and str(int(record[2])) or False,
                        'date_received': record[3] or False,
                        'user_id': user_ids and user_ids[0] or sat_user_ids[0],
                        'partner_id': partner_ids and partner_ids[0] or False,
                        'delivery_address_id': partner_ids and partner_ids[0] or False,
                        'invoice_type': record[6],
                        'comercial': comercial_ids and comercial_ids[0] or False,
                        'description': record[8],
                        'name': record[12],
                        'claim_type': 'customer',
                        'stage_id': self.search("crm.claim.stage", [('name', "=", record[14])], context=context)[0]
                    }
                    rma_id = self.create("crm.claim", vals)
                    rma_ids = [rma_id]

                if last_number == str(int(record[0])):
                    if record[10] or record[11] or record[13]:
                        substate_ids = self.search("substate.substate", [('name', '=', record[15])], context=context)
                        if record[10]:
                            product_ids = self.search("product.product", [('default_code', '=', record[10])])
                        else:
                            product_ids = []
                        line_vals = {
                            'substate_id': substate_ids and substate_ids[0] or False,
                            'claim_id': rma_ids[0],
                            'internal_description': record[13],
                            'name': record[11],
                            'product_id': product_ids and product_ids[0] or False
                        }
                        self.create("claim.line", line_vals)


                print "%s de %s" % (cont, all_lines)
                cont += 1
            except Exception, e:
                print "EXCEPTION: REC: ",record, e

        return True


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print u"Uso: %s <dbname> <user> <password> <rma_orders.csv>" % sys.argv[0]
    else:
        import_rma_order(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
