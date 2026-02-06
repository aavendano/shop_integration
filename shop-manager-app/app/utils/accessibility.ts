/**
 * Accessibility utilities for WCAG 2.1 AA compliance
 * Provides helpers for ARIA labels, semantic HTML, and keyboard navigation
 * Requirements: 17.3, 17.4, 17.5, 17.6, 17.7
 */

/**
 * Generate ARIA label for list items
 * Ensures screen readers can identify list items properly
 */
export function generateListItemAriaLabel(item: any, context: string): string {
  if (typeof item === 'string') {
    return `${context}: ${item}`;
  }
  if (item.title) {
    return `${context}: ${item.title}`;
  }
  if (item.name) {
    return `${context}: ${item.name}`;
  }
  return context;
}

/**
 * Generate ARIA label for action buttons
 * Provides context for screen readers
 */
export function generateActionButtonAriaLabel(action: string, itemName: string): string {
  return `${action} ${itemName}`;
}

/**
 * Generate ARIA label for status badges
 * Ensures status is announced to screen readers
 */
export function generateStatusAriaLabel(status: string, context: string): string {
  return `${context} status: ${status}`;
}

/**
 * Generate ARIA label for pagination controls
 * Helps users navigate through pages
 */
export function generatePaginationAriaLabel(currentPage: number, totalPages?: number): string {
  if (totalPages) {
    return `Page ${currentPage} of ${totalPages}`;
  }
  return `Page ${currentPage}`;
}

/**
 * Generate ARIA label for filter controls
 * Describes what the filter does
 */
export function generateFilterAriaLabel(filterName: string, filterValue?: string): string {
  if (filterValue) {
    return `Filter by ${filterName}: ${filterValue}`;
  }
  return `Filter by ${filterName}`;
}

/**
 * Generate ARIA label for sort controls
 * Describes the sort order
 */
export function generateSortAriaLabel(sortField: string, sortOrder: 'asc' | 'desc'): string {
  const order = sortOrder === 'asc' ? 'ascending' : 'descending';
  return `Sort by ${sortField} in ${order} order`;
}

/**
 * Generate ARIA label for loading states
 * Informs users that content is loading
 */
export function generateLoadingAriaLabel(context: string): string {
  return `Loading ${context}`;
}

/**
 * Generate ARIA label for error messages
 * Ensures errors are announced to screen readers
 */
export function generateErrorAriaLabel(errorMessage: string): string {
  return `Error: ${errorMessage}`;
}

/**
 * Generate ARIA label for modal dialogs
 * Describes the purpose of the modal
 */
export function generateModalAriaLabel(modalTitle: string): string {
  return `Dialog: ${modalTitle}`;
}

/**
 * Generate ARIA label for table headers
 * Helps users understand column content
 */
export function generateTableHeaderAriaLabel(columnName: string, sortable?: boolean): string {
  if (sortable) {
    return `${columnName}, sortable column`;
  }
  return columnName;
}

/**
 * Generate ARIA label for form fields
 * Provides context for form inputs
 */
export function generateFormFieldAriaLabel(fieldName: string, required?: boolean): string {
  if (required) {
    return `${fieldName}, required`;
  }
  return fieldName;
}

/**
 * Check if element should have keyboard focus
 * Determines if an element is keyboard accessible
 */
export function isKeyboardAccessible(element: HTMLElement): boolean {
  const tabindex = element.getAttribute('tabindex');
  const isNaturallyFocusable = ['BUTTON', 'A', 'INPUT', 'SELECT', 'TEXTAREA'].includes(
    element.tagName
  );
  
  return isNaturallyFocusable || (tabindex !== null && parseInt(tabindex) >= 0);
}

/**
 * Get all keyboard-accessible elements within a container
 * Useful for managing focus within modals or sections
 */
export function getKeyboardAccessibleElements(container: HTMLElement): HTMLElement[] {
  const selector = [
    'button',
    'a[href]',
    'input',
    'select',
    'textarea',
    '[tabindex]:not([tabindex="-1"])',
  ].join(',');
  
  return Array.from(container.querySelectorAll(selector));
}

/**
 * Focus first keyboard-accessible element in container
 * Useful for modal focus management
 */
export function focusFirstAccessibleElement(container: HTMLElement): void {
  const elements = getKeyboardAccessibleElements(container);
  if (elements.length > 0) {
    (elements[0] as HTMLElement).focus();
  }
}

/**
 * Focus last keyboard-accessible element in container
 * Useful for modal focus management
 */
export function focusLastAccessibleElement(container: HTMLElement): void {
  const elements = getKeyboardAccessibleElements(container);
  if (elements.length > 0) {
    (elements[elements.length - 1] as HTMLElement).focus();
  }
}

/**
 * Trap focus within a container (for modals)
 * Prevents focus from leaving the modal
 */
export function trapFocus(container: HTMLElement, event: KeyboardEvent): void {
  if (event.key !== 'Tab') return;

  const elements = getKeyboardAccessibleElements(container);
  if (elements.length === 0) return;

  const firstElement = elements[0] as HTMLElement;
  const lastElement = elements[elements.length - 1] as HTMLElement;
  const activeElement = document.activeElement as HTMLElement;

  if (event.shiftKey) {
    // Shift + Tab
    if (activeElement === firstElement) {
      event.preventDefault();
      lastElement.focus();
    }
  } else {
    // Tab
    if (activeElement === lastElement) {
      event.preventDefault();
      firstElement.focus();
    }
  }
}

/**
 * Announce message to screen readers
 * Uses aria-live region for dynamic announcements
 */
export function announceToScreenReader(message: string, priority: 'polite' | 'assertive' = 'polite'): void {
  const announcement = document.createElement('div');
  announcement.setAttribute('role', 'status');
  announcement.setAttribute('aria-live', priority);
  announcement.setAttribute('aria-atomic', 'true');
  announcement.className = 'sr-only'; // Visually hidden but available to screen readers
  announcement.textContent = message;
  
  document.body.appendChild(announcement);
  
  // Remove after announcement
  setTimeout(() => {
    document.body.removeChild(announcement);
  }, 1000);
}

/**
 * Check color contrast ratio (WCAG 2.1 AA)
 * Returns true if contrast ratio meets AA standards (4.5:1 for normal text, 3:1 for large text)
 */
export function checkColorContrast(foreground: string, background: string, largeText: boolean = false): boolean {
  const fgLuminance = getRelativeLuminance(foreground);
  const bgLuminance = getRelativeLuminance(background);
  
  const lighter = Math.max(fgLuminance, bgLuminance);
  const darker = Math.min(fgLuminance, bgLuminance);
  
  const contrastRatio = (lighter + 0.05) / (darker + 0.05);
  
  // AA standard: 4.5:1 for normal text, 3:1 for large text
  return largeText ? contrastRatio >= 3 : contrastRatio >= 4.5;
}

/**
 * Calculate relative luminance of a color
 * Used for contrast ratio calculation
 */
function getRelativeLuminance(color: string): number {
  const rgb = parseColor(color);
  if (!rgb) return 0;
  
  const [r, g, b] = rgb.map(c => {
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
  if (color.startsWith('#')) {
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
