# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2007-TODAY ASPerience SARL (<http://www.asperience.fr>).
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import fields, models, _, api, exceptions, tools
from odoo.tools import ustr
from odoo import sql_db
from datetime import datetime
import os
import csv
import re
import codecs
from io import StringIO
import shutil
from ftplib import FTP
import threading
import logging
from lxml import etree

_logger = logging.getLogger(__name__)
try:
    asperience_log = tools.asperience_log
except:
    _logger_deco = logging.getLogger(__name__)

    def asperience_log(f):
        def called(*args, **kargs):
            try:
                msg = str(args[0].__class__.__name__)+"."+str(f.__name__)+"("+str([i for i in args if not isinstance(i,dict)][3:])+")"
            except:
                try:
                    msg = str(args[0].__class__.__name__)+"."+str(f.__name__)+"("+str(args)+")"
                except:
                    msg = str(f)
            _logger_deco.info("=={{STARTING}}== %s" % (msg))
            date_start = datetime.now()
            res = f(*args, **kargs)
            delay = datetime.now() - date_start
            _logger_deco.info("=={{STOPPING}}== %s : %s" % (msg, str(delay)))
            return res
        return called

def dict2xml(root,level=0):
    level_xml = '\t'*level
    xml = ""
    for key in sorted(root.keys()):
        if isinstance(root[key], dict):
            xml = '%s%s<%s>\n%s%s</%s>\n' % (xml, level_xml, key, dict2xml(root[key],level+1), level_xml, key)
        elif isinstance(root[key], list):
            xml = '%s%s<%s>\n' % (xml, level_xml, key)
            for item in root[key]:
                xml = '%s%s' % (xml, dict2xml(item,level+1))
            xml = '%s%s</%s>\n' % (xml, level_xml, key)
        else:
            value = root[key]
            xml = '%s%s<%s>%s</%s>\n' % (xml, level_xml, key, value, key)
    return xml

def xml2dict(tree,level=0):
    res = {}
    res[tree.tag] = {}

    tmp = {}
    for i in tree.getchildren():
        if not i.tag in tmp:
            tmp[i.tag] = 0
        tmp[i.tag] += 1

    if len(tree.getchildren()) == 0:
        if not tree.attrib:
            res[tree.tag] = tree.text
        else:
            res[tree.tag]['data'] = tree.text
    else:
        for i in tree.getchildren():
            if tmp[i.tag] == 1:
                res[tree.tag].update(xml2dict(i))
            else:
                if not "childs" in res[tree.tag]:
                    res[tree.tag]["childs"] = []
                res[tree.tag]["childs"].append(xml2dict(i))

    if tree.attrib:
        for i in tree.attrib:
            if i not in res[tree.tag]:
                res[tree.tag][i] = tree.attrib[i]
            else:
                if 'attrs' not in res[tree.tag]:
                    res[tree.tag]['attrs'] = {}
                res[tree.tag]['attrs'][i] = tree.attrib[i]
    return res

def unicode_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):
    csv_reader = csv.reader(utf_8_encoder(unicode_csv_data), dialect=dialect, **kwargs)
    for row in csv_reader:
        yield [unicode(cell, 'utf-8') for cell in row]

class UnicodeWriter:
    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        self.queue = StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        row2 = []
        for s in row:
            if isinstance(s,unicode):
                s2 = s
                for i in s :
                    if ord(i) > 255 :
                        s2 = s2.replace(i,'')
                row2.append(s2.encode("utf-8"))
            else:
                row2.append(s)
        self.writer.writerow(row2)
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        data = self.encoder.encode(data)
        self.stream.write(data)
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

def utf_8_encoder(unicode_csv_data):
    for line in unicode_csv_data:
        yield line.encode('utf-8')

def stripnulls(data, parameters, type, cast):
    if type == 'float':
        data = data.replace(".",parameters['separator'])
    data = data.replace("\00", "").strip()
    while len(data) and data[-1] == ' ':
        data=data[:-2]
    if type == 'float':
        data = float(data)
    elif type == 'int':
        data = int(data)

    return data

def fillleft(data, parameters, length, type, cast):
    data = ustr(data)
    if type == 'float':
        data = data.replace(".",parameters['separator'])
    length+=1
    if len(data)>length :
        data=data[:length]
    while len(data)<length:
        data=" "+data
    return data

def fillright(data, parameters, length, type, cast):
    data = ustr(data)
    if type == 'float':
        data = data.replace(".",parameters['separator'])
    length+=1
    if len(data)>length :
        data=data[:length]
    while len(data)<length:
        data=data+" "
    return data

def fillzero(data, parameters, length, type, cast):
    length+=1
    if type == 'float':
        before = re.compile('\(\d+\,').findall(cast)
        after = re.compile('\,\d+\)').findall(cast)
        if before and len(before) == 1 and len(before[0]) > 2 and after and len(after) == 1 and len(after[0]) > 2:
            before = before[0][1:-1]
            after = after[0][1:-1]
            caststr = '%'+before+'.'+after+'f'
            data = caststr % data
            data = data.replace('.',parameters['separator'])
            data = data.replace(' ',"0")

    if len(ustr(data))>length :
        data=ustr(data)[:length]
    while len(ustr(data))<length:
        data="0"+str(data)
    return data

