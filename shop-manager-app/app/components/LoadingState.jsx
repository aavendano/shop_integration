import {
  SkeletonPage,
  SkeletonBodyText,
  SkeletonThumbnail,
  Layout,
  Card,
  BlockStack,
} from "@shopify/polaris";

/**
 * LoadingState Component
 * Displays appropriate loading skeleton for different view types
 * Requirements: 16.1
 */

/**
 * Generic loading skeleton for list views
 */
export function ListLoadingState({ lines = 10 }) {
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
              <SkeletonBodyText lines={lines} />
            </BlockStack>
          </Card>
        </Layout.Section>
      </Layout>
    </SkeletonPage>
  );
}

/**
 * Loading skeleton for detail views
 */
export function DetailLoadingState() {
  return (
    <SkeletonPage primaryAction>
      <Layout>
        <Layout.Section>
          <Card>
            <BlockStack gap="300">
              <SkeletonBodyText lines={3} />
            </BlockStack>
          </Card>
        </Layout.Section>
        <Layout.Section>
          <Card>
            <BlockStack gap="300">
              <SkeletonThumbnail size="large" />
              <SkeletonBodyText lines={5} />
            </BlockStack>
          </Card>
        </Layout.Section>
      </Layout>
    </SkeletonPage>
  );
}

/**
 * Loading skeleton for dashboard
 */
export function DashboardLoadingState() {
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
        <Layout.Section variant="oneThird">
          <Card>
            <BlockStack gap="300">
              <SkeletonBodyText lines={2} />
            </BlockStack>
          </Card>
        </Layout.Section>
        <Layout.Section variant="oneThird">
          <Card>
            <BlockStack gap="300">
              <SkeletonBodyText lines={2} />
            </BlockStack>
          </Card>
        </Layout.Section>
        <Layout.Section variant="oneThird">
          <Card>
            <BlockStack gap="300">
              <SkeletonBodyText lines={2} />
            </BlockStack>
          </Card>
        </Layout.Section>
        <Layout.Section>
          <Card>
            <BlockStack gap="300">
              <SkeletonBodyText lines={3} />
            </BlockStack>
          </Card>
        </Layout.Section>
      </Layout>
    </SkeletonPage>
  );
}

/**
 * Loading skeleton for table rows
 */
export function TableRowLoadingState({ count = 5 }) {
  return (
    <SkeletonPage>
      <Layout>
        <Layout.Section>
          <Card>
            <BlockStack gap="300">
              {Array.from({ length: count }).map((_, i) => (
                <SkeletonBodyText key={i} lines={1} />
              ))}
            </BlockStack>
          </Card>
        </Layout.Section>
      </Layout>
    </SkeletonPage>
  );
}
