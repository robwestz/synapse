/**
 * @fileoverview Smart Pipelines Module - The Orchestration Layer
 * 
 * APEX Generation Metadata:
 * - Pattern: Fractal Decomposition
 * - Iteration: 1 (Probe)
 * - Signed by: Roxanne (Architect), Aria (Orchestrator)
 * 
 * This module is the "glue" that registers all pipeline components:
 * - Database entities (TypeORM)
 * - Queue system (BullMQ)  
 * - External integrations (SIE-X, BACOWR)
 */

import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { BullModule } from '@nestjs/bullmq';
import { EventEmitterModule } from '@nestjs/event-emitter';

// Controllers
import { PipelinesController } from './pipelines.controller';

// Services
import { PipelineRunnerService } from './engine/pipeline-runner.service';
import { PipelineProcessor } from './engine/pipeline.processor';

// Entities
import { Pipeline, PipelineExecution, PipelineTemplate } from './entities/pipeline.entity';

// External Integrations (assumes these exist in your platform)
import { IntegrationsModule } from '../integrations/integrations.module';

/**
 * Queue configuration for pipeline execution
 * Aria: Using Redis-backed BullMQ for reliable async processing
 */
const PIPELINE_QUEUE_CONFIG = {
  name: 'pipeline-queue',
  defaultJobOptions: {
    attempts: 3,
    backoff: {
      type: 'exponential' as const,
      delay: 1000,
    },
    removeOnComplete: 100, // Keep last 100 completed jobs
    removeOnFail: 50,      // Keep last 50 failed jobs for debugging
  },
};

@Module({
  imports: [
    // ═══════════════════════════════════════════════════════════════
    // DATABASE LAYER (Chen: Strict typing for data integrity)
    // ═══════════════════════════════════════════════════════════════
    TypeOrmModule.forFeature([
      Pipeline,
      PipelineExecution,
      PipelineTemplate,
    ]),

    // ═══════════════════════════════════════════════════════════════
    // QUEUE SYSTEM (Aria: Async execution with self-healing)
    // ═══════════════════════════════════════════════════════════════
    BullModule.registerQueue(PIPELINE_QUEUE_CONFIG),

    // ═══════════════════════════════════════════════════════════════
    // EVENT SYSTEM (For real-time status updates to frontend)
    // ═══════════════════════════════════════════════════════════════
    EventEmitterModule.forRoot(),

    // ═══════════════════════════════════════════════════════════════
    // EXTERNAL INTEGRATIONS (Leo: SIE-X brain + BACOWR muscles)
    // ═══════════════════════════════════════════════════════════════
    IntegrationsModule,
  ],

  controllers: [
    PipelinesController,
  ],

  providers: [
    // Core execution engine
    PipelineRunnerService,
    
    // BullMQ processor (worker that picks jobs from queue)
    PipelineProcessor,
  ],

  exports: [
    // Allow other modules to trigger pipelines programmatically
    PipelineRunnerService,
  ],
})
export class PipelinesModule {
  /**
   * Roxanne's Architecture Notes:
   * 
   * This module follows the "Clean Architecture" pattern:
   * 
   * ┌─────────────────────────────────────────────────────────────┐
   * │                    PipelinesController                      │
   * │                    (HTTP Interface)                         │
   * └─────────────────────────┬───────────────────────────────────┘
   *                           │
   * ┌─────────────────────────▼───────────────────────────────────┐
   * │                 PipelineRunnerService                       │
   * │                 (Business Logic)                            │
   * └─────────────────────────┬───────────────────────────────────┘
   *                           │
   *          ┌────────────────┼────────────────┐
   *          │                │                │
   *          ▼                ▼                ▼
   *    ┌──────────┐    ┌──────────┐    ┌──────────────┐
   *    │ TypeORM  │    │ BullMQ   │    │ Integrations │
   *    │ (Data)   │    │ (Queue)  │    │ (SIE-X/etc)  │
   *    └──────────┘    └──────────┘    └──────────────┘
   * 
   * The PipelineProcessor listens to BullMQ and calls back into
   * PipelineRunnerService. This separation allows:
   * 1. Horizontal scaling (multiple workers)
   * 2. Graceful failure handling
   * 3. Job persistence across restarts
   */
}