class edi_edi (models.Model):
    _name = 'edi.edi'
    _description = 'edi.edi'

    @api.multi
    def _length(self):
        for edi in self:
            if edi.stop_identifier <= 0  and edi.start_identifier <= 0:
                edi.length_identifier = 0
            else:
                edi.length_identifier = edi.stop_identifier - edi.start_identifier + 1

    name = fields.Char('Name', size=128, required=True)
    code = fields.Char('Code', size=128, required=True)
    start_identifier = fields.Integer('Start identifier', required=True, default=0)
    stop_identifier = fields.Integer('Stop identifier', required=True, default=0)
    length_identifier = fields.Integer(compute="_length", string='Length identifier')
    log_ids = fields.One2many('edi.edi.log', 'edi', 'Log')
    result_ids = fields.One2many('edi.edi.result', 'edi', 'Result')
    file_template = fields.Char('Template File (Regular Expression)', size=128, default=".*")
    type = fields.Selection([('edi','edi'),('csv','csv'),('xml','xml'),('csv_struct','csv structured')], 'Type', required=True, size=24)
    thread = fields.Boolean('Progress',readonly=True)

    charset = fields.Selection([('UTF-8','UTF-8'),('ISO-8859-1','ISO-8859-1'),('ISO-8859-2','ISO-8859-2'),], 'Charset', required=True, size=24, default="UTF-8")
    end_line = fields.Selection([('simple','Unix/Linux'),('win','Windows')], 'End line', required=True, size=24, default="simple")
    float_separator = fields.Selection([(',',','),('.','.')], 'Float Separator', required=True, size=5, default=".")
    delimiter = fields.Char('Delimiter', size=1, required=True, default=';')
    quotechar = fields.Char('Quotechar', size=1, default="\"")

    force = fields.Boolean('Force')
    no_empty_file = fields.Boolean('No Empty File', default=True)
    header_xml = fields.Char('Header XML', size=256,)

    skip_first = fields.Boolean('Skip the First')
    line_start = fields.Integer('Start line', required=True, default=-1)
    line_stop = fields.Integer('Stop line', required=True, default=-1)

    eval_in = fields.Text('IN')
    eval_out = fields.Text('OUT')
    path_in = fields.Char('Path In', size=128, default='./addons/asperience_edi/data_import/')
    path_in_move = fields.Char('Path In Move', size=128,)
    path_out = fields.Char('Path Out', size=128, default='./addons/asperience_edi/data_export/')

    line_edi_ids = fields.One2many('edi.edi.line.edi', 'edi', 'Line Edi')
    fields_ids = fields.One2many('edi.edi.csv.field', 'edi', 'Fields')
    fields_xml_ids = fields.One2many('edi.edi.xml.field', 'edi', 'Fields')
    line_csv_ids = fields.One2many('edi.edi.line.csv', 'edi', 'Line Structured CSV')

    copy_in = fields.Boolean('Copy before import')
    ftp_path_in = fields.Char('Path In', size=128,)
    ftp_url_in = fields.Char('Url In', size=128)
    ftp_port_in = fields.Integer('port In')
    ftp_login_in = fields.Char('Login In', size=128)
    ftp_password_in = fields.Char('password', size=128)
    ftp_path_in_archive = fields.Char('Path In Archive', size=128,)

    copy_out = fields.Boolean('Copy after export')
    ftp_path_out = fields.Char('Path Out', size=128,)
    ftp_url_out = fields.Char('Url Out', size=128)
    ftp_port_out = fields.Integer('port Out')
    ftp_login_out = fields.Char('Login Out', size=128)
    ftp_password_out = fields.Char('Password Out', size=128)

    def copy(self, cr, uid, id, default={}, context={}):
        default.update( {'log_ids':[],'result_ids':[]})
        return super(edi_edi, self).copy(cr, uid, id, default, context)

    def _create_struct_edi(self, cr, uid, ids, context=False):
        result = {}
        for edi in self.browse(cr,uid,ids,context):
            result[edi.id] = {}
            if edi.end_line == 'win':
                end_line = '\r\n'
            else:
                end_line = '\n'
            result[edi.id]["<<>>"] = {
                    'start':edi.start_identifier,
                    'stop':edi.stop_identifier,
                    'separator':edi.float_separator,
                    'charset':edi.charset,
                    'end_line': end_line,
            }

            for line in edi.line_edi_ids:
                result[edi.id][str(line.name)] = {}

                for field in line.fields_ids:
                    result[edi.id][str(line.name)][str(field.name)] = {
                        'start':field.start,
                        'stop':field.stop,
                        'align': field.align,
                        'type': field.type,
                        'cast':field.cast,
                    }
        return result

    def _create_struct_csv(self, cr, uid, ids, context=False):
        result = {}
        for edi in self.browse(cr,uid,ids,context):
            result[edi.id] = {}
            if edi.end_line == 'win':
                end_line = '\r\n'
            else:
                end_line = '\n'
            result[edi.id]["<<>>"] = {
                    'separator':edi.float_separator,
                    'charset':edi.charset,
                    'end_line':end_line,
            }

            for field in edi.fields_ids:
                result[edi.id][field.sequence-1] = {
                        'name': str(field.name),
                        'type': field.type,
                        'cast': field.cast,
                        'description': field.description,
                }
        return result

    def _create_struct_csv_struct(self, cr, uid, ids, context=False):
        result = {}
        for edi in self.browse(cr,uid,ids,context):
            result[edi.id] = {}
            if edi.end_line == 'win':
                end_line = '\r\n'
            else:
                end_line = '\n'

            result[edi.id]["<<>>"] = {
                    'start':edi.start_identifier,
                    'stop':edi.stop_identifier,
                    'separator':edi.float_separator,
                    'charset':edi.charset,
                    'end_line':end_line,
            }
            for line in edi.line_csv_ids:
                result[edi.id][str(line.name)] = {}
                for field in line.fields_ids:
                    result[edi.id][str(line.name)][field.sequence-1] = {
                        'name': str(field.name),
                        'type': field.type,
                        'cast': field.cast,
                        'sequence': field.sequence - 1
                    }
        return result

    def _create_attachment(self, cr, uid, ids, file_path, context=False):
        edi = self.browse(cr,uid,ids,context)[0]
        data_attach = {
            'name': os.path.basename(file_path),
            'datas':open(file_path, "rb").read().encode("base64"),
            'datas_fname': os.path.basename(file_path),
            'description': 'export',
            'res_model': 'edi.edi',
            'res_id': edi.id
        }
        cc = 0
        while self.pool.get('ir.attachment').search(cr,uid,[('res_model','=',data_attach['res_model']),('name','=',data_attach['name']),('datas_fname','=',data_attach['datas_fname'])]):
            data_attach['name'] = os.path.basename(file_path) + "(%s)" % (cc,)
            data_attach['datas_fname'] = os.path.basename(file_path) + "(%s)" % (cc,)
            cc+=1
        self.pool.get('ir.attachment').create(cr,uid, data_attach)

    def _create_files(self, cr, uid, ids, data, context=False):
        edi = self.browse(cr,uid,ids,context)[0]
        for filename in data:
            file = codecs.open(context['path_out']+filename,"w",edi.charset)
            for line in data[filename]:
                file.write(line)
            file.close()
            edi._create_attachment(file_path=context['path_out']+filename,context=context)
            if edi.copy_out:
                _logger.debug("Export: %s " % (filename))
                ftp = FTP(edi.ftp_url_out,edi.ftp_login_out,edi.ftp_password_out)
                file = codecs.open(str(context['path_out'])+str(filename),"r",edi.charset)
                ftp_filename = str(edi.ftp_path_out)+str(filename)
                _logger.debug("FTP: %s " % (ftp_filename))
                ftp.cwd(edi.ftp_path_out)
                ftp.storbinary('STOR '+ftp_filename, file)

                file.close()
                ftp_size = ftp.size(ftp_filename)
                _logger.debug("FTP Size: %s " % (ftp_size))
                if not ftp_size:
                    raise Exception(_('FTP export failed'))

                ftp.quit()
        return {}

    def _create_files_csv(self, cr, uid, ids, data, context=False):
        edi = self.browse(cr,uid,ids,context)[0]
        for filename in data:
            if not data[filename] or (edi.skip_first and len(data[filename]) <= 1):
                data[filename] = ""
                if edi.no_empty_file:
                    continue
