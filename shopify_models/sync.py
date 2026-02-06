"""
Shopify synchronization module for Market, Catalog, Publication, and PriceList.
Handles bi-directional sync with Shopify GraphQL API.
"""
import logging
from typing import Optional
from django.conf import settings
from shopify_client import ShopifyGraphQLClient
from accounts.models import Session

log = logging.getLogger(__name__)


def get_shopify_client() -> ShopifyGraphQLClient:
    """Get an authenticated Shopify GraphQL client."""
    session = Session.objects.first()
    if not session:
        raise Exception("No active Shopify session found")
    return ShopifyGraphQLClient(session.site, session.token, settings.API_VERSION)


def sync_market(market_instance) -> dict:
    """
    Synchronize a Market instance with Shopify.
    Creates or updates the market in Shopify.
    
    Args:
        market_instance: Market model instance
        
    Returns:
        dict: Response from Shopify with market data and any errors
    """
    client = get_shopify_client()
    
    if market_instance.shopify_id:
        # Update existing market
        mutation = """
        mutation marketUpdate($id: ID!, $input: MarketUpdateInput!) {
            marketUpdate(id: $id, input: $input) {
                market {
                    id
                    name
                    handle
                    currencySettings {
                        baseCurrency {
                            currencyCode
                        }
                    }
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """
        variables = {
            "id": market_instance.shopify_id,
            "input": {
                "name": market_instance.name,
                "handle": market_instance.handle,
            }
        }
        response, _extensions = client._execute(mutation, variables, include_extensions=True)
        result = response.get("marketUpdate", {})
    else:
        # Create new market
        mutation = """
        mutation marketCreate($input: MarketCreateInput!) {
            marketCreate(input: $input) {
                market {
                    id
                    name
                    handle
                    currencySettings {
                        baseCurrency {
                            currencyCode
                        }
                    }
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """
        variables = {
            "input": {
                "name": market_instance.name,
                "handle": market_instance.handle,
                "status": "ACTIVE" if market_instance.enabled else "INACTIVE",
            }
        }
        response, _extensions = client._execute(mutation, variables, include_extensions=True)
        result = response.get("marketCreate", {})
    
    # Handle errors
    user_errors = result.get("userErrors", [])
    if user_errors:
        error_messages = [f"{err.get('field')}: {err.get('message')}" for err in user_errors]
        log.error(f"Market sync errors: {error_messages}")
        raise Exception(f"Market sync failed: {', '.join(error_messages)}")
    
    # Update local instance with Shopify data
    market_data = result.get("market", {})
    if market_data:
        market_instance.shopify_id = market_data.get("id")
        market_instance.save()
        log.info(f"Market synced successfully: {market_instance.name} ({market_instance.shopify_id})")
    
    return result


def sync_publication(publication_instance) -> dict:
    """
    Synchronize a Publication instance with Shopify.
    Creates or updates the publication in Shopify.
    
    Args:
        publication_instance: Publication model instance
        
    Returns:
        dict: Response from Shopify with publication data and any errors
    """
    client = get_shopify_client()
    
    if publication_instance.shopify_id:
        # Update existing publication
        mutation = """
        mutation publicationUpdate($id: ID!, $input: PublicationUpdateInput!) {
            publicationUpdate(id: $id, input: $input) {
                publication {
                    id
                    autoPublish
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """
        variables = {
            "id": publication_instance.shopify_id,
            "input": {
                "autoPublish": publication_instance.auto_publish,
            }
        }
        response, _extensions = client._execute(mutation, variables, include_extensions=True)
        result = response.get("publicationUpdate", {})
    else:
        # Create new publication
        mutation = """
        mutation publicationCreate($input: PublicationCreateInput!) {
            publicationCreate(input: $input) {
                publication {
                    id
                    autoPublish
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """
        variables = {
            "input": {
                "autoPublish": publication_instance.auto_publish,
            }
        }
        response, _extensions = client._execute(mutation, variables, include_extensions=True)
        result = response.get("publicationCreate", {})
    
    # Handle errors
    user_errors = result.get("userErrors", [])
    if user_errors:
        error_messages = [f"{err.get('field')}: {err.get('message')}" for err in user_errors]
        log.error(f"Publication sync errors: {error_messages}")
        raise Exception(f"Publication sync failed: {', '.join(error_messages)}")
    
    # Update local instance with Shopify data
    publication_data = result.get("publication", {})
    if publication_data:
        publication_instance.shopify_id = publication_data.get("id")
        publication_instance.save()
        log.info(f"Publication synced successfully: {publication_instance.shopify_id}")
    
    return result


