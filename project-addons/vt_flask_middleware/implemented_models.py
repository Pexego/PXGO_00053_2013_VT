from country import Country
from product import Product, ProductCategory, ProductBrand, \
    ProductBrandCountryRel
from customer import Customer
from invoice import Invoice
from commercial import Commercial
from rma import RmaStatus, RmaStage, Rma, RmaProduct
from picking import Picking, PickingProduct
#from post import Post
MODELS_CLASS = {
    'invoice': Invoice, 'customer': Customer, 'product': Product,
    'productcategory': ProductCategory, 'rmastatus': RmaStatus,
    'rmastage': RmaStage, 'rma': Rma, 'picking': Picking, 'pickingproduct': PickingProduct,
    'rmaproduct': RmaProduct, 'country': Country, 'commercial': Commercial,
    'productbrand': ProductBrand, 'productbrandcountryrel': ProductBrandCountryRel}#, 'post': Post}

MASTER_CLASSES = {'commercial': Commercial,'productcategory': ProductCategory,
                  'rmastatus': RmaStatus, 'rmastage': RmaStage,
                  'country': Country, 'productbrand': ProductBrand}

DEPENDENT_CLASSES = {'invoice': Invoice, 'customer': Customer, 'product': Product,
                     'picking': Picking, 'pickingproduct': PickingProduct,
                     'rma': Rma, 'rmaproduct': RmaProduct,
                     'productbrandcountryrel': ProductBrandCountryRel}
