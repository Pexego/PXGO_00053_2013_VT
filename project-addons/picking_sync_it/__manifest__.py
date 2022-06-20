{
    'name': 'Sync pickings IT',
    'description': "Synchronize with odoo spain when the products arrive",
    'version': '11.0.0.0.1',
    'author': 'Visiotech',
    'category': '',
    'depends': ['stock', 'purchase', 'base_synchro', 'picking_incidences', 'queue_job'],
    'data': ["views/stock_picking_view.xml",
             "views/email_template.xml"],
    'active': False,
    'installable': True,
}