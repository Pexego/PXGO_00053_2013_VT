from country import Country
from product import Product, ProductCategory, ProductBrand, \
    ProductBrandCountryRel
from customer import Customer
from commercial import Commercial
from rma import RmaStatus, Rma, RmaProduct
MODELS_CLASS = {
    'customer': Customer, 'product': Product,
    'productcategory': ProductCategory, 'rmastatus': RmaStatus, 'rma': Rma,
    'rmaproduct': RmaProduct, 'country': Country, 'commercial': Commercial,
    'productbrand': ProductBrand, 'productbrandcountryrel':
    ProductBrandCountryRel}

MASTER_CLASSES = {'commercial': Commercial,'productcategory': ProductCategory,
                  'rmastatus': RmaStatus,'country': Country,
                  'productbrand': ProductBrand}

DEPENDENT_CLASSES = {'customer': Customer,'product': Product,
                     'rma': Rma, 'rmaproduct': RmaProduct,
                     'productbrandcountryrel': ProductBrandCountryRel}