#            file = codecs.open(context['path_out']+filename,"w",edi.charset)
            file = open(context['path_out']+filename,"wb")
            if edi.quotechar:
                csv_writer = UnicodeWriter(file, encoding=edi.charset, delimiter=str(edi.delimiter[0]), quotechar=str(edi.quotechar), quoting=csv.QUOTE_NONNUMERIC)
            else:
                csv_writer = UnicodeWriter(file, encoding=edi.charset, delimiter=str(edi.delimiter[0]))
            if edi.charset == 'UTF-8':
                file.write("\xEF\xBB\xBF")
            first = True
            for line in data[filename]:
                if first and edi.skip_first:
                    first = False
                else:
                    csv_writer.writerow(line)
            file.close()
            edi._create_attachment(file_path=context['path_out']+filename,context=context)
            if edi.copy_out:
                _logger.debug("Export: %s " % (filename))
                ftp = FTP(edi.ftp_url_out,edi.ftp_login_out,edi.ftp_password_out)
                #file = codecs.open(str(context['path_out'])+str(filename),"rb",edi.charset)
                file = open(context['path_out']+filename,"rb")
                ftp_filename = str(edi.ftp_path_out)+str(filename)
                _logger.debug("FTP: %s " % (ftp_filename))
                ftp.cwd(edi.ftp_path_out)
                ftp.storbinary('STOR '+ftp_filename, file)

                file.close()
                ftp_size = ftp.size(ftp_filename)
                _logger.debug("FTP Size: %s " % (ftp_size))
                if not ftp_size:
                    raise Exception(_('FTP export failed'))

                ftp.quit()
        return {}

    def _create_files_xml(self, cr, uid, ids, data, context=False):
        edi = self.browse(cr,uid,ids,context)[0]
        for filename in data:
            if not data[filename]:
                data[filename] = ""
                if edi.no_empty_file:
                    continue

