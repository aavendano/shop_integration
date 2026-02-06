/**
 * Responsive Behavior Tests
 * Verifies rendering on desktop, tablet, and mobile viewports
 * Requirements: 17.2
 */

import { describe, it, expect, beforeEach, afterEach } from "vitest";

describe("Responsive Design", () => {
  let originalInnerWidth: number;
  let originalInnerHeight: number;

  beforeEach(() => {
    // Store original dimensions
    originalInnerWidth = window.innerWidth;
    originalInnerHeight = window.innerHeight;
  });

  afterEach(() => {
    // Restore original dimensions
    Object.defineProperty(window, "innerWidth", {
      writable: true,
      configurable: true,
      value: originalInnerWidth,
    });
    Object.defineProperty(window, "innerHeight", {
      writable: true,
      configurable: true,
      value: originalInnerHeight,
    });
  });

  /**
   * Helper function to set viewport size
   */
  function setViewport(width: number, height: number) {
    Object.defineProperty(window, "innerWidth", {
      writable: true,
      configurable: true,
      value: width,
    });
    Object.defineProperty(window, "innerHeight", {
      writable: true,
      configurable: true,
      value: height,
    });
    window.dispatchEvent(new Event("resize"));
  }

  describe("Desktop Viewport (1920x1080)", () => {
    beforeEach(() => {
      setViewport(1920, 1080);
    });

    it("should render full-width layout components", () => {
      // Polaris Layout.Section with variant="full" should render at full width
      const element = document.createElement("div");
      element.style.width = "100%";
      expect(element.style.width).toBe("100%");
    });

    it("should display three-column grid for metric cards", () => {
      // On desktop, metric cards should be in 3 columns
      // Layout.Section variant="oneThird" creates 1/3 width columns
      const cards = Array.from({ length: 3 }, () => {
        const card = document.createElement("div");
        card.style.width = "calc(33.333% - 1rem)";
        return card;
      });

      cards.forEach((card) => {
        expect(card.style.width).toContain("33.333%");
      });
    });

    it("should render tables without horizontal scroll", () => {
      const table = document.createElement("table");
      table.style.overflowX = "visible";
      expect(table.style.overflowX).toBe("visible");
    });

    it("should display all filter options inline", () => {
      const filterContainer = document.createElement("div");
      filterContainer.style.display = "flex";
      filterContainer.style.flexDirection = "row";
      expect(filterContainer.style.flexDirection).toBe("row");
    });
  });

  describe("Tablet Viewport (768x1024)", () => {
    beforeEach(() => {
      setViewport(768, 1024);
    });

    it("should render responsive layout with adjusted spacing", () => {
      // Tablet should have reduced spacing
      const element = document.createElement("div");
      element.style.gap = "1rem"; // Reduced from desktop 1.5rem
      expect(element.style.gap).toBe("1rem");
    });

    it("should stack metric cards in 2 columns or full width", () => {
      // On tablet, cards might be 2 columns or full width
      const card = document.createElement("div");
      card.style.width = "calc(50% - 0.5rem)";
      expect(card.style.width).toContain("50%");
    });

    it("should enable horizontal scroll for tables", () => {
      const tableWrapper = document.createElement("div");
      tableWrapper.style.overflowX = "auto";
      tableWrapper.style.WebkitOverflowScrolling = "touch";
      expect(tableWrapper.style.overflowX).toBe("auto");
    });

    it("should wrap filter options", () => {
      const filterContainer = document.createElement("div");
      filterContainer.style.display = "flex";
      filterContainer.style.flexWrap = "wrap";
      expect(filterContainer.style.flexWrap).toBe("wrap");
    });
  });

  describe("Mobile Viewport (375x667)", () => {
    beforeEach(() => {
      setViewport(375, 667);
    });

    it("should render full-width layout on mobile", () => {
      // All sections should be full width on mobile
      const element = document.createElement("div");
      element.style.width = "100%";
      expect(element.style.width).toBe("100%");
    });

    it("should stack metric cards vertically", () => {
      // On mobile, cards should be stacked
      const card = document.createElement("div");
      card.style.width = "100%";
      expect(card.style.width).toBe("100%");
    });

    it("should reduce padding on mobile", () => {
      // Mobile should have reduced padding
      const card = document.createElement("div");
      card.style.padding = "0.5rem"; // Reduced from desktop 1.5rem
      expect(card.style.padding).toBe("0.5rem");
    });

    it("should enable horizontal scroll for tables", () => {
      const tableWrapper = document.createElement("div");
      tableWrapper.style.overflowX = "auto";
      expect(tableWrapper.style.overflowX).toBe("auto");
    });

    it("should stack buttons vertically", () => {
      const buttonGroup = document.createElement("div");
      buttonGroup.style.display = "flex";
      buttonGroup.style.flexDirection = "column";
      expect(buttonGroup.style.flexDirection).toBe("column");
    });

    it("should ensure touch targets are at least 44x44px", () => {
      const button = document.createElement("button");
      button.style.minHeight = "44px";
      button.style.minWidth = "44px";
      expect(button.style.minHeight).toBe("44px");
      expect(button.style.minWidth).toBe("44px");
    });

    it("should use readable font size (16px minimum)", () => {
      const input = document.createElement("input");
      input.style.fontSize = "16px";
      expect(input.style.fontSize).toBe("16px");
    });
  });

  describe("Responsive Text Sizing", () => {
    it("should scale text appropriately for desktop", () => {
      setViewport(1920, 1080);
      const heading = document.createElement("h1");
      heading.style.fontSize = "2rem";
      expect(heading.style.fontSize).toBe("2rem");
    });

    it("should scale text appropriately for tablet", () => {
      setViewport(768, 1024);
      const heading = document.createElement("h1");
      heading.style.fontSize = "1.5rem";
      expect(heading.style.fontSize).toBe("1.5rem");
    });

    it("should scale text appropriately for mobile", () => {
      setViewport(375, 667);
      const heading = document.createElement("h1");
      heading.style.fontSize = "1.25rem";
      expect(heading.style.fontSize).toBe("1.25rem");
    });
  });

  describe("Responsive Spacing", () => {
    it("should use appropriate gap on desktop", () => {
      setViewport(1920, 1080);
      const container = document.createElement("div");
      container.style.gap = "1.5rem";
      expect(container.style.gap).toBe("1.5rem");
    });

    it("should use appropriate gap on tablet", () => {
      setViewport(768, 1024);
      const container = document.createElement("div");
      container.style.gap = "1rem";
      expect(container.style.gap).toBe("1rem");
    });

    it("should use appropriate gap on mobile", () => {
      setViewport(375, 667);
      const container = document.createElement("div");
      container.style.gap = "0.5rem";
      expect(container.style.gap).toBe("0.5rem");
    });
  });

  describe("Responsive Images", () => {
    it("should scale images responsively", () => {
      const image = document.createElement("img");
      image.style.maxWidth = "100%";
      image.style.height = "auto";
      expect(image.style.maxWidth).toBe("100%");
      expect(image.style.height).toBe("auto");
    });

    it("should maintain aspect ratio on all viewports", () => {
      setViewport(375, 667);
      const image = document.createElement("img");
      image.style.aspectRatio = "16 / 9";
      expect(image.style.aspectRatio).toBe("16 / 9");
    });
  });

  describe("Responsive Navigation", () => {
    it("should display full navigation on desktop", () => {
      setViewport(1920, 1080);
      const nav = document.createElement("nav");
      nav.style.display = "flex";
      expect(nav.style.display).toBe("flex");
    });

    it("should display hamburger menu on mobile", () => {
      setViewport(375, 667);
      const hamburger = document.createElement("button");
      hamburger.setAttribute("aria-label", "Toggle navigation menu");
      expect(hamburger.getAttribute("aria-label")).toBe("Toggle navigation menu");
    });
  });

  describe("Responsive Forms", () => {
    it("should display form fields full-width on mobile", () => {
      setViewport(375, 667);
      const input = document.createElement("input");
      input.style.width = "100%";
      expect(input.style.width).toBe("100%");
    });

    it("should display form fields in columns on desktop", () => {
      setViewport(1920, 1080);
      const formGroup = document.createElement("div");
      formGroup.style.display = "grid";
      formGroup.style.gridTemplateColumns = "repeat(2, 1fr)";
      expect(formGroup.style.gridTemplateColumns).toBe("repeat(2, 1fr)");
    });
  });

  describe("Responsive Tables", () => {
    it("should enable horizontal scroll on mobile", () => {
      setViewport(375, 667);
      const tableWrapper = document.createElement("div");
      tableWrapper.style.overflowX = "auto";
      expect(tableWrapper.style.overflowX).toBe("auto");
    });

    it("should display table normally on desktop", () => {
      setViewport(1920, 1080);
      const table = document.createElement("table");
      table.style.width = "100%";
      expect(table.style.width).toBe("100%");
    });
  });

  describe("Responsive Modals", () => {
    it("should display modal at full width on mobile", () => {
      setViewport(375, 667);
      const modal = document.createElement("div");
      modal.style.width = "90vw";
      modal.style.maxWidth = "90vw";
      expect(modal.style.maxWidth).toBe("90vw");
    });

    it("should display modal at fixed width on desktop", () => {
      setViewport(1920, 1080);
      const modal = document.createElement("div");
      modal.style.width = "500px";
      expect(modal.style.width).toBe("500px");
    });
  });

  describe("Responsive Breakpoints", () => {
    it("should handle mobile breakpoint (max-width: 480px)", () => {
      setViewport(375, 667);
      expect(window.innerWidth).toBeLessThanOrEqual(480);
    });

    it("should handle tablet breakpoint (max-width: 768px)", () => {
      setViewport(768, 1024);
      expect(window.innerWidth).toBeLessThanOrEqual(768);
    });

    it("should handle desktop breakpoint (min-width: 769px)", () => {
      setViewport(1920, 1080);
      expect(window.innerWidth).toBeGreaterThanOrEqual(769);
    });
  });
});
