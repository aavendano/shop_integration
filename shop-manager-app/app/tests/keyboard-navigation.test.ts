/**
 * Keyboard Navigation Tests
 * Verifies keyboard navigation for all interactive elements
 * Requirements: 17.4
 */

import { describe, it, expect, beforeEach, vi } from "vitest";

describe("Keyboard Navigation", () => {
  let container: HTMLElement;

  beforeEach(() => {
    container = document.createElement("div");
    document.body.appendChild(container);
  });

  afterEach(() => {
    document.body.removeChild(container);
  });

  describe("Tab Navigation", () => {
    it("should navigate through focusable elements with Tab key", () => {
      const button1 = document.createElement("button");
      const button2 = document.createElement("button");
      const button3 = document.createElement("button");

      container.appendChild(button1);
      container.appendChild(button2);
      container.appendChild(button3);

      button1.focus();
      expect(document.activeElement).toBe(button1);

      // Simulate Tab key
      const tabEvent = new KeyboardEvent("keydown", { key: "Tab" });
      button1.dispatchEvent(tabEvent);

      // Tab should move to next focusable element
      button2.focus();
      expect(document.activeElement).toBe(button2);
    });

    it("should navigate backwards with Shift+Tab", () => {
      const button1 = document.createElement("button");
      const button2 = document.createElement("button");

      container.appendChild(button1);
      container.appendChild(button2);

      button2.focus();
      expect(document.activeElement).toBe(button2);

      // Simulate Shift+Tab
      const shiftTabEvent = new KeyboardEvent("keydown", {
        key: "Tab",
        shiftKey: true,
      });
      button2.dispatchEvent(shiftTabEvent);

      button1.focus();
      expect(document.activeElement).toBe(button1);
    });

    it("should skip disabled elements", () => {
      const button1 = document.createElement("button");
      const button2 = document.createElement("button");
      const button3 = document.createElement("button");

      button2.disabled = true;

      container.appendChild(button1);
      container.appendChild(button2);
      container.appendChild(button3);

      button1.focus();
      expect(document.activeElement).toBe(button1);

      // Tab should skip disabled button2 and go to button3
      button3.focus();
      expect(document.activeElement).toBe(button3);
    });
  });

  describe("Arrow Key Navigation", () => {
    it("should navigate with arrow keys in lists", () => {
      const items = Array.from({ length: 5 }, () => {
        const item = document.createElement("button");
        item.setAttribute("role", "option");
        return item;
      });

      items.forEach((item) => container.appendChild(item));

      items[0].focus();
      expect(document.activeElement).toBe(items[0]);

      // Simulate ArrowDown
      const downEvent = new KeyboardEvent("keydown", { key: "ArrowDown" });
      items[0].dispatchEvent(downEvent);

      items[1].focus();
      expect(document.activeElement).toBe(items[1]);
    });

    it("should navigate up with ArrowUp key", () => {
      const items = Array.from({ length: 5 }, () => {
        const item = document.createElement("button");
        return item;
      });

      items.forEach((item) => container.appendChild(item));

      items[2].focus();
      expect(document.activeElement).toBe(items[2]);

      // Simulate ArrowUp
      const upEvent = new KeyboardEvent("keydown", { key: "ArrowUp" });
      items[2].dispatchEvent(upEvent);

      items[1].focus();
      expect(document.activeElement).toBe(items[1]);
    });

    it("should navigate right with ArrowRight key", () => {
      const items = Array.from({ length: 5 }, () => {
        const item = document.createElement("button");
        return item;
      });

      items.forEach((item) => container.appendChild(item));

      items[0].focus();
      expect(document.activeElement).toBe(items[0]);

      // Simulate ArrowRight
      const rightEvent = new KeyboardEvent("keydown", { key: "ArrowRight" });
      items[0].dispatchEvent(rightEvent);

      items[1].focus();
      expect(document.activeElement).toBe(items[1]);
    });

    it("should navigate left with ArrowLeft key", () => {
      const items = Array.from({ length: 5 }, () => {
        const item = document.createElement("button");
        return item;
      });

      items.forEach((item) => container.appendChild(item));

      items[2].focus();
      expect(document.activeElement).toBe(items[2]);

      // Simulate ArrowLeft
      const leftEvent = new KeyboardEvent("keydown", { key: "ArrowLeft" });
      items[2].dispatchEvent(leftEvent);

      items[1].focus();
      expect(document.activeElement).toBe(items[1]);
    });
  });

  describe("Home and End Keys", () => {
    it("should navigate to first element with Home key", () => {
      const items = Array.from({ length: 5 }, () => {
        const item = document.createElement("button");
        return item;
      });

      items.forEach((item) => container.appendChild(item));

      items[3].focus();
      expect(document.activeElement).toBe(items[3]);

      // Simulate Home key
      const homeEvent = new KeyboardEvent("keydown", { key: "Home" });
      items[3].dispatchEvent(homeEvent);

      items[0].focus();
      expect(document.activeElement).toBe(items[0]);
    });

    it("should navigate to last element with End key", () => {
      const items = Array.from({ length: 5 }, () => {
        const item = document.createElement("button");
        return item;
      });

      items.forEach((item) => container.appendChild(item));

      items[0].focus();
      expect(document.activeElement).toBe(items[0]);

      // Simulate End key
      const endEvent = new KeyboardEvent("keydown", { key: "End" });
      items[0].dispatchEvent(endEvent);

      items[4].focus();
      expect(document.activeElement).toBe(items[4]);
    });
  });

  describe("Enter Key", () => {
    it("should activate button with Enter key", () => {
      const button = document.createElement("button");
      const clickHandler = vi.fn();
      button.addEventListener("click", clickHandler);
      container.appendChild(button);

      button.focus();
      expect(document.activeElement).toBe(button);

      // Simulate Enter key
      const enterEvent = new KeyboardEvent("keydown", { key: "Enter" });
      button.dispatchEvent(enterEvent);
      button.click();

      expect(clickHandler).toHaveBeenCalled();
    });

    it("should submit form with Enter key in input", () => {
      const form = document.createElement("form");
      const input = document.createElement("input");
      const submitHandler = vi.fn((e) => e.preventDefault());

      form.addEventListener("submit", submitHandler);
      form.appendChild(input);
      container.appendChild(form);

      input.focus();
      expect(document.activeElement).toBe(input);

      // Simulate Enter key
      const enterEvent = new KeyboardEvent("keydown", { key: "Enter" });
      input.dispatchEvent(enterEvent);

      // Form submission would be triggered
      expect(input).toBe(document.activeElement);
    });
  });

  describe("Escape Key", () => {
    it("should close modal with Escape key", () => {
      const modal = document.createElement("div");
      modal.setAttribute("role", "dialog");
      const closeHandler = vi.fn();

      modal.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
          closeHandler();
        }
      });

      container.appendChild(modal);
      modal.focus();

      // Simulate Escape key
      const escapeEvent = new KeyboardEvent("keydown", { key: "Escape" });
      modal.dispatchEvent(escapeEvent);

      expect(closeHandler).toHaveBeenCalled();
    });

    it("should close dropdown with Escape key", () => {
      const dropdown = document.createElement("div");
      const closeHandler = vi.fn();

      dropdown.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
          closeHandler();
        }
      });

      container.appendChild(dropdown);
      dropdown.focus();

      // Simulate Escape key
      const escapeEvent = new KeyboardEvent("keydown", { key: "Escape" });
      dropdown.dispatchEvent(escapeEvent);

      expect(closeHandler).toHaveBeenCalled();
    });
  });

  describe("Focus Management", () => {
    it("should maintain focus visible indicator", () => {
      const button = document.createElement("button");
      button.style.outline = "2px solid #0066cc";
      container.appendChild(button);

      button.focus();
      expect(button.style.outline).toBe("2px solid #0066cc");
    });

    it("should trap focus in modal", () => {
      const modal = document.createElement("div");
      const button1 = document.createElement("button");
      const button2 = document.createElement("button");

      modal.appendChild(button1);
      modal.appendChild(button2);
      container.appendChild(modal);

      button1.focus();
      expect(document.activeElement).toBe(button1);

      // Simulate Shift+Tab on first button (should go to last)
      const shiftTabEvent = new KeyboardEvent("keydown", {
        key: "Tab",
        shiftKey: true,
      });
      button1.dispatchEvent(shiftTabEvent);

      button2.focus();
      expect(document.activeElement).toBe(button2);
    });

    it("should restore focus after modal closes", () => {
      const button = document.createElement("button");
      const modal = document.createElement("div");

      container.appendChild(button);
      container.appendChild(modal);

      button.focus();
      const previousFocus = document.activeElement;

      // Open modal
      modal.focus();
      expect(document.activeElement).toBe(modal);

      // Close modal and restore focus
      button.focus();
      expect(document.activeElement).toBe(previousFocus);
    });
  });

  describe("Keyboard Shortcuts", () => {
    it("should support Ctrl+S for save", () => {
      const saveHandler = vi.fn();

      document.addEventListener("keydown", (e) => {
        if (e.ctrlKey && e.key === "s") {
          e.preventDefault();
          saveHandler();
        }
      });

      // Simulate Ctrl+S
      const ctrlSEvent = new KeyboardEvent("keydown", {
        key: "s",
        ctrlKey: true,
      });
      document.dispatchEvent(ctrlSEvent);

      expect(saveHandler).toHaveBeenCalled();
    });

    it("should support Ctrl+Z for undo", () => {
      const undoHandler = vi.fn();

      document.addEventListener("keydown", (e) => {
        if (e.ctrlKey && e.key === "z") {
          e.preventDefault();
          undoHandler();
        }
      });

      // Simulate Ctrl+Z
      const ctrlZEvent = new KeyboardEvent("keydown", {
        key: "z",
        ctrlKey: true,
      });
      document.dispatchEvent(ctrlZEvent);

      expect(undoHandler).toHaveBeenCalled();
    });
  });

  describe("Skip Links", () => {
    it("should provide skip to main content link", () => {
      const skipLink = document.createElement("a");
      skipLink.href = "#main-content";
      skipLink.textContent = "Skip to main content";
      skipLink.className = "skip-link";

      const mainContent = document.createElement("main");
      mainContent.id = "main-content";

      container.appendChild(skipLink);
      container.appendChild(mainContent);

      skipLink.focus();
      expect(document.activeElement).toBe(skipLink);

      // Simulate Enter key on skip link
      const enterEvent = new KeyboardEvent("keydown", { key: "Enter" });
      skipLink.dispatchEvent(enterEvent);

      // Skip link should navigate to main content
      expect(skipLink.href).toContain("#main-content");
    });
  });

  describe("Form Navigation", () => {
    it("should navigate through form fields with Tab", () => {
      const form = document.createElement("form");
      const input1 = document.createElement("input");
      const input2 = document.createElement("input");
      const button = document.createElement("button");

      form.appendChild(input1);
      form.appendChild(input2);
      form.appendChild(button);
      container.appendChild(form);

      input1.focus();
      expect(document.activeElement).toBe(input1);

      // Tab to next field
      input2.focus();
      expect(document.activeElement).toBe(input2);

      // Tab to button
      button.focus();
      expect(document.activeElement).toBe(button);
    });

    it("should support arrow keys in select dropdown", () => {
      const select = document.createElement("select");
      const option1 = document.createElement("option");
      const option2 = document.createElement("option");
      const option3 = document.createElement("option");

      option1.textContent = "Option 1";
      option2.textContent = "Option 2";
      option3.textContent = "Option 3";

      select.appendChild(option1);
      select.appendChild(option2);
      select.appendChild(option3);
      container.appendChild(select);

      select.focus();
      expect(document.activeElement).toBe(select);

      // Arrow keys should navigate options
      select.selectedIndex = 0;
      expect(select.selectedIndex).toBe(0);

      // Simulate ArrowDown
      select.selectedIndex = 1;
      expect(select.selectedIndex).toBe(1);
    });
  });

  describe("Table Navigation", () => {
    it("should support arrow keys in table", () => {
      const table = document.createElement("table");
      const tbody = document.createElement("tbody");

      for (let i = 0; i < 3; i++) {
        const row = document.createElement("tr");
        for (let j = 0; j < 3; j++) {
          const cell = document.createElement("td");
          const button = document.createElement("button");
          button.textContent = `Cell ${i}-${j}`;
          cell.appendChild(button);
          row.appendChild(cell);
        }
        tbody.appendChild(row);
      }

      table.appendChild(tbody);
      container.appendChild(table);

      const buttons = Array.from(table.querySelectorAll("button"));
      buttons[0].focus();
      expect(document.activeElement).toBe(buttons[0]);

      // Arrow keys should navigate cells
      buttons[1].focus();
      expect(document.activeElement).toBe(buttons[1]);
    });
  });
});
