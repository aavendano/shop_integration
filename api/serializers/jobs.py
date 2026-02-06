"""
Job serializers for API responses.

These serializers transform Job and JobLog models into render-ready JSON responses
for the Remix frontend. They provide complete job information including status,
progress, timestamps, and logs for monitoring background operations.
"""

from rest_framework import serializers
from api.models import Job, JobLog


class JobLogSerializer(serializers.ModelSerializer):
    """
    Serializer for job log entries.
    
    Returns log data in chronological order for display in job detail views.
    """
    
    class Meta:
        model = JobLog
        fields = ['timestamp', 'message']


class JobListSerializer(serializers.ModelSerializer):
    """
    Serializer for job list view.
    
    Provides summary data optimized for IndexTable display in Polaris,
    including job type, status, progress, and timing information.
    """
    
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = Job
        fields = [
            'id',
            'job_type',
            'status',
            'progress',
            'started_at',
            'completed_at',
            'duration',
            'error_message',
            'created_at',
        ]
    
    def get_duration(self, obj):
        """
        Get job duration in seconds.
        
        Returns None if job hasn't completed yet.
        """
        return obj.duration


class JobDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for job detail view.
    
    Provides complete job information including all log entries,
    formatted for direct consumption by Polaris Layout and Card components.
    """
    
    logs = JobLogSerializer(many=True, read_only=True)
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = Job
        fields = [
            'id',
            'job_type',
            'status',
            'progress',
            'started_at',
            'completed_at',
            'duration',
            'error_message',
            'logs',
            'created_at',
            'updated_at',
        ]
    
    def get_duration(self, obj):
        """
        Get job duration in seconds.
        
        Returns None if job hasn't completed yet.
        """
        return obj.duration
