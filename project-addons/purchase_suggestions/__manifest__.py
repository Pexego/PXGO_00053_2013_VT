{
    'name': "Purchase Suggestions",
    'version': '1.0',
    'category': 'Custom',
    'description': """Add Purchase Suggestions from Sales Data""",
    'author': 'Visiotech',
    "depends": ['base', 'sale', 'product', 'purchase', 'report_xlsx'],
    "data": [
             "wizard/purchase_suggestions_wizard.xml"
             ],
    "installable": True
}
