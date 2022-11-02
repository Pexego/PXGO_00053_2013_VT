
from odoo.tests.common import SavepointCase


class TestMrpBom(SavepointCase):
    post_install = True
    at_install = True

    @classmethod
    def setUpClass(cls):
        super(TestMrpBom, cls).setUpClass()
        cls.mrp_bom_model = cls.env['mrp.bom']
        cls.uom_unit = cls.env.ref('product.product_uom_unit')
        cls.product_model = cls.env['product.product']

        cls.product_id = cls.product_model.create({'name': "Test",
                                                   'default_code': "Test"})

        cls.product_id2 = cls.product_model.create({'name': "Test2",
                                                     'default_code': "Test2"})
        cls.mrp_bom_obj = cls.mrp_bom_model.create({
            'product_id': cls.product_id.id,
            'product_tmpl_id': cls.product_id.product_tmpl_id.id,
            'product_uom_id': cls.uom_unit.id,
            'product_qty': 1.0,
            'type': 'phantom',
            'bom_line_ids': [(0,0,{'product_id': cls.product_id2.id,
            'product_qty': 2})]
        })

    def test_when_unlink_mrp_bom_it_must_be_archived(self):

        #act
        self.mrp_bom_obj.unlink()

        #assert
        self.assertFalse(self.mrp_bom_obj.active)
        self.assertTrue(self.mrp_bom_obj.exists())

    def test_when_unlink_mrp_bom_line_it_must_be_archived_but_not_its_bom(self):

        #act
        self.mrp_bom_obj.bom_line_ids.unlink()
        line = self.mrp_bom_obj.bom_line_ids

        #assert
        self.assertTrue(line.exists())
        self.assertFalse(line.active)

