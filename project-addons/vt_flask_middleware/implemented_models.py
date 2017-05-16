from country import Country
from product import Product, ProductCategory, ProductBrand, \
    ProductBrandCountryRel
from customer import Customer
from invoice import Invoice
from commercial import Commercial
from rma import RmaStatus, RmaStage, Rma, RmaProduct
MODELS_CLASS = {
    'invoice': Invoice, 'customer': Customer, 'product': Product,
    'productcategory': ProductCategory, 'rmastatus': RmaStatus,
    'rmastage': RmaStage, 'rma': Rma, 'rmaproduct': RmaProduct,
    'country': Country, 'commercial': Commercial, 'productbrand': ProductBrand,
    'productbrandcountryrel': ProductBrandCountryRel}

MASTER_CLASSES = {'invoice': Invoice, 'commercial': Commercial,'productcategory': ProductCategory,
                  'rmastatus': RmaStatus, 'rmastage': RmaStage ,
                  'country': Country, 'productbrand': ProductBrand}

DEPENDENT_CLASSES = {'customer': Customer,'product': Product,
                     'rma': Rma, 'rmaproduct': RmaProduct,
                     'productbrandcountryrel': ProductBrandCountryRel}
