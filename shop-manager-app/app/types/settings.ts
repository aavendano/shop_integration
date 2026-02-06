/**
 * Settings Types
 * Defines TypeScript interfaces for settings-related data
 */

export interface ShopSettings {
  id: number;
  name: string;
  domain: string;
  currency: string;
  pricing_config_enabled: boolean;
  sync_preferences: {
    auto_sync_enabled: boolean;
    sync_frequency: 'hourly' | 'daily' | 'weekly' | 'manual';
  };
}

export interface SettingsSaveResult {
  success: boolean;
  message: string;
  settings?: ShopSettings;
}
