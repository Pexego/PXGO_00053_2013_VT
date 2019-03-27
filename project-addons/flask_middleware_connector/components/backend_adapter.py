# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import AbstractComponent, Component
from odoo.addons.queue_job.exception import RetryableJobError
from odoo.addons.connector.exception import NetworkRetryableError
import socket
import logging
import xmlrpc
from datetime import datetime
_logger = logging.getLogger(__name__)


class MiddlewareCRUDAdapter(AbstractComponent):
    """ External Records Adapter for Magento """

    _name = 'middleware.crud.adapter'
    _inherit = ['base.backend.adapter']

    def __init__(self, connector_env):
        """

        :param connector_env: current environment (backend, session, ...)
        :type connector_env: :class:`connector.connector.ConnectorEnvironment`
        """
        super(MiddlewareCRUDAdapter, self).__init__(connector_env)
        backend = self.backend_record
        self.server = xmlrpc.client.ServerProxy(backend.location)
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
        except xmlrpc.client.ProtocolError as err:
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
        except xmlrpc.client.ProtocolError as err:
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
            except Exception:
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
        except xmlrpc.client.ProtocolError as err:
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


class GenericAdapter(AbstractComponent):

    _name = 'middleware.adapter'
    _inherit = 'middleware.crud.adapter'
    _usage = 'backend.adapter'

    def insert(self, data):
        """ Create a record on the external system """
        return self.create(self._middleware_model, data)

    def update(self, id, data):
        """ Update records on the external system """
        return self.write(self._middleware_model, int(id), data)

    def remove(self, id):
        """ Delete a record on the external system """
        return self.delete(self._middleware_model, int(id))

    def insert_rel(self, model_name, data):
        # Tenemos función propia para este unlink ya que se llama desde el adapter de res.partner
        return self.create(model_name, data)

    def remove_rel(self, model_name, id):
        # Tenemos función propia para este unlink ya que se llama desde el adapter de res.partner
        return self.delete(model_name, int(id))
