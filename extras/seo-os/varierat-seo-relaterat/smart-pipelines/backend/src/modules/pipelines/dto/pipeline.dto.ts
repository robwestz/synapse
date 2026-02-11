/**
 * @fileoverview Pipeline DTOs (Data Transfer Objects)
 * 
 * APEX Generation Metadata:
 * - Signed by: Roxanne (Architect)
 * - Purpose: Strict validation of all incoming data
 * 
 * These DTOs ensure that:
 * 1. Frontend can't send malformed data
 * 2. API responses are consistent
 * 3. TypeScript catches errors at compile time
 */

import {
  IsString,
  IsBoolean,
  IsOptional,
  IsArray,
  IsObject,
  IsEnum,
  IsUUID,
  IsInt,
  Min,
  Max,
  ValidateNested,
  IsNotEmpty,
  MaxLength,
  MinLength,
  Matches,
} from 'class-validator';
import { Type } from 'class-transformer';
import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import {
  NodeActionType,
  PipelineDefinition,
  PipelineNode,
  PipelineEdge,
  PipelineExecutionStatus,
  RetryConfig,
} from '../entities/pipeline.entity';

// ═══════════════════════════════════════════════════════════════════════════
// NESTED DTOs (Building blocks)
// ═══════════════════════════════════════════════════════════════════════════

export class PositionDto {
  @ApiProperty({ example: 250 })
  @IsInt()
  x: number;

  @ApiProperty({ example: 100 })
  @IsInt()
  y: number;
}

export class RetryConfigDto implements RetryConfig {
  @ApiProperty({ example: 3 })
  @IsInt()
  @Min(1)
  @Max(10)
  maxAttempts: number;

  @ApiProperty({ enum: ['fixed', 'exponential'], example: 'exponential' })
  @IsEnum(['fixed', 'exponential'])
  backoffType: 'fixed' | 'exponential';

  @ApiProperty({ example: 1000 })
  @IsInt()
  @Min(100)
  @Max(60000)
  backoffDelay: number;
}

export class PipelineNodeDto implements PipelineNode {
  @ApiProperty({ example: 'node_abc123' })
  @IsString()
  @IsNotEmpty()
  @MaxLength(100)
  id: string;

  @ApiProperty({ enum: NodeActionType, example: NodeActionType.ACTION_BACOWR_GENERATE })
  @IsEnum(NodeActionType)
  type: NodeActionType;

  @ApiProperty({ example: 'Generate Article' })
  @IsString()
  @MaxLength(100)
  label: string;

  @ApiProperty({ type: PositionDto })
  @ValidateNested()
  @Type(() => PositionDto)
  position: PositionDto;

  @ApiProperty({ 
    example: { topic: '{{trigger.keyword}}', tone: 'professional' },
    description: 'Input mappings using {{step_id.path}} syntax'
  })
  @IsObject()
  inputs: Record<string, any>;

  @ApiPropertyOptional({ example: { maxTokens: 4000 } })
  @IsOptional()
  @IsObject()
  config?: Record<string, any>;

  @ApiPropertyOptional({ type: RetryConfigDto })
  @IsOptional()
  @ValidateNested()
  @Type(() => RetryConfigDto)
  retryConfig?: RetryConfigDto;

  @ApiPropertyOptional({ example: 30000, description: 'Timeout in milliseconds' })
  @IsOptional()
  @IsInt()
  @Min(1000)
  @Max(600000) // Max 10 minutes
  timeoutMs?: number;

  @ApiPropertyOptional({ enum: ['fail', 'continue', 'retry'], example: 'retry' })
  @IsOptional()
  @IsEnum(['fail', 'continue', 'retry'])
  onError?: 'fail' | 'continue' | 'retry';
}

export class PipelineEdgeDto implements PipelineEdge {
  @ApiProperty({ example: 'edge_xyz789' })
  @IsString()
  @IsNotEmpty()
  @MaxLength(100)
  id: string;

  @ApiProperty({ example: 'node_abc123' })
  @IsString()
  @IsNotEmpty()
  source: string;

  @ApiProperty({ example: 'node_def456' })
  @IsString()
  @IsNotEmpty()
  target: string;