#            file = codecs.open(context['path_out']+filename,"w",edi.charset)
            file = open(context['path_out']+filename,"wb")
            if edi.header_xml:
                file.write(edi.header_xml+"\n")
            if data[filename]:
                file.write(dict2xml(data[filename]))
            file.close()
            edi._create_attachment(file_path=context['path_out']+filename,context=context)
            if edi.copy_out:
                _logger.debug("Export: %s " % (filename))
                ftp = FTP(edi.ftp_url_out,edi.ftp_login_out,edi.ftp_password_out)
                #file = codecs.open(context['path_out']+filename,"r",edi.charset)
                file = open(context['path_out']+filename,"rb")
                ftp_filename = str(edi.ftp_path_out)+str(filename)
                _logger.debug("FTP: %s " % (ftp_filename))
                ftp.storbinary('STOR '+ftp_filename, file)
                file.close()
                ftp_size = ftp.size(ftp_filename)
                _logger.debug("FTP Size: %s " % (ftp_size))
                if not ftp_size:
                    raise Exception(_('FTP export failed'))

                ftp.quit()
        return {}

    def _get_files(self, cr, uid, ids, path, template=False, context=False):
        edi = self.browse(cr,uid,ids,context)[0]
        _logger.info("_get_files : %s, pattern : %s" % (path,template))
        result = []
        if edi.copy_in:
            ftp = FTP(edi.ftp_url_in,edi.ftp_login_in,edi.ftp_password_in)
            ftp.cwd(edi.ftp_path_in)
            list = ftp.nlst()
            if '.' in list:
                list.remove('.')
            if '..' in list:
                list.remove('..')
            for file_name in list:
                if not os.path.exists(path+file_name):
                    _logger.debug("RETR : %s, DEST : %s" % (file_name,path+file_name))
                    ftp.retrbinary('RETR '+file_name, open(path+file_name, 'wb').write)
            try:
                ftp.cwd(edi.ftp_path_in_archive)
            except:
                ftp.mkd(edi.ftp_path_in_archive)
            ftp.cwd(edi.ftp_path_in)
            for file_name in list:
                _logger.debug("File name: %s " % (file_name))
                try:
                    size = ftp.size(edi.ftp_path_in+file_name)
                    _logger.debug("File size: %s " % (size))
                    tmp = ftp.sendcmd('RNFR '+edi.ftp_path_in+file_name)
                    _logger.debug(tmp)
                    tmp = ftp.sendcmd('RNTO '+edi.ftp_path_in_archive+file_name)
                    _logger.debug(tmp)
                except Exception as e:
                    pass

            ftp.quit()
        template_cpled = re.compile(template)
        for i in os.listdir(path):
            if os.path.isfile(path+i) and i[0]!='.':
                if template_cpled and not template_cpled.search(i):
                    _logger.debug("File : %s : Not Match" % (i))
                    continue
                _logger.info("File : %s : Match" % (i))
                result.append(path+i)
        return result

    def _create_header_csv(self, cr, uid, ids, struct, context=False):
        result = []
        for field in struct:
            if field == '<<>>':
                continue
            if struct[field]['description'] :
                result.append(struct[field]['description'])
            else :
                result.append("")
        return result

    def _create_line_csv(self, cr, uid, ids, line, struct, context=False):
        result = []
        for field in struct:
            if field == '<<>>':
                continue
            if struct[field]['name'] in line :
                data = line[struct[field]['name']]
                if struct[field]['type'] == 'float':
                    data = ustr(data).replace(".",struct['<<>>']['separator'])
                result.append(data)

        return result

    def _create_line(self, cr, uid, ids, line, type, structs, context=False):
        struct = structs[type]
        max = 0
        for field in struct:
            if struct[field]['stop'] > max :
                max = struct[field]['stop']
        outline = type+" "*(max-(len(type))) + structs['<<>>']['end_line']
        for field in struct:
            start = struct[field]['start']
            stop = struct[field]['stop']
            writeFunc = fillright
            if struct[field]['align'] == 'right':
                writeFunc = fillright
            elif struct[field]['align'] == 'left':
                writeFunc = fillleft
            elif struct[field]['align'] == 'zero':
                writeFunc = fillzero
            str_field = writeFunc(line[field], structs['<<>>'], stop-start, struct[field]['type'], struct[field]['cast'])
            outline = outline[0:start-1]+str_field+outline[stop:]
        return outline

    def _parse_line_edi(self, cr, uid, ids, line, structs, context=False):
        result = {}
        start_identifier = structs['<<>>']['start']-1
        stop_identifier = structs['<<>>']['stop']
        identifier = line[start_identifier:stop_identifier]

        if identifier not in structs:
            raise Exception(_('%s not found in EDI structure') % (identifier,))
        struct = structs[identifier]

        for field in struct:
            start = struct[field]['start']
            stop = struct[field]['stop']
            parseFunc = stripnulls
            result[field] = parseFunc(line[start-1:stop],structs['<<>>'], struct[field]['type'], struct[field]['cast'])

        return identifier,result

    def _parse_line_csv(self, cr, uid, ids, line, structs, context=False):
        result = {}
        for key in structs:
            if len(line) > key:
                result[structs[key]['name']] = line[key].strip()
        return result

    def _parse_line_csv_struct(self, cr, uid, ids, line, structs, context=False):
        result = {}
        if structs['<<>>']['stop']:
            start_identifier = structs['<<>>']['start']-1
            stop_identifier = structs['<<>>']['stop']
            identifier = line[0][start_identifier:stop_identifier]
        else:
            identifier = line[0]
        if identifier not in structs:
            raise Exception(_('%s not found in CSV structured structure') % (identifier,))
        struct = structs[identifier]

        #First data = identifier
        for field in struct:
            parseFunc = stripnulls
            if len(line) > struct[field]['sequence']:
                result[struct[field]['name']] = parseFunc(line[struct[field]['sequence']],structs['<<>>'], struct[field]['type'], struct[field]['cast'])
            else:
                result[struct[field]['name']] = False

        return identifier,result

    def _search_warning(self, cr, uid, ids, model, filter, type='raise',context={}):
        model_obj = self.pool.get(model)
        obj_ids = model_obj.search(cr,uid,filter)
        if len(obj_ids) != 1:
            if len(obj_ids) == 0:
                if type == 'log':
                    _logger.info(_('%s Not Found with filter %s') % (model,filter))
                elif type == 'raise':
                    raise Exception(_('%s Not Found with filter %s') % (model,filter))
                else:
                    print('{} Not Found with filter {}').format(model, filter)
            else:
                if type == 'log':
                    _logger.info(_('Many %s with filter %s') % (model,filter))
                elif type == 'raise':
                    raise Exception(_('Many %s with filter %s') % (model,filter))
                else:
                    print('Many {} with filter {}').format(model, filter)
        else:
            obj_ids = obj_ids[0]
        return obj_ids

    @asperience_log
    def import_edi_thread(self, cr, uid, ids, context=False):
        _logger.debug('IMPORT EDI THREAD %s' % (ids))
        cr2 = sql_db.db_connect(self.env.cr.dbname).cursor()
        thread_ptr = threading.Thread(target=self.import_edi, args=(cr2, uid, ids, context))
        thread_ptr.start()
        return {}

    @asperience_log
    def import_edi(self, cr, uid, ids, context=False):
        _logger.debug('IMPORT EDI %s' % (ids))
        thread = False
        if "thread" in context:
            thread = context["thread"]
        cr2 = sql_db.db_connect(self.env.cr.dbname).cursor()
        cr2.autocommit(True)
        exception = False
        if not ids :
            if 'edi.code' in context:
                ids = self.search(cr,uid,[('code','=',context['edi.code'])])
            else:
                return False
        exception = False
        for edi in self.browse(cr,uid,ids,context):
            self.write(cr2,uid,[edi.id],{'thread':True})
            filename = False
            cr2.commit()
            try:
                structs = edi._create_struct_edi()[edi.id]
                if not edi.eval_in:
                    continue
                data = {}
                for filename in edi._get_files(edi.path_in, edi.file_template):
                    _logger.info("Import file : %s" % (filename))
                    result = ""
                    context['edi'] = edi.id
                    context['type'] = 'import'
                    context['filename'] = filename
                    try:
                        file = codecs.open(filename,'r',edi.charset)
                        data[filename] = []
                        for line in file:
                            data[filename].append(edi._parse_line_edi(line,structs))
                        file.close()
                        edi.eval_in = edi.eval_in.replace(chr(13),"\n")
                        _logger.debug("IMPORT EDI EVAL %s" % (edi.id))
                        exec(edi.eval_in)
                        _logger.debug("IMPORT EDI EVAL %s" % (edi.id))
                    except Exception as e:
                        if not os.path.exists (edi.path_in+"error/"):
                            os.makedirs(edi.path_in+"error/")
                        shutil.move(edi.path_in+os.path.basename(filename), edi.path_in+"error/"+os.path.basename(filename))
                        raise e
                    if edi.path_in_move:
                        if not os.path.exists (edi.path_in_move):
                            os.makedirs(edi.path_in_move)
                        shutil.move(edi.path_in+os.path.basename(filename), edi.path_in_move+os.path.basename(filename))
                    _logger.info("End Import file : %s" % (filename))
                    self.pool.get('edi.edi.result').create(cr,uid,{"name":"file_import_edi_ok","value":filename,"edi":edi.id})
                    if result:
                        self.pool.get('edi.edi.result').create(cr,uid,{"name":"result_import_edi_ok","value":result,"edi":edi.id})
            except Exception as e:
                import sys,traceback
                tb = sys.exc_info()
                tb_s = "".join(traceback.format_exception(*tb))
                info = tb_s
                try:
                    info += "\n"+ustr(e.value)
                except:
                    pass
                _logger.info("Except : %s" % (info))
                cr.rollback()
                if filename:
                    self.pool.get('edi.edi.result').create(cr,uid,{"name":"file_import_edi_nok","value":filename,"edi":edi.id})
                if info:
                    self.pool.get('edi.edi.result').create(cr,uid,{"name":"info_import_edi_nok","value":info,"edi":edi.id})
                cr.commit()
                exception = True
        if not exception:
            cr.commit()
        for i in ids :
            cr2.execute("update edi_edi set thread = False where id = %s" % i)
        if thread :
            cr.close()
        cr2.close()
        if not thread and exception:
            raise Exception(info)
        return True

    @asperience_log
    def export_edi_thread(self, cr, uid, ids, context=False):
        _logger.debug("EXPORT EDI THREAD %s" % (ids))
        cr2 = sql_db.db_connect(self.env.cr.dbname).cursor()
        thread_ptr = threading.Thread(target=self.export_edi, args=(cr2, uid, ids, context))
        thread_ptr.start()
        return {}

    @asperience_log
    def export_edi(self, cr, uid, ids, context=False):
        _logger.debug("EXPORT EDI %s" % (ids))
        thread = False
        if "thread" in context:
            thread = context["thread"]
        cr2 = sql_db.db_connect(self.env.cr.dbname).cursor()
        cr2.autocommit(True)
        exception = False
        if not ids :
            if 'edi.code' in context:
                ids = self.search(cr,uid,[('code','=',context['edi.code'])])
            else:
                return False

        for edi in self.browse(cr,uid,ids,context):
            self.write(cr2,uid,[edi.id],{'thread':True})
            cr2.commit()
            result = ""
            context['edi'] = edi.id
            context['type'] = 'export'
            try :
                structs = edi._create_struct_edi()[edi.id]
                if not edi.eval_out:
                    continue
                data = {}
                eval_out = edi.eval_out.replace(chr(13),"\n")
                _logger.debug("EXPORT EDI EVAL %s" % (edi.id))
                exec(eval_out)
                _logger.debug("EXPORT EDI EVAL END %s" % (edi.id))
                context['path_out'] = edi.path_out
                edi._create_files(data,context=context)
                if result:
                    self.pool.get('edi.edi.result').create(cr,uid,{"name":"result_export_edi_ok","value":result,"edi":edi.id})
            except Exception as e:
                import sys,traceback
                tb = sys.exc_info()
                tb_s = "".join(traceback.format_exception(*tb))
                info = tb_s
                _logger.info("Except : %s" % (info))
                cr.rollback()
                if info:
                    self.pool.get('edi.edi.result').create(cr,uid,{"name":"info_export_edi_nok","value":info,"edi":edi.id})
                cr.commit()
                exception = True
        if not exception:
            cr.commit()
        for i in ids :
            cr2.execute("update edi_edi set thread = False where id = %s" % i)
        if thread :
            cr.close()
        cr2.close()
        return True

    @asperience_log
    def import_csv_thread(self, cr, uid, ids, context=False):
        _logger.debug("IMPORT CSV THREAD %s" % (ids))
        cr2 = sql_db.db_connect(self.env.cr.dbname).cursor()
        thread_ptr = threading.Thread(target=self.import_csv, args=(cr2, uid, ids, context))
        thread_ptr.start()
        return {}

    @asperience_log
    def import_csv(self, cr, uid, ids, context=False):
        _logger.debug("IMPORT CSV %s" % (ids))
        thread = False
        if "thread" in context:
            thread = context["thread"]
        cr2 = sql_db.db_connect(self.env.cr.dbname).cursor()
        cr2.autocommit(True)
        exception = False
        if not ids :
            if 'edi.code' in context:
                ids = self.search(cr,uid,[('code','=',context['edi.code'])])
            else:
                return False
        for edi in self.browse(cr,uid,ids,context):
            self.write(cr2,uid,[edi.id],{'thread':True})
            filename = False
            try :
                structs = edi._create_struct_csv()[edi.id]
                if not edi.eval_in:
                    continue
                edi.eval_in = edi.eval_in.replace(chr(13),"\n")
                data = {}
                gobreak = False
                for filename in edi._get_files(edi.path_in, edi.file_template):
                    _logger.info("Import file : %s" % (filename))
                    result = ""
                    context['edi'] = edi.id
                    context['type'] = 'import'
                    context['filename'] = filename
                    try:
                        file = codecs.open(filename,'rb',edi.charset)
                        file_csv = unicode_csv_reader(file, delimiter=str(edi.delimiter[0]), quotechar=str(edi.quotechar))
                        data[filename] = []
                        nb_line = 0
                        first = True
                        for line in file_csv:
                            nb_line+=1
                            _logger.info("Import line : %s" % (str(nb_line)))
                            if first and edi.skip_first:
                                nb_line = 0
                                first = False
                                continue
                            if edi.line_start > 0 and nb_line < edi.line_start:
                                continue
                            if edi.line_stop > 0 and nb_line > edi.line_stop:
                                break
                            data[filename].append(edi._parse_line_csv(line,structs))
                            vals_import = edi._parse_line_csv(line,structs)

                            _logger.debug("IMPORT CSV EVAL %s" % (ids))
                            exec(edi.eval_in)
                            _logger.debug("IMPORT CSV EVAL END %s" % (ids))
                            if gobreak :
                                break
                        file.close()
                    except Exception as e:
                        if not os.path.exists (edi.path_in+"error/"):
                            os.makedirs(edi.path_in+"error/")
                        shutil.move(edi.path_in+os.path.basename(filename), edi.path_in+"error/"+os.path.basename(filename))
                        raise e
                    if edi.path_in_move:
                        shutil.move(edi.path_in+os.path.basename(filename), edi.path_in_move+os.path.basename(filename))
                    _logger.info("End Import file : %s" % (filename))

                    self.pool.get('edi.edi.result').create(cr,uid,{"name":"file_import_csv_ok","value":filename,"edi":edi.id})
                    if result :
                        self.pool.get('edi.edi.result').create(cr,uid,{"name":"result_import_csv_ok","value":result,"edi":edi.id})
            except Exception as e:
                import sys,traceback
                tb = sys.exc_info()
                tb_s = "".join(traceback.format_exception(*tb))
                info = tb_s
                try:
                    info += "\n"+ustr(e.value)
                except:
                    pass
                _logger.info("Except : %s" % (info))
                cr.rollback()
                if filename:
                    self.pool.get('edi.edi.result').create(cr,uid,{"name":"file_import_csv_nok","value":filename,"edi":edi.id})
                if info:
                    self.pool.get('edi.edi.result').create(cr,uid,{"name":"info_import_csv_nok","value":info,"edi":edi.id})
                cr.commit()
                exception = True
        if not exception:
            cr.commit()
        for i in ids :
            cr2.execute("update edi_edi set thread = False where id = %s" % i)
        if thread :
            cr.close()
        cr2.close()
        if not thread and exception:
            raise Exception(info)
        return True

    @asperience_log
    def export_csv_thread(self, cr, uid, ids, context=False):
        _logger.debug("EXPORT CSV THREAD %s" % (ids))
        cr2 = sql_db.db_connect(self.env.cr.dbname).cursor()
        thread_ptr = threading.Thread(target=self.export_csv, args=(cr2, uid, ids, context))
        thread_ptr.start()
        return {}

    def export_csv(self, cr, uid, ids, context=False):
        _logger.debug("EXPORT CSV %s" % (ids))
        thread = False
        if not context:
            context = {}
        ctx = dict(context)
        if "thread" in ctx:
            thread = ctx["thread"]
        cr2 = sql_db.db_connect(self.env.cr.dbname).cursor()
        cr2.autocommit(True)
        exception = False
        if not ids :
            if 'edi.code' in ctx:
                ids = self.search(cr,uid,[('code','=',ctx['edi.code'])])
            else:
                return False

        for edi in self.browse(cr,uid,ids,ctx):
            self.write(cr2,uid,[edi.id],{'thread':True})
            result = ""
            cr2.commit()
            ctx['edi'] = edi.id
            ctx['type'] = 'export'
            try:
                structs = edi._create_struct_csv()[edi.id]
                if not edi.eval_out:
                    continue
                eval_out = edi.eval_out.replace(chr(13),"\n")
                data = {}
                _logger.debug("EXPORT CSV EVAL %s" % (ids))
                exec(eval_out)
                _logger.debug("EXPORT CSV EVAL END %s" % (ids))
                ctx['path_out'] = edi.path_out
                self._create_files_csv(cr, uid, [edi.id], data=data,context=ctx)
                if result:
                    self.pool.get('edi.edi.result').create(cr,uid,{"name":"result_export_csv_ok","value":result,"edi":edi.id})
            except:
                import sys,traceback
                tb = sys.exc_info()
                tb_s = "".join(traceback.format_exception(*tb))
                info = tb_s
                _logger.info("Except : %s" % (info))
                cr.rollback()
                if info:
                    self.pool.get('edi.edi.result').create(cr,uid,{"name":"info_export_csv_nok","value":info,"edi":edi.id})
                cr.commit()
                exception = True
        if not exception:
            cr.commit()
        for i in ids :
            cr2.execute("update edi_edi set thread = False where id = %s" % i)
        if thread :
            cr.close()
        cr2.close()
        return True

    def import_xml_thread(self, cr, uid, ids, context=False):
        _logger.debug("IMPORT XML THREAD %s" % (ids))
        cr2 = sql_db.db_connect(self.env.cr.dbname).cursor()
        thread_ptr = threading.Thread(target=self.import_xml, args=(cr2, uid, ids, context))
        thread_ptr.start()
        return {}

    def import_xml(self, cr, uid, ids, context=False):
        _logger.debug("IMPORT XML %s" % (ids))
        info = ""
        thread = False
        if "thread" in context:
            thread = context["thread"]
        cr2 = sql_db.db_connect(self.env.cr.dbname).cursor()
        cr2.autocommit(True)
        exception = False
        if not ids :
            if 'edi.code' in context:
                ids = self.search(cr,uid,[('code','=',context['edi.code'])])
            else:
                return False
        for edi in self.browse(cr,uid,ids,context):
            self.write(cr2,uid,[edi.id],{'thread':True})
            filename = False
            result = ""
            try :
