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
  Modal,
  TextContainer,
  Frame,
  BlockStack,
  InlineStack,
} from "@shopify/polaris";
import { TitleBar, useAppBridge } from "@shopify/app-bridge-react";
import { authenticate } from "../shopify.server";
import { createApiClient } from "../services/api";
import { ProductsService } from "../services/products";
import { useAppBridgeNavigation, useAppBridgeToast } from "../utils/appBridge";
import { ListLoadingState } from "../components/LoadingState";
import { ErrorBanner } from "../components/ErrorDisplay";
import { logError, formatErrorForDisplay } from "../utils/errors";
import { 
  generateListItemAriaLabel,
  generateActionButtonAriaLabel,
  generateStatusAriaLabel,
  announceToScreenReader,
  focusFirstAccessibleElement
} from "../utils/accessibility";

/**
 * Products List Loader
 * Fetches products with pagination, filtering, and sorting
 * Requirements: 8.1, 8.2, 8.3, 8.6, 8.7, 8.8
 */
export const loader = async ({ request }) => {
  try {
    const { sessionToken } = await authenticate.admin(request);
    const api = await createApiClient(request, sessionToken);
    const productsService = new ProductsService(api);

    // Parse query parameters
    const url = new URL(request.url);
    const page = parseInt(url.searchParams.get("page") || "1");
    const pageSize = parseInt(url.searchParams.get("pageSize") || "50");
    const title = url.searchParams.get("title") || undefined;
    const vendor = url.searchParams.get("vendor") || undefined;
    const productType = url.searchParams.get("productType") || undefined;
    const tags = url.searchParams.get("tags") || undefined;
    const ordering = url.searchParams.get("ordering") || undefined;

    // Fetch products with filters and sorting
    const data = await productsService.list({
      page,
      page_size: pageSize,
      title,
      vendor,
      product_type: productType,
      tags,
      ordering,
    });

    return {
      products: data.results,
      count: data.count,
      next: data.next,
      previous: data.previous,
      currentPage: page,
      pageSize,
      filters: {
        title,
        vendor,
        productType,
        tags,
        ordering,
      },
    };
  } catch (error) {
    logError(error, "Products.loader");
    throw error;
  }
};

/**
 * Products Action Handler
 * Handles bulk sync operations
 * Requirements: 8.9, 8.10, 8.11
 */
export const action = async ({ request }) => {
  if (request.method !== "POST") {
    return { success: false, error: "Invalid method" };
  }

  try {
    const { sessionToken } = await authenticate.admin(request);
    const api = await createApiClient(request, sessionToken);
    const productsService = new ProductsService(api);

    const formData = await request.formData();
    const actionType = formData.get("actionType");

    if (actionType === "bulk-sync") {
      const productIds = JSON.parse(formData.get("productIds") || "[]");
      const result = await productsService.bulkSync(productIds);
      return {
        success: true,
        action: "bulk-sync",
        result,
      };
    }

    return { success: false, error: "Unknown action" };
  } catch (error) {
    logError(error, "Products.action");
    return {
      success: false,
      error: error.message || "An error occurred",
    };
  }
};

/**
 * Products List Component
 * Displays products in an IndexTable with filters, sorting, and pagination
 * Responsive design for desktop, tablet, and mobile
 * Accessibility: ARIA labels, semantic HTML, keyboard navigation
 * Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9, 8.10, 8.11, 17.1, 17.2, 17.4, 17.5, 17.6
 */
