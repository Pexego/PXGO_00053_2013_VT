#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import xmlrpclib
import socket

from datetime import datetime
from dateutil.relativedelta import MO, SU, relativedelta
import xlwt


class weekly_stock_report(object):
    def __init__(self, dbname, user, passwd, start_date, end_date,
                 name_file_dest):
        """método incial"""

        try:
            self.url_template = "http://%s:%s/xmlrpc/%s"
            self.server = "localhost"
            self.port = 9069
            self.dbname = dbname
            self.user_name = user
            self.user_passwd = passwd
            self.start_date = start_date
            self.end_date = end_date
            self.name_file_dest = name_file_dest
            if '.xls' not in name_file_dest:
                raise Exception(u'El nombre del fichero destino tiene que '
                                u'terminar en .xls')

            #
            # Conectamos con OpenERP
            #
            login_facade = xmlrpclib.\
                ServerProxy(self.url_template %
                            (self.server, self.port, 'common'))
            self.user_id = login_facade.login(self.dbname, self.user_name,
                                              self.user_passwd)
            self.object_facade = xmlrpclib.\
                ServerProxy(self.url_template % (self.server, self.port,
                                                 'object'))

            res = self.create_stock_report()
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

    def read_group(self, model, domain, fields, groupby, offset=0, limit=False,
                   context={}, orderby=False, lazy=True):
        """
        Wrapper del metodo read_group.
        """
        try:
            res = self.object_facade.\
                execute(self.dbname, self.user_id, self.user_passwd,
                        model, 'read_group', domain, fields, groupby, offset,
                        limit, context, orderby, lazy)
            return res
        except socket.error, err:
                raise Exception(u'Conexion rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
                raise Exception(u'Error %s en read_group: %s' %
                                (err.faultCode, err.faultString))

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
                    raise Exception(u'Error %s en unlink: %s' %
                                    (err.faultCode, err.faultString))

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
                raise Exception('Error %s en default_get: %s' %
                                (err.faultCode, err.faultString))

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
            self.object_facade.exec_workflow(self.dbname, self.user_id,
                                             self.user_passwd, model, signal,
                                             ids)
            #return res
        except socket.error, err:
            raise Exception(u'Conexión rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception(u'Error %s en exec_workflow: %s' %
                            (err.faultCode, err.faultString))

    def create_stock_report(self):
        start_date = datetime.strptime(self.start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(self.end_date, "%Y-%m-%d").date()
        next_sunday = start_date+relativedelta(weekday=SU)
        products = self.search("product.product", [('type', '=', 'product')])
        products_len = len(products)
        wb = xlwt.Workbook()

        while (next_sunday <= end_date):
            ws = wb.add_sheet(start_date.strftime("%d%m%Y") + " - " +
                              next_sunday.strftime("%d%m%Y"))
            print "NEW SHEET: ", start_date.strftime("%d/%m/%Y") + " - " + \
                next_sunday.strftime("%d/%m/%Y")
            line = 0
            ws.write(line, 0, "Producto")
            ws.write(line, 1, "Uds.")
            ws.write(line, 2, "Zona")
            ws.write(line, 3, "Fecha entrada")
            prod = 0
            for product_id in products:
                prod += 1
                product_data = self.read("product.product", [product_id],
                                         ['default_code'])[0]
                product_stock_data = self.\
                    read_group("stock.history",
                               [('product_id', '=', product_id),
                                ('location_id.usage', '=', 'internal'),
                                ('date', '<=',
                                 next_sunday.strftime("%Y-%m-%d 23:23:59"))],
                               ['location_id', 'quantity'], ['location_id'])
                for data in product_stock_data:
                    if data['quantity']:
                        line += 1
                        move_ids = self.\
                            search("stock.move",
                                   [('product_id', '=', product_id),
                                    ('location_dest_id', '=',
                                     data['location_id'][0]),
                                    ('date', '<=',
                                     next_sunday.strftime("%Y-%m-%d"))],
                                   limit=1, order="date desc")
                        in_date = self.read('stock.move', move_ids,
                                            ['date'])[0]['date'][:11]
                        ws.write(line, 0, product_data['default_code'])
                        ws.write(line, 1, data['quantity'])
                        ws.write(line, 2, data['location_id'][1])
                        ws.write(line, 3, in_date)
                print "Prod %s de %s" % (prod, products_len)

            start_date = next_sunday+relativedelta(weekday=MO)
            next_sunday = start_date+relativedelta(weekday=SU)
        wb.save(self.name_file_dest)

        return True

if __name__ == "__main__":
    if len(sys.argv) < 6:
        print """Uso: %s <dbname> <user> <password> <date_start (AAAA-MM-DD)>
 <date_end (AAAA-MM-DD)> <name_file_dest.xls>""" % sys.argv[0]
    else:
        weekly_stock_report(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4],
                            sys.argv[5], sys.argv[6])
