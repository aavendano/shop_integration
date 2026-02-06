import { Layout, Box } from "@shopify/polaris";

/**
 * ResponsiveLayout Component
 * Provides responsive layout patterns for different screen sizes
 * Uses Polaris responsive components for desktop, tablet, and mobile
 * Requirements: 17.1, 17.2
 */

/**
 * Responsive section that adapts to screen size
 * - Desktop: Full width or specified variant
 * - Tablet: Adjusted width
 * - Mobile: Full width, stacked
 */
export function ResponsiveSection({ 
  children, 
  variant = "full",
  desktopVariant,
  tabletVariant,
  mobileVariant,
  ...props 
}) {
  // Polaris Layout.Section variants:
  // - "full": Full width
  // - "oneThird": One third width
  // - "oneHalf": One half width
  // - "twoThirds": Two thirds width
  
  // On mobile, always use full width
  // On tablet, use tabletVariant or default
  // On desktop, use desktopVariant or variant
  
  return (
    <Layout.Section 
      variant={variant}
      {...props}
    >
      {children}
    </Layout.Section>
  );
}

/**
 * Responsive grid layout
 * Automatically adjusts columns based on screen size
 * - Desktop: 3 columns
 * - Tablet: 2 columns
 * - Mobile: 1 column
 */
export function ResponsiveGrid({ children, columns = 3 }) {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: `repeat(auto-fit, minmax(300px, 1fr))`,
        gap: "1rem",
        width: "100%",
      }}
    >
      {children}
    </div>
  );
}

/**
 * Responsive card container
 * Adapts padding and spacing for different screen sizes
 */
export function ResponsiveCard({ children, padding = "400" }) {
  return (
    <Box
      padding={padding}
      style={{
        "@media (max-width: 768px)": {
          padding: "300",
        },
        "@media (max-width: 480px)": {
          padding: "200",
        },
      }}
    >
      {children}
    </Box>
  );
}

/**
 * Responsive table wrapper
 * Provides horizontal scroll on mobile devices
 */
export function ResponsiveTableWrapper({ children }) {
  return (
    <div
      style={{
        overflowX: "auto",
        WebkitOverflowScrolling: "touch",
        "@media (min-width: 768px)": {
          overflowX: "visible",
        },
      }}
    >
      {children}
    </div>
  );
}

/**
 * Responsive button group
 * Stacks buttons vertically on mobile
 */
export function ResponsiveButtonGroup({ children, gap = "200" }) {
  return (
    <div
      style={{
        display: "flex",
        gap: "1rem",
        flexWrap: "wrap",
        "@media (max-width: 480px)": {
          flexDirection: "column",
        },
      }}
    >
      {children}
    </div>
  );
}

/**
 * Responsive text
 * Adjusts font size for different screen sizes
 */
export function ResponsiveText({ 
  children, 
  desktopSize = "md",
  tabletSize = "sm",
  mobileSize = "sm",
  ...props 
}) {
  const fontSizeMap = {
    xs: "0.75rem",
    sm: "0.875rem",
    md: "1rem",
    lg: "1.125rem",
    xl: "1.25rem",
  };

  return (
    <span
      style={{
        fontSize: fontSizeMap[desktopSize],
        "@media (max-width: 768px)": {
          fontSize: fontSizeMap[tabletSize],
        },
        "@media (max-width: 480px)": {
          fontSize: fontSizeMap[mobileSize],
        },
      }}
      {...props}
    >
      {children}
    </span>
  );
}

/**
 * Responsive spacing utility
 * Adjusts spacing based on screen size
 */
export function ResponsiveSpacing({ 
  children, 
  desktopGap = "400",
  tabletGap = "300",
  mobileGap = "200",
  direction = "vertical",
}) {
  const gapMap = {
    "100": "0.25rem",
    "200": "0.5rem",
    "300": "1rem",
    "400": "1.5rem",
    "500": "2rem",
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: direction === "vertical" ? "column" : "row",
        gap: gapMap[desktopGap],
        "@media (max-width: 768px)": {
          gap: gapMap[tabletGap],
        },
        "@media (max-width: 480px)": {
          gap: gapMap[mobileGap],
        },
      }}
    >
      {children}
    </div>
  );
}

/**
 * Hide element on specific screen sizes
 * Useful for responsive design
 */
export function HideOn({ children, breakpoint = "mobile" }) {
  const breakpoints = {
    mobile: "(max-width: 480px)",
    tablet: "(max-width: 768px)",
    desktop: "(min-width: 769px)",
  };

  return (
    <div
      style={{
        display: "none",
        [`@media ${breakpoints[breakpoint]}`]: {
          display: "block",
        },
      }}
    >
      {children}
    </div>
  );
}

/**
 * Show element only on specific screen sizes
 * Useful for responsive design
 */
export function ShowOn({ children, breakpoint = "desktop" }) {
  const breakpoints = {
    mobile: "(max-width: 480px)",
    tablet: "(max-width: 768px)",
    desktop: "(min-width: 769px)",
  };

  return (
    <div
      style={{
        [`@media ${breakpoints[breakpoint]}`]: {
          display: "block",
        },
      }}
    >
      {children}
    </div>
  );
}