  @ApiPropertyOptional({ example: 'true', description: 'For conditional nodes' })
  @IsOptional()
  @IsString()
  @MaxLength(50)
  sourceHandle?: string;

  @ApiPropertyOptional({ example: 'On Success' })
  @IsOptional()
  @IsString()
  @MaxLength(100)
  label?: string;
}

export class PipelineDefinitionDto implements PipelineDefinition {
  @ApiProperty({ example: '1.0.0' })
  @IsString()
  @Matches(/^\d+\.\d+\.\d+$/, { message: 'Version must be semver format (e.g., 1.0.0)' })
  version: string;

  @ApiProperty({ type: [PipelineNodeDto] })
  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => PipelineNodeDto)
  nodes: PipelineNodeDto[];

  @ApiProperty({ type: [PipelineEdgeDto] })
  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => PipelineEdgeDto)
  edges: PipelineEdgeDto[];

  @ApiPropertyOptional({ example: { apiKey: '{{env.API_KEY}}' } })
  @IsOptional()
  @IsObject()
  variables?: Record<string, any>;
}

// ═══════════════════════════════════════════════════════════════════════════
// REQUEST DTOs (What the client sends)
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Create a new pipeline
 */
export class CreatePipelineDto {
  @ApiProperty({ example: 'Competitor Monitor' })
  @IsString()
  @IsNotEmpty()
  @MinLength(3)
  @MaxLength(255)
  name: string;

  @ApiPropertyOptional({ example: 'Monitors competitor URLs and generates counter-content' })
  @IsOptional()
  @IsString()
  @MaxLength(2000)
  description?: string;

  @ApiProperty({ example: 'trigger_1' })
  @IsString()
  @IsNotEmpty()
  triggerNodeId: string;

  @ApiProperty({ type: PipelineDefinitionDto })
  @ValidateNested()
  @Type(() => PipelineDefinitionDto)
  definition: PipelineDefinitionDto;

  @ApiPropertyOptional({ example: '0 9 * * 1', description: 'Cron expression for scheduled pipelines' })
  @IsOptional()
  @IsString()
  @MaxLength(100)
  cronExpression?: string;

  @ApiPropertyOptional({ example: ['seo', 'content'] })
  @IsOptional()
  @IsArray()
  @IsString({ each: true })
  tags?: string[];

  @ApiPropertyOptional({ example: { priority: 'high' } })
  @IsOptional()
  @IsObject()
  metadata?: Record<string, any>;
}

/**
 * Update an existing pipeline
 */
export class UpdatePipelineDto {
  @ApiPropertyOptional({ example: 'Updated Pipeline Name' })
  @IsOptional()
  @IsString()
  @MinLength(3)
  @MaxLength(255)
  name?: string;

  @ApiPropertyOptional()
  @IsOptional()
  @IsString()
  @MaxLength(2000)
  description?: string;

  @ApiPropertyOptional()
  @IsOptional()
  @IsBoolean()
  isActive?: boolean;

  @ApiPropertyOptional()
  @IsOptional()
  @IsString()
  triggerNodeId?: string;

  @ApiPropertyOptional({ type: PipelineDefinitionDto })
  @IsOptional()
  @ValidateNested()
  @Type(() => PipelineDefinitionDto)
  definition?: PipelineDefinitionDto;

  @ApiPropertyOptional()
  @IsOptional()
  @IsString()
  @MaxLength(100)
  cronExpression?: string;

  @ApiPropertyOptional()
  @IsOptional()
  @IsArray()
  @IsString({ each: true })
  tags?: string[];

  @ApiPropertyOptional()
  @IsOptional()
  @IsObject()
  metadata?: Record<string, any>;
}

/**
 * Execute a pipeline (trigger it)
 */
export class ExecutePipelineDto {
  @ApiPropertyOptional({ 
    example: { url: 'https://competitor.com/blog/post', keyword: 'seo tips' },
    description: 'Initial payload passed to the trigger node'
  })
  @IsOptional()
  @IsObject()
  payload?: Record<string, any>;

  @ApiPropertyOptional({ 
    example: false,
    description: 'If true, validates the pipeline without actually executing'
  })
  @IsOptional()
  @IsBoolean()
  dryRun?: boolean;

