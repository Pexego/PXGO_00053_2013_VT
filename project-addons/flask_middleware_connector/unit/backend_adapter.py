##############################################################################
#
#    Copyright (C) 2015 Comunitea All Rights Reserved
#    $Omar Castiñeira Saavedra <omar@comunitea.com>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import socket
import logging
import xmlrpclib

from openerp.addons.connector.unit.backend_adapter import CRUDAdapter
from openerp.addons.connector.exception import (NetworkRetryableError,
                                                RetryableJobError)
from datetime import datetime
_logger = logging.getLogger(__name__)


class MiddlewareCRUDAdapter(CRUDAdapter):
    """ External Records Adapter for Magento """

    def __init__(self, connector_env):
        """

        :param connector_env: current environment (backend, session, ...)
        :type connector_env: :class:`connector.connector.ConnectorEnvironment`
        """
        super(MiddlewareCRUDAdapter, self).__init__(connector_env)
        backend = self.backend_record
        self.server = xmlrpclib.ServerProxy(backend.location)
        self.uid = self.server.login(backend.username, backend.password)
        self.password = backend.password

    def search(self, filters=None):
        """ Search records according to some criterias
        and returns a list of ids """
        raise NotImplementedError

    def read(self, id, attributes=None):
        """ Returns the information of a record """
        raise NotImplementedError

    def search_read(self, filters=None):
        """ Search records according to some criterias
        and returns their information"""
        raise NotImplementedError

    def create(self, model, data):
        """ Create a record on the external system """
        try:
            start = datetime.now()
            try:
                result = self.server.create(self.uid, self.password, model,
                                            data)
            except Exception as err:
                _logger.error("create(%s, %s) failed", model, data)
                raise RetryableJobError(err)
            else:
                _logger.debug("create(%s, %s) returned %s in %s seconds",
                              model, data, result,
                              (datetime.now() - start).seconds)
            return result
        except (socket.gaierror, socket.error, socket.timeout) as err:
            raise NetworkRetryableError(
                'A network error caused the failure of the job: '
                '%s' % err)
        except xmlrpclib.ProtocolError as err:
            if err.errcode in [502,   # Bad gateway
                               503,   # Service unavailable
                               504]:  # Gateway timeout
                raise RetryableJobError(
                    'A protocol error caused the failure of the job:\n'
                    'URL: %s\n'
                    'HTTP/HTTPS headers: %s\n'
                    'Error code: %d\n'
                    'Error message: %s\n' %
                    (err.url, err.headers, err.errcode, err.errmsg))
            else:
                raise


    def write(self, model, id, data):
        """ Update records on the external system """
        try:
            start = datetime.now()
            try:
                result = self.server.write(self.uid, self.password, model, id,
                                           data)
            except Exception as err:
                _logger.error("write(%s, %s, %s) failed", model, id, data)
                raise RetryableJobError(err)
            else:
                _logger.debug("write(%s, %s, %s) returned %s in %s seconds",
                              model, id, data, result,
                              (datetime.now() - start).seconds)
            return result
        except (socket.gaierror, socket.error, socket.timeout) as err:
            raise NetworkRetryableError(
                'A network error caused the failure of the job: '
                '%s' % err)
        except xmlrpclib.ProtocolError as err:
            if err.errcode in [502,   # Bad gateway
                               503,   # Service unavailable
                               504]:  # Gateway timeout
                raise RetryableJobError(
                    'A protocol error caused the failure of the job:\n'
                    'URL: %s\n'
                    'HTTP/HTTPS headers: %s\n'
                    'Error code: %d\n'
                    'Error message: %s\n' %
                    (err.url, err.headers, err.errcode, err.errmsg))
            else:
                raise

    def delete(self, model, id):
        """ Delete a record on the external system """
        try:
            start = datetime.now()
            try:
                result = self.server.unlink(self.uid, self.password, model, id)
            except:
                _logger.error("unlink(%s, %s) failed", model, id)
                raise
            else:
                _logger.debug("unlink(%s, %s) returned %s in %s seconds",
                              model, id, result,
                              (datetime.now() - start).seconds)
            return result
        except (socket.gaierror, socket.error, socket.timeout) as err:
            raise NetworkRetryableError(
                'A network error caused the failure of the job: '
                '%s' % err)
        except xmlrpclib.ProtocolError as err:
            if err.errcode in [502,   # Bad gateway
                               503,   # Service unavailable
                               504]:  # Gateway timeout
                raise RetryableJobError(
                    'A protocol error caused the failure of the job:\n'
                    'URL: %s\n'
                    'HTTP/HTTPS headers: %s\n'
                    'Error code: %d\n'
                    'Error message: %s\n' %
                    (err.url, err.headers, err.errcode, err.errmsg))
            else:
                raise


class GenericAdapter(MiddlewareCRUDAdapter):

    _model_name = None
    _middleware_model = None

    def insert(self, data):
        """ Create a record on the external system """
        return self.create(self._middleware_model, data)

    def update(self, id, data):
        """ Update records on the external system """
        return self.write(self._middleware_model, int(id), data)

    def remove(self, id):
        """ Delete a record on the external system """
        return self.delete(self._middleware_model, int(id))
