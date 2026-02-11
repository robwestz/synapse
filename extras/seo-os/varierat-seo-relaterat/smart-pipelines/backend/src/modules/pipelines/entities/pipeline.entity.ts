/**
 * @fileoverview Pipeline Database Entities
 * 
 * APEX Generation Metadata:
 * - Signed by: Chen (Data Alchemist)
 * - Key Decision: JSONB for graph storage (future-proof)
 * 
 * These entities define the persistence layer for:
 * - Pipeline definitions (the "blueprint")
 * - Pipeline executions (the "runs")
 * - Pipeline templates (pre-built workflows)
 */

import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
  ManyToOne,
  OneToMany,
  Index,
  JoinColumn,
} from 'typeorm';

// ═══════════════════════════════════════════════════════════════════════════
// TYPE DEFINITIONS (Chen: Strict interfaces for data integrity)
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Node types available in the pipeline builder
 * Leo: These are SEO-specific operations
 */
export enum NodeActionType {
  // ─── Triggers ───
  TRIGGER_MANUAL = 'TRIGGER_MANUAL',
  TRIGGER_SCHEDULE = 'TRIGGER_SCHEDULE',
  TRIGGER_WEBHOOK = 'TRIGGER_WEBHOOK',
  TRIGGER_RSS = 'TRIGGER_RSS',
  
  // ─── SEO Intelligence Actions (SIE-X) ───
  ACTION_SIEX_ANALYZE = 'ACTION_SIEX_ANALYZE',
  ACTION_SIEX_EXTRACT_ENTITIES = 'ACTION_SIEX_EXTRACT_ENTITIES',
  ACTION_SIEX_COMPARE_SERP = 'ACTION_SIEX_COMPARE_SERP',
  ACTION_SERP_CHECK = 'ACTION_SERP_CHECK',
  
  // ─── Content Generation Actions (BACOWR) ───
  ACTION_BACOWR_GENERATE = 'ACTION_BACOWR_GENERATE',
  ACTION_BACOWR_REWRITE = 'ACTION_BACOWR_REWRITE',
  ACTION_BACOWR_PATCH = 'ACTION_BACOWR_PATCH',
  
  // ─── Data Actions ───
  ACTION_HTTP_REQUEST = 'ACTION_HTTP_REQUEST',
  ACTION_SEND_EMAIL = 'ACTION_SEND_EMAIL',
  ACTION_SLACK_NOTIFY = 'ACTION_SLACK_NOTIFY',
  ACTION_SAVE_TO_DB = 'ACTION_SAVE_TO_DB',
  
  // ─── Logic Nodes (Aria: Agentic control flow) ───
  LOGIC_CONDITION = 'LOGIC_CONDITION',
  LOGIC_DELAY = 'LOGIC_DELAY',
  LOGIC_LOOP = 'LOGIC_LOOP',
  LOGIC_SWITCH = 'LOGIC_SWITCH',
  LOGIC_MERGE = 'LOGIC_MERGE',
}

/**
 * Execution status for pipelines
 */
export enum PipelineExecutionStatus {
  PENDING = 'PENDING',
  QUEUED = 'QUEUED',
  RUNNING = 'RUNNING',
  PAUSED = 'PAUSED',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  CANCELLED = 'CANCELLED',
}

/**
 * Retry configuration for nodes
 * Aria: Self-healing capabilities
 */
export interface RetryConfig {
  maxAttempts: number;
  backoffType: 'fixed' | 'exponential';
  backoffDelay: number; // milliseconds
}

/**
 * Input mapping configuration
 * Chen: How data flows between nodes using {{step_id.path}} syntax
 */
export interface InputMapping {
  [key: string]: string | number | boolean | InputMapping;
}

/**
 * A single node in the pipeline graph
 */
export interface PipelineNode {
  id: string;
  type: NodeActionType;
  label: string;
  position: { x: number; y: number };
  
  // Configuration
  inputs: InputMapping;
  config?: Record<string, any>;
  
  // Error handling (Aria)
  retryConfig?: RetryConfig;
  timeoutMs?: number;
  onError?: 'fail' | 'continue' | 'retry';
}

/**
 * An edge connecting two nodes
 */
export interface PipelineEdge {
  id: string;
  source: string;      // Source node ID
  target: string;      // Target node ID
  sourceHandle?: string; // For conditional nodes: 'true', 'false', 'default'
  label?: string;
}

/**
 * The complete pipeline definition (graph structure)
 * Chen: Stored as JSONB for flexibility
 */
export interface PipelineDefinition {
  version: string;     // Schema version for migrations
  nodes: PipelineNode[];
  edges: PipelineEdge[];
  variables?: Record<string, any>; // Global variables for the pipeline
}

/**
 * Execution context - data flowing through the pipeline
 */
export interface ExecutionContext {
  trigger: Record<string, any>;
  [stepId: string]: any;
}

/**
 * Step execution log entry
 */
export interface StepExecutionLog {
  stepId: string;
  nodeType: NodeActionType;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  startedAt?: Date;
  completedAt?: Date;
  input?: any;
  output?: any;
  error?: string;
  retryCount?: number;
}

// ═══════════════════════════════════════════════════════════════════════════
// DATABASE ENTITIES
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Main Pipeline entity - the "blueprint"
 */
