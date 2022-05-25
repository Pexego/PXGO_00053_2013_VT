{
    'name': 'RMA Scanner',
    'version': '11.0.0.0.0',
    'summary': 'Scan the RMAs with a barcode scanner and print a label',
    'author': 'Visiotech',
    'license': 'AGPL-3',
    'depends': ['base', 'barcode_action', 'crm_claim', 'crm_claim_rma', 'crm_claim_rma_custom', 'printer_zpl2'],
    'data': ['views/claim_views.xml', 'views/vstock_location_views.xml', 'views/res_user_view.xml',
             'security/ir.model.access.csv', 'data/label.xml',
             'wizard/print_record_label.xml'],
    'installable': True,
}
