import { useState, useCallback } from "react";
import { useLoaderData, useNavigation, useParams } from "@remix-run/react";
import {
  Page,
  Layout,
  Card,
  Button,
  Badge,
  DataTable,
  Thumbnail,
  EmptyState,
  SkeletonPage,
  SkeletonBodyText,
  Frame,
  BlockStack,
  InlineStack,
  Text,
  Box,
  Divider,
} from "@shopify/polaris";
import { TitleBar, useAppBridge } from "@shopify/app-bridge-react";
import { authenticate } from "../shopify.server";
import { createApiClient } from "../services/api";
import { ProductsService } from "../services/products";
import { useAppBridgeNavigation, useAppBridgeToast } from "../utils/appBridge";
import { 
  generateStatusAriaLabel,
  generateActionButtonAriaLabel,
  announceToScreenReader
} from "../utils/accessibility";

/**
 * Product Detail Loader
 * Fetches product details including variants and images
 * Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6
 */
export const loader = async ({ request, params }) => {
  try {
    const { sessionToken } = await authenticate.admin(request);
    const api = await createApiClient(request, sessionToken);
    const productsService = new ProductsService(api);

    const productId = parseInt(params.id);
    if (isNaN(productId)) {
      throw new Error("Invalid product ID");
    }

    const product = await productsService.get(productId);
    return { product };
  } catch (error) {
    console.error("Product detail loader error:", error);
    throw error;
  }
};

/**
 * Product Detail Action Handler
 * Handles sync operations
 * Requirements: 9.7, 9.8, 9.9, 9.10
 */
export const action = async ({ request, params }) => {
  if (request.method !== "POST") {
    return { success: false, error: "Invalid method" };
  }

  try {
    const { sessionToken } = await authenticate.admin(request);
    const api = await createApiClient(request, sessionToken);
    const productsService = new ProductsService(api);

    const formData = await request.formData();
    const actionType = formData.get("actionType");

    if (actionType === "sync") {
      const productId = parseInt(params.id);
      const result = await productsService.sync(productId);
      return {
        success: true,
        action: "sync",
        result,
      };
    }

    return { success: false, error: "Unknown action" };
  } catch (error) {
    console.error("Product detail action error:", error);
    return {
      success: false,
      error: error.message || "An error occurred",
    };
  }
};

/**
 * Product Detail Component
 * Displays detailed product information including images, variants, and sync functionality
 * Responsive design for desktop, tablet, and mobile
 * Accessibility: ARIA labels, semantic HTML, keyboard navigation
 * Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8, 9.9, 9.10, 9.11, 9.12, 17.1, 17.2, 17.4, 17.5, 17.6
 */
