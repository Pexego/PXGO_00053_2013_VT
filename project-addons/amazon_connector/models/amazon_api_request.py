from odoo import _
from sp_api.api import Orders, Reports
from sp_api.base import Marketplaces
from sp_api.base.exceptions import SellingApiException, SellingApiRequestThrottledException
from odoo.exceptions import UserError
import time


class AmazonAPIRequest(object):
    def __init__(self, company_id, rate_time_limit, marketplaces=None):
        self.company_id = company_id
        self.credentials = self._get_credentials()
        self.rate_time_limit = rate_time_limit
        if not marketplaces:
            marketplaces = self._get_marketplaces()
        self.marketplace_ids = marketplaces
        self.reports_obj = Reports(marketplace=Marketplaces.ES, credentials=self.credentials)
        self.orders_obj = Orders(marketplace=Marketplaces.ES, credentials=self.credentials)

    def _get_marketplaces(self):
        return self.company_id.marketplace_ids.mapped('code')

    def _get_credentials(self):
        return dict(
            refresh_token=self.company_id.refresh_token,
            lwa_app_id=self.company_id.lwa_app_id,
            lwa_client_secret=self.company_id.lwa_client_secret,
            aws_secret_key=self.company_id.aws_secret_key,
            aws_access_key=self.company_id.aws_access_key,
            role_arn=self.company_id.role_arn,
        )

    def create_report(self, report_name, data_start_time, data_end_time):
        try:
            return self.reports_obj.create_report(reportType=report_name,
                                                  marketplaceIds=self.marketplace_ids,
                                                  dataStartTime=data_start_time,
                                                  dataEndTime=data_end_time).payload
        except SellingApiException as e:
            raise UserError(_("Amazon API Error. No order was created due to errors. '%s' \n") % e)

    def get_report(self, report_id):
        report_state = ""
        report = {}
        while report_state != 'DONE':
            try:
                report = self.reports_obj.get_report(report_id).payload
                report_state = report.get("processingStatus")
            except SellingApiRequestThrottledException:
                time.sleep(self.rate_time_limit)
                continue
            except SellingApiException as e:
                raise UserError(_("Amazon API Error. Report %s. '%s' \n") % (report_id, e))
        return report

    def get_report_document(self, report_document_id):
        while True:
            try:
                return self.reports_obj.get_report_document(report_document_id,
                                                            download=True, decrypt=True).payload
            except SellingApiRequestThrottledException:
                time.sleep(self.rate_time_limit)
            except SellingApiException as e:
                raise UserError(_("Amazon API Error. Report %s. '%s' \n") % (report_document_id, e))

    def call_api_order_method(self, order_method, order_name):
        while True:
            try:
                return getattr(self.orders_obj, order_method)(order_id=order_name).payload
            except SellingApiRequestThrottledException:
                time.sleep(self.rate_time_limit)
            except SellingApiException as e:
                raise UserError(_("Amazon API Error. Method: %s.Order %s. '%s' \n") % (order_method, order_name, e))

    def get_order_buyer_info(self, order_name):
        return self.call_api_order_method("get_order_buyer_info", order_name)

    def get_order_items(self, order_name):
        return self.call_api_order_method("get_order_items", order_name)

    def get_order(self, order_name):
        return self.call_api_order_method("get_order", order_name)

    def get_order_address(self, order_name):
        return self.call_api_order_method("get_order_address", order_name)

    def get_reports(self, report_types, created_since, page_size, next_token=False):
        if next_token:
            reports_res = self.reports_obj.get_reports(next_token=next_token)
        else:
            reports_res = self.reports_obj.get_reports(reportTypes=report_types,
                                                       createdSince=created_since, pageSize=page_size)
        return reports_res
