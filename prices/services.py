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
from shopify_client import ShopifyGraphQLClient
from shopify_client.exceptions import ShopifyClientError, ShopifyGraphQLError

logger = logging.getLogger(__name__)


def _get_graphql_client(session: Session) -> ShopifyGraphQLClient:
    return ShopifyGraphQLClient(
        session.site,
        session.token,
        settings.API_VERSION,
    )


def get_catalog_id_by_title(session: Session, title: str) -> Optional[str]:
    """Retrieve catalog ID by title using GraphQL."""
    client = _get_graphql_client(session)
    try:
        catalog = client.get_catalog_by_title(title)
    except ShopifyClientError as exc:
        logger.error(f"GraphQL error fetching catalog: {exc}")
        return None
    if not catalog:
        return None
    return catalog.get("id")


def get_price_list_id_by_name(session: Session, name: str) -> Optional[str]:
    """Retrieve price list ID by name using GraphQL (filtering in code)."""
    # priceLists query doesn't support 'query' filter, so we fetch and filter manually
    client = _get_graphql_client(session)
    try:
        price_list = client.get_price_list_by_name(name)
    except ShopifyClientError as exc:
        logger.error(f"GraphQL error fetching price list: {exc}")
        return None
    if not price_list:
        return None
    return price_list.get("id")


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
    client = _get_graphql_client(session)
    try:
        catalog = client.create_catalog(title=title, country_code=country_code)
    except ShopifyGraphQLError as exc:
        for error in exc.errors:
            logger.error(f"Catalog creation error: {error.get('message', str(exc))}")
        return None
    except ShopifyClientError as exc:
        logger.error(f"Error creating catalog: {exc}")
        return None
    if catalog:
        logger.info(f"Created catalog: {catalog['title']} ({catalog['id']})")
        return catalog["id"]
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
    client = _get_graphql_client(session)
    try:
        price_list = client.create_price_list(
            name=name,
            currency=currency,
            catalog_id=catalog_id,
        )
    except ShopifyGraphQLError as exc:
        for error in exc.errors:
            logger.error(f"Price list creation error: {error.get('message', str(exc))}")
        return None
    except ShopifyClientError as exc:
        logger.error(f"Error creating price list: {exc}")
        return None
    if price_list:
        logger.info(f"Created price list: {price_list['name']} ({price_list['id']})")
        return price_list["id"]
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
    # Check if already configured in settings
    if settings.SHOPIFY_CATALOG_ID and settings.SHOPIFY_PRICE_LIST_ID:
        logger.info("Using existing catalog and price list from settings")
        return settings.SHOPIFY_CATALOG_ID, settings.SHOPIFY_PRICE_LIST_ID, False
    
    catalog_id = settings.SHOPIFY_CATALOG_ID
    price_list_id = settings.SHOPIFY_PRICE_LIST_ID
    newly_created = False
    
    # 1. Get or Create Catalog
    if not catalog_id:
        title = settings.SHOPIFY_CATALOG_NAME
        
        # Check if exists
        logger.info(f"Checking for existing catalog: {title}")
        catalog_id = get_catalog_id_by_title(session, title)
        
        if catalog_id:
            logger.info(f"Found existing catalog: {catalog_id}")
        else:
            # Create new
            logger.info(f"Creating new catalog: {title}")
            catalog_id = create_catalog(
                session=session,
                title=title,
                country_code=settings.SHOPIFY_COUNTRY
            )
            if catalog_id:
                newly_created = True
    
    if not catalog_id:
        logger.error("Failed to get or create catalog")
        return None, None, False
    
    # 2. Get or Create Price List
    if not price_list_id:
        name = f"{settings.SHOPIFY_CATALOG_NAME} Pricing"
        
        # Check if exists
        logger.info(f"Checking for existing price list: {name}")
        price_list_id = get_price_list_id_by_name(session, name)
        
        if price_list_id:
            logger.info(f"Found existing price list: {price_list_id}")
        else:
            # Create new
            logger.info(f"Creating new price list: {name}")
            price_list_id = create_price_list(
                session=session,
                name=name,
                currency=settings.SHOPIFY_CURRENCY,
                catalog_id=catalog_id
            )
            if price_list_id:
                newly_created = True
    
    if not price_list_id:
        logger.error("Failed to get or create price list")
        return catalog_id, None, False
    
    return catalog_id, price_list_id, newly_created


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
    client = _get_graphql_client(session)
    # Prepare price inputs
    price_inputs = []
    for variant in variants:
        variant_id = getattr(variant, 'admin_graphql_api_id', None)
        
        # If no admin_graphql_api_id, try to construct from shopify_id
        if not variant_id and hasattr(variant, 'shopify_id') and variant.shopify_id:
            variant_id = f"gid://shopify/ProductVariant/{variant.shopify_id}"
            
        if not variant_id:
            logger.warning(f"Variant {variant.id} has no Shopify ID, skipping")
            continue
        
        price_input = {
            "variantId": variant_id,
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
            "errors": ["No valid variants to sync. Ensure product is synced to Shopify first."]
        }
    
    # Process in batches of 100 (Shopify limit)
    batch_size = 100
    total_success = 0
    total_errors = 0
    all_errors = []
    
    for i in range(0, len(price_inputs), batch_size):
        batch = price_inputs[i:i + batch_size]
        try:
            payload = client.sync_variant_prices(price_list_id, batch)
            prices = payload.get("prices", [])
            total_success += len(prices)
        except ShopifyGraphQLError as exc:
            errors = exc.errors or [{"message": str(exc)}]
            for error in errors:
                error_msg = error.get("message", str(exc))
                logger.error(f"Price sync error: {error_msg}")
                all_errors.append(error_msg)
            total_errors += len(errors) or len(batch)
        except ShopifyClientError as exc:
            error_msg = f"Batch {i//batch_size + 1} failed: {exc}"
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
