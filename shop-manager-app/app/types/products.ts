/**
 * Product Types
 * Defines TypeScript interfaces for product-related API responses
 */

export interface ProductListItem {
  id: number;
  title: string;
  vendor: string;
  product_type: string;
  tags: string;
  variant_count: number;
  sync_status: 'synced' | 'pending' | 'error';
  last_synced_at: string;
  created_at: string;
}

export interface ProductImage {
  id: number;
  src: string;
  position: number;
}

export interface ProductVariant {
  id: number;
  shopify_id: string;
  title: string;
  supplier_sku: string;
  price: string;
  compare_at_price: string | null;
  barcode: string | null;
  inventory_quantity: number | null;
  inventory_policy: string;
  option1: string | null;
  option2: string | null;
  option3: string | null;
}

export interface ProductDetail {
  id: number;
  shopify_id: string;
  title: string;
  description: string;
  vendor: string;
  product_type: string;
  tags: string;
  handle: string;
  images: ProductImage[];
  variants: ProductVariant[];
  sync_status: 'synced' | 'pending' | 'error';
  last_synced_at: string;
}

export interface SyncResult {
  success: boolean;
  message: string;
  synced_at?: string;
}

export interface BulkSyncResult {
  success_count: number;
  error_count: number;
  results: Array<{
    id: number;
    success: boolean;
    error?: string;
  }>;
}