#                structs = edi._create_struct_xml()[edi.id]
                if not edi.eval_in:
                    continue
                edi.eval_in = edi.eval_in.replace(chr(13),"\n")
                data = {}
                gobreak = False
                for filename in edi._get_files(edi.path_in, edi.file_template):
                    _logger.info("Import file : %s" % (filename))
                    result = ""
                    context['edi'] = edi.id
                    context['type'] = 'import'
                    context['filename'] = filename
                    try:
                        file = codecs.open(filename,'r',edi.charset)
                        file_dict = xml2dict(etree.parse(file).getroot())
                        file.close()
                        _logger.debug("IMPORT XML EVAL %s" % (ids))
                        exec(edi.eval_in)
                        _logger.debug("IMPORT XML EVAL END %s" % (ids))
                    except Exception as e:
                        if not os.path.exists (edi.path_in+"error/"):
                            os.makedirs(edi.path_in+"error/")
                        shutil.move(edi.path_in+os.path.basename(filename), edi.path_in+"error/"+os.path.basename(filename))
                        raise e
                    if edi.path_in_move:
                        shutil.move(edi.path_in+os.path.basename(filename), edi.path_in_move+os.path.basename(filename))
                    _logger.info("End Import file : %s" % (filename))
                    self.pool.get('edi.edi.result').create(cr,uid,{"name":"file_import_xml_ok","value":filename,"edi":edi.id})
                    if result :
                        self.pool.get('edi.edi.result').create(cr,uid,{"name":"result_import_xml_ok","value":result,"edi":edi.id})
            except Exception as e:
                import sys,traceback
                tb = sys.exc_info()
                tb_s = "".join(traceback.format_exception(*tb))
                info = tb_s
                try:
                    info += "\n"+ustr(e.value)
                except:
                    pass
                _logger.info("Except : %s" % (info))
                cr.rollback()
                if filename:
                    self.pool.get('edi.edi.result').create(cr,uid,{"name":"file_import_xml_nok","value":filename,"edi":edi.id})
                if info:
                    self.pool.get('edi.edi.result').create(cr,uid,{"name":"info_import_xml_nok","value":info,"edi":edi.id})
                cr.commit()
                exception = True
        if not exception:
            cr.commit()
        for i in ids :
            cr2.execute("update edi_edi set thread = False where id = %s" % i)
        if thread :
            cr.close()
        cr2.close()
        if not thread and exception:
            raise Exception(info)
        return True

    @asperience_log
    def export_xml_thread(self, cr, uid, ids, context=False):
        cr2 = sql_db.db_connect(self.env.cr.dbname).cursor()
        thread_ptr = threading.Thread(target=self.export_xml, args=(cr2, uid, ids, context))
        thread_ptr.start()
        return {}

    @asperience_log
    def export_xml(self, cr, uid, ids, context=False):
        thread = False
        if "thread" in context:
            thread = context["thread"]
        cr2 = sql_db.db_connect(self.env.cr.dbname).cursor()
        cr2.autocommit(True)
        exception = False
        if not ids :
            if 'edi.code' in context:
                ids = self.search(cr,uid,[('code','=',context['edi.code'])])
            else:
                return False

        for edi in self.browse(cr,uid,ids,context):
            self.write(cr2,uid,[edi.id],{'thread':True})
            cr2.commit()
            result = ""
            context['edi'] = edi.id
            context['type'] = 'export'
            try:
