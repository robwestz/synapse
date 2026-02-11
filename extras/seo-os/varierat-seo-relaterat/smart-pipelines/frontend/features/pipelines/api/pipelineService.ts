/**
 * @fileoverview Pipeline API Service
 * 
 * APEX Generation Metadata:
 * - Signed by: Roxanne (Infrastructure)
 * - Purpose: All HTTP communication with the pipelines backend
 * 
 * This service handles:
 * - CRUD operations for pipelines
 * - Execution triggers and status polling
 * - Template fetching
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import {
  Pipeline,
  PipelineSummary,
  PipelineExecution,
  ExecutionStatus,
  PipelineTemplate,
  CreatePipelineRequest,
  UpdatePipelineRequest,
  ExecutePipelineRequest,
  ExecutionStartedResponse,
  PaginatedResponse,
} from '../types/pipeline.types';

// ═══════════════════════════════════════════════════════════════════════════
// CONFIGURATION
// ═══════════════════════════════════════════════════════════════════════════

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api/v1';

// ═══════════════════════════════════════════════════════════════════════════
// ERROR HANDLING
// ═══════════════════════════════════════════════════════════════════════════

export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public details?: any,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

function handleApiError(error: AxiosError): never {
  if (error.response) {
    const data = error.response.data as any;
    throw new ApiError(
      data.message || 'An error occurred',
      error.response.status,
      data,
    );
  }
  throw new ApiError('Network error', 0);
}

// ═══════════════════════════════════════════════════════════════════════════
// API CLIENT
// ═══════════════════════════════════════════════════════════════════════════

class PipelineApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: `${API_BASE_URL}/pipelines`,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add auth token to all requests
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('accessToken');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Handle errors globally
    this.client.interceptors.response.use(
      (response) => response,
      (error) => handleApiError(error),
    );
  }

  // ═══════════════════════════════════════════════════════════════════════
  // PIPELINE CRUD
  // ═══════════════════════════════════════════════════════════════════════

  /**
   * Create a new pipeline
   */
  async createPipeline(data: CreatePipelineRequest): Promise<Pipeline> {
    const response = await this.client.post<Pipeline>('/', data);
    return response.data;
  }

  /**
   * List all pipelines with pagination and filters
   */
  async listPipelines(params?: {
    page?: number;
    limit?: number;
    search?: string;
    isActive?: boolean;
    tags?: string[];
    sortBy?: string;
    sortOrder?: 'asc' | 'desc';
  }): Promise<PaginatedResponse<PipelineSummary>> {
    const response = await this.client.get<PaginatedResponse<PipelineSummary>>('/', {
      params,
    });
    return response.data;
  }

  /**
   * Get a single pipeline by ID
   */
  async getPipeline(id: string): Promise<Pipeline> {
    const response = await this.client.get<Pipeline>(`/${id}`);
    return response.data;
  }

  /**
   * Update a pipeline
   */
  async updatePipeline(id: string, data: UpdatePipelineRequest): Promise<Pipeline> {
    const response = await this.client.put<Pipeline>(`/${id}`, data);
    return response.data;
  }

  /**
   * Delete a pipeline
   */
  async deletePipeline(id: string): Promise<void> {
    await this.client.delete(`/${id}`);
  }

  /**
   * Duplicate a pipeline
   */
  async duplicatePipeline(id: string): Promise<Pipeline> {
    const response = await this.client.post<Pipeline>(`/${id}/duplicate`);
    return response.data;
  }

  /**
   * Toggle pipeline active state
   */
  async togglePipeline(id: string): Promise<{ isActive: boolean }> {
    const response = await this.client.put<{ isActive: boolean }>(`/${id}/toggle`);
    return response.data;
  }

  // ═══════════════════════════════════════════════════════════════════════
  // EXECUTION
  // ═══════════════════════════════════════════════════════════════════════

  /**
   * Execute a pipeline
   */
  async executePipeline(
    id: string,
    data?: ExecutePipelineRequest,
  ): Promise<ExecutionStartedResponse> {
    const response = await this.client.post<ExecutionStartedResponse>(
      `/${id}/execute`,
      data || {},
    );
    return response.data;
  }

  /**
   * Validate a pipeline without executing (dry run)
   */
  async validatePipeline(id: string): Promise<ExecutionStartedResponse> {
    return this.executePipeline(id, { dryRun: true });
  }

  /**
   * List executions for a pipeline
   */
  async listExecutions(
    pipelineId: string,
    params?: {
      page?: number;
      limit?: number;
      status?: string;
      startedAfter?: string;
      startedBefore?: string;
    },
  ): Promise<PaginatedResponse<ExecutionStatus>> {
    const response = await this.client.get<PaginatedResponse<ExecutionStatus>>(
      `/${pipelineId}/executions`,
      { params },
    );
    return response.data;
  }

  /**
   * Get execution status
   */
  async getExecution(executionId: string): Promise<ExecutionStatus> {
    const response = await this.client.get<ExecutionStatus>(
      `/executions/${executionId}`,
    );
    return response.data;
  }

  /**
   * Cancel a running execution
   */
  async cancelExecution(executionId: string): Promise<{ message: string }> {
    const response = await this.client.post<{ message: string }>(
      `/executions/${executionId}/cancel`,
    );
    return response.data;
  }

  /**
   * Poll execution status until complete
   * Returns an async generator for real-time updates
   */
  async *pollExecution(
    executionId: string,
    intervalMs: number = 2000,
    maxAttempts: number = 60,
  ): AsyncGenerator<ExecutionStatus> {
    let attempts = 0;

    while (attempts < maxAttempts) {
      const status = await this.getExecution(executionId);
      yield status;

      if (['COMPLETED', 'FAILED', 'CANCELLED'].includes(status.status)) {
        return;
      }

      await new Promise((resolve) => setTimeout(resolve, intervalMs));
      attempts++;
    }

    throw new Error('Execution polling timed out');
  }

  // ═══════════════════════════════════════════════════════════════════════
  // TEMPLATES
  // ═══════════════════════════════════════════════════════════════════════

  /**
   * List available templates
   */
  async listTemplates(category?: string): Promise<PipelineTemplate[]> {
    const response = await this.client.get<PipelineTemplate[]>('/templates', {
      params: category ? { category } : undefined,
    });
    return response.data;
  }

  /**
   * Create a pipeline from a template
   */
  async useTemplate(templateId: string, name?: string): Promise<Pipeline> {
    const response = await this.client.post<Pipeline>(
      `/templates/${templateId}/use`,
      { name },
    );
    return response.data;
  }
}

// Export singleton instance
export const pipelineApi = new PipelineApiService();

// Export class for testing/mocking
export { PipelineApiService };