  @ApiPropertyOptional({ 
    example: 'high',
    description: 'Queue priority (affects execution order)'
  })
  @IsOptional()
  @IsEnum(['low', 'normal', 'high'])
  priority?: 'low' | 'normal' | 'high';
}

/**
 * Query pipelines with filters
 */
export class QueryPipelinesDto {
  @ApiPropertyOptional({ example: 1 })
  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(1)
  page?: number = 1;

  @ApiPropertyOptional({ example: 20 })
  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(1)
  @Max(100)
  limit?: number = 20;

  @ApiPropertyOptional({ example: 'content' })
  @IsOptional()
  @IsString()
  search?: string;

  @ApiPropertyOptional({ example: true })
  @IsOptional()
  @Type(() => Boolean)
  @IsBoolean()
  isActive?: boolean;

  @ApiPropertyOptional({ example: ['seo', 'automation'] })
  @IsOptional()
  @IsArray()
  @IsString({ each: true })
  tags?: string[];

  @ApiPropertyOptional({ enum: ['createdAt', 'updatedAt', 'name', 'lastExecutedAt'] })
  @IsOptional()
  @IsEnum(['createdAt', 'updatedAt', 'name', 'lastExecutedAt'])
  sortBy?: string = 'updatedAt';

  @ApiPropertyOptional({ enum: ['asc', 'desc'] })
  @IsOptional()
  @IsEnum(['asc', 'desc'])
  sortOrder?: 'asc' | 'desc' = 'desc';
}

/**
 * Query pipeline executions
 */
export class QueryExecutionsDto {
  @ApiPropertyOptional({ example: 1 })
  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(1)
  page?: number = 1;

  @ApiPropertyOptional({ example: 20 })
  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(1)
  @Max(100)
  limit?: number = 20;

  @ApiPropertyOptional({ enum: PipelineExecutionStatus })
  @IsOptional()
  @IsEnum(PipelineExecutionStatus)
  status?: PipelineExecutionStatus;

  @ApiPropertyOptional({ example: '2024-01-01T00:00:00Z' })
  @IsOptional()
  @IsString()
  startedAfter?: string;

  @ApiPropertyOptional({ example: '2024-12-31T23:59:59Z' })
  @IsOptional()
  @IsString()
  startedBefore?: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// RESPONSE DTOs (What the server returns)
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Pipeline summary (for list views)
 */
export class PipelineSummaryDto {
  @ApiProperty()
  id: string;

  @ApiProperty()
  name: string;

  @ApiProperty()
  description: string;

  @ApiProperty()
  isActive: boolean;

  @ApiProperty()
  totalExecutions: number;

  @ApiProperty()
  successfulExecutions: number;

  @ApiProperty()
  failedExecutions: number;

  @ApiProperty()
  lastExecutedAt: Date;

  @ApiProperty()
  tags: string[];

  @ApiProperty()
  createdAt: Date;

  @ApiProperty()
  updatedAt: Date;
}

/**
 * Execution trigger response
 */
export class ExecutionStartedDto {
  @ApiProperty({ example: 'exec_abc123' })
  executionId: string;

  @ApiProperty({ example: 'QUEUED' })
  status: string;

  @ApiProperty({ example: 'Pipeline queued for execution' })
  message: string;

  @ApiProperty({ example: 3 })
  queuePosition?: number;
}

/**
 * Execution status response
 */
export class ExecutionStatusDto {
  @ApiProperty()
  id: string;

  @ApiProperty()
  pipelineId: string;

  @ApiProperty({ enum: PipelineExecutionStatus })
  status: PipelineExecutionStatus;

  @ApiProperty()
  currentStepId: string;

  @ApiProperty()
  progress: number; // 0-100

  @ApiProperty()
  stepLogs: any[];

  @ApiProperty()
  error?: string;

  @ApiProperty()
  startedAt: Date;

  @ApiProperty()
  completedAt?: Date;

  @ApiProperty()
  durationMs?: number;
}

/**
 * Paginated response wrapper
 */
export class PaginatedResponseDto<T> {
  @ApiProperty()
  data: T[];

  @ApiProperty()
  total: number;

  @ApiProperty()
  page: number;

  @ApiProperty()
  limit: number;

  @ApiProperty()
  totalPages: number;

  @ApiProperty()
  hasNext: boolean;

  @ApiProperty()
  hasPrev: boolean;
}
