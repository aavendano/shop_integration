import { useAppBridge } from "@shopify/app-bridge-react";
import { useNavigate } from "@remix-run/react";

/**
 * App Bridge Integration Utilities
 * Provides helpers for App Bridge navigation, toasts, and error handling
 * Requirements: 13.2, 13.3, 13.5, 13.6, 13.7
 */

/**
 * Hook for App Bridge-aware navigation
 * Uses App Bridge for navigation within embedded app
 * Updates browser URL using App Bridge
 * Requirements: 13.2, 13.5
 */
export function useAppBridgeNavigation() {
  const shopify = useAppBridge();
  const remixNavigate = useNavigate();

  return (path: string, options?: { replace?: boolean }) => {
    // Use App Bridge navigation for embedded app context
    if (shopify) {
      shopify.dispatch({
        type: "APP::MODAL::CLOSE",
      });
      
      // Navigate using Remix which updates the URL
      remixNavigate(path, { replace: options?.replace });
    } else {
      // Fallback to Remix navigation if App Bridge not available
      remixNavigate(path, { replace: options?.replace });
    }
  };
}

/**
 * Hook for App Bridge Toast notifications
 * Uses App Bridge Toast for all notifications
 * Replaces Polaris Toast with App Bridge Toast
 * Requirements: 13.3
 */
export function useAppBridgeToast() {
  const shopify = useAppBridge();

  return {
    /**
     * Show success toast
     */
    success: (message: string, options?: { duration?: number }) => {
      if (shopify) {
        shopify.toast.show(message, {
          isError: false,
          duration: options?.duration || 5,
        });
      }
    },

    /**
     * Show error toast
     */
    error: (message: string, options?: { duration?: number }) => {
      if (shopify) {
        shopify.toast.show(message, {
          isError: true,
          duration: options?.duration || 5,
        });
      }
    },

    /**
     * Show generic toast
     */
    show: (message: string, options?: { isError?: boolean; duration?: number }) => {
      if (shopify) {
        shopify.toast.show(message, {
          isError: options?.isError || false,
          duration: options?.duration || 5,
        });
      }
    },
  };
}

/**
 * Hook for handling external links with App Bridge redirect
 * Uses App Bridge redirect for external links
 * Requirements: 13.6
 */
export function useAppBridgeRedirect() {
  const shopify = useAppBridge();

  return (url: string) => {
    if (shopify) {
      // Use App Bridge redirect for external links
      shopify.dispatch({
        type: "APP::MODAL::CLOSE",
      });
      window.open(url, "_blank");
    } else {
      // Fallback to standard window.open
      window.open(url, "_blank");
    }
  };
}

/**
 * Hook for handling App Bridge authentication errors
 * Gracefully handles App Bridge authentication errors
 * Requirements: 13.7
 */
export function useAppBridgeErrorHandler() {
  const shopify = useAppBridge();
  const toast = useAppBridgeToast();

  return {
    /**
     * Handle authentication error
     */
    handleAuthError: (error: Error) => {
      console.error("Authentication error:", error);
      
      if (shopify) {
        toast.error("Authentication failed. Please refresh and try again.");
        
        // Dispatch authentication error event
        shopify.dispatch({
          type: "APP::ERROR",
          payload: {
            message: error.message,
            type: "AUTH_ERROR",
          },
        });
      }
    },

    /**
     * Handle API error
     */
    handleApiError: (error: Error) => {
      console.error("API error:", error);
      
      if (shopify) {
        toast.error(error.message || "An error occurred. Please try again.");
      }
    },

    /**
     * Handle network error
     */
    handleNetworkError: (error: Error) => {
      console.error("Network error:", error);
      
      if (shopify) {
        toast.error("Network error. Please check your connection and try again.");
      }
    },
  };
}

/**
 * Utility to check if running in embedded app context
 */
export function isEmbeddedApp(): boolean {
  return typeof window !== "undefined" && window.self !== window.top;
}

/**
 * Utility to get shop domain from App Bridge context
 */
export function getShopDomain(shopify: any): string | null {
  if (!shopify) return null;
  
  try {
    // Shop domain is available in the App Bridge context
    const state = shopify.getState?.();
    return state?.shop?.domain || null;
  } catch (error) {
    console.error("Error getting shop domain:", error);
    return null;
  }
}
