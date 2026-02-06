import { Page, Text } from "@shopify/polaris";
import { TitleBar } from "@shopify/app-bridge-react";

export default function AdditionalPage() {
  return (
    <Page>
      <TitleBar title="Additional" />
      <Text as="p" variant="bodyMd">
        Placeholder page for embedded navigation.
      </Text>
    </Page>
  );
}
