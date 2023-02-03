from odoo.addons.component.core import Component
from odoo.addons.queue_job.job import job
from odoo import api, fields, models

class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    web = fields.Boolean()
    related_pricelist_item_ids = fields.One2many('product.pricelist.item', "base_pricelist_id")

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def export_pricelist(self,fields):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.update(self, 'insert')
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def update_pricelist(self,fields):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.update(self, 'update')
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def unlink_pricelist(self):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.delete(self)
        return True

class ProductPricelistListener(Component):
    _name = 'product.pricelist.event.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['product.pricelist']

    def on_record_write(self, record, fields=None):
        up_fields = ["name", "brand_group_id", "web"]
        if "web" in fields:
            if record.web:
                record.with_delay(priority=11, eta=80).export_pricelist(fields)
            else:
                record.with_delay(priority=11, eta=80).unlink_pricelist()
        elif record.web:
            for field in up_fields:
                if field in fields:
                    record.with_delay(priority=11, eta=80).update_pricelist(fields=fields)
                    break

    def on_record_create(self, record, fields=None):
        up_fields = ["name", "brand_group_id", "web"]
        if record.web:
            for field in up_fields:
                if field in fields:
                    record.with_delay(priority=11, eta=80).export_pricelist(fields=fields)
                    break

    def on_record_unlink(self, record):
        if record.web:
            record.with_delay(priority=11, eta=80).unlink_pricelist(fields=fields)

class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def export_pricelist_item(self, product):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.update(self, 'insert', product)
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def update_pricelist_item(self, product):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.update(self, 'update', product)
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def unlink_pricelist_item(self, product):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.delete(self,product)
        return True

    def get_related_web_items(self, brand_id, categ_id, pricelist_processed=None):
        if pricelist_processed is None:
            pricelist_processed = set()
        pricelist_items = self.env['product.pricelist.item']
        if self.pricelist_id.web:
            for p in self.pricelist_id.related_pricelist_item_ids.filtered(lambda i,categ=categ_id,brand=brand_id:
                                                    i.applied_on=='3_global' or
                                                    (categ and i.applied_on=='2_product_category'  and i.categ_id==categ) or
                                                    (brand and i.applied_on=='25_product_brand'  and i.product_brand_id==brand)):
                if p.pricelist_id.id in pricelist_processed:
                    continue
                pricelist_processed.add(p.pricelist_id.id)
                pricelist_items |= p
                pricelist_items |= p.get_related_web_items(brand_id,categ_id,pricelist_processed)
        return pricelist_items

class ProductPricelistItemListener(Component):
    _name = 'product.pricelist.item.event.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['product.pricelist.item']

    def on_record_write(self, record, fields=None):
        up_fields = ["fixed_price"]
        if record.pricelist_id.web or (not record.pricelist_id and record.pricelist_calculated.web):
            for field in up_fields:
                if field in fields:
                    record.with_delay(priority=11, eta=80).update_pricelist_item(record.product_id)
                    items = record.get_related_web_items(record.product_id.categ_id,record.product_id.product_brand_id)
                    for i in items:
                        i.with_delay(priority=11, eta=80).update_pricelist_item(record.product_id)
                    break

    def on_record_create(self, record, fields=None):
        up_fields = [
            'pricelist_id',
            'pricelist_calculated',
            'product_id',
            'applied_on',
            'product_tmpl_id',
            'fixed_price',
            'calculated_price'
        ]
        if (record.pricelist_id.web or (not record.pricelist_id and record.pricelist_calculated.web)) and record.product_id:
            for field in up_fields:
                if field in fields:
                    record.with_delay(priority=11, eta=80).export_pricelist_item(record.product_id)
                    items = record.get_related_web_items(record.product_id.categ_id, record.product_id.product_brand_id)
                    if items:
                        for i in items:
                            i.with_delay(priority=11, eta=80).export_pricelist_item(record.product_id)
                    break


    def on_record_unlink(self, record):
        if record.pricelist_id.web:
            record.with_delay(priority=11, eta=80).unlink_pricelist_item(record.product_id)
            items = record.get_related_web_items(record.product_id.categ_id, record.product_id.product_brand_id)
            for i in items:
                i.with_delay(priority=11, eta=80).unlink_pricelist_item(record.product_id)

