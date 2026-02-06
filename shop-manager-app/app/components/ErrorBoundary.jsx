import { Component } from 'react';
import { Page, Layout, Banner, Button, BlockStack, Text } from '@shopify/polaris';
import { TitleBar } from '@shopify/app-bridge-react';
import { logger } from '../utils/logger';
import { sanitizeErrorMessage } from '../utils/errors';

/**
 * ErrorBoundary Component
 * Catches and displays unexpected errors in the application
 * Requirements: 16.7
 */
export class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
    };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Generate unique error ID for tracking
    const errorId = `ERR_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    // Log error with full details
    logger.error(
      'ErrorBoundary',
      'Uncaught error in component tree',
      error,
      {
        errorId,
        componentStack: errorInfo.componentStack,
      }
    );

    this.setState({
      error,
      errorInfo,
      errorId,
    });
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
    });
  };

  render() {
    if (this.state.hasError) {
      const sanitizedMessage = sanitizeErrorMessage(this.state.error);

      return (
        <Page>
          <TitleBar title="Error" />
          <Layout>
            <Layout.Section>
              <Banner tone="critical" title="Something went wrong">
                <BlockStack gap="200">
                  <Text as="p" variant="bodyMd">
                    An unexpected error occurred. Please try refreshing the page or contact support if the problem persists.
                  </Text>
                  <Text as="p" variant="bodySmall" tone="subdued">
                    Error ID: {this.state.errorId}
                  </Text>
                  {process.env.NODE_ENV === 'development' && (
                    <details style={{ marginTop: '16px', padding: '8px', backgroundColor: '#f5f5f5', borderRadius: '4px' }}>
                      <summary style={{ cursor: 'pointer', fontWeight: 'bold' }}>
                        Error Details (Development Only)
                      </summary>
                      <pre style={{ marginTop: '8px', overflow: 'auto', fontSize: '12px' }}>
                        {sanitizedMessage}
                        {this.state.errorInfo && `\n\n${this.state.errorInfo.componentStack}`}
                      </pre>
                    </details>
                  )}
                  <BlockStack gap="100">
                    <Button onClick={this.handleReset} variant="primary">
                      Try Again
                    </Button>
                    <Button onClick={() => window.location.href = '/'} variant="plain">
                      Go to Home
                    </Button>
                  </BlockStack>
                </BlockStack>
              </Banner>
            </Layout.Section>
          </Layout>
        </Page>
      );
    }

    return this.props.children;
  }
}

/**
 * Error Fallback Component
 * Used with React Router error boundaries
 */
export function ErrorFallback({ error, resetErrorBoundary }) {
  logger.error('ErrorFallback', 'Route error', error);

  const sanitizedMessage = sanitizeErrorMessage(error);

  return (
    <Page>
      <TitleBar title="Error" />
      <Layout>
        <Layout.Section>
          <Banner tone="critical" title="Page Error">
            <BlockStack gap="200">
              <Text as="p" variant="bodyMd">
                {sanitizedMessage}
              </Text>
              {process.env.NODE_ENV === 'development' && (
                <details style={{ marginTop: '16px', padding: '8px', backgroundColor: '#f5f5f5', borderRadius: '4px' }}>
                  <summary style={{ cursor: 'pointer', fontWeight: 'bold' }}>
                    Error Details (Development Only)
                  </summary>
                  <pre style={{ marginTop: '8px', overflow: 'auto', fontSize: '12px' }}>
                    {error?.stack || String(error)}
                  </pre>
                </details>
              )}
              <BlockStack gap="100">
                <Button onClick={resetErrorBoundary} variant="primary">
                  Try Again
                </Button>
                <Button onClick={() => window.location.href = '/'} variant="plain">
                  Go to Home
                </Button>
              </BlockStack>
            </BlockStack>
          </Banner>
        </Layout.Section>
      </Layout>
    </Page>
  );
}