def sync_price_list(price_list_instance) -> dict:
    """
    Synchronize a PriceList instance with Shopify.
    Creates or updates the price list in Shopify.
    
    Note: When creating a PriceList, the 'parent' field is required by Shopify.
    If not provided in the instance, a default 0% adjustment is used.
    
    Args:
        price_list_instance: PriceList model instance
        
    Returns:
        dict: Response from Shopify with price list data and any errors
    """
    client = get_shopify_client()
    
    if price_list_instance.shopify_id:
        # Update existing price list
        mutation = """
        mutation priceListUpdate($id: ID!, $input: PriceListUpdateInput!) {
            priceListUpdate(id: $id, input: $input) {
                priceList {
                    id
                    name
                    currency
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """
        variables = {
            "id": price_list_instance.shopify_id,
            "input": {
                "name": price_list_instance.name,
            }
        }
        response, _extensions = client._execute(mutation, variables, include_extensions=True)
        result = response.get("priceListUpdate", {})
    else:
        # Create new price list
        mutation = """
        mutation priceListCreate($input: PriceListCreateInput!) {
            priceListCreate(input: $input) {
                priceList {
                    id
                    name
                    currency
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """
        # Build input - parent is REQUIRED for PriceList creation
        input_data = {
            "name": price_list_instance.name,
            "currency": price_list_instance.currency,
            "parent": {
                "adjustment": {
                    "type": "PERCENTAGE_DECREASE",
                    "value": 0.0
                }
            }
        }
        
        # Override with custom parent if provided
        if price_list_instance.parent and isinstance(price_list_instance.parent, dict):
            input_data["parent"] = price_list_instance.parent
        
        variables = {"input": input_data}
            
        response, _extensions = client._execute(mutation, variables, include_extensions=True)
        result = response.get("priceListCreate", {})
    
    # Handle errors
    user_errors = result.get("userErrors", [])
    if user_errors:
        error_messages = [f"{err.get('field')}: {err.get('message')}" for err in user_errors]
        log.error(f"PriceList sync errors: {error_messages}")
        raise Exception(f"PriceList sync failed: {', '.join(error_messages)}")
    
    # Update local instance with Shopify data
    price_list_data = result.get("priceList", {})
    if price_list_data:
        price_list_instance.shopify_id = price_list_data.get("id")
        price_list_instance.save()
        log.info(f"PriceList synced successfully: {price_list_instance.name} ({price_list_instance.shopify_id})")
    
    return result