export default function ProductsIndex() {
  const data = useLoaderData();
  const navigation = useNavigation();
  const revalidator = useRevalidator();
  const shopify = useAppBridge();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useAppBridgeNavigation();
  const toast = useAppBridgeToast();

  // State management
  const [selectedResources, setSelectedResources] = useState([]);
  const [showBulkSyncModal, setShowBulkSyncModal] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [error, setError] = useState(null);

  // Filter state
  const [titleFilter, setTitleFilter] = useState(data?.filters?.title || "");
  const [vendorFilter, setVendorFilter] = useState(data?.filters?.vendor || "");
  const [typeFilter, setTypeFilter] = useState(data?.filters?.productType || "");
  const [tagsFilter, setTagsFilter] = useState(data?.filters?.tags || "");
  const [sortOrder, setSortOrder] = useState(data?.filters?.ordering || "");

  const isLoading = navigation.state === "loading";

  // Handle filter changes
  const handleFilterChange = useCallback((filterName, value) => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set("page", "1"); // Reset to first page on filter change

    if (value) {
      newParams.set(filterName, value);
    } else {
      newParams.delete(filterName);
    }

    setSearchParams(newParams);
    // Announce filter change to screen readers
    announceToScreenReader(`Filtered by ${filterName}: ${value || "cleared"}`);
  }, [searchParams, setSearchParams]);

  // Handle sort change
  const handleSortChange = useCallback((value) => {
    setSortOrder(value);
    const newParams = new URLSearchParams(searchParams);
    newParams.set("page", "1");

    if (value) {
      newParams.set("ordering", value);
    } else {
      newParams.delete("ordering");
    }

    setSearchParams(newParams);
    // Announce sort change to screen readers
    announceToScreenReader(`Sorted by ${value || "default order"}`);
  }, [searchParams, setSearchParams]);

  // Handle pagination
  const handlePreviousPage = useCallback(() => {
    const newParams = new URLSearchParams(searchParams);
    const currentPage = parseInt(newParams.get("page") || "1");
    if (currentPage > 1) {
      newParams.set("page", String(currentPage - 1));
      setSearchParams(newParams);
      announceToScreenReader(`Navigated to page ${currentPage - 1}`);
    }
  }, [searchParams, setSearchParams]);

  const handleNextPage = useCallback(() => {
    const newParams = new URLSearchParams(searchParams);
    const currentPage = parseInt(newParams.get("page") || "1");
    newParams.set("page", String(currentPage + 1));
    setSearchParams(newParams);
    announceToScreenReader(`Navigated to page ${currentPage + 1}`);
  }, [searchParams, setSearchParams]);

  // Handle bulk sync with App Bridge toast
  const handleBulkSync = useCallback(async () => {
    setShowBulkSyncModal(false);
    setIsSyncing(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("actionType", "bulk-sync");
      formData.append("productIds", JSON.stringify(selectedResources.map(id => parseInt(id))));

      const response = await fetch(window.location.href, {
        method: "POST",
        body: formData,
      });

      const result = await response.json();

      if (result.success) {
        // Use App Bridge Toast instead of Polaris Toast
        const message = `Successfully synced ${result.result.success_count} product(s). ${result.result.error_count} failed.`;
        toast.success(message);
        announceToScreenReader(message, "assertive");
        setSelectedResources([]);
        revalidator.revalidate();
      } else {
        const errorMsg = result.error || "Sync failed";
        setError(errorMsg);
        toast.error(errorMsg);
        announceToScreenReader(errorMsg, "assertive");
        logError(errorMsg, "Products.handleBulkSync");
      }
    } catch (error) {
      const errorMsg = error.message || "An error occurred during sync";
      setError(errorMsg);
      toast.error(errorMsg);
      announceToScreenReader(errorMsg, "assertive");
      logError(error, "Products.handleBulkSync");
    } finally {
      setIsSyncing(false);
    }
  }, [selectedResources, revalidator, toast]);

  // Resource name for IndexTable
  const resourceName = {
    singular: "product",
    plural: "products",
  };

  // Build row markup with App Bridge navigation and accessibility
  const rowMarkup = useMemo(() => {
    return (data?.products || []).map((product, index) => (
      <IndexTable.Row
        id={product.id.toString()}
        key={product.id}
        position={index}
        selected={selectedResources.includes(product.id.toString())}
      >
        <IndexTable.Cell>
          <Button 
            onClick={() => navigate(`/app/products/${product.id}`)}
            variant="plain"
            aria-label={generateActionButtonAriaLabel("View details for", product.title)}
          >
            {product.title}
          </Button>
        </IndexTable.Cell>
        <IndexTable.Cell>{product.vendor || "-"}</IndexTable.Cell>
        <IndexTable.Cell>{product.product_type || "-"}</IndexTable.Cell>
        <IndexTable.Cell>{product.variant_count}</IndexTable.Cell>
        <IndexTable.Cell>
          <Badge
            tone={
              product.sync_status === "synced"
                ? "success"
                : product.sync_status === "error"
                  ? "critical"
                  : "warning"
            }
            aria-label={generateStatusAriaLabel(product.sync_status, product.title)}
          >
            {product.sync_status}
          </Badge>
        </IndexTable.Cell>
      </IndexTable.Row>
    ));
  }, [data?.products, selectedResources, navigate]);

  // Show loading skeleton
  if (isLoading) {
    return <ListLoadingState />;
  }

  // Show empty state
  if (!data?.products || data.products.length === 0) {
    return (
      <Page>
        <TitleBar title="Products" />
        <Layout>
          <Layout.Section>
            <EmptyState
              heading="No products yet"
              image="https://cdn.shopify.com/s/files/1/0262/4071/2726/files/emptystate-files.png"
            >
              <p>Start by importing products from your suppliers.</p>
            </EmptyState>
          </Layout.Section>
        </Layout>
      </Page>
    );
  }

  return (
    <Frame>
      <Page>
        <TitleBar title="Products" />
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

          {/* Filters Card - Responsive */}
          <Layout.Section>
            <Card>
              <BlockStack gap="300">
                <Filters
                  queryValue={titleFilter}
                  onQueryChange={(value) => {
                    setTitleFilter(value);
                    handleFilterChange("title", value);
                  }}
                  onQueryClear={() => {
                    setTitleFilter("");
                    handleFilterChange("title", "");
                  }}
                  filters={[
                    {
                      key: "vendor",
                      label: "Vendor",
                      filter: (
                        <ChoiceList
                          title="Vendor"
                          titleHidden
                          choices={[
                            { label: "All", value: "" },
                            { label: "Vendor A", value: "vendor-a" },
                            { label: "Vendor B", value: "vendor-b" },
                          ]}
                          selected={vendorFilter ? [vendorFilter] : [""]}
                          onChange={(value) => {
                            setVendorFilter(value[0] || "");
                            handleFilterChange("vendor", value[0] || "");
                          }}
                        />
                      ),
                    },
                  ]}
                  onClearAll={() => {
                    setTitleFilter("");
                    setVendorFilter("");
                    setTypeFilter("");
                    setTagsFilter("");
                    setSortOrder("");
                    setSearchParams(new URLSearchParams());
                    announceToScreenReader("All filters cleared");
                  }}
                >
                  <InlineStack gap="300" wrap={true}>
                    <ChoiceList
                      title="Sort By"
                      titleHidden
                      choices={[
                        { label: "Newest", value: "-created_at" },
                        { label: "Oldest", value: "created_at" },
                        { label: "Recently Updated", value: "-updated_at" },
                        { label: "Title A-Z", value: "title" },
                      ]}
                      selected={sortOrder ? [sortOrder] : []}
                      onChange={(value) => handleSortChange(value[0] || "")}
                    />
                  </InlineStack>
                </Filters>
              </BlockStack>
            </Card>
          </Layout.Section>

          {/* Products Table - Responsive with horizontal scroll on mobile */}
          <Layout.Section>
            <Card padding="0">
              <div style={{ overflowX: "auto", WebkitOverflowScrolling: "touch" }}>
                <IndexTable
                  resourceName={resourceName}
                  itemCount={data?.products?.length || 0}
                  selectedItemsCount={selectedResources.length}
                  onSelectionChange={(selected) => {
                    if (selected === "all") {
                      setSelectedResources(
                        data.products.map((p) => p.id.toString())
                      );
                      announceToScreenReader(`Selected all ${data.products.length} products`);
                    } else if (selected === "none") {
                      setSelectedResources([]);
                      announceToScreenReader("Deselected all products");
                    } else {
                      setSelectedResources(selected);
                      announceToScreenReader(`Selected ${selected.length} product(s)`);
                    }
                  }}
                  headings={[
                    { title: "Title" },
                    { title: "Vendor" },
                    { title: "Type" },
                    { title: "Variants" },
                    { title: "Status" },
                  ]}
                  promotedBulkActions={[
                    {
                      content: "Sync to Shopify",
                      onAction: () => {
                        setShowBulkSyncModal(true);
                        announceToScreenReader(`Ready to sync ${selectedResources.length} product(s)`);
                      },
                      disabled: selectedResources.length === 0 || isSyncing,
                    },
                  ]}
                >
                  {rowMarkup}
                </IndexTable>
              </div>
            </Card>
          </Layout.Section>

          {/* Pagination - Responsive */}
          <Layout.Section>
            <InlineStack align="center">
              <Pagination
                hasPrevious={!!data?.previous}
                hasNext={!!data?.next}
                onPrevious={handlePreviousPage}
                onNext={handleNextPage}
                label={`Page ${data?.currentPage || 1}`}
              />
            </InlineStack>
          </Layout.Section>
        </Layout>

        {/* Bulk Sync Modal - Accessible */}
        <Modal
          open={showBulkSyncModal}
          onClose={() => setShowBulkSyncModal(false)}
          title="Confirm Bulk Sync"
          primaryAction={{
            content: "Sync",
            onAction: handleBulkSync,
            loading: isSyncing,
          }}
          secondaryActions={[
            {
              content: "Cancel",
              onAction: () => setShowBulkSyncModal(false),
            },
          ]}
        >
          <Modal.Section>
            <TextContainer>
              <p>
                You are about to sync {selectedResources.length} product(s) to
                Shopify. This action cannot be undone.
              </p>
            </TextContainer>
          </Modal.Section>
        </Modal>
      </Page>
    </Frame>
  );
}