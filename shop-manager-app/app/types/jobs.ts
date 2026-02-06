/**
 * Jobs Types
 * Defines TypeScript interfaces for job-related API responses
 */

export interface JobListItem {
  id: number;
  job_type: string;
  status: 'running' | 'completed' | 'failed' | 'pending';
  progress: number;
  started_at: string;
  completed_at: string | null;
  error_message: string | null;
}

export interface JobDetail {
  id: number;
  job_type: string;
  status: 'running' | 'completed' | 'failed' | 'pending';
  progress: number;
  started_at: string;
  completed_at: string | null;
  logs: Array<{
    timestamp: string;
    message: string;
  }>;
}