#                structs = edi._create_struct_xml()[edi.id]
                if not edi.eval_out:
                    continue
                edi.eval_out = edi.eval_out.replace(chr(13),"\n")
                data = {}
                _logger.debug("EXPORT XML EVAL %s" % (ids))
                exec(edi.eval_out)
                _logger.debug("EXPORT XML EVAL END %s" % (ids))
                context['path_out'] = edi.path_out
                edi._create_files_xml(data=data,context=context)
                if result :
                    self.pool.get('edi.edi.result').create(cr,uid,{"name":"result_export_xml_ok","value":result,"edi":edi.id})
            except:
                import sys,traceback
                tb = sys.exc_info()
                tb_s = "".join(traceback.format_exception(*tb))
                info = tb_s
                _logger.info("Except : %s" % (info))
                cr.rollback()
                if info:
                    self.pool.get('edi.edi.result').create(cr,uid,{"name":"info_export_xml_nok","value":info,"edi":edi.id})
                cr.commit()
                exception = True
        if not exception:
            cr.commit()
        for i in ids :
            cr2.execute("update edi_edi set thread = False where id = %s" % i)
        if thread :
            cr.close()
        cr2.close()
        return True

    @asperience_log
    def import_csv_struct_thread(self, cr, uid, ids, context=False):
        _logger.debug("IMPORT CSV STRUCT THREAD %s" % (ids))
        cr2 = sql_db.db_connect(self.env.cr.dbname).cursor()
        thread_ptr = threading.Thread(target=self.import_csv_struct, args=(cr2, uid, ids, context))
        thread_ptr.start()
        return {}

    @asperience_log
    def import_csv_struct(self, cr, uid, ids, context=False):
        _logger.debug("IMPORT CSV STRUCT %s" % (ids))
        thread = False
        if "thread" in context:
            thread = context["thread"]
        cr2 = sql_db.db_connect(self.env.cr.dbname).cursor()
        cr2.autocommit(True)
        exception = False
        if not ids :
            if 'edi.code' in context:
                ids = self.search(cr,uid,[('code','=',context['edi.code'])])
            else:
                return False
        for edi in self.browse(cr,uid,ids,context):
            self.write(cr2,uid,[edi.id],{'thread':True})
            filename = False
            try :
                structs = edi._create_struct_csv_struct()[edi.id]
                if not edi.eval_in:
                    continue
                edi.eval_in = edi.eval_in.replace(chr(13),"\n")
                data = {}
                gobreak = False
                for filename in edi._get_files(edi.path_in, edi.file_template):
                    _logger.info("Import file : %s" % (filename))
                    result = ""
                    context['edi'] = edi.id
                    context['type'] = 'import'
                    context['filename'] = filename
                    try:
                        file = codecs.open(filename,'rb',edi.charset)
                        file_csv = unicode_csv_reader(file, delimiter=str(edi.delimiter[0]), quotechar=str(edi.quotechar))
                        data[filename] = []
                        first = True
                        nb_line = 0
                        for line in file_csv:
                            if first and edi.skip_first:
                                nb_line = 0
                                first = False
                                continue
                            if edi.line_start > 0 and nb_line < edi.line_start:
                                continue
                            if edi.line_stop > 0 and nb_line > edi.line_stop:
                                break
                            data[filename].append(edi._parse_line_csv_struct(line,structs))
                        file.close()
                        edi.eval_in = edi.eval_in.replace(chr(13),"\n")
                        _logger.debug("IMPORT CSV STRUCT EVAL %s" % (ids))
                        exec(edi.eval_in)
                        _logger.debug("IMPORT CSV STRUCT EVAL END %s" % (ids))
                    except Exception as e:
                        if not os.path.exists (edi.path_in+"error/"):
                            os.makedirs(edi.path_in+"error/")
                        shutil.move(edi.path_in+os.path.basename(filename), edi.path_in+"error/"+os.path.basename(filename))
                        raise e
                    if edi.path_in_move:
                        shutil.move(edi.path_in+os.path.basename(filename), edi.path_in_move+os.path.basename(filename))
                    _logger.info("End Import file : %s" % (filename))

                    self.pool.get('edi.edi.result').create(cr,uid,{"name":"file_import_csv_struct_ok","value":filename,"edi":edi.id})
                    if result:
                        self.pool.get('edi.edi.result').create(cr,uid,{"name":"result_import_csv_struct_ok","value":result,"edi":edi.id})
            except Exception as e:
                import sys,traceback
                tb = sys.exc_info()
                tb_s = "".join(traceback.format_exception(*tb))
                info = tb_s
                try:
                    info += "\n"+ustr(e.value)
                except:
                    pass
                _logger.info("Except : %s" % (info))
                cr.rollback()
                if filename:
                    self.pool.get('edi.edi.result').create(cr,uid,{"name":"file_import_csv_struct_nok","value":filename,"edi":edi.id})
                if info:
                    self.pool.get('edi.edi.result').create(cr,uid,{"name":"info_import_csv_struct_nok","value":info,"edi":edi.id})
                cr.commit()
                exception = True
        if not exception:
            cr.commit()
        for i in ids :
            cr2.execute("update edi_edi set thread = False where id = %s" % i)
        if thread :
            cr.close()
        cr2.close()
        if not thread and exception:
            raise Exception(info)
        return True

    @asperience_log
    def export_csv_struct_thread(self, cr, uid, ids, context=False):
        _logger.debug("EXPORT CSV STRUCT THREAD %s" % (ids))
        raise Exception(_("EXPORT CSV STRUCT THREAD NOT IMPLEMENTED"))

    @asperience_log
    def export_csv_struct(self, cr, uid, ids, context=False):
        _logger.debug("EXPORT CSV STRUCT %s" % (ids))
        raise Exception(_("EXPORT CSV STRUCT NOT IMPLEMENTED"))

    def _get_log(self, cr, uid, ids, context=False):
        edi = self.read(cr,uid,context['edi'],['force'])
        if not edi['force'] :
            cr.execute("select object_id from edi_edi_log where edi = %s" % str(context['edi']) )
            res = cr.dictfetchall()
            for log in res:
                (model_name, id) = log['object_id'].split(',')
                id = int(id)
                if model_name == context['model_log'] and id in context['ids_log']:
                    context['ids_log'].remove(id)
        return context['ids_log']

    def _get_log_ext(self, cr, uid, ids, context=False):
        self.pool.get(context['model_log'])
        edi = self.browse(cr,uid,context['edi'])
        if not edi.force :
            for log in edi.log_ids:
                if log.ref == context['ref']:
                    return False
        return True

    def _log(self, cr, uid, ids, context=False):
        log_obj = self.pool.get('edi.edi.log')
        vals = {
            'name':context['filename'],
            'edi':context['edi'],
            'object_id' :context['model_log']+','+str(context['id_log']),
            'type':context['type'],
            'ref':'ref' in context and context['ref'],
        }
        if 'write_access' in context:
            vals['write_access'] = context['write_access']
        else:
            vals['write_access'] = True
        message = "%s edi %s : %s %s" % (vals['type'],vals['name'],vals['object_id'],vals['write_access'])
        self.log(cr, uid, ids[0], message)
        log_obj.create(cr,uid,vals)


