/**
 * Inventory Service
 * Handles all inventory-related API operations
 */

import { ApiClient } from './api';
import { InventoryItem, ReconcileResult } from '../types/inventory';
import { PaginatedResponse } from '../types/api';

export class InventoryService {
  constructor(private api: ApiClient) {}

  async list(params?: {
    page?: number;
    page_size?: number;
    product_title?: string;
    sku?: string;
  }): Promise<PaginatedResponse<InventoryItem>> {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          queryParams.append(key, String(value));
        }
      });
    }

    const endpoint = `/api/admin/inventory/?${queryParams.toString()}`;
    return this.api.get<PaginatedResponse<InventoryItem>>(endpoint);
  }

  async reconcile(): Promise<ReconcileResult> {
    return this.api.post('/api/admin/inventory/reconcile/');
  }
}
