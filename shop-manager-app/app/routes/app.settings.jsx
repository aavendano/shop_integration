import { Page, Text } from "@shopify/polaris";
import { TitleBar } from "@shopify/app-bridge-react";

export default function SettingsPage() {
  return (
    <Page>
      <TitleBar title="Settings" />
      <Text as="p" variant="bodyMd">
        Embedded Settings view placeholder.
      </Text>
    </Page>
  );
}