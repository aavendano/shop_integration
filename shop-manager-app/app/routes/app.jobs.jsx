import { Page, Text } from "@shopify/polaris";
import { TitleBar } from "@shopify/app-bridge-react";

export default function JobsPage() {
  return (
    <Page>
      <TitleBar title="Jobs" />
      <Text as="p" variant="bodyMd">
        Embedded Jobs view placeholder.
      </Text>
    </Page>
  );
}