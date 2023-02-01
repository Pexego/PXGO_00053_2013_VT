from country import Country, CountryState
from product import Product, ProductCategory, ProductBrand, \
    ProductBrandCountryRel, ProductTag, ProductTagProductRel, ProductBrandGroup
from customer import Customer, CustomerTag, CustomerTagCustomerRel
from invoice import Invoice
from order import Order, OrderProduct
from commercial import Commercial
from rma import RmaStatus, RmaStage, Rma, RmaProduct
from picking import Picking, PickingProduct
from rappel import Rappel, RappelCustomerInfo, RappelSection
from translation import Translation
from payment import PaymentLine
from point_programme import CustomerSalePointProgrammeRule, CustomerSalePointProgramme
from pricelist import ProductPricelist,ProductPricelistItem

#from post import Post
MODELS_CLASS = {
    'customer': Customer, 'customertag': CustomerTag, 'customertagcustomerrel': CustomerTagCustomerRel, 'invoice': Invoice,
    'product': Product, 'productcategory': ProductCategory, 'rmastatus': RmaStatus,
    'rmastage': RmaStage, 'rma': Rma, 'picking': Picking, 'pickingproduct': PickingProduct,
    'rmaproduct': RmaProduct, 'country': Country, 'commercial': Commercial,
    'productbrand': ProductBrand, 'productbrandcountryrel': ProductBrandCountryRel,
    'order': Order, 'orderproduct': OrderProduct, 'rappel': Rappel, 'rappelcustomerinfo': RappelCustomerInfo,
    'rappelsection': RappelSection, 'countrystate': CountryState, 'producttag': ProductTag, 'producttagproductrel': ProductTagProductRel,
    'translation': Translation, 'paymentline': PaymentLine, 'Customersalepointprogrammerule': CustomerSalePointProgrammeRule,
    'Customersalepointprogramme':CustomerSalePointProgramme, 'productbrandgroup': ProductBrandGroup,
    'productpricelist':ProductPricelist,'productpricelistitem':ProductPricelistItem}#, 'post': Post}

MASTER_CLASSES = {'commercial': Commercial,'productcategory': ProductCategory,
                  'rmastatus': RmaStatus, 'rmastage': RmaStage,
                  'country': Country,  'rappel': Rappel,
                  'translation': Translation, 'paymentline': PaymentLine, 'productbrandgroup': ProductBrandGroup}

SECOND_LEVEL_CLASSES = {'productbrand': ProductBrand, 'customer': Customer, 'product': Product}

DEPENDENT_CLASSES = {'customertag': CustomerTag,'invoice': Invoice,
                     'picking': Picking, 'pickingproduct': PickingProduct,
                     'rma': Rma, 'rmaproduct': RmaProduct,
                     'productbrandcountryrel': ProductBrandCountryRel, 'order': Order, 'producttag': ProductTag, 'producttagproductrel': ProductTagProductRel,
                     'orderproduct': OrderProduct, 'rappelcustomerinfo': RappelCustomerInfo, 'countrystate': CountryState,'productpricelist':ProductPricelist
                     }

FOUR_LEVEL_CLASSES = {'Customersalepointprogrammerule': CustomerSalePointProgrammeRule, 'productpricelistitem':ProductPricelistItem}

LAST_CLASSES = {'Customersalepointprogramme': CustomerSalePointProgramme,
                'customertagcustomerrel': CustomerTagCustomerRel}
