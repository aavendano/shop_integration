"""Persistence adapters for canonical product data."""

from .django_adapter import PersistOptions, PersistSummary, persist_records

__all__ = ["PersistOptions", "PersistSummary", "persist_records"]