export default function ProductDetail() {
  const data = useLoaderData();
  const navigation = useNavigation();
  const params = useParams();
  const shopify = useAppBridge();
  const navigate = useAppBridgeNavigation();
  const toast = useAppBridgeToast();

  // State management
  const [isSyncing, setIsSyncing] = useState(false);

  const isLoading = navigation.state === "loading";
  const product = data?.product;

  // Handle sync action with App Bridge toast
  const handleSync = useCallback(async () => {
    setIsSyncing(true);
    announceToScreenReader("Starting product sync", "assertive");

    try {
      const formData = new FormData();
      formData.append("actionType", "sync");

      const response = await fetch(window.location.href, {
        method: "POST",
        body: formData,
      });

      const result = await response.json();

      if (result.success) {
        const message = "Product synced successfully";
        toast.success(message);
        announceToScreenReader(message, "assertive");
        // Revalidate to get updated sync status
        window.location.reload();
      } else {
        const errorMsg = result.error || "Sync failed";
        toast.error(errorMsg);
        announceToScreenReader(errorMsg, "assertive");
      }
    } catch (error) {
      const errorMsg = error.message || "An error occurred during sync";
      toast.error(errorMsg);
      announceToScreenReader(errorMsg, "assertive");
    } finally {
      setIsSyncing(false);
    }
  }, [toast]);

  // Show loading skeleton
  if (isLoading) {
    return (
      <SkeletonPage>
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
                <SkeletonBodyText lines={5} />
              </BlockStack>
            </Card>
          </Layout.Section>
        </Layout>
      </SkeletonPage>
    );
  }

  // Show empty state if product not found
  if (!product) {
    return (
      <Page>
        <TitleBar title="Product Not Found" />
        <Layout>
          <Layout.Section>
            <EmptyState
              heading="Product not found"
              image="https://cdn.shopify.com/s/files/1/0262/4071/2726/files/emptystate-files.png"
            >
              <p>The product you're looking for doesn't exist or has been deleted.</p>
              <Button 
                onClick={() => navigate("/app/products")}
                variant="primary"
                aria-label="Return to products list"
              >
                Back to Products
              </Button>
            </EmptyState>
          </Layout.Section>
        </Layout>
      </Page>
    );
  }

  // Build variant table rows
  const variantRows = (product.variants || []).map((variant) => [
    variant.title || "-",
    variant.supplier_sku || "-",
    `${parseFloat(variant.price).toFixed(2)}`,
    variant.inventory_quantity !== null ? variant.inventory_quantity : "-",
    <Badge
      key={`${variant.id}-badge`}
      tone={product.sync_status === "synced" ? "success" : "warning"}
      aria-label={generateStatusAriaLabel(product.sync_status, variant.title)}
    >
      {product.sync_status}
    </Badge>,
  ]);

  // Build image thumbnails with accessibility
  const imageThumbnails = (product.images || []).map((image) => (
    <Box key={image.id} paddingInlineEnd="200">
      <Thumbnail 
        source={image.src} 
        alt={`Product image ${image.position}: ${product.title}`}
      />
    </Box>
  ));

  return (
    <Frame>
      <Page>
        <TitleBar title={product.title} />
        <Layout>
          {/* Product Information Card - Responsive */}
          <Layout.Section>
            <Card>
              <BlockStack gap="400">
                <div>
                  <Text 
                    variant="headingMd" 
                    as="h2"
                    id="product-info-heading"
                  >
                    Product Information
                  </Text>
                </div>
                <Divider />
                <BlockStack 
                  gap="200"
                  role="region"
                  aria-labelledby="product-info-heading"
                >
                  <InlineStack 
                    align="space-between"
                    wrap={true}
                    blockAlign="start"
                  >
                    <Text as="span" tone="subdued">
                      Title
                    </Text>
                    <Text as="span" fontWeight="semibold">
                      {product.title}
                    </Text>
                  </InlineStack>
                  <InlineStack 
                    align="space-between"
                    wrap={true}
                    blockAlign="start"
                  >
                    <Text as="span" tone="subdued">
                      Vendor
                    </Text>
                    <Text as="span" fontWeight="semibold">
                      {product.vendor || "-"}
                    </Text>
                  </InlineStack>
                  <InlineStack 
                    align="space-between"
                    wrap={true}
                    blockAlign="start"
                  >
                    <Text as="span" tone="subdued">
                      Type
                    </Text>
                    <Text as="span" fontWeight="semibold">
                      {product.product_type || "-"}
                    </Text>
                  </InlineStack>
                  <InlineStack 
                    align="space-between"
                    wrap={true}
                    blockAlign="start"
                  >
                    <Text as="span" tone="subdued">
                      Tags
                    </Text>
                    <Text as="span" fontWeight="semibold">
                      {product.tags || "-"}
                    </Text>
                  </InlineStack>
                  <InlineStack 
                    align="space-between"
                    wrap={true}
                    blockAlign="center"
                  >
                    <Text as="span" tone="subdued">
                      Sync Status
                    </Text>
                    <Badge
                      tone={
                        product.sync_status === "synced"
                          ? "success"
                          : product.sync_status === "error"
                            ? "critical"
                            : "warning"
                      }
                      aria-label={generateStatusAriaLabel(product.sync_status, "Product")}
                    >
                      {product.sync_status}
                    </Badge>
                  </InlineStack>
                </BlockStack>
              </BlockStack>
            </Card>
          </Layout.Section>

          {/* Description Card */}
          {product.description && (
            <Layout.Section>
              <Card>
                <BlockStack gap="400">
                  <div>
                    <Text 
                      variant="headingMd" 
                      as="h2"
                      id="description-heading"
                    >
                      Description
                    </Text>
                  </div>
                  <Divider />
                  <Text 
                    as="p"
                    role="region"
                    aria-labelledby="description-heading"
                  >
                    {product.description}
                  </Text>
                </BlockStack>
              </Card>
            </Layout.Section>
          )}

          {/* Images Card - Responsive */}
          {product.images && product.images.length > 0 && (
            <Layout.Section>
              <Card>
                <BlockStack gap="400">
                  <div>
                    <Text 
                      variant="headingMd" 
                      as="h2"
                      id="images-heading"
                    >
                      Images ({product.images.length})
                    </Text>
                  </div>
                  <Divider />
                  <InlineStack 
                    gap="300" 
                    wrap={true}
                    role="region"
                    aria-labelledby="images-heading"
                  >
                    {imageThumbnails}
                  </InlineStack>
                </BlockStack>
              </Card>
            </Layout.Section>
          )}

          {/* Variants Card - Responsive table with horizontal scroll on mobile */}
          <Layout.Section>
            <Card>
              <BlockStack gap="400">
                <div>
                  <Text 
                    variant="headingMd" 
                    as="h2"
                    id="variants-heading"
                  >
                    Variants ({product.variants?.length || 0})
                  </Text>
                </div>
                <Divider />
                {product.variants && product.variants.length > 0 ? (
                  <div 
                    style={{ 
                      overflowX: "auto", 
                      WebkitOverflowScrolling: "touch" 
                    }}
                    role="region"
                    aria-labelledby="variants-heading"
                  >
                    <DataTable
                      columnContentTypes={[
                        "text",
                        "text",
                        "numeric",
                        "numeric",
                        "text",
                      ]}
                      headings={[
                        "Title",
                        "SKU",
                        "Price",
                        "Inventory",
                        "Status",
                      ]}
                      rows={variantRows}
                    />
                  </div>
                ) : (
                  <Text as="p" tone="subdued">
                    No variants available
                  </Text>
                )}
              </BlockStack>
            </Card>
          </Layout.Section>

          {/* Sync Action Card */}
          <Layout.Section>
            <Card>
              <BlockStack gap="400">
                <div>
                  <Text 
                    variant="headingMd" 
                    as="h2"
                    id="sync-heading"
                  >
                    Sync to Shopify
                  </Text>
                </div>
                <Divider />
                <Text 
                  as="p" 
                  tone="subdued"
                  role="region"
                  aria-labelledby="sync-heading"
                >
                  Synchronize this product with your Shopify store.
                </Text>
                <Button
                  variant="primary"
                  onClick={handleSync}
                  loading={isSyncing}
                  disabled={isSyncing}
                  aria-label={generateActionButtonAriaLabel("Sync", product.title)}
                >
                  Sync Product
                </Button>
              </BlockStack>
            </Card>
          </Layout.Section>

          {/* Back Button */}
          <Layout.Section>
            <Button 
              onClick={() => navigate("/app/products")}
              variant="secondary"
              aria-label="Return to products list"
            >
              Back to Products
            </Button>
          </Layout.Section>
        </Layout>
      </Page>
    </Frame>
  );
}
