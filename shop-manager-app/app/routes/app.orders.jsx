import { Page, Text } from "@shopify/polaris";
import { TitleBar } from "@shopify/app-bridge-react";

export default function OrdersPage() {
  return (
    <Page>
      <TitleBar title="Orders" />
      <Text as="p" variant="bodyMd">
        Embedded Orders view placeholder.
      </Text>
    </Page>
  );
}