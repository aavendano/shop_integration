/**
 * Context Service
 * Handles retrieval of shop context and user information from the API
 */

import { ApiClient } from './api';
import { ShopContext } from '../types/api';

export class ContextService {
  constructor(private api: ApiClient) {}

  async getContext(): Promise<ShopContext> {
    return this.api.get<ShopContext>('/api/admin/context/');
  }
}
