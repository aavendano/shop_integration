from .models import Session


def get_access_token(shop_domain):
    try:
        session = Session.objects.get(site=shop_domain)
        return session.token
    except Session.DoesNotExist:
        return None
