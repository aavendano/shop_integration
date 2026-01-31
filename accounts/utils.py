from .models import Session


class ShopifySession:
    def __init__(self, shop_domain):
        self.shop_domain = shop_domain
        self.session = Session.objects.get(site=shop_domain)

    def get_access_token(self):
        return self.session.token
    
    def get_shop_domain(self):
        return self.session.site
    