def sync_catalog(catalog_instance, create_dependencies: bool = True) -> dict:
    """
    Synchronize a Catalog instance with Shopify.
    Creates or updates the catalog in Shopify.
    Optionally creates Publication and PriceList if they don't exist.
    
    Args:
        catalog_instance: Catalog model instance
        create_dependencies: If True, create Publication and PriceList if not provided
        
    Returns:
        dict: Response from Shopify with catalog data and any errors
    """
    from .models import Publication, PriceList
    
    client = get_shopify_client()
    
    # Create dependencies if needed
    if create_dependencies:
        if not catalog_instance.publication:
            publication = Publication.objects.create(auto_publish=False)
            sync_publication(publication)
            catalog_instance.publication = publication
            catalog_instance.save()
            
        if not catalog_instance.price_list:
            price_list = PriceList.objects.create(
                name=f"{catalog_instance.title} Price List",
                currency=catalog_instance.market.currency if catalog_instance.market else "USD"
            )
            sync_price_list(price_list)
            catalog_instance.price_list = price_list
            catalog_instance.save()
    
    if catalog_instance.shopify_id:
        # Update existing catalog
        mutation = """
        mutation catalogUpdate($id: ID!, $input: CatalogUpdateInput!) {
            catalogUpdate(id: $id, input: $input) {
                catalog {
                    id
                    title
                    status
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """
        variables = {
            "id": catalog_instance.shopify_id,
            "input": {
                "title": catalog_instance.title,
                "status": catalog_instance.status,
            }
        }
        response, _extensions = client._execute(mutation, variables, include_extensions=True)
        result = response.get("catalogUpdate", {})
    else:
        # Create new catalog
        mutation = """
        mutation catalogCreate($input: CatalogCreateInput!) {
            catalogCreate(input: $input) {
                catalog {
                    id
                    title
                    status
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """
        
        # Build context
        context = {}
        if catalog_instance.market and catalog_instance.market.shopify_id:
            context["marketIds"] = [catalog_instance.market.shopify_id]
        
        variables = {
            "input": {
                "title": catalog_instance.title,
                "status": catalog_instance.status,
                "context": context,
            }
        }
        
        # Add publication and price list if available
        if catalog_instance.publication and catalog_instance.publication.shopify_id:
            variables["input"]["publicationId"] = catalog_instance.publication.shopify_id
        if catalog_instance.price_list and catalog_instance.price_list.shopify_id:
            variables["input"]["priceListId"] = catalog_instance.price_list.shopify_id
            
        response, _extensions = client._execute(mutation, variables, include_extensions=True)
        result = response.get("catalogCreate", {})
    
    # Handle errors
    user_errors = result.get("userErrors", [])
    if user_errors:
        error_messages = [f"{err.get('field')}: {err.get('message')}" for err in user_errors]
        log.error(f"Catalog sync errors: {error_messages}")
        raise Exception(f"Catalog sync failed: {', '.join(error_messages)}")
    
    # Update local instance with Shopify data
    catalog_data = result.get("catalog", {})
    if catalog_data:
        catalog_instance.shopify_id = catalog_data.get("id")
        catalog_instance.save()
        log.info(f"Catalog synced successfully: {catalog_instance.title} ({catalog_instance.shopify_id})")
    
    return result


def sync_product_publication(product, publication, publish: bool = True) -> dict:
    """
    Publish or unpublish a product to/from a publication.
    
    Args:
        product: Product model instance
        publication: Publication model instance
        publish: If True, publish the product; if False, unpublish it
        
    Returns:
        dict: Response from Shopify
    """
    client = get_shopify_client()
    
    if not product.shopify_id:
        raise Exception(f"Product {product.title} has no shopify_id")
    
    if not publication.shopify_id:
        raise Exception(f"Publication has no shopify_id")
    
    if publish:
        mutation = """
        mutation publishablePublish($id: ID!, $input: [PublicationInput!]!) {
            publishablePublish(id: $id, input: $input) {
                publishable {
                    ... on Product {
                        id
                        title
                    }
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """
        variables = {
            "id": product.shopify_id,
            "input": [
                {
                    "publicationId": publication.shopify_id
                }
            ]
        }
        response, _extensions = client._execute(mutation, variables, include_extensions=True)
        result = response.get("publishablePublish", {})
        action = "published"
    else:
        mutation = """
        mutation publishableUnpublish($id: ID!, $input: [PublicationInput!]!) {
            publishableUnpublish(id: $id, input: $input) {
                publishable {
                    ... on Product {
                        id
                        title
                    }
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """
        variables = {
            "id": product.shopify_id,
            "input": [
                {
                    "publicationId": publication.shopify_id
                }
            ]
        }
        response, _extensions = client._execute(mutation, variables, include_extensions=True)
        result = response.get("publishableUnpublish", {})
        action = "unpublished"
    
    # Handle errors
    user_errors = result.get("userErrors", [])
    if user_errors:
        error_messages = [f"{err.get('field')}: {err.get('message')}" for err in user_errors]
        log.error(f"Product publication sync errors: {error_messages}")
        raise Exception(f"Product publication sync failed: {', '.join(error_messages)}")
    
    log.info(f"Product {product.title} {action} to publication {publication.shopify_id}")
    
    return result
