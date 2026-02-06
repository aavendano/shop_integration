import { useState, useEffect } from "react";
import { useLoaderData, useNavigation } from "@remix-run/react";
import {
  Page,
  Layout,
  Card,
  BlockStack,
  InlineStack,
  Text,
  Button,
} from "@shopify/polaris";
import { TitleBar } from "@shopify/app-bridge-react";
import { authenticate } from "../shopify.server";
import { createApiClient } from "../services/api";
import { ContextService } from "../services/context";
import { ProductsService } from "../services/products";
import { InventoryService } from "../services/inventory";
import { JobsService } from "../services/jobs";
import { DashboardLoadingState } from "../components/LoadingState";
import { ErrorBanner } from "../components/ErrorDisplay";
import { logError } from "../utils/errors";
import { 
  generateListItemAriaLabel, 
  announceToScreenReader 
} from "../utils/accessibility";

/**
 * Dashboard Loader
 * Fetches context, product count, pending sync count, inventory count, and recent jobs
 * Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6
 */
export const loader = async ({ request }) => {
  try {
    const { sessionToken } = await authenticate.admin(request);

    // Create API client with session token
    const api = await createApiClient(request, sessionToken);

    // Fetch all metrics in parallel with error handling
    const results = await Promise.allSettled([
      new ContextService(api).getContext(),
      new ProductsService(api).list({ page_size: 1 }),
      new InventoryService(api).list({ page_size: 1 }),
      new JobsService(api).list({ page_size: 5 }),
    ]);

    const [contextResult, productsResult, inventoryResult, jobsResult] = results;

    // Extract successful results or use defaults
    const context = contextResult.status === "fulfilled" ? contextResult.value : null;
    const products = productsResult.status === "fulfilled" ? productsResult.value : { count: 0, results: [] };
    const inventory = inventoryResult.status === "fulfilled" ? inventoryResult.value : { count: 0, results: [] };
    const jobs = jobsResult.status === "fulfilled" ? jobsResult.value : { results: [] };

    // Log any failures for debugging
    if (contextResult.status === "rejected") {
      logError(contextResult.reason, "Dashboard.loader.context");
    }
    if (productsResult.status === "rejected") {
      logError(productsResult.reason, "Dashboard.loader.products");
    }
    if (inventoryResult.status === "rejected") {
      logError(inventoryResult.reason, "Dashboard.loader.inventory");
    }
    if (jobsResult.status === "rejected") {
      logError(jobsResult.reason, "Dashboard.loader.jobs");
    }

    // Count products with pending sync status
    const pendingSyncCount = products.results.filter(
      (p) => p.sync_status === "pending"
    ).length;

    return {
      shop: context?.shop || { name: "Shop", domain: "example.com", currency: "USD" },
      user: context?.user || { id: 0, username: "User", email: "user@example.com" },
      metrics: {
        productCount: products.count,
        pendingSyncCount,
        inventoryCount: inventory.count,
        recentJobs: jobs.results,
      },
    };
  } catch (error) {
    logError(error, "Dashboard.loader");
    throw error;
  }
};

/**
 * Dashboard Component
 * Displays key metrics using Polaris Card components
 * Responsive design for desktop, tablet, and mobile
 * Accessibility: ARIA labels, semantic HTML, keyboard navigation
 * Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 17.1, 17.2, 17.4, 17.5, 17.6
 */
