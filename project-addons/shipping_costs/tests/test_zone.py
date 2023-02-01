from odoo.tests.common import SavepointCase
from odoo.exceptions import ValidationError


class TestPostalCodeRange(SavepointCase):
    post_install = True
    at_install = True

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.postal_code_range = cls.env['postal.code.range'].create({
            'first_code': '01234',
            'last_code': '10234'
        })

    def test_bad_range_construction(self):
        with self.assertRaises(ValidationError):
            self.env['postal.code.range'].create({
                'first_code': '99999',
                'last_code': '00001'
            })

    def test_range_with_not_full_postal_code_at_creation_is_created_fully_filled(self):
        range_not_full_at_creation = self.env['postal.code.range'].create({
            'first_code': '1',
            'last_code': '10'
        })
        self.assertFalse(range_not_full_at_creation.first_code == '1')
        self.assertTrue(range_not_full_at_creation.first_code == '00001')
        self.assertFalse(range_not_full_at_creation.last_code == '10')
        self.assertTrue(range_not_full_at_creation.last_code == '00010')

    def test_check_postal_code_is_in_range(self):
        self.assertTrue(self.postal_code_range.is_postal_code_in_range('10023'))
        self.assertTrue(self.postal_code_range.is_postal_code_in_range('1523'))
        self.assertFalse(self.postal_code_range.is_postal_code_in_range('13'))
        self.assertFalse(self.postal_code_range.is_postal_code_in_range('21523'))


class TestShippingZone(SavepointCase):
    post_install = True
    at_install = True

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.postal_code_range = cls.env['postal.code.range'].create({
            'first_code': '00123',
            'last_code': '00200'
        })
        cls.shipping_zone = cls.env['shipping.zone'].create({
            'name': 'Zona test',
            'postal_code_ids': [(0, 0, {
                'first_code': '00123',
                'last_code': '00200'
            })]
        })

    def test_check_postal_code_is_in_zone(self):
        self.assertTrue(self.shipping_zone.is_postal_code_in_zone('00150'))
        self.assertTrue(self.shipping_zone.is_postal_code_in_zone('00194'))
        self.assertFalse(self.shipping_zone.is_postal_code_in_zone('01194'))
        self.assertFalse(self.shipping_zone.is_postal_code_in_zone('00094'))
