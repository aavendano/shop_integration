"""
Pricing Service for Shopify Contextual Pricing

This service manages Catalogs, Price Lists, and contextual pricing for product variants.
It uses Shopify's GraphQL Admin API to create and manage price lists based on country
and provider context.
"""

import logging
from typing import Dict, List, Tuple, Optional
from django.conf import settings
from accounts.models import Session

logger = logging.getLogger(__name__)


def execute_graphql(session: Session, query: str, variables: dict = None) -> dict:
    """
    Execute a GraphQL query against Shopify Admin API.
    
    Args:
        session: Shopify session with token and site
        query: GraphQL query/mutation string
        variables: Optional variables for the query
    
    Returns:
        Response data dict
    """
    import requests
    
    url = f"https://{session.site}/admin/api/{settings.API_VERSION}/graphql.json"
    
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": session.token
    }
    
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Check for GraphQL errors
        if "errors" in data:
            for error in data["errors"]:
                logger.error(f"GraphQL error: {error.get('message', 'Unknown error')}")
            return {"errors": data["errors"]}
        
        return data.get("data", {})
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        return {"errors": [{"message": str(e)}]}
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {"errors": [{"message": str(e)}]}


def create_catalog(session: Session, title: str, country_code: str) -> Optional[str]:
    """
    Create a new Catalog in Shopify.
    
    Args:
        session: Shopify session
        title: Catalog title (e.g., "US-NALPAC")
        country_code: Country code (e.g., "US")
    
    Returns:
        Catalog GID if successful, None otherwise
    """
    mutation = """
    mutation CreateCatalog($input: CatalogCreateInput!) {
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
    
    variables = {
        "input": {
            "title": title,
            "status": "ACTIVE",
            "context": {
                # Must provide exactly one context type
                # Using empty marketIds array for a general catalog
                "marketIds": []
            }
        }
    }
    
    try:
        response = execute_graphql(session, mutation, variables)
        
        if response.get("userErrors"):
            for error in response["userErrors"]:
                logger.error(f"Catalog creation error: {error['message']}")
            return None
        
        catalog = response.get("catalogCreate", {}).get("catalog")
        if catalog:
            logger.info(f"Created catalog: {catalog['title']} ({catalog['id']})")
            return catalog["id"]
        
        return None
        
    except Exception as e:
        logger.error(f"Error creating catalog: {str(e)}")
        return None


def create_price_list(
    session: Session,
    name: str,
    currency: str,
    catalog_id: Optional[str] = None
) -> Optional[str]:
    """
    Create a new Price List in Shopify.
    
    Args:
        session: Shopify session
        name: Price list name (e.g., "US-NALPAC Pricing")
        currency: Currency code (e.g., "USD")
        catalog_id: Optional catalog ID to associate with
    
    Returns:
        Price List GID if successful, None otherwise
    """
    mutation = """
    mutation CreatePriceList($input: PriceListCreateInput!) {
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
    
    variables = {
        "input": {
            "name": name,
            "currency": currency,
            "parent": {
                "adjustment": {
                    "type": "PERCENTAGE_DECREASE",
                    "value": 0.0
                }
            }
        }
    }
    
    # Add catalog association if provided
    if catalog_id:
        variables["input"]["catalogId"] = catalog_id
    
    try:
        response = execute_graphql(session, mutation, variables)
        
        if response.get("userErrors"):
            for error in response["userErrors"]:
                logger.error(f"Price list creation error: {error['message']}")
            return None
        
        price_list = response.get("priceListCreate", {}).get("priceList")
        if price_list:
            logger.info(f"Created price list: {price_list['name']} ({price_list['id']})")
            return price_list["id"]
        
        return None
        
    except Exception as e:
        logger.error(f"Error creating price list: {str(e)}")
        return None


def get_or_create_catalog_and_price_list(session: Session) -> Tuple[Optional[str], Optional[str], bool]:
    """
    Get existing or create new Catalog and Price List based on settings.
    
    Args:
        session: Shopify session
    
    Returns:
        Tuple of (catalog_id, price_list_id, created)
        - catalog_id: Catalog GID
        - price_list_id: Price List GID
        - created: True if newly created, False if existing
    """
    # Check if already configured
    if settings.SHOPIFY_CATALOG_ID and settings.SHOPIFY_PRICE_LIST_ID:
        logger.info("Using existing catalog and price list from settings")
        return settings.SHOPIFY_CATALOG_ID, settings.SHOPIFY_PRICE_LIST_ID, False
    
    # Create new catalog
    catalog_id = create_catalog(
        session=session,
        title=settings.SHOPIFY_CATALOG_NAME,
        country_code=settings.SHOPIFY_COUNTRY
    )
    
    if not catalog_id:
        logger.error("Failed to create catalog")
        return None, None, False
    
    # Create new price list
    price_list_id = create_price_list(
        session=session,
        name=f"{settings.SHOPIFY_CATALOG_NAME} Pricing",
        currency=settings.SHOPIFY_CURRENCY,
        catalog_id=catalog_id
    )
    
    if not price_list_id:
        logger.error("Failed to create price list")
        return catalog_id, None, False
    
    return catalog_id, price_list_id, True


def sync_variant_prices(
    session: Session,
    price_list_id: str,
    variants: List
) -> Dict[str, any]:
    """
    Bulk sync prices for multiple variants to a Price List.
    
    Args:
        session: Shopify session
        price_list_id: Price List GID
        variants: List of Variant model instances
    
    Returns:
        Dict with success_count, error_count, and errors list
    """
    mutation = """
    mutation AddFixedPrices($priceListId: ID!, $prices: [PriceListPriceInput!]!) {
      priceListFixedPricesAdd(priceListId: $priceListId, prices: $prices) {
        prices {
          price {
            amount
            currencyCode
          }
          variant {
            id
          }
        }
        userErrors {
          field
          message
        }
      }
    }
    """
    
    # Prepare price inputs
    price_inputs = []
    for variant in variants:
        if not variant.admin_graphql_api_id:
            logger.warning(f"Variant {variant.id} has no Shopify GID, skipping")
            continue
        
        price_input = {
            "variantId": variant.admin_graphql_api_id,
            "price": {
                "amount": str(variant.price),
                "currencyCode": settings.SHOPIFY_CURRENCY
            }
        }
        
        # Add compare at price if available
        if variant.compare_at_price:
            price_input["compareAtPrice"] = {
                "amount": str(variant.compare_at_price),
                "currencyCode": settings.SHOPIFY_CURRENCY
            }
        
        price_inputs.append(price_input)
    
    if not price_inputs:
        return {
            "success_count": 0,
            "error_count": 0,
            "errors": ["No valid variants to sync"]
        }
    
    # Process in batches of 100 (Shopify limit)
    batch_size = 100
    total_success = 0
    total_errors = 0
    all_errors = []
    
    for i in range(0, len(price_inputs), batch_size):
        batch = price_inputs[i:i + batch_size]
        
        variables = {
            "priceListId": price_list_id,
            "prices": batch
        }
        
        try:
            response = execute_graphql(session, mutation, variables)
            
            if response.get("errors"):
                for error in response["errors"]:
                    error_msg = error.get('message', 'Unknown error')
                    logger.error(f"Price sync error: {error_msg}")
                    all_errors.append(error_msg)
                    total_errors += len(batch)
                continue
            
            if response.get("userErrors"):
                for error in response["userErrors"]:
                    error_msg = f"{error.get('field', 'unknown')}: {error['message']}"
                    logger.error(f"Price sync error: {error_msg}")
                    all_errors.append(error_msg)
                    total_errors += 1
            
            prices = response.get("priceListFixedPricesAdd", {}).get("prices", [])
            total_success += len(prices)
            
        except Exception as e:
            error_msg = f"Batch {i//batch_size + 1} failed: {str(e)}"
            logger.error(error_msg)
            all_errors.append(error_msg)
            total_errors += len(batch)
    
    logger.info(f"Synced {total_success} variant prices, {total_errors} errors")
    
    return {
        "success_count": total_success,
        "error_count": total_errors,
        "errors": all_errors
    }


def sync_product_prices(
    session: Session,
    price_list_id: str,
    product
) -> Dict[str, any]:
    """
    Sync all variant prices for a product to a Price List.
    
    Args:
        session: Shopify session
        price_list_id: Price List GID
        product: Product model instance
    
    Returns:
        Dict with success_count, error_count, and errors list
    """
    variants = list(product.variants.all())
    
    if not variants:
        return {
            "success_count": 0,
            "error_count": 0,
            "errors": ["Product has no variants"]
        }
    
    return sync_variant_prices(session, price_list_id, variants)