class edi_edi_log (models.Model):
    _name = 'edi.edi.log'

    def write_access(self, cr, uid, model,ids):
        #Each id returns its write_access
        res = {}
        for id in ids:
            log_ids = self.search(cr, uid, [('object_id','=',str(model)+','+str(id))],order="date desc")
            logs = self.browse(cr, uid, log_ids)
            #If we don't have any log
            res[id] = True
            for log in logs:
                #Only most recent log line can block access
                res[id] = log.write_access
                break
        return res

    def write_access_global(self, cr, uid, model,ids):
        #Last id with write_access = False returns False
        for id in ids:
            log_ids = self.search(cr, uid, [('object_id','=',str(model)+','+str(id))],order="date desc")
            logs = self.browse(cr, uid, log_ids)
            #If we don't have any log
            for log in logs:
                #Only most recent log line can block access
                if not log.write_access:
                    _logger.debug(_("Write access false: %s") % (log.object_id,))
                    return False
                break
        return True

    @api.model
    def _models_get(self):
        obj = self.env['ir.model']
        ids = obj.search([])
        return [(r.model, r.name) for r in ids]

    name = fields.Char('Name', size=128, required=True)
    date = fields.Datetime('Date', default=fields.Datetime.now)
    edi = fields.Many2one('edi.edi', 'Edi', required=True)
    object_id = fields.Reference(string='Object', selection=_models_get, size=64)
    type = fields.Selection([('export','export'),('import','import')], 'Type', required=True, size=24)
    ref = fields.Char('Ref', size=128)
    write_access = fields.Boolean('Write access', default=True)

    _order = "date desc, id desc"


