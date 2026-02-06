import { useState, useCallback } from "react";
import { useLoaderData, useNavigation, useFetcher } from "@remix-run/react";
import {
  Page,
  Layout,
  Card,
  Button,
  ChoiceList,
  SkeletonPage,
  SkeletonBodyText,
  Banner,
  BlockStack,
  InlineStack,
  Text,
} from "@shopify/polaris";
import { TitleBar } from "@shopify/app-bridge-react";
import { authenticate } from "../shopify.server";
import { createApiClient } from "../services/api";
import { SettingsService } from "../services/settings";
import { useAppBridgeToast } from "../utils/appBridge";

/**
 * Settings Loader
 * Fetches shop info and settings
 * Requirements: 12.1, 12.2, 12.3, 12.4, 12.5
 */
export const loader = async ({ request }) => {
  try {
    const { sessionToken } = await authenticate.admin(request);
    const api = await createApiClient(request, sessionToken);
    const settingsService = new SettingsService(api);

    // Fetch settings
    const settings = await settingsService.getSettings();

    return {
      settings,
    };
  } catch (error) {
    console.error("Settings loader error:", error);
    throw error;
  }
};

/**
 * Settings Action Handler
 * Handles save operations
 * Requirements: 12.6, 12.7, 12.8
 */
export const action = async ({ request }) => {
  if (request.method !== "POST") {
    return { success: false, error: "Invalid method" };
  }

  try {
    const { sessionToken } = await authenticate.admin(request);
    const api = await createApiClient(request, sessionToken);
    const settingsService = new SettingsService(api);

    const formData = await request.formData();
    const actionType = formData.get("actionType");

    if (actionType === "save-settings") {
      const settings = {
        sync_preferences: {
          auto_sync_enabled: formData.get("autoSyncEnabled") === "true",
          sync_frequency: formData.get("syncFrequency"),
        },
      };

      const result = await settingsService.saveSettings(settings);
      return {
        success: result.success,
        message: result.message,
        settings: result.settings,
      };
    }

    return { success: false, error: "Unknown action" };
  } catch (error) {
    console.error("Settings action error:", error);
    return {
      success: false,
      error: error.message || "An error occurred",
    };
  }
};

/**
 * Settings Component
 * Displays shop settings with pricing configuration and sync preferences
 * Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8
 */
