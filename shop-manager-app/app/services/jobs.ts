/**
 * Jobs Service
 * Handles all job-related API operations
 */

import { ApiClient } from './api';
import { JobListItem, JobDetail } from '../types/jobs';
import { PaginatedResponse } from '../types/api';

export class JobsService {
  constructor(private api: ApiClient) {}

  async list(params?: {
    page?: number;
    page_size?: number;
    status?: string;
    job_type?: string;
  }): Promise<PaginatedResponse<JobListItem>> {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          queryParams.append(key, String(value));
        }
      });
    }

    const endpoint = `/api/admin/jobs/?${queryParams.toString()}`;
    return this.api.get<PaginatedResponse<JobListItem>>(endpoint);
  }

  async get(id: number): Promise<JobDetail> {
    return this.api.get<JobDetail>(`/api/admin/jobs/${id}/`);
  }
}
