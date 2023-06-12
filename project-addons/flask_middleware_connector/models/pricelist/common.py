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
            record.with_delay(priority=11, eta=80).unlink_pricelist()

class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def export_pricelist_item(self, product, pricelist):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.update('insert', product, pricelist)
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def update_pricelist_item(self, product, pricelist):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.update('update', product, pricelist)
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def unlink_pricelist_item(self, product, pricelist):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.delete(product, pricelist)
        return True

    def get_related_web_items(self, categ_id, brand_id, pricelist_processed=None):
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
                pricelist_items |= p.get_related_web_items(categ_id,brand_id,pricelist_processed)

        return pricelist_items

    def get_related_cost_items(self, categ_id, brand_id, cost_field):
        """
            Get the pricelist items dependent on cost_field
            :param categ_id product.category
            :param brand_id product.brand
            :param cost_field: field to search
        """
        pricelist_items = self.env['product.pricelist.item']
        if cost_field == 'pricelist':
            return pricelist_items

        pricelist_processed = set()
        items = self.env['product.pricelist.item'].search(['&',('base','=',cost_field),'|', ('applied_on', '=', '3_global'), '|', '&',
                                                           ('applied_on', '=', '2_product_category'),
                                                           ('categ_id', '=', categ_id.id), '&',
                                                           ('applied_on', '=', '25_product_brand'),
                                                           ('product_brand_id', '=', brand_id.id)])
        for p in items:
            if not p.pricelist_id.web or p.pricelist_id.id in pricelist_processed:
                continue
            pricelist_processed.add(p.pricelist_id.id)
            pricelist_items |= p
            pricelist_items |= p.get_related_web_items(categ_id, brand_id, pricelist_processed)

        return pricelist_items

class ProductPricelistItemListener(Component):
    _name = 'product.pricelist.item.event.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['product.pricelist.item']

    def _create_product_pricelist_items_works(self, record, up_fields, fields, mode):
        """
        This function creates jobs (export,update or unlinks) of product pricelist items for a given record and
        its related pricelist items.

        :param record: The pricelist item that has changed
                :type record: product.pricelist.item
        :param up_fields: The fields that when modified trigger the generation of the job
                :type up_fields: list<string>
        :param fields: The fields modified
            :type fields: list<string>
        :param mode: The mode of the job operation (export, update or unlink)
            :type mode: str
        :return: None
        """
        pricelists = record.pricelist_id | record.pricelist_calculated
        if record.pricelist_id.brand_group_id and record.pricelist_calculated:
            return
        brand = self.env.context.get('old_brand') or record.product_id.product_brand_id
        for pricelist in pricelists:
            if pricelist.web and pricelist.base_pricelist and record.product_id:
                for field in up_fields:
                    if field in fields:
                        pricelist = record.pricelist_calculated if (record.item_id or not record.pricelist_id) \
                                                                     and record.pricelist_calculated else record.pricelist_id
                        #This line calls the job creation (f.e item._export_pricelist_item(product))
                        getattr(record.with_delay(priority=11, eta=80), f'{mode}_pricelist_item')(record.product_id, pricelist)
                        items = record.get_related_web_items(record.product_id.categ_id, brand)
                        for i in items:
                            pricelist_item = i.pricelist_calculated if (i.item_id or not i.pricelist_id) \
                                                                       and i.pricelist_calculated else i.pricelist_id
                            # This line calls the job creation (f.e item._export_pricelist_item(product))
                            getattr(i.with_delay(priority=11, eta=80), f'{mode}_pricelist_item')(record.product_id, pricelist_item)
                        break

    def on_record_write(self, record, fields=None):
        if 'active' in fields:
            self._create_product_pricelist_items_works(record, [None], [None], "export" if record.active else "unlink")
        else:
            up_fields = ["fixed_price"]
            self._create_product_pricelist_items_works(record, up_fields, fields, "update")

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
        self._create_product_pricelist_items_works(record, up_fields, fields, "export")

    def on_record_unlink(self, record):
        self._create_product_pricelist_items_works(record, [None], [None], "unlink")
