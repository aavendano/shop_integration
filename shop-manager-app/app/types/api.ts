/**
 * API Response Types
 * Defines TypeScript interfaces for all API responses from the Django backend
 */

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ApiError {
  detail: string;
  field_errors?: Record<string, string[]>;
}

export interface ShopContext {
  shop: {
    myshopify_domain: string;
    name: string;
    domain: string;
    currency: string;
  };
  user: {
    id: number;
    username: string;
    email: string;
  };
  permissions: {
    can_sync_products: boolean;
    can_manage_inventory: boolean;
    can_view_orders: boolean;
  };
}