export default function SettingsPage() {
  const data = useLoaderData();
  const navigation = useNavigation();
  const fetcher = useFetcher();
  const toast = useAppBridgeToast();

  // State management
  const [autoSyncEnabled, setAutoSyncEnabled] = useState(
    data?.settings?.sync_preferences?.auto_sync_enabled || false
  );
  const [syncFrequency, setSyncFrequency] = useState(
    data?.settings?.sync_preferences?.sync_frequency || "daily"
  );
  const [toastShown, setToastShown] = useState(false);

  const isLoading = navigation.state === "loading";
  const isSaving = fetcher.state === "submitting";

  // Handle save
  const handleSave = useCallback(() => {
    const formData = new FormData();
    formData.append("actionType", "save-settings");
    formData.append("autoSyncEnabled", String(autoSyncEnabled));
    formData.append("syncFrequency", syncFrequency);

    fetcher.submit(formData, { method: "post" });
  }, [autoSyncEnabled, syncFrequency, fetcher]);

  // Handle fetcher response with App Bridge toast
  if (fetcher.data && !toastShown) {
    setToastShown(true);
    if (fetcher.data.success) {
      toast.success(fetcher.data.message || "Settings saved successfully");
    } else {
      toast.error(fetcher.data.error || "Failed to save settings");
    }
    // Reset toast shown flag after a delay
    setTimeout(() => setToastShown(false), 5000);
  }

  // Show loading skeleton
  if (isLoading) {
    return (
      <SkeletonPage primaryAction>
        <Layout>
          <Layout.Section>
            <Card>
              <BlockStack gap="300">
                <SkeletonBodyText lines={2} />
              </BlockStack>
            </Card>
          </Layout.Section>
          <Layout.Section>
            <Card>
              <BlockStack gap="300">
                <SkeletonBodyText lines={5} />
              </BlockStack>
            </Card>
          </Layout.Section>
          <Layout.Section>
            <Card>
              <BlockStack gap="300">
                <SkeletonBodyText lines={5} />
              </BlockStack>
            </Card>
          </Layout.Section>
        </Layout>
      </SkeletonPage>
    );
  }

  if (!data || !data.settings) {
    return (
      <Page>
        <TitleBar title="Settings" />
        <Layout>
          <Layout.Section>
            <Banner tone="critical" title="Error loading settings">
              <p>Unable to load settings. Please try refreshing the page.</p>
              <Button onClick={() => window.location.reload()}>
                Retry
              </Button>
            </Banner>
          </Layout.Section>
        </Layout>
      </Page>
    );
  }

  const { settings } = data;

  return (
    <Page>
      <TitleBar title="Settings" />
      <Layout>
        {/* Shop Information Card - Requirements: 12.1, 12.2, 12.3 */}
        <Layout.Section>
          <Card>
            <BlockStack gap="300">
              <Text as="h2" variant="headingMd">
                Shop Information
              </Text>
              <InlineStack gap="300">
                <BlockStack gap="100">
                  <Text as="span" variant="bodySmall" tone="subdued">
                    Shop Name
                  </Text>
                  <Text as="p" variant="bodyMd">
                    {settings.name}
                  </Text>
                </BlockStack>
                <BlockStack gap="100">
                  <Text as="span" variant="bodySmall" tone="subdued">
                    Domain
                  </Text>
                  <Text as="p" variant="bodyMd">
                    {settings.domain}
                  </Text>
                </BlockStack>
                <BlockStack gap="100">
                  <Text as="span" variant="bodySmall" tone="subdued">
                    Currency
                  </Text>
                  <Text as="p" variant="bodyMd">
                    {settings.currency}
                  </Text>
                </BlockStack>
              </InlineStack>
            </BlockStack>
          </Card>
        </Layout.Section>

        {/* Pricing Configuration Card - Requirements: 12.4 */}
        <Layout.Section>
          <Card>
            <BlockStack gap="300">
              <Text as="h2" variant="headingMd">
                Pricing Configuration
              </Text>
              <InlineStack gap="300" align="space-between" blockAlign="center">
                <BlockStack gap="100">
                  <Text as="span" variant="bodySmall" tone="subdued">
                    Status
                  </Text>
                  <Text as="p" variant="bodyMd">
                    {settings.pricing_config_enabled ? "Enabled" : "Disabled"}
                  </Text>
                </BlockStack>
              </InlineStack>
            </BlockStack>
          </Card>
        </Layout.Section>

        {/* Sync Preferences Card - Requirements: 12.5 */}
        <Layout.Section>
          <Card>
            <BlockStack gap="300">
              <Text as="h2" variant="headingMd">
                Sync Preferences
              </Text>

              {/* Auto Sync Toggle */}
              <ChoiceList
                title="Auto Sync"
                choices={[
                  { label: "Enable automatic synchronization", value: "enabled" },
                ]}
                selected={autoSyncEnabled ? ["enabled"] : []}
                onChange={(value) => setAutoSyncEnabled(value.includes("enabled"))}
              />

              {/* Sync Frequency */}
              {autoSyncEnabled && (
                <ChoiceList
                  title="Sync Frequency"
                  choices={[
                    { label: "Hourly", value: "hourly" },
                    { label: "Daily", value: "daily" },
                    { label: "Weekly", value: "weekly" },
                  ]}
                  selected={[syncFrequency]}
                  onChange={(value) => setSyncFrequency(value[0])}
                />
              )}
            </BlockStack>
          </Card>
        </Layout.Section>

        {/* Save Button Card - Requirements: 12.6, 12.7, 12.8 */}
        <Layout.Section>
          <Card>
            <BlockStack gap="300">
              <Button
                variant="primary"
                onClick={handleSave}
                loading={isSaving}
                disabled={isSaving}
              >
                Save Settings
              </Button>
            </BlockStack>
          </Card>
        </Layout.Section>
      </Layout>
    </Page>
  );
}