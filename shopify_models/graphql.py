from django.conf import settings
import warnings

from shopify_client import ShopifyGraphQLClient as CoreShopifyGraphQLClient


class ShopifyGraphQLError(Exception):
    def __init__(self, message, errors=None):
        super().__init__(message)
        self.errors = errors or []


class ShopifyGraphQLClient:
    def __init__(
        self,
        session,
        *,
        api_version=settings.API_VERSION,
        timeout=30,
        min_available=50,
        throttle=True,
    ):
        warnings.warn(
            "shopify_models.graphql.ShopifyGraphQLClient is deprecated; "
            "use shopify_client.ShopifyGraphQLClient instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.session = session
        self.api_version = api_version
        self.timeout = timeout
        self.min_available = min_available
        self.throttle = throttle
        self._client = CoreShopifyGraphQLClient(
            session.site,
            session.token,
            api_version,
        )

    def execute(self, query, variables=None):
        data = self._client._execute(query, variables)
        return data, {}
