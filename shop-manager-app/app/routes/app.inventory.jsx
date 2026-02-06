import { useState, useCallback, useMemo } from "react";
import { useLoaderData, useNavigation, useSearchParams, useRevalidator } from "@remix-run/react";
import {
  Page,
  Layout,
  Card,
  IndexTable,
  Badge,
  Button,
  Filters,
  ChoiceList,
  Pagination,
  EmptyState,
  Frame,
  BlockStack,
  InlineStack,
} from "@shopify/polaris";
import { TitleBar } from "@shopify/app-bridge-react";
import { authenticate } from "../shopify.server";
import { createApiClient } from "../services/api";
import { InventoryService } from "../services/inventory";
import { useAppBridgeToast } from "../utils/appBridge";
import { ListLoadingState } from "../components/LoadingState";
import { ErrorBanner } from "../components/ErrorDisplay";
import { logError } from "../utils/errors";

/**
 * Inventory List Loader
 * Fetches inventory items with pagination and filtering
 * Requirements: 10.1, 10.2, 10.3, 10.4
 */
export const loader = async ({ request }) => {
  try {
    const { sessionToken } = await authenticate.admin(request);
    const api = await createApiClient(request, sessionToken);
    const inventoryService = new InventoryService(api);

    // Parse query parameters
    const url = new URL(request.url);
    const page = parseInt(url.searchParams.get("page") || "1");
    const pageSize = parseInt(url.searchParams.get("pageSize") || "50");
    const productTitle = url.searchParams.get("productTitle") || undefined;
    const sku = url.searchParams.get("sku") || undefined;

    // Fetch inventory items with filters
    const data = await inventoryService.list({
      page,
      page_size: pageSize,
      product_title: productTitle,
      sku,
    });

    return {
      items: data.results,
      count: data.count,
      next: data.next,
      previous: data.previous,
      currentPage: page,
      pageSize,
      filters: {
        productTitle,
        sku,
      },
    };
  } catch (error) {
    logError(error, "Inventory.loader");
    throw error;
  }
};

/**
 * Inventory Action Handler
 * Handles reconcile operations
 * Requirements: 10.5, 10.6, 10.7
 */
export const action = async ({ request }) => {
  if (request.method !== "POST") {
    return { success: false, error: "Invalid method" };
  }

  try {
    const { sessionToken } = await authenticate.admin(request);
    const api = await createApiClient(request, sessionToken);
    const inventoryService = new InventoryService(api);

    const formData = await request.formData();
    const actionType = formData.get("actionType");

    if (actionType === "reconcile") {
      const result = await inventoryService.reconcile();
      return {
        success: true,
        action: "reconcile",
        result,
      };
    }

    return { success: false, error: "Unknown action" };
  } catch (error) {
    logError(error, "Inventory.action");
    return {
      success: false,
      error: error.message || "An error occurred",
    };
  }
};

/**
 * Inventory List Component
 * Displays inventory items in an IndexTable with filters and pagination
 * Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8
 */
