import { Page, Text } from "@shopify/polaris";
import { TitleBar } from "@shopify/app-bridge-react";

export default function ProductsIndex() {
  return (
    <Page>
      <TitleBar title="Products" />
      <Text as="p" variant="bodyMd">
        Embedded Products view placeholder.
      </Text>
    </Page>
  );
}