"""
API models for background jobs and processes.
"""

from django.db import models
from django.utils import timezone


class Job(models.Model):
    """
    Model for tracking background jobs and long-running operations.
    
    This model stores information about asynchronous tasks such as
    product syncs, inventory reconciliation, and bulk operations.
    """
    
    JOB_TYPE_CHOICES = [
        ('product_sync', 'Product Sync'),
        ('bulk_sync', 'Bulk Product Sync'),
        ('inventory_reconcile', 'Inventory Reconciliation'),
        ('order_import', 'Order Import'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    job_type = models.CharField(
        max_length=50,
        choices=JOB_TYPE_CHOICES,
        help_text="Type of background job"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Current status of the job"
    )
    progress = models.IntegerField(
        default=0,
        help_text="Progress percentage (0-100)"
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the job started execution"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the job completed (success or failure)"
    )
    error_message = models.TextField(
        null=True,
        blank=True,
        help_text="Error message if job failed"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the job was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When the job was last updated"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'job_type']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_job_type_display()} - {self.get_status_display()}"
    
    @property
    def duration(self):
        """
        Calculate job duration in seconds.
        
        Returns None if job hasn't started or completed.
        """
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class JobLog(models.Model):
    """
    Model for storing log entries for jobs.
    
    Each job can have multiple log entries tracking its progress
    and any issues encountered during execution.
    """
    
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='logs',
        help_text="The job this log entry belongs to"
    )
    timestamp = models.DateTimeField(
        default=timezone.now,
        help_text="When this log entry was created"
    )
    message = models.TextField(
        help_text="Log message content"
    )
    
    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['job', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.job.id} - {self.timestamp}: {self.message[:50]}"