export default function InventoryIndex() {
  const data = useLoaderData();
  const navigation = useNavigation();
  const revalidator = useRevalidator();
  const [searchParams, setSearchParams] = useSearchParams();
  const toast = useAppBridgeToast();

  // State management
  const [isReconciling, setIsReconciling] = useState(false);
  const [error, setError] = useState(null);

  // Filter state
  const [productTitleFilter, setProductTitleFilter] = useState(
    data?.filters?.productTitle || ""
  );
  const [skuFilter, setSkuFilter] = useState(data?.filters?.sku || "");

  const isLoading = navigation.state === "loading";

  // Handle filter changes
  const handleFilterChange = useCallback(
    (filterName, value) => {
      const newParams = new URLSearchParams(searchParams);
      newParams.set("page", "1"); // Reset to first page on filter change

      if (value) {
        newParams.set(filterName, value);
      } else {
        newParams.delete(filterName);
      }

      setSearchParams(newParams);
    },
    [searchParams, setSearchParams]
  );

  // Handle pagination
  const handlePreviousPage = useCallback(() => {
    const newParams = new URLSearchParams(searchParams);
    const currentPage = parseInt(newParams.get("page") || "1");
    if (currentPage > 1) {
      newParams.set("page", String(currentPage - 1));
      setSearchParams(newParams);
    }
  }, [searchParams, setSearchParams]);

  const handleNextPage = useCallback(() => {
    const newParams = new URLSearchParams(searchParams);
    const currentPage = parseInt(newParams.get("page") || "1");
    newParams.set("page", String(currentPage + 1));
    setSearchParams(newParams);
  }, [searchParams, setSearchParams]);

  // Handle reconcile action with App Bridge toast
  const handleReconcile = useCallback(async () => {
    setIsReconciling(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("actionType", "reconcile");

      const response = await fetch(window.location.href, {
        method: "POST",
        body: formData,
      });

      const result = await response.json();

      if (result.success) {
        toast.success(
          `Successfully reconciled ${result.result.reconciled_count} inventory item(s)`
        );
        revalidator.revalidate();
      } else {
        const errorMsg = result.error || "Reconciliation failed";
        setError(errorMsg);
        toast.error(errorMsg);
        logError(errorMsg, "Inventory.handleReconcile");
      }
    } catch (error) {
      const errorMsg = error.message || "An error occurred during reconciliation";
      setError(errorMsg);
      toast.error(errorMsg);
      logError(error, "Inventory.handleReconcile");
    } finally {
      setIsReconciling(false);
    }
  }, [revalidator, toast]);

  // Resource name for IndexTable
  const resourceName = {
    singular: "item",
    plural: "items",
  };

  // Build row markup
  const rowMarkup = useMemo(() => {
    return (data?.items || []).map((item, index) => (
      <IndexTable.Row
        id={item.id.toString()}
        key={item.id}
        position={index}
      >
        <IndexTable.Cell>{item.product_title || "-"}</IndexTable.Cell>
        <IndexTable.Cell>{item.variant_title || "-"}</IndexTable.Cell>
        <IndexTable.Cell>{item.sku || "-"}</IndexTable.Cell>
        <IndexTable.Cell>{item.source_quantity || 0}</IndexTable.Cell>
        <IndexTable.Cell>
          <Badge
            tone={
              item.sync_pending ? "warning" : "success"
            }
          >
            {item.sync_pending ? "pending" : "synced"}
          </Badge>
        </IndexTable.Cell>
      </IndexTable.Row>
    ));
  }, [data?.items]);

  // Show loading skeleton
  if (isLoading) {
    return <ListLoadingState />;
  }

  // Show empty state
  if (!data?.items || data.items.length === 0) {
    return (
      <Page>
        <TitleBar title="Inventory" />
        <Layout>
          <Layout.Section>
            <EmptyState
              heading="No inventory items yet"
              image="https://cdn.shopify.com/s/files/1/0262/4071/2726/files/emptystate-files.png"
            >
              <p>Start by importing products with tracked inventory.</p>
            </EmptyState>
          </Layout.Section>
        </Layout>
      </Page>
    );
  }

  return (
    <Frame>
      <Page>
        <TitleBar title="Inventory" />
        <Layout>
          {/* Error Banner */}
          {error && (
            <Layout.Section>
              <ErrorBanner
                title="Error"
                message={error}
                onRetry={() => setError(null)}
              />
            </Layout.Section>
          )}

          {/* Filters Card */}
          <Layout.Section>
            <Card>
              <BlockStack gap="300">
                <Filters
                  queryValue={productTitleFilter}
                  onQueryChange={(value) => {
                    setProductTitleFilter(value);
                    handleFilterChange("productTitle", value);
                  }}
                  onQueryClear={() => {
                    setProductTitleFilter("");
                    handleFilterChange("productTitle", "");
                  }}
                  filters={[
                    {
                      key: "sku",
                      label: "SKU",
                      filter: (
                        <ChoiceList
                          title="SKU"
                          titleHidden
                          choices={[
                            { label: "All", value: "" },
                          ]}
                          selected={skuFilter ? [skuFilter] : [""]}
                          onChange={(value) => {
                            setSkuFilter(value[0] || "");
                            handleFilterChange("sku", value[0] || "");
                          }}
                        />
                      ),
                    },
                  ]}
                  onClearAll={() => {
                    setProductTitleFilter("");
                    setSkuFilter("");
                    setSearchParams(new URLSearchParams());
                  }}
                />
              </BlockStack>
            </Card>
          </Layout.Section>

          {/* Inventory Table */}
          <Layout.Section>
            <Card padding="0">
              <IndexTable
                resourceName={resourceName}
                itemCount={data?.items?.length || 0}
                headings={[
                  { title: "Product" },
                  { title: "Variant" },
                  { title: "SKU" },
                  { title: "Quantity" },
                  { title: "Status" },
                ]}
              >
                {rowMarkup}
              </IndexTable>
            </Card>
          </Layout.Section>

          {/* Pagination */}
          <Layout.Section>
            <InlineStack align="center">
              <Pagination
                hasPrevious={!!data?.previous}
                hasNext={!!data?.next}
                onPrevious={handlePreviousPage}
                onNext={handleNextPage}
              />
            </InlineStack>
          </Layout.Section>

          {/* Reconcile Action Card */}
          <Layout.Section>
            <Card>
              <BlockStack gap="300">
                <Button
                  variant="primary"
                  onClick={handleReconcile}
                  loading={isReconciling}
                  disabled={isReconciling}
                >
                  Reconcile Inventory
                </Button>
              </BlockStack>
            </Card>
          </Layout.Section>
        </Layout>
      </Page>
    </Frame>
  );
}