class edi_edi_result (models.Model):
    _name = 'edi.edi.result'
    _description = 'edi.edi.result'

    name = fields.Char('Name', size=128, required=True)
    date = fields.Datetime('Date', default=fields.Datetime.now)
    edi = fields.Many2one('edi.edi', 'Edi', required=True)
    value = fields.Text('Value')

    _order = "date desc, id desc"


class edi_edi_line_edi (models.Model):
    _name = 'edi.edi.line.edi'
    _description = 'edi.edi.line.edi'

    @api.constrains('name')
    def check_name(self):
        for line in self:
            if len(line.name) != int(line.edi.length_identifier) and int(line.edi.length_identifier) != 0:
                raise exceptions.ValidationError(_("Invalid length for name"))

    @api.multi
    def _dict_fields_ids(self):
        for line in self:
            for field in line.fields_ids:
                line.dict += "\""+field.name+"\":False,\r"

            char = '0'
            for field in line.fields_ids:
                line.dict += char*field.length
                if char == '0':
                    char = '1'
                else:
                    char = '0'

    name = fields.Char('Name', size=128, required=True)
    sequence = fields.Integer('Sequence', required=True, default=1)
    edi = fields.Many2one('edi.edi', 'Line', required=True)
    fields_ids = fields.One2many('edi.edi.line.edi.field', 'line', 'Fields')
    dict = fields.Text(compute="_dict_fields_ids", string='Dict to put in eval')

    _order = "sequence"


class edi_edi_line_edi_field (models.Model):
    _name = 'edi.edi.line.edi.field'
    _description = 'edi.edi.line.edi.field'

    @api.constrains("start","stop")
    def check_start_stop(self):
        for field in self:
            if field.start > field.stop:
                raise exceptions.ValidationError(_("Invalid start stop"))
            for next in field.line.fields_ids:
                if field.start >= next.start and field.start <= next.stop and field.id != next.id:
                    raise exceptions.ValidationError(_("Invalid start stop"))
                elif field.stop >= next.start and field.stop <= next.stop and field.id != next.id:
                    raise exceptions.ValidationError(_("Invalid start stop"))
    @api.constrains("name")
    def check_name(self):
        for field in self:
            for next in field.line.fields_ids:
                if field.name == next.name and field.id != next.id:
                    raise exceptions.ValidationError(_("The name must be unique !"))

    @api.multi
    def _length(self):
        for field in self:
            field.length = field.stop - field.start + 1

    name = fields.Char('Name', size=128, required=True)
    line = fields.Many2one('edi.edi.line.edi', 'Line', required=True)
    start = fields.Integer('Start', required=True)
    stop = fields.Integer('Stop', required=True)
    length = fields.Integer(compute="_length", string='Length')
    align = fields.Selection([('right','right'),('left','left'),('zero','zero')], 'Align', required=True, size=24)
    type = fields.Selection([('int','int'),('float','float'),('char','char')], 'Type', required=True, size=24)
    cast = fields.Char('Cast', size=128,)
    description = fields.Char('Description', size=128,)

    _order = "line,start"


class edi_edi_csv_field (models.Model):
    _name = 'edi.edi.csv.field'
    _description = 'edi.edi.csv.field'

    @api.constrains('name')
    def check_name(self):
        for field in self:
            for next in field.edi.fields_ids:
                if field.name == next.name and field.id != next.id:
                    raise exceptions.ValidationError(_("The name must be unique !"))

    @api.constrains('sequence')
    def check_sequence(self):
        for field in self:
            for next in field.edi.fields_ids:
                if field.sequence == next.sequence and field.id != next.id:
                    raise exceptions.ValidationError(_("The sequence must be unique !"))

    name = fields.Char('Name', size=128, required=True)
    sequence = fields.Integer('Sequence', required=True, default=1)
    edi = fields.Many2one('edi.edi', 'Edi', required=True)
    type = fields.Selection([('int','int'),('float','float'),('char','char')], 'Type', required=True, size=24)
    cast = fields.Char('Cast', size=128,)
    description = fields.Char('Description', size=128,)

    _order = "edi,sequence"


class edi_edi_xml_field (models.Model):
    _name = 'edi.edi.xml.field'
    _description = 'edi.edi.xml.field'

    @api.constrains('name')
    def check_name(self):
        for field in self:
            for next in field.edi.fields_ids:
                if field.name == next.name and field.id != next.id:
                    raise exceptions.ValidationError(_("The name must be unique !"))

    name = fields.Char('Name', size=128, required=True)
    sequence = fields.Integer('Sequence', required=True, default=1)
    parent = fields.Many2one('edi.edi.xml.field', 'Parent')
    edi = fields.Many2one('edi.edi', 'Edi', required=True)
    type = fields.Selection([('int','int'),('float','float'),('char','char')], 'Type', required=True, size=24)
    cast = fields.Char('Cast', size=128,)
    description = fields.Char('Description', size=128,)

    _order = "parent,sequence"


class edi_edi_line_csv (models.Model):
    _name = 'edi.edi.line.csv'
    _description = 'Lines for structured CSV'

    @api.constrains('name')
    def check_name(self):
        for line in self:
            if len(line.name) != int(line.edi.length_identifier) and int(line.edi.length_identifier) != 0:
                raise exceptions.ValidationError(_("Invalid length for name"))

    @api.multi
    def _dict_fields_ids(self):
        for line in self:
            for field in line.fields_ids:
                line.dict += "\""+field.name+"\":False,\r"

    name = fields.Char('Name', size=128, required=True)
    sequence = fields.Integer('Sequence', required=True, default=1)
    edi = fields.Many2one('edi.edi', 'Line', required=True)
    fields_ids = fields.One2many('edi.edi.line.csv.field', 'line', 'Fields')
    dict = fields.Text(compute="_dict_fields_ids", string='Dict to put in eval')
    description = fields.Char('Description', size=128,)

    _order = "edi,sequence"


class edi_edi_line_csv_field (models.Model):
    _name = 'edi.edi.line.csv.field'
    _description = 'Fields for structured CSV lines'

    @api.constrains('name')
    def check_name(self):
        for field in self:
            for next in field.line.fields_ids:
                if field.name == next.name and field.id != next.id:
                    raise exceptions.ValidationError(_("The name must be unique !"))

    @api.constrains('sequence')
    def check_sequence(self):
        for field in self:
            for next in field.line.fields_ids:
                if field.sequence == next.sequence and field.id != next.id:
                    raise exceptions.ValidationError(_("The sequence must be unique !"))

    line = fields.Many2one('edi.edi.line.csv', 'Line', required=True)
    name = fields.Char('Name', size=128, required=True)
    sequence = fields.Integer('Sequence', required=True)
    type = fields.Selection([('int','int'),('float','float'),('char','char')], 'Type', required=True, size=24)
    cast = fields.Char('Cast', size=128,)
    description = fields.Char('Description', size=128,)

    _order = "line,sequence"

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