@Entity('pipelines')
@Index(['ownerId', 'isActive'])
@Index(['createdAt'])
export class Pipeline {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ length: 255 })
  name: string;

  @Column({ type: 'text', nullable: true })
  description: string;

  @Column({ default: false })
  isActive: boolean;

  @Column({ default: false })
  isTemplate: boolean;

  /**
   * The ID of the trigger node (entry point)
   */
  @Column({ length: 100 })
  triggerNodeId: string;

  /**
   * Chen: JSONB storage for the entire graph structure
   * This allows flexible querying and future schema evolution
   */
  @Column({ type: 'jsonb' })
  definition: PipelineDefinition;

  /**
   * Optional cron expression for scheduled pipelines
   */
  @Column({ length: 100, nullable: true })
  cronExpression: string;

  /**
   * Owner relationship (assumes User entity exists)
   */
  @Column({ type: 'uuid' })
  ownerId: string;

  /**
   * Execution statistics (denormalized for performance)
   */
  @Column({ default: 0 })
  totalExecutions: number;

  @Column({ default: 0 })
  successfulExecutions: number;

  @Column({ default: 0 })
  failedExecutions: number;

  @Column({ type: 'timestamp', nullable: true })
  lastExecutedAt: Date;

  /**
   * Metadata
   */
  @Column({ type: 'jsonb', nullable: true })
  metadata: Record<string, any>;

  @Column({ type: 'simple-array', nullable: true })
  tags: string[];

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;

  // Relations
  @OneToMany(() => PipelineExecution, (execution) => execution.pipeline)
  executions: PipelineExecution[];
}

/**
 * Pipeline Execution entity - a single "run"
 */
@Entity('pipeline_executions')
@Index(['pipelineId', 'status'])
@Index(['startedAt'])
@Index(['ownerId', 'status'])
export class PipelineExecution {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ type: 'uuid' })
  pipelineId: string;

  @ManyToOne(() => Pipeline, (pipeline) => pipeline.executions, { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'pipelineId' })
  pipeline: Pipeline;

  @Column({
    type: 'enum',
    enum: PipelineExecutionStatus,
    default: PipelineExecutionStatus.PENDING,
  })
  status: PipelineExecutionStatus;

  /**
   * Current step being executed (for UI progress display)
   */
  @Column({ length: 100, nullable: true })
  currentStepId: string;

  /**
   * Chen: The execution context - all data flowing through the pipeline
   * Format: { trigger: {...}, step_1: {...}, step_2: {...} }
   */
  @Column({ type: 'jsonb', default: {} })
  context: ExecutionContext;

  /**
   * Detailed log of each step's execution
   * Roxanne: Essential for debugging failed pipelines
   */
  @Column({ type: 'jsonb', default: [] })
  stepLogs: StepExecutionLog[];

  /**
   * Error information if pipeline failed
   */
  @Column({ type: 'text', nullable: true })
  error: string;

  @Column({ length: 100, nullable: true })
  errorStepId: string;

  /**
   * Retry tracking
   */
  @Column({ default: 0 })
  retryCount: number;

  @Column({ nullable: true })
  parentExecutionId: string; // For retry lineage

  /**
   * Owner (for multi-tenant queries)
   */
  @Column({ type: 'uuid' })
  ownerId: string;

  /**
   * Timing
   */
  @CreateDateColumn()
  startedAt: Date;

  @Column({ type: 'timestamp', nullable: true })
  completedAt: Date;

  /**
   * Duration in milliseconds (calculated on completion)
   */
  @Column({ type: 'int', nullable: true })
  durationMs: number;

  /**
   * Token/cost tracking (for LLM-heavy pipelines)
   */
  @Column({ type: 'jsonb', nullable: true })
  usage: {
    totalTokens?: number;
    estimatedCostUsd?: number;
    apiCalls?: number;
  };
}

/**
 * Pipeline Template entity - pre-built workflows
 * Marcus: For the "Wizard" feature
 */
@Entity('pipeline_templates')
@Index(['category'])
@Index(['isPublic'])
export class PipelineTemplate {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ length: 255 })
  name: string;

  @Column({ type: 'text' })
  description: string;

  @Column({ length: 100 })
  category: string; // e.g., 'competitor-monitoring', 'content-generation'

  /**
   * The template definition (same structure as Pipeline)
   */
  @Column({ type: 'jsonb' })
  definition: PipelineDefinition;

  /**
   * Icon for UI display
   */
  @Column({ length: 100, nullable: true })
  icon: string;

  /**
   * Complexity indicator for user guidance
   */
  @Column({ default: 1 })
  complexity: number; // 1-5

  /**
   * Estimated execution time
   */
  @Column({ length: 50, nullable: true })
  estimatedDuration: string; // e.g., "2-5 minutes"

  /**
   * Required integrations
   */
  @Column({ type: 'simple-array', nullable: true })
  requiredIntegrations: string[]; // e.g., ['siex', 'bacowr', 'slack']

  /**
   * Public templates are visible to all users
   */
  @Column({ default: false })
  isPublic: boolean;

  /**
   * Creator (null for system templates)
   */
  @Column({ type: 'uuid', nullable: true })
  creatorId: string;

  /**
   * Usage statistics
   */
  @Column({ default: 0 })
  usageCount: number;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}
