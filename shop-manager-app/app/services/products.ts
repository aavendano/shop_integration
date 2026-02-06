/**
 * Products Service
 * Handles all product-related API operations
 */

import { ApiClient } from './api';
import {
  ProductListItem,
  ProductDetail,
  SyncResult,
  BulkSyncResult,
} from '../types/products';
import { PaginatedResponse } from '../types/api';

export class ProductsService {
  constructor(private api: ApiClient) {}

  async list(params?: {
    page?: number;
    page_size?: number;
    title?: string;
    vendor?: string;
    product_type?: string;
    tags?: string;
    ordering?: string;
  }): Promise<PaginatedResponse<ProductListItem>> {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          queryParams.append(key, String(value));
        }
      });
    }

    const endpoint = `/api/admin/products/?${queryParams.toString()}`;
    return this.api.get<PaginatedResponse<ProductListItem>>(endpoint);
  }

  async get(id: number): Promise<ProductDetail> {
    return this.api.get<ProductDetail>(`/api/admin/products/${id}/`);
  }

  async sync(id: number): Promise<SyncResult> {
    return this.api.post(`/api/admin/products/${id}/sync/`);
  }

  async bulkSync(productIds: number[]): Promise<BulkSyncResult> {
    return this.api.post('/api/admin/products/bulk-sync/', {
      product_ids: productIds,
    });
  }
}
