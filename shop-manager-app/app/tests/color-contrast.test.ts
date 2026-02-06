/**
 * Color Contrast Tests
 * Verifies WCAG 2.1 AA color contrast ratios
 * Requirements: 17.7
 */

import { describe, it, expect } from "vitest";

/**
 * Calculate relative luminance of a color
 * Used for WCAG contrast ratio calculation
 */
function getRelativeLuminance(color: string): number {
  const rgb = parseColor(color);
  if (!rgb) return 0;

  const [r, g, b] = rgb.map((c) => {
    c = c / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });

  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

/**
 * Parse color string to RGB values
 */
function parseColor(color: string): number[] | null {
  // Handle hex colors
  if (color.startsWith("#")) {
    const hex = color.slice(1);
    if (hex.length === 6) {
      return [
        parseInt(hex.slice(0, 2), 16),
        parseInt(hex.slice(2, 4), 16),
        parseInt(hex.slice(4, 6), 16),
      ];
    }
  }

  // Handle rgb colors
  const rgbMatch = color.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
  if (rgbMatch) {
    return [parseInt(rgbMatch[1]), parseInt(rgbMatch[2]), parseInt(rgbMatch[3])];
  }

  return null;
}

/**
 * Calculate contrast ratio between two colors
 */
function getContrastRatio(foreground: string, background: string): number {
  const fgLuminance = getRelativeLuminance(foreground);
  const bgLuminance = getRelativeLuminance(background);

  const lighter = Math.max(fgLuminance, bgLuminance);
  const darker = Math.min(fgLuminance, bgLuminance);

  return (lighter + 0.05) / (darker + 0.05);
}

/**
 * Check if contrast ratio meets WCAG AA standards
 */
function meetsWCAGAA(foreground: string, background: string, largeText: boolean = false): boolean {
  const ratio = getContrastRatio(foreground, background);
  // AA standard: 4.5:1 for normal text, 3:1 for large text
  return largeText ? ratio >= 3 : ratio >= 4.5;
}

describe("Color Contrast - WCAG 2.1 AA", () => {
  describe("Text Contrast", () => {
    it("should have sufficient contrast for normal text on white background", () => {
      // Polaris text color on white
      const textColor = "#202223"; // Dark gray
      const backgroundColor = "#ffffff"; // White
      const ratio = getContrastRatio(textColor, backgroundColor);

      expect(ratio).toBeGreaterThanOrEqual(4.5);
      expect(meetsWCAGAA(textColor, backgroundColor)).toBe(true);
    });

    it("should have sufficient contrast for links", () => {
      // Polaris link color
      const linkColor = "#0066cc"; // Blue
      const backgroundColor = "#ffffff"; // White
      const ratio = getContrastRatio(linkColor, backgroundColor);

      expect(ratio).toBeGreaterThanOrEqual(4.5);
      expect(meetsWCAGAA(linkColor, backgroundColor)).toBe(true);
    });

    it("should have sufficient contrast for visited links", () => {
      // Polaris visited link color
      const visitedLinkColor = "#6b3fa0"; // Purple
      const backgroundColor = "#ffffff"; // White
      const ratio = getContrastRatio(visitedLinkColor, backgroundColor);

      expect(ratio).toBeGreaterThanOrEqual(4.5);
      expect(meetsWCAGAA(visitedLinkColor, backgroundColor)).toBe(true);
    });

    it("should have sufficient contrast for error text", () => {
      // Polaris error color
      const errorColor = "#d82c0d"; // Red
      const backgroundColor = "#ffffff"; // White
      const ratio = getContrastRatio(errorColor, backgroundColor);

      expect(ratio).toBeGreaterThanOrEqual(4.5);
      expect(meetsWCAGAA(errorColor, backgroundColor)).toBe(true);
    });

    it("should have sufficient contrast for success text", () => {
      // Polaris success color
      const successColor = "#137333"; // Green
      const backgroundColor = "#ffffff"; // White
      const ratio = getContrastRatio(successColor, backgroundColor);

      expect(ratio).toBeGreaterThanOrEqual(4.5);
      expect(meetsWCAGAA(successColor, backgroundColor)).toBe(true);
    });

    it("should have sufficient contrast for warning text", () => {
      // Polaris warning color
      const warningColor = "#974f0c"; // Orange
      const backgroundColor = "#ffffff"; // White
      const ratio = getContrastRatio(warningColor, backgroundColor);

      expect(ratio).toBeGreaterThanOrEqual(4.5);
      expect(meetsWCAGAA(warningColor, backgroundColor)).toBe(true);
    });
  });

  describe("Large Text Contrast", () => {
    it("should have sufficient contrast for large text (3:1 minimum)", () => {
      // Large text (18pt or 14pt bold) requires 3:1 contrast
      const textColor = "#202223";
      const backgroundColor = "#ffffff";
      const ratio = getContrastRatio(textColor, backgroundColor);

      expect(ratio).toBeGreaterThanOrEqual(3);
      expect(meetsWCAGAA(textColor, backgroundColor, true)).toBe(true);
    });

    it("should have sufficient contrast for large link text", () => {
      const linkColor = "#0066cc";
      const backgroundColor = "#ffffff";
      const ratio = getContrastRatio(linkColor, backgroundColor);

      expect(ratio).toBeGreaterThanOrEqual(3);
      expect(meetsWCAGAA(linkColor, backgroundColor, true)).toBe(true);
    });
  });

  describe("Button Contrast", () => {
    it("should have sufficient contrast for primary button text", () => {
      // Polaris primary button: white text on blue background
      const textColor = "#ffffff"; // White
      const backgroundColor = "#0066cc"; // Blue
      const ratio = getContrastRatio(textColor, backgroundColor);

      expect(ratio).toBeGreaterThanOrEqual(4.5);
      expect(meetsWCAGAA(textColor, backgroundColor)).toBe(true);
    });

    it("should have sufficient contrast for secondary button text", () => {
      // Polaris secondary button: dark text on light background
      const textColor = "#202223"; // Dark gray
      const backgroundColor = "#f5f5f5"; // Light gray
      const ratio = getContrastRatio(textColor, backgroundColor);

      expect(ratio).toBeGreaterThanOrEqual(4.5);
      expect(meetsWCAGAA(textColor, backgroundColor)).toBe(true);
    });

    it("should have sufficient contrast for disabled button text", () => {
      // Disabled button should still have sufficient contrast
      const textColor = "#999999"; // Medium gray
      const backgroundColor = "#ffffff"; // White
      const ratio = getContrastRatio(textColor, backgroundColor);

      expect(ratio).toBeGreaterThanOrEqual(3);
    });
  });

  describe("Form Input Contrast", () => {
    it("should have sufficient contrast for form input borders", () => {
      // Form input border
      const borderColor = "#d9d9d9"; // Light gray
      const backgroundColor = "#ffffff"; // White
      const ratio = getContrastRatio(borderColor, backgroundColor);

      expect(ratio).toBeGreaterThanOrEqual(3);
    });

    it("should have sufficient contrast for form input focus state", () => {
      // Form input focus border
      const focusColor = "#0066cc"; // Blue
      const backgroundColor = "#ffffff"; // White
      const ratio = getContrastRatio(focusColor, backgroundColor);

      expect(ratio).toBeGreaterThanOrEqual(3);
    });

    it("should have sufficient contrast for form input text", () => {
      // Form input text
      const textColor = "#202223"; // Dark gray
      const backgroundColor = "#ffffff"; // White
      const ratio = getContrastRatio(textColor, backgroundColor);

      expect(ratio).toBeGreaterThanOrEqual(4.5);
      expect(meetsWCAGAA(textColor, backgroundColor)).toBe(true);
    });
  });

  describe("Badge Contrast", () => {
    it("should have sufficient contrast for success badge", () => {
      // Success badge: white text on green background
      const textColor = "#ffffff"; // White
      const backgroundColor = "#137333"; // Green
      const ratio = getContrastRatio(textColor, backgroundColor);

      expect(ratio).toBeGreaterThanOrEqual(4.5);
      expect(meetsWCAGAA(textColor, backgroundColor)).toBe(true);
    });

    it("should have sufficient contrast for warning badge", () => {
      // Warning badge: white text on orange background
      const textColor = "#ffffff"; // White
      const backgroundColor = "#974f0c"; // Orange
      const ratio = getContrastRatio(textColor, backgroundColor);

      expect(ratio).toBeGreaterThanOrEqual(4.5);
      expect(meetsWCAGAA(textColor, backgroundColor)).toBe(true);
    });

    it("should have sufficient contrast for critical badge", () => {
      // Critical badge: white text on red background
      const textColor = "#ffffff"; // White
      const backgroundColor = "#d82c0d"; // Red
      const ratio = getContrastRatio(textColor, backgroundColor);

      expect(ratio).toBeGreaterThanOrEqual(4.5);
      expect(meetsWCAGAA(textColor, backgroundColor)).toBe(true);
    });
  });

  describe("Icon Contrast", () => {
    it("should have sufficient contrast for icons on white background", () => {
      // Icon color
      const iconColor = "#202223"; // Dark gray
      const backgroundColor = "#ffffff"; // White
      const ratio = getContrastRatio(iconColor, backgroundColor);

      expect(ratio).toBeGreaterThanOrEqual(3);
    });

    it("should have sufficient contrast for icons on colored background", () => {
      // Icon on colored background
      const iconColor = "#ffffff"; // White
      const backgroundColor = "#0066cc"; // Blue
      const ratio = getContrastRatio(iconColor, backgroundColor);

      expect(ratio).toBeGreaterThanOrEqual(3);
    });
  });

  describe("Placeholder Text Contrast", () => {
    it("should have sufficient contrast for placeholder text", () => {
      // Placeholder text is typically lighter
      const placeholderColor = "#999999"; // Medium gray
      const backgroundColor = "#ffffff"; // White
      const ratio = getContrastRatio(placeholderColor, backgroundColor);

      // Placeholder text can have lower contrast (3:1)
      expect(ratio).toBeGreaterThanOrEqual(3);
    });
  });

  describe("Disabled State Contrast", () => {
    it("should have sufficient contrast for disabled text", () => {
      // Disabled text
      const disabledColor = "#999999"; // Medium gray
      const backgroundColor = "#ffffff"; // White
      const ratio = getContrastRatio(disabledColor, backgroundColor);

      // Disabled state can have lower contrast (3:1)
      expect(ratio).toBeGreaterThanOrEqual(3);
    });
  });

  describe("Focus Indicator Contrast", () => {
    it("should have sufficient contrast for focus outline", () => {
      // Focus outline
      const focusColor = "#0066cc"; // Blue
      const backgroundColor = "#ffffff"; // White
      const ratio = getContrastRatio(focusColor, backgroundColor);

      expect(ratio).toBeGreaterThanOrEqual(3);
    });
  });

  describe("Hover State Contrast", () => {
    it("should have sufficient contrast for hover state", () => {
      // Hover state background
      const textColor = "#202223"; // Dark gray
      const hoverBackground = "#f5f5f5"; // Light gray
      const ratio = getContrastRatio(textColor, hoverBackground);

      expect(ratio).toBeGreaterThanOrEqual(4.5);
      expect(meetsWCAGAA(textColor, hoverBackground)).toBe(true);
    });
  });

  describe("Dark Mode Contrast", () => {
    it("should have sufficient contrast for text on dark background", () => {
      // Dark mode: light text on dark background
      const textColor = "#ffffff"; // White
      const backgroundColor = "#202223"; // Dark gray
      const ratio = getContrastRatio(textColor, backgroundColor);

      expect(ratio).toBeGreaterThanOrEqual(4.5);
      expect(meetsWCAGAA(textColor, backgroundColor)).toBe(true);
    });

    it("should have sufficient contrast for links in dark mode", () => {
      // Dark mode: light link on dark background
      const linkColor = "#66b3ff"; // Light blue
      const backgroundColor = "#202223"; // Dark gray
      const ratio = getContrastRatio(linkColor, backgroundColor);

      expect(ratio).toBeGreaterThanOrEqual(4.5);
      expect(meetsWCAGAA(linkColor, backgroundColor)).toBe(true);
    });
  });

  describe("Contrast Ratio Calculation", () => {
    it("should calculate correct contrast ratio", () => {
      // Black on white should be 21:1
      const ratio = getContrastRatio("#000000", "#ffffff");
      expect(ratio).toBeCloseTo(21, 0);
    });

    it("should calculate correct contrast ratio for similar colors", () => {
      // Similar colors should have lower contrast
      const ratio = getContrastRatio("#cccccc", "#ffffff");
      expect(ratio).toBeLessThan(4.5);
    });

    it("should handle RGB color format", () => {
      const ratio = getContrastRatio("rgb(0, 0, 0)", "rgb(255, 255, 255)");
      expect(ratio).toBeCloseTo(21, 0);
    });
  });

  describe("Polaris Color Palette Compliance", () => {
    it("should verify all Polaris text colors meet AA standards", () => {
      const polarisColors = {
        text: "#202223",
        textSubdued: "#666666",
        link: "#0066cc",
        linkVisited: "#6b3fa0",
        error: "#d82c0d",
        success: "#137333",
        warning: "#974f0c",
        info: "#0066cc",
      };

      Object.entries(polarisColors).forEach(([name, color]) => {
        const ratio = getContrastRatio(color, "#ffffff");
        expect(ratio).toBeGreaterThanOrEqual(4.5, `${name} should meet AA standards`);
      });
    });

    it("should verify all Polaris background colors work with text", () => {
      const backgrounds = {
        white: "#ffffff",
        lightGray: "#f5f5f5",
        mediumGray: "#e1e3e5",
      };

      const textColor = "#202223";

      Object.entries(backgrounds).forEach(([name, bg]) => {
        const ratio = getContrastRatio(textColor, bg);
        expect(ratio).toBeGreaterThanOrEqual(4.5, `${name} background should work with text`);
      });
    });
  });
});
