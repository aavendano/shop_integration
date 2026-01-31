"""
Custom template tags and filters for Shopify models
"""
from django import template
import json
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def placeholder(value, default="—"):
    """
    Return placeholder if value is None or empty
    
    Usage: {{ product.vendor|placeholder:"N/A" }}
    """
    if value is None or value == "":
        return default
    return value


@register.filter
def format_json(value, indent=2):
    """
    Format JSON field for display with proper indentation
    
    Usage: {{ inventory_level.quantities|format_json }}
    """
    if not value:
        return "—"
    try:
        if isinstance(value, str):
            value = json.loads(value)
        return json.dumps(value, indent=indent, ensure_ascii=False)
    except (json.JSONDecodeError, TypeError):
        return str(value)


@register.filter
def boolean_badge(value):
    """
    Return Bulma badge for boolean values
    
    Usage: {{ variant.taxable|boolean_badge }}
    """
    if value:
        return mark_safe('<span class="tag is-success is-light">Yes</span>')
    return mark_safe('<span class="tag is-light">No</span>')


@register.filter
def sync_status_badge(value):
    """
    Return badge for sync status (pending or synced)
    
    Usage: {{ inventory_level.sync_pending|sync_status_badge }}
    """
    if value:
        return mark_safe('<span class="tag is-warning is-light"><span class="icon is-small"><i class="lucide-clock"></i></span><span>Pending</span></span>')
    return mark_safe('<span class="tag is-success is-light"><span class="icon is-small"><i class="lucide-check"></i></span><span>Synced</span></span>')


@register.filter
def active_badge(value):
    """
    Return badge for active/inactive status
    
    Usage: {{ location.is_active|active_badge }}
    """
    if value:
        return mark_safe('<span class="tag is-success">Active</span>')
    return mark_safe('<span class="tag is-light">Inactive</span>')


@register.filter
def currency(value, currency_code="USD"):
    """
    Format decimal value as currency
    
    Usage: {{ variant.price|currency:"USD" }}
    """
    if value is None:
        return "—"
    try:
        return f"${float(value):,.2f} {currency_code}"
    except (ValueError, TypeError):
        return str(value)


@register.filter
def format_weight(grams):
    """
    Format weight in grams to a readable format
    
    Usage: {{ variant.grams|format_weight }}
    """
    if grams is None:
        return "—"
    try:
        grams = float(grams)
        if grams >= 1000:
            return f"{grams/1000:.2f} kg"
        return f"{grams:.0f} g"
    except (ValueError, TypeError):
        return str(grams)


@register.filter
def format_address(address_json):
    """
    Format address JSON field as readable address
    
    Usage: {{ location.address|format_address }}
    """
    if not address_json:
        return "—"
    
    try:
        if isinstance(address_json, str):
            address = json.loads(address_json)
        else:
            address = address_json
        
        parts = []
        if address.get('address1'):
            parts.append(address['address1'])
        if address.get('address2'):
            parts.append(address['address2'])
        if address.get('city'):
            parts.append(address['city'])
        if address.get('province'):
            parts.append(address['province'])
        if address.get('zip'):
            parts.append(address['zip'])
        if address.get('country'):
            parts.append(address['country'])
        
        return ', '.join(parts) if parts else "—"
    except (json.JSONDecodeError, TypeError, AttributeError):
        return str(address_json)


@register.filter
def shopify_id_badge(shopify_id):
    """
    Display Shopify ID with appropriate badge
    
    Usage: {{ product.shopify_id|shopify_id_badge }}
    """
    if shopify_id:
        return mark_safe(f'<span class="tag is-info is-light"><span class="icon is-small"><i class="lucide-link"></i></span><span>{shopify_id}</span></span>')
    return mark_safe('<span class="tag is-warning is-light"><span class="icon is-small"><i class="lucide-alert-circle"></i></span><span>Not synced</span></span>')


@register.filter
def truncate_id(value, length=8):
    """
    Truncate long IDs for display
    
    Usage: {{ product.shopify_id|truncate_id:12 }}
    """
    if not value:
        return "—"
    value_str = str(value)
    if len(value_str) > length:
        return f"{value_str[:length]}..."
    return value_str
