# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Order scheduled shipment",
    "summary": "Sale order with scheduled shipment",
    "version": "8.0.1.0.0",
    "category": "Connector",
    "author": "Nadia Ferreyra",
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "base",
        "sale",
        "connector",
        "sale_stock",
        "picking_invoice_pending"
    ],
    "data": [
        'data/job_channel_data.xml',
        'views/sale_view.xml',
    ],
}
