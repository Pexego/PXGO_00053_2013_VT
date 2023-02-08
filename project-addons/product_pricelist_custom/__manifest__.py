# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Product Pricelist Custom",
    "version": "11.0.0.0.0",
    "author": "Nadia Ferreyra",
    "category": "Product",
    "description": """
    Product Pricelist Customizations
    Add margins and relations on product pricelist
""",
    "depends": ["base", "product", "product_brand", "sale", "sale_customer_discount"],
    "data": [
        "security/ir.model.access.csv",
        "views/brand_group_view.xml",
        "views/product_view.xml",
        "views/partner_view.xml",
        "security/product_pricelist_custom.xml",
        "views/sale_view.xml"
    ],
    "demo": [],
    'auto_install': False,
    "installable": True,
    'images': [],
}
