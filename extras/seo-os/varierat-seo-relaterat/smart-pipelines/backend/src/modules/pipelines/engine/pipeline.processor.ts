/**
 * @fileoverview Pipeline Processor - BullMQ Job Consumer
 * 
 * APEX Generation Metadata:
 * - Signed by: Aria (Orchestrator), Roxanne (Infrastructure)
 * 
 * This is the "worker bee" that:
 * 1. Listens to the pipeline-queue
 * 2. Picks up jobs and delegates to PipelineRunnerService
 * 3. Handles crashes, retries, and dead-letter scenarios
 */

import { Processor, WorkerHost, OnWorkerEvent } from '@nestjs/bullmq';
import { Logger } from '@nestjs/common';
import { Job } from 'bullmq';
import { PipelineRunnerService, StepExecutionPayload } from './pipeline-runner.service';

@Processor('pipeline-queue', {
  // Roxanne: Concurrency settings for production
  concurrency: 5, // Process 5 jobs simultaneously
  limiter: {
    max: 100,
    duration: 60000, // Max 100 jobs per minute to prevent API overload
  },
})
export class PipelineProcessor extends WorkerHost {
  private readonly logger = new Logger(PipelineProcessor.name);

  constructor(private readonly runnerService: PipelineRunnerService) {
    super();
  }

  /**
   * Main job processor
   * Aria: This is where jobs from the queue are actually executed
   */
  async process(job: Job<StepExecutionPayload>): Promise<any> {
    const { executionId, stepId, retryCount } = job.data;

    this.logger.log(
      `Processing job ${job.id}: execution=${executionId}, step=${stepId}, retry=${retryCount}`,
    );

    try {
      // Delegate to the runner service
      await this.runnerService.executeStep(job.data);

      return { success: true, processedAt: new Date() };
    } catch (error) {
      this.logger.error(
        `Job ${job.id} failed: ${error.message}`,
        error.stack,
      );

      // Re-throw to trigger BullMQ's built-in retry mechanism
      throw error;
    }
  }

  // ═══════════════════════════════════════════════════════════════════════
  // WORKER EVENTS (Logging & Monitoring)
  // ═══════════════════════════════════════════════════════════════════════

  @OnWorkerEvent('active')
  onActive(job: Job) {
    this.logger.debug(
      `Job ${job.id} is now active (attempt ${job.attemptsMade + 1})`,
    );
  }

  @OnWorkerEvent('completed')
  onCompleted(job: Job, result: any) {
    this.logger.log(
      `Job ${job.id} completed successfully`,
    );
  }

  @OnWorkerEvent('failed')
  onFailed(job: Job, error: Error) {
    this.logger.error(
      `Job ${job.id} failed after ${job.attemptsMade} attempts: ${error.message}`,
    );

    // Aria: Here we could implement dead-letter queue logic
    // or send alerts for persistent failures
    if (job.attemptsMade >= (job.opts.attempts || 3)) {
      this.logger.warn(
        `Job ${job.id} has exhausted all retries, moving to dead-letter`,
      );
      // TODO: Implement dead-letter handling
    }
  }

  @OnWorkerEvent('progress')
  onProgress(job: Job, progress: number | object) {
    this.logger.debug(
      `Job ${job.id} progress: ${JSON.stringify(progress)}`,
    );
  }

  @OnWorkerEvent('stalled')
  onStalled(jobId: string) {
    this.logger.warn(
      `Job ${jobId} has stalled (worker may have crashed)`,
    );
  }

  @OnWorkerEvent('error')
  onError(error: Error) {
    this.logger.error(
      `Worker error: ${error.message}`,
      error.stack,
    );
  }
}
