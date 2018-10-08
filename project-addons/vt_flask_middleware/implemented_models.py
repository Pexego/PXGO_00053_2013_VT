from country import Country, CountryState
from product import Product, ProductCategory, ProductBrand, \
    ProductBrandCountryRel
from customer import Customer, CustomerTag, CustomerTagCustomerRel
from invoice import Invoice
from order import Order, OrderProduct
from commercial import Commercial
from rma import RmaStatus, RmaStage, Rma, RmaProduct
from picking import Picking, PickingProduct
from rappel import Rappel, RappelCustomerInfo, RappelSection
#from post import Post
MODELS_CLASS = {
    'invoice': Invoice, 'customer': Customer, 'customertag': CustomerTag, 'customertagcustomerrel': CustomerTagCustomerRel,
    'product': Product, 'productcategory': ProductCategory, 'rmastatus': RmaStatus,
    'rmastage': RmaStage, 'rma': Rma, 'picking': Picking, 'pickingproduct': PickingProduct,
    'rmaproduct': RmaProduct, 'country': Country, 'commercial': Commercial,
    'productbrand': ProductBrand, 'productbrandcountryrel': ProductBrandCountryRel, 
    'order': Order, 'orderproduct': OrderProduct, 'rappel': Rappel, 'rappelcustomerinfo': RappelCustomerInfo,
    'rappelsection':RappelSection, 'countrystate': CountryState}#, 'post': Post}

MASTER_CLASSES = {'commercial': Commercial,'productcategory': ProductCategory,
                  'rmastatus': RmaStatus, 'rmastage': RmaStage,
                  'country': Country, 'productbrand': ProductBrand, 'rappel': Rappel}

DEPENDENT_CLASSES = {'invoice': Invoice, 'customer': Customer, 'customertag': CustomerTag, 'customertagcustomerrel': CustomerTagCustomerRel,
                     'product': Product, 'picking': Picking, 'pickingproduct': PickingProduct,
                     'rma': Rma, 'rmaproduct': RmaProduct,
                     'productbrandcountryrel': ProductBrandCountryRel, 'order': Order,
                     'orderproduct': OrderProduct, 'rappelcustomerinfo': RappelCustomerInfo, 'countrystate': CountryState}