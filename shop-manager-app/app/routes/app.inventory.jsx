import { Page, Text } from "@shopify/polaris";
import { TitleBar } from "@shopify/app-bridge-react";

export default function InventoryPage() {
  return (
    <Page>
      <TitleBar title="Inventory" />
      <Text as="p" variant="bodyMd">
        Embedded Inventory view placeholder.
      </Text>
    </Page>
  );
}