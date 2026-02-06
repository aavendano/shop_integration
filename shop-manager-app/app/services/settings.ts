/**
 * Settings Service
 * Handles all settings-related API operations
 */

import { ApiClient } from './api';
import { ShopSettings, SettingsSaveResult } from '../types/settings';

export class SettingsService {
  constructor(private api: ApiClient) {}

  async getSettings(): Promise<ShopSettings> {
    return this.api.get<ShopSettings>('/api/admin/settings/');
  }

  async saveSettings(settings: Partial<ShopSettings>): Promise<SettingsSaveResult> {
    return this.api.put('/api/admin/settings/', settings);
  }
}
