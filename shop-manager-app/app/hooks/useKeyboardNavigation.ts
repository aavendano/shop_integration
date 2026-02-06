/**
 * useKeyboardNavigation Hook
 * Provides keyboard navigation support for interactive elements
 * Requirements: 17.4
 */

import { useEffect, useRef, useCallback } from "react";

/**
 * Hook for managing keyboard navigation in lists and tables
 * Supports arrow keys, Enter, and Escape
 */
export function useKeyboardNavigation(
  containerRef: React.RefObject<HTMLElement>,
  onSelect?: (index: number) => void,
  onEscape?: () => void
) {
  const currentIndexRef = useRef(0);

  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!containerRef.current) return;

      const focusableElements = Array.from(
        containerRef.current.querySelectorAll(
          "button, a[href], input, select, textarea, [tabindex]:not([tabindex='-1'])"
        )
      ) as HTMLElement[];

      if (focusableElements.length === 0) return;

      switch (event.key) {
        case "ArrowDown":
        case "ArrowRight":
          event.preventDefault();
          currentIndexRef.current = Math.min(
            currentIndexRef.current + 1,
            focusableElements.length - 1
          );
          focusableElements[currentIndexRef.current].focus();
          break;

        case "ArrowUp":
        case "ArrowLeft":
          event.preventDefault();
          currentIndexRef.current = Math.max(currentIndexRef.current - 1, 0);
          focusableElements[currentIndexRef.current].focus();
          break;

        case "Home":
          event.preventDefault();
          currentIndexRef.current = 0;
          focusableElements[0].focus();
          break;

        case "End":
          event.preventDefault();
          currentIndexRef.current = focusableElements.length - 1;
          focusableElements[focusableElements.length - 1].focus();
          break;

        case "Enter":
          event.preventDefault();
          if (onSelect) {
            onSelect(currentIndexRef.current);
          }
          (focusableElements[currentIndexRef.current] as HTMLElement).click();
          break;

        case "Escape":
          event.preventDefault();
          if (onEscape) {
            onEscape();
          }
          break;

        default:
          break;
      }
    },
    [containerRef, onSelect, onEscape]
  );

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    container.addEventListener("keydown", handleKeyDown);
    return () => {
      container.removeEventListener("keydown", handleKeyDown);
    };
  }, [handleKeyDown, containerRef]);
}

/**
 * Hook for managing focus trap in modals
 * Prevents focus from leaving the modal
 */
export function useFocusTrap(
  containerRef: React.RefObject<HTMLElement>,
  isActive: boolean = true
) {
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!isActive || !containerRef.current) return;

      if (event.key !== "Tab") return;

      const focusableElements = Array.from(
        containerRef.current.querySelectorAll(
          "button, a[href], input, select, textarea, [tabindex]:not([tabindex='-1'])"
        )
      ) as HTMLElement[];

      if (focusableElements.length === 0) return;

      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];
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
    },
    [containerRef, isActive]
  );

  useEffect(() => {
    if (!isActive) return;

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [handleKeyDown, isActive]);
}

/**
 * Hook for managing focus on element mount
 * Useful for modals and dialogs
 */
export function useAutoFocus(
  containerRef: React.RefObject<HTMLElement>,
  shouldFocus: boolean = true
) {
  useEffect(() => {
    if (!shouldFocus || !containerRef.current) return;

    const focusableElements = Array.from(
      containerRef.current.querySelectorAll(
        "button, a[href], input, select, textarea, [tabindex]:not([tabindex='-1'])"
      )
    ) as HTMLElement[];

    if (focusableElements.length > 0) {
      focusableElements[0].focus();
    }
  }, [shouldFocus, containerRef]);
}

/**
 * Hook for managing skip links
 * Allows users to skip to main content
 */
export function useSkipLink(targetId: string) {
  const handleSkipLink = useCallback(() => {
    const target = document.getElementById(targetId);
    if (target) {
      target.focus();
      target.scrollIntoView({ behavior: "smooth" });
    }
  }, [targetId]);

  return handleSkipLink;
}

/**
 * Hook for managing keyboard shortcuts
 * Allows custom keyboard shortcuts for actions
 */
export function useKeyboardShortcut(
  key: string,
  callback: () => void,
  ctrlKey: boolean = false,
  shiftKey: boolean = false,
  altKey: boolean = false
) {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (
        event.key === key &&
        event.ctrlKey === ctrlKey &&
        event.shiftKey === shiftKey &&
        event.altKey === altKey
      ) {
        event.preventDefault();
        callback();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [key, callback, ctrlKey, shiftKey, altKey]);
}

/**
 * Hook for managing Enter key submission
 * Useful for forms and search inputs
 */
export function useEnterKeySubmit(
  callback: () => void,
  enabled: boolean = true
) {
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (enabled && event.key === "Enter") {
        event.preventDefault();
        callback();
      }
    },
    [callback, enabled]
  );

  return handleKeyDown;
}

/**
 * Hook for managing Escape key close
 * Useful for modals and dropdowns
 */
export function useEscapeKeyClose(
  callback: () => void,
  enabled: boolean = true
) {
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (enabled && event.key === "Escape") {
        event.preventDefault();
        callback();
      }
    },
    [callback, enabled]
  );

  return handleKeyDown;
}

/**
 * Hook for managing arrow key navigation in grids
 * Supports 2D navigation with arrow keys
 */
export function useGridKeyboardNavigation(
  containerRef: React.RefObject<HTMLElement>,
  columns: number = 3
) {
  const currentIndexRef = useRef(0);

  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!containerRef.current) return;

      const focusableElements = Array.from(
        containerRef.current.querySelectorAll(
          "button, a[href], input, select, textarea, [tabindex]:not([tabindex='-1'])"
        )
      ) as HTMLElement[];

      if (focusableElements.length === 0) return;

      const currentIndex = currentIndexRef.current;
      let newIndex = currentIndex;

      switch (event.key) {
        case "ArrowDown":
          event.preventDefault();
          newIndex = Math.min(currentIndex + columns, focusableElements.length - 1);
          break;

        case "ArrowUp":
          event.preventDefault();
          newIndex = Math.max(currentIndex - columns, 0);
          break;

        case "ArrowRight":
          event.preventDefault();
          newIndex = Math.min(currentIndex + 1, focusableElements.length - 1);
          break;

        case "ArrowLeft":
          event.preventDefault();
          newIndex = Math.max(currentIndex - 1, 0);
          break;

        case "Home":
          event.preventDefault();
          newIndex = 0;
          break;

        case "End":
          event.preventDefault();
          newIndex = focusableElements.length - 1;
          break;

        default:
          return;
      }

      currentIndexRef.current = newIndex;
      focusableElements[newIndex].focus();
    },
    [containerRef, columns]
  );

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    container.addEventListener("keydown", handleKeyDown);
    return () => {
      container.removeEventListener("keydown", handleKeyDown);
    };
  }, [handleKeyDown, containerRef]);
}
