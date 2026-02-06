import {
  Banner,
  Button,
  InlineError,
  BlockStack,
  Card,
  Layout,
  Page,
  Text,
} from "@shopify/polaris";
import { TitleBar } from "@shopify/app-bridge-react";

/**
 * ErrorDisplay Components
 * Provides consistent error display across the application
 * Requirements: 16.2, 16.3, 16.4, 16.7
 */

/**
 * Full-page error banner for critical errors
 */
export function ErrorBanner({
  title = "Error",
  message,
  onRetry,
  tone = "critical",
}) {
  return (
    <Banner tone={tone} title={title}>
      <BlockStack gap="200">
        <Text as="p" variant="bodyMd">
          {message}
        </Text>
        {onRetry && (
          <Button onClick={onRetry} variant="primary" size="slim">
            Retry
          </Button>
        )}
      </BlockStack>
    </Banner>
  );
}

/**
 * Page-level error display with retry option
 */
export function ErrorPage({
  title = "Error",
  message,
  onRetry,
  pageTitle = "Error",
}) {
  return (
    <Page>
      <TitleBar title={pageTitle} />
      <Layout>
        <Layout.Section>
          <ErrorBanner
            title={title}
            message={message}
            onRetry={onRetry}
            tone="critical"
          />
        </Layout.Section>
      </Layout>
    </Page>
  );
}

/**
 * Field-level validation error display
 */
export function FieldError({ error, label }) {
  if (!error) return null;

  return (
    <InlineError message={error} fieldID={label} />
  );
}

/**
 * Inline error message for forms
 */
export function FormError({ message, onDismiss }) {
  if (!message) return null;

  return (
    <Card>
      <BlockStack gap="200">
        <ErrorBanner
          title="Form Error"
          message={message}
          tone="warning"
        />
        {onDismiss && (
          <Button onClick={onDismiss} variant="plain" size="slim">
            Dismiss
          </Button>
        )}
      </BlockStack>
    </Card>
  );
}

/**
 * Network error specific display
 */
export function NetworkErrorBanner({ onRetry }) {
  return (
    <ErrorBanner
      title="Connection Error"
      message="Unable to connect to the server. Please check your connection and try again."
      onRetry={onRetry}
      tone="critical"
    />
  );
}

/**
 * Generic error fallback display
 */
export function GenericErrorBanner({ onRetry }) {
  return (
    <ErrorBanner
      title="Unexpected Error"
      message="An unexpected error occurred. Please try again or contact support if the problem persists."
      onRetry={onRetry}
      tone="critical"
    />
  );
}

/**
 * Validation errors display for multiple fields
 */
export function ValidationErrorsList({ errors }) {
  if (!errors || Object.keys(errors).length === 0) return null;

  return (
    <Card>
      <BlockStack gap="200">
        <Text as="h3" variant="headingMd">
          Please fix the following errors:
        </Text>
        <BlockStack gap="100">
          {Object.entries(errors).map(([field, messages]) => (
            <div key={field}>
              <Text as="p" variant="bodyMd" tone="critical">
                <strong>{field}:</strong> {Array.isArray(messages) ? messages.join(", ") : messages}
              </Text>
            </div>
          ))}
        </BlockStack>
      </BlockStack>
    </Card>
  );
}
