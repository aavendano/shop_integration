"""
Unit tests for job serializers.

Tests verify that job serializers correctly transform Job and JobLog models
into render-ready JSON responses for the Remix frontend.
"""

import pytest
from django.utils import timezone
from datetime import timedelta
from api.models import Job, JobLog
from api.serializers import JobListSerializer, JobDetailSerializer, JobLogSerializer


@pytest.mark.django_db
class TestJobLogSerializer:
    """Test JobLogSerializer functionality."""
    
    def test_serialize_job_log(self):
        """Test that job log is serialized with timestamp and message."""
        # Create a job and log entry
        job = Job.objects.create(
            job_type='product_sync',
            status='running',
            progress=50
        )
        log = JobLog.objects.create(
            job=job,
            timestamp=timezone.now(),
            message="Processing product 1 of 10"
        )
        
        # Serialize
        serializer = JobLogSerializer(log)
        data = serializer.data
        
        # Verify fields
        assert 'timestamp' in data
        assert 'message' in data
        assert data['message'] == "Processing product 1 of 10"


@pytest.mark.django_db
class TestJobListSerializer:
    """Test JobListSerializer functionality."""
    
    def test_serialize_pending_job(self):
        """Test serialization of a pending job."""
        job = Job.objects.create(
            job_type='product_sync',
            status='pending',
            progress=0
        )
        
        serializer = JobListSerializer(job)
        data = serializer.data
        
        # Verify required fields
        assert data['id'] == job.id
        assert data['job_type'] == 'product_sync'
        assert data['status'] == 'pending'
        assert data['progress'] == 0
        assert data['started_at'] is None
        assert data['completed_at'] is None
        assert data['duration'] is None
        assert data['error_message'] is None
        assert 'created_at' in data
    
    def test_serialize_running_job(self):
        """Test serialization of a running job."""
        started = timezone.now()
        job = Job.objects.create(
            job_type='bulk_sync',
            status='running',
            progress=45,
            started_at=started
        )
        
        serializer = JobListSerializer(job)
        data = serializer.data
        
        assert data['status'] == 'running'
        assert data['progress'] == 45
        assert data['started_at'] is not None
        assert data['completed_at'] is None
        assert data['duration'] is None  # Not completed yet
    
    def test_serialize_completed_job_with_duration(self):
        """Test serialization of a completed job includes duration."""
        started = timezone.now()
        completed = started + timedelta(minutes=5)
        
        job = Job.objects.create(
            job_type='inventory_reconcile',
            status='completed',
            progress=100,
            started_at=started,
            completed_at=completed
        )
        
        serializer = JobListSerializer(job)
        data = serializer.data
        
        assert data['status'] == 'completed'
        assert data['progress'] == 100
        assert data['duration'] == 300.0  # 5 minutes in seconds
    
    def test_serialize_failed_job_with_error(self):
        """Test serialization of a failed job includes error message."""
        job = Job.objects.create(
            job_type='product_sync',
            status='failed',
            progress=25,
            started_at=timezone.now(),
            completed_at=timezone.now(),
            error_message="Shopify API error: Product not found"
        )
        
        serializer = JobListSerializer(job)
        data = serializer.data
        
        assert data['status'] == 'failed'
        assert data['error_message'] == "Shopify API error: Product not found"


