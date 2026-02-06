/**
 * Form Validation Utilities
 * Provides functions for form validation and error handling
 * Requirements: 16.4
 */

import { getFieldErrors } from './errors';

/**
 * Validates a single field
 */
export function validateField(
  value: any,
  rules: ValidationRule[]
): string | null {
  for (const rule of rules) {
    const error = rule.validate(value);
    if (error) {
      return error;
    }
  }
  return null;
}

/**
 * Validates multiple fields
 */
export function validateFields(
  values: Record<string, any>,
  schema: Record<string, ValidationRule[]>
): Record<string, string> {
  const errors: Record<string, string> = {};

  for (const [field, rules] of Object.entries(schema)) {
    const error = validateField(values[field], rules);
    if (error) {
      errors[field] = error;
    }
  }

  return errors;
}

/**
 * Extracts field errors from API response
 */
export function extractFieldErrors(error: unknown): Record<string, string> {
  const fieldErrors = getFieldErrors(error);
  const result: Record<string, string> = {};

  for (const [field, messages] of Object.entries(fieldErrors)) {
    result[field] = Array.isArray(messages) ? messages[0] : messages;
  }

  return result;
}

/**
 * Validation rule interface
 */
export interface ValidationRule {
  validate: (value: any) => string | null;
}

/**
 * Common validation rules
 */
export const ValidationRules = {
  /**
   * Required field validation
   */
  required: (message = 'This field is required'): ValidationRule => ({
    validate: (value) => {
      if (!value || (typeof value === 'string' && value.trim() === '')) {
        return message;
      }
      return null;
    },
  }),

  /**
   * Email validation
   */
  email: (message = 'Please enter a valid email'): ValidationRule => ({
    validate: (value) => {
      if (!value) return null;
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      return emailRegex.test(value) ? null : message;
    },
  }),

  /**
   * Minimum length validation
   */
  minLength: (min: number, message?: string): ValidationRule => ({
    validate: (value) => {
      if (!value) return null;
      const len = typeof value === 'string' ? value.length : String(value).length;
      return len >= min ? null : message || `Minimum ${min} characters required`;
    },
  }),

  /**
   * Maximum length validation
   */
  maxLength: (max: number, message?: string): ValidationRule => ({
    validate: (value) => {
      if (!value) return null;
      const len = typeof value === 'string' ? value.length : String(value).length;
      return len <= max ? null : message || `Maximum ${max} characters allowed`;
    },
  }),

  /**
   * Pattern validation
   */
  pattern: (pattern: RegExp, message = 'Invalid format'): ValidationRule => ({
    validate: (value) => {
      if (!value) return null;
      return pattern.test(String(value)) ? null : message;
    },
  }),

  /**
   * Number validation
   */
  number: (message = 'Please enter a valid number'): ValidationRule => ({
    validate: (value) => {
      if (!value && value !== 0) return null;
      return !isNaN(Number(value)) ? null : message;
    },
  }),

  /**
   * Minimum value validation
   */
  min: (min: number, message?: string): ValidationRule => ({
    validate: (value) => {
      if (!value && value !== 0) return null;
      return Number(value) >= min ? null : message || `Minimum value is ${min}`;
    },
  }),

  /**
   * Maximum value validation
   */
  max: (max: number, message?: string): ValidationRule => ({
    validate: (value) => {
      if (!value && value !== 0) return null;
      return Number(value) <= max ? null : message || `Maximum value is ${max}`;
    },
  }),

  /**
   * Custom validation
   */
  custom: (validator: (value: any) => boolean, message = 'Invalid value'): ValidationRule => ({
    validate: (value) => {
      return validator(value) ? null : message;
    },
  }),
};

/**
 * Form state management hook helper
 */
export function useFormValidation<T extends Record<string, any>>(
  initialValues: T,
  schema: Record<keyof T, ValidationRule[]>
) {
  const [values, setValues] = React.useState<T>(initialValues);
  const [errors, setErrors] = React.useState<Record<string, string>>({});
  const [touched, setTouched] = React.useState<Record<string, boolean>>({});

  const validateForm = () => {
    const newErrors = validateFields(values, schema as any);
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (field: keyof T, value: any) => {
    setValues((prev) => ({ ...prev, [field]: value }));
    
    // Clear error when user starts typing
    if (errors[field as string]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[field as string];
        return newErrors;
      });
    }
  };

  const handleBlur = (field: keyof T) => {
    setTouched((prev) => ({ ...prev, [field]: true }));
    
    // Validate field on blur
    const rules = schema[field];
    if (rules) {
      const error = validateField(values[field], rules);
      if (error) {
        setErrors((prev) => ({ ...prev, [field]: error }));
      }
    }
  };

  const getFieldError = (field: keyof T): string | null => {
    return touched[field as string] ? (errors[field as string] || null) : null;
  };

  return {
    values,
    errors,
    touched,
    setValues,
    setErrors,
    validateForm,
    handleChange,
    handleBlur,
    getFieldError,
  };
}

// Add React import for the hook
import React from 'react';
