/**
 * Inventory Types
 * Defines TypeScript interfaces for inventory-related API responses
 */

export interface InventoryItem {
  id: number;
  product_title: string;
  variant_title: string;
  sku: string;
  source_quantity: number;
  tracked: boolean;
  sync_pending: boolean;
  last_synced_at: string;
}

export interface ReconcileResult {
  success: boolean;
  reconciled_count: number;
  message: string;
}