@pytest.mark.django_db
class TestJobDetailSerializer:
    """Test JobDetailSerializer functionality."""
    
    def test_serialize_job_with_logs(self):
        """Test that job detail includes all log entries."""
        job = Job.objects.create(
            job_type='product_sync',
            status='completed',
            progress=100,
            started_at=timezone.now(),
            completed_at=timezone.now()
        )
        
        # Create multiple log entries
        JobLog.objects.create(
            job=job,
            timestamp=timezone.now(),
            message="Job started"
        )
        JobLog.objects.create(
            job=job,
            timestamp=timezone.now(),
            message="Processing products"
        )
        JobLog.objects.create(
            job=job,
            timestamp=timezone.now(),
            message="Job completed"
        )
        
        serializer = JobDetailSerializer(job)
        data = serializer.data
        
        # Verify logs are included
        assert 'logs' in data
        assert len(data['logs']) == 3
        assert data['logs'][0]['message'] == "Job started"
        assert data['logs'][2]['message'] == "Job completed"
    
    def test_serialize_job_detail_includes_all_fields(self):
        """Test that job detail includes all required fields."""
        started = timezone.now()
        completed = started + timedelta(minutes=2)
        
        job = Job.objects.create(
            job_type='bulk_sync',
            status='completed',
            progress=100,
            started_at=started,
            completed_at=completed,
            error_message=None
        )
        
        serializer = JobDetailSerializer(job)
        data = serializer.data
        
        # Verify all fields from requirements
        required_fields = [
            'id', 'job_type', 'status', 'progress',
            'started_at', 'completed_at', 'duration',
            'error_message', 'logs', 'created_at', 'updated_at'
        ]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        assert data['duration'] == 120.0  # 2 minutes in seconds
    
    def test_serialize_job_without_logs(self):
        """Test that job detail works even without log entries."""
        job = Job.objects.create(
            job_type='product_sync',
            status='pending',
            progress=0
        )
        
        serializer = JobDetailSerializer(job)
        data = serializer.data
        
        assert 'logs' in data
        assert len(data['logs']) == 0



@pytest.mark.django_db
class TestJobDetailView:
    """Test JobDetailView API endpoint."""
    
    def test_get_job_detail_success(self, client):
        """Test successful retrieval of job detail."""
        # Create a job with logs
        started = timezone.now()
        completed = started + timedelta(minutes=3)
        
        job = Job.objects.create(
            job_type='product_sync',
            status='completed',
            progress=100,
            started_at=started,
            completed_at=completed
        )
        
        JobLog.objects.create(
            job=job,
            timestamp=started,
            message="Job started"
        )
        JobLog.objects.create(
            job=job,
            timestamp=completed,
            message="Job completed successfully"
        )
        
        # Make request
        response = client.get(f'/api/admin/jobs/{job.id}/')
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Verify job data
        assert data['id'] == job.id
        assert data['job_type'] == 'product_sync'
        assert data['status'] == 'completed'
        assert data['progress'] == 100
        assert data['duration'] == 180.0  # 3 minutes
        
        # Verify logs are included
        assert 'logs' in data
        assert len(data['logs']) == 2
        assert data['logs'][0]['message'] == "Job started"
        assert data['logs'][1]['message'] == "Job completed successfully"
    
    def test_get_job_detail_not_found(self, client):
        """Test that requesting non-existent job returns 404."""
        response = client.get('/api/admin/jobs/99999/')
        
        assert response.status_code == 404
        data = response.json()
        assert 'detail' in data
        assert data['detail'] == 'Job not found'
    
    def test_get_job_detail_with_error_message(self, client):
        """Test job detail includes error message for failed jobs."""
        job = Job.objects.create(
            job_type='bulk_sync',
            status='failed',
            progress=50,
            started_at=timezone.now(),
            completed_at=timezone.now(),
            error_message="Shopify API rate limit exceeded"
        )
        
        response = client.get(f'/api/admin/jobs/{job.id}/')
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'failed'
        assert data['error_message'] == "Shopify API rate limit exceeded"
    
    def test_get_job_detail_running_job(self, client):
        """Test job detail for a currently running job."""
        job = Job.objects.create(
            job_type='inventory_reconcile',
            status='running',
            progress=65,
            started_at=timezone.now()
        )
        
        JobLog.objects.create(
            job=job,
            timestamp=timezone.now(),
            message="Reconciling inventory items"
        )
        
        response = client.get(f'/api/admin/jobs/{job.id}/')
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'running'
        assert data['progress'] == 65
        assert data['completed_at'] is None
        assert data['duration'] is None  # Not completed yet
        assert len(data['logs']) == 1