export default function Dashboard() {
  const data = useLoaderData();
  const navigation = useNavigation();
  const [error, setError] = useState(null);

  // Check for loader errors
  useEffect(() => {
    if (data?.error) {
      setError(data.error);
      logError(data.error, "Dashboard.component");
      // Announce error to screen readers
      announceToScreenReader(`Error: ${data.error}`, "assertive");
    }
  }, [data?.error]);

  const isLoading = navigation.state === "loading";

  // Show loading skeleton while fetching
  if (isLoading) {
    return <DashboardLoadingState />;
  }

  // Show error banner if there's an error
  if (error) {
    return (
      <Page>
        <TitleBar title="Dashboard" />
        <Layout>
          <Layout.Section>
            <ErrorBanner
              title="Error loading dashboard"
              message={error}
              onRetry={() => {
                setError(null);
                window.location.reload();
              }}
            />
          </Layout.Section>
        </Layout>
      </Page>
    );
  }

  if (!data || !data.shop || !data.metrics) {
    return (
      <Page>
        <TitleBar title="Dashboard" />
        <Layout>
          <Layout.Section>
            <ErrorBanner
              title="Dashboard data unavailable"
              message="Unable to load dashboard data. Please try refreshing the page."
              onRetry={() => window.location.reload()}
            />
          </Layout.Section>
        </Layout>
      </Page>
    );
  }

  const { shop, metrics } = data;

  return (
    <Page>
      <TitleBar title="Dashboard" />
      <Layout>
        {/* Shop Info Card - Responsive: Full width on all screens */}
        <Layout.Section>
          <Card>
            <BlockStack gap="300">
              <Text as="h2" variant="headingMd">
                Welcome to {shop.name}
              </Text>
              {/* Responsive inline stack - wraps on mobile */}
              <InlineStack 
                gap="300"
                wrap={true}
                blockAlign="start"
              >
                <BlockStack gap="100">
                  <Text 
                    as="span" 
                    variant="bodySmall" 
                    tone="subdued"
                    id="store-domain-label"
                  >
                    Store Domain
                  </Text>
                  <Text 
                    as="p" 
                    variant="bodyMd"
                    aria-labelledby="store-domain-label"
                  >
                    {shop.domain}
                  </Text>
                </BlockStack>
                <BlockStack gap="100">
                  <Text 
                    as="span" 
                    variant="bodySmall" 
                    tone="subdued"
                    id="currency-label"
                  >
                    Currency
                  </Text>
                  <Text 
                    as="p" 
                    variant="bodyMd"
                    aria-labelledby="currency-label"
                  >
                    {shop.currency}
                  </Text>
                </BlockStack>
              </InlineStack>
            </BlockStack>
          </Card>
        </Layout.Section>

        {/* Metric Cards - Responsive: 3 columns on desktop, 1 on mobile */}
        {/* Product Count Metric */}
        <Layout.Section variant="oneThird">
          <Card>
            <BlockStack gap="200">
              <Text 
                as="h3" 
                variant="headingMd"
                id="product-count-heading"
              >
                Total Products
              </Text>
              <Text 
                as="p" 
                variant="heading2xl"
                aria-labelledby="product-count-heading"
              >
                {metrics.productCount}
              </Text>
              <Button 
                url="/app/products" 
                variant="plain"
                aria-label={generateListItemAriaLabel(
                  `${metrics.productCount} products`,
                  "View products"
                )}
              >
                View Products
              </Button>
            </BlockStack>
          </Card>
        </Layout.Section>

        {/* Pending Sync Count Metric */}
        <Layout.Section variant="oneThird">
          <Card>
            <BlockStack gap="200">
              <Text 
                as="h3" 
                variant="headingMd"
                id="pending-sync-heading"
              >
                Pending Sync
              </Text>
              <Text 
                as="p" 
                variant="heading2xl"
                aria-labelledby="pending-sync-heading"
              >
                {metrics.pendingSyncCount}
              </Text>
              <Button 
                url="/app/products" 
                variant="plain"
                aria-label={generateListItemAriaLabel(
                  `${metrics.pendingSyncCount} products pending sync`,
                  "Sync now"
                )}
              >
                Sync Now
              </Button>
            </BlockStack>
          </Card>
        </Layout.Section>

        {/* Inventory Count Metric */}
        <Layout.Section variant="oneThird">
          <Card>
            <BlockStack gap="200">
              <Text 
                as="h3" 
                variant="headingMd"
                id="inventory-count-heading"
              >
                Inventory Items
              </Text>
              <Text 
                as="p" 
                variant="heading2xl"
                aria-labelledby="inventory-count-heading"
              >
                {metrics.inventoryCount}
              </Text>
              <Button 
                url="/app/inventory" 
                variant="plain"
                aria-label={generateListItemAriaLabel(
                  `${metrics.inventoryCount} inventory items`,
                  "Manage inventory"
                )}
              >
                Manage Inventory
              </Button>
            </BlockStack>
          </Card>
        </Layout.Section>

        {/* Recent Jobs Card - Full width, responsive */}
        <Layout.Section>
          <Card>
            <BlockStack gap="300">
              <Text 
                as="h3" 
                variant="headingMd"
                id="recent-jobs-heading"
              >
                Recent Jobs
              </Text>
              {metrics.recentJobs.length === 0 ? (
                <Text 
                  as="p" 
                  variant="bodyMd" 
                  tone="subdued"
                  aria-labelledby="recent-jobs-heading"
                >
                  No recent jobs
                </Text>
              ) : (
                <BlockStack 
                  gap="200"
                  role="list"
                  aria-labelledby="recent-jobs-heading"
                >
                  {metrics.recentJobs.map((job) => (
                    <InlineStack
                      key={job.id}
                      align="space-between"
                      blockAlign="center"
                      wrap={true}
                      role="listitem"
                      aria-label={generateListItemAriaLabel(
                        `${job.job_type} - ${job.status}`,
                        "Job"
                      )}
                    >
                      <BlockStack gap="100">
                        <Text as="p" variant="bodyMd">
                          {job.job_type}
                        </Text>
                        <Text 
                          as="span" 
                          variant="bodySmall" 
                          tone="subdued"
                        >
                          {new Date(job.started_at).toLocaleString()}
                        </Text>
                      </BlockStack>
                      <Text
                        as="span"
                        variant="bodyMd"
                        tone={
                          job.status === "completed"
                            ? "success"
                            : job.status === "failed"
                              ? "critical"
                              : "warning"
                        }
                        role="status"
                        aria-label={`Job status: ${job.status}`}
                      >
                        {job.status}
                      </Text>
                    </InlineStack>
                  ))}
                </BlockStack>
              )}
              <Button 
                url="/app/jobs" 
                variant="plain"
                aria-label="View all background jobs"
              >
                View All Jobs
              </Button>
            </BlockStack>
          </Card>
        </Layout.Section>
      </Layout>
    </Page>
  );
}
