from odoo.tests.common import SavepointCase
from odoo.exceptions import ValidationError


class TestPostalCodeFormat(SavepointCase):
    post_install = True
    at_install = True

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.postal_code_format = cls.env['postal.code.format'].create({
            'name': 'Test format',
            'regex': r'\A(\d{5})$',
            'postal_code_sample': '12345'
        })

    def test_create_format_with_bad_sample(self):
        with self.assertRaisesRegex(ValidationError, 'Not valid postal code sample: "1345"'):
            self.env['postal.code.format'].with_context({'lang': 'en'}).create({
                'name': 'Test format',
                'regex': r'\A(\d{5})$',
                'postal_code_sample': '1345'
            })

    def test_update_format_with_bad_sample(self):
        with self.assertRaisesRegex(ValidationError, 'Not valid postal code sample: "1345"'):
            self.postal_code_format.with_context({'lang': 'en'}).write({'postal_code_sample': '1345'})

    def test_update_format_with_bad_regex(self):
        with self.assertRaisesRegex(ValidationError, 'Not valid postal code sample: "12345"'):
            self.postal_code_format.with_context({'lang': 'en'}).write({'regex': 'Bad regex'})


class TestPostalCodeRange(SavepointCase):
    post_install = True
    at_install = True

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.postal_code_format = cls.env['postal.code.format'].create({
            'name': 'Test format',
            'regex': r'\A(\d{5})$',
            'postal_code_sample': '12345'
        })
        cls.country = cls.env['res.country'].create({
            'name': 'Test Country',
            'postal_code_format_id': cls.postal_code_format.id
        })
        cls.shipping_zone = cls.env['shipping.zone'].create({
            'name': 'Test zone',
            'country_id': cls.country.id
        })
        cls.postal_code_range = cls.env['postal.code.range'].create({
            'first_code': '01234',
            'last_code': '10234',
            'shipping_zone_id': cls.shipping_zone.id
        })

    def test_bad_range_construction(self):
        with self.assertRaisesRegex(ValidationError, 'Error!:: End code is lower than first code.'):
            self.env['postal.code.range'].with_context({'lang': 'en'}).create({
                'first_code': '99999',
                'last_code': '00001',
                'shipping_zone_id': self.shipping_zone.id
            })

    def test_first_code_not_fitted_with_the_format(self):
        with self.assertRaisesRegex(
            ValidationError,
            'Not valid postal code value: "1". Please, try using one like this "12345"'
        ):
            self.env['postal.code.range'].with_context({'lang': 'en'}).create({
                'first_code': '1',
                'last_code': '00010',
                'shipping_zone_id': self.shipping_zone.id
            })

    def test_last_code_not_fitted_with_the_format(self):
        with self.assertRaisesRegex(
            ValidationError,
            'Not valid postal code value: "10". Please, try using one like this "12345"'
        ):
            self.env['postal.code.range'].with_context({'lang': 'en'}).create({
                'first_code': '00001',
                'last_code': '10',
                'shipping_zone_id': self.shipping_zone.id
            })

    def test_check_postal_code_is_in_range(self):
        self.assertTrue(self.postal_code_range.is_postal_code_in_range('10023'))
        self.assertTrue(self.postal_code_range.is_postal_code_in_range('01523'))
        self.assertFalse(self.postal_code_range.is_postal_code_in_range('00013'))
        self.assertFalse(self.postal_code_range.is_postal_code_in_range('21523'))


class TestShippingZone(SavepointCase):
    post_install = True
    at_install = True

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.postal_code_format = cls.env['postal.code.format'].create({
            'name': 'Test format',
            'regex': r'\A(\d{5})$',
            'postal_code_sample': '12345'
        })
        cls.country = cls.env['res.country'].create({
            'name': 'Test Country',
            'postal_code_format_id': cls.postal_code_format.id
        })
        cls.shipping_zone = cls.env['shipping.zone'].create({
            'name': 'Zona test',
            'country_id': cls.country.id
        })
        cls.postal_code_range = cls.env['postal.code.range'].create({
            'first_code': '00123',
            'last_code': '00200',
            'shipping_zone_id': cls.shipping_zone.id
        })

    def test_check_postal_code_is_in_zone(self):
        self.assertTrue(self.shipping_zone.is_postal_code_in_zone('00150'))
        self.assertTrue(self.shipping_zone.is_postal_code_in_zone('00194'))
        self.assertFalse(self.shipping_zone.is_postal_code_in_zone('01194'))
        self.assertFalse(self.shipping_zone.is_postal_code_in_zone('00094'))
