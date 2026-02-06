import { useEffect } from "react";
import { AppProvider } from "@shopify/polaris";
import enTranslations from "@shopify/polaris/locales/en.json";

/**
 * AppProviders Component
 * Initializes Polaris provider
 * App Bridge is automatically initialized by the Shopify App Remix framework
 * Requirements: 13.1
 */
export default function AppProviders({ children, apiKey }) {
  useEffect(() => {
    // App Bridge is automatically initialized by the Shopify App Remix framework
    // through the shopify.server.js configuration
    console.log("App initialized with API key:", apiKey);
  }, [apiKey]);

  return (
    <AppProvider i18n={enTranslations}>
      {children}
    </AppProvider>
  );
}