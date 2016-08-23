#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import xmlrpclib
import socket
import traceback
import xlrd
import datetime

class import_sale_order_lines(object):
    def __init__(self, dbname, user, passwd, customers_file):
        """método incial"""

        try:
            self.url_template = "http://%s:%s/xmlrpc/%s"
            self.server = "localhost"
            self.port = 9069
            self.dbname = dbname
            self.user_name = user
            self.user_passwd = passwd
            self.customers_file = customers_file

            #
            # Conectamos con OpenERP
            #
            login_facade = xmlrpclib.ServerProxy(self.url_template % (self.server, self.port, 'common'))
            self.user_id = login_facade.login(self.dbname, self.user_name, self.user_passwd)
            self.object_facade = xmlrpclib.ServerProxy(self.url_template % (self.server, self.port, 'object'))

            res = self.import_lines()
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


    def import_lines(self):
        cwb = xlrd.open_workbook(self.customers_file, encoding_override="utf-8")
        sh = cwb.sheet_by_index(0)
        visited_orders = []
        cont = 1
        all_lines = sh.nrows - 1
        print "lines no: ", all_lines
        import pdb; pdb.set_trace()
        for rownum in range(1, all_lines):
            record = sh.row_values(rownum)
            try:
                product_ids = self.search("product.product", [('default_code', '=', record[0])])
                print "ORDER: ", str(record[6]).strip()
                order_ids = self.search("sale.order", [('name', '=', str(record[6]).strip())])
                if order_ids:
                    tax_id = self.search("account.tax", [("name", "=", record[7]),('company_id', '=', 1)])
                    if order_ids[0] not in visited_orders:
                        visited_orders.append(order_ids[0])
                        lines_ids = self.search('sale.order.line', [('order_id','=',order_ids[0])])
                        if lines_ids:
                            self.write("sale.order.line", lines_ids, {'state': 'draft'})
                            for line_id in lines_ids:
                                try:
                                    self.unlink("sale.order.line", line_id) 
                                except Exception, e:
                                    print "Exception: ", e
                    lines_vals = {
                        "product_id": product_ids and product_ids[0] or False,
                        "name": record[1],
                        "product_uom_qty": record[2] and float(record[2]) or 0.0,
                        "product_uom": 1,
                        "price_unit": record[4] and float(record[4]) or 0.0,
                        "discount": record[5] and float(record[5]) or 0.0,
                        "order_id": order_ids[0],
                        "tax_id": [(6,0,tax_id)],}           

                    if len(record) > 8 and record[8] and record[9]:
                        lines_vals.update({
                        'deposit': record[8],
                        'deposit_date': datetime.
                            datetime(*xlrd.xldate_as_tuple(record[9],
                                                           cwb.datemode)).
                            strftime("%Y-%m-%d")})
                    self.create("sale.order.line", lines_vals)

                print "%s de %s" % (cont, all_lines)
                cont += 1
            except Exception, e:
                print "EXCEPTION: REC: ",record, e

        return True


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print u"Uso: %s <dbname> <user> <password> <sale_line_ids.xls>" % sys.argv[0]
    else:
        import_sale_order_lines(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
