/**
 * @fileoverview Pipelines Controller - HTTP API Layer
 * 
 * APEX Generation Metadata:
 * - Signed by: Marcus (Product/UX), Roxanne (Security)
 * 
 * This controller exposes all pipeline operations via REST API:
 * - CRUD operations for pipelines
 * - Execution triggers and status
 * - Template management
 */

import {
  Controller,
  Get,
  Post,
  Put,
  Delete,
  Body,
  Param,
  Query,
  UseGuards,
  Request,
  HttpCode,
  HttpStatus,
  ParseUUIDPipe,
  BadRequestException,
  NotFoundException,
} from '@nestjs/common';
import {
  ApiTags,
  ApiOperation,
  ApiResponse,
  ApiBearerAuth,
  ApiParam,
  ApiQuery,
} from '@nestjs/swagger';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository, Like, In } from 'typeorm';

// Auth (assumes these exist in your platform)
import { JwtAuthGuard } from '../../auth/guards/jwt-auth.guard';
import { CurrentUser } from '../../auth/decorators/current-user.decorator';

// Entities & Services
import { Pipeline, PipelineExecution, PipelineTemplate } from './entities/pipeline.entity';
import { PipelineRunnerService } from './engine/pipeline-runner.service';

// DTOs
import {
  CreatePipelineDto,
  UpdatePipelineDto,
  ExecutePipelineDto,
  QueryPipelinesDto,
  QueryExecutionsDto,
  PipelineSummaryDto,
  ExecutionStartedDto,
  ExecutionStatusDto,
  PaginatedResponseDto,
} from './dto/pipeline.dto';

@ApiTags('Pipelines')
@ApiBearerAuth()
@Controller('api/v1/pipelines')
@UseGuards(JwtAuthGuard)
export class PipelinesController {
  constructor(
    @InjectRepository(Pipeline)
    private readonly pipelineRepo: Repository<Pipeline>,

    @InjectRepository(PipelineExecution)
    private readonly executionRepo: Repository<PipelineExecution>,

    @InjectRepository(PipelineTemplate)
    private readonly templateRepo: Repository<PipelineTemplate>,

    private readonly runnerService: PipelineRunnerService,
  ) {}

  // ═══════════════════════════════════════════════════════════════════════
  // PIPELINE CRUD
  // ═══════════════════════════════════════════════════════════════════════

  @Post()
  @ApiOperation({ summary: 'Create a new pipeline' })
  @ApiResponse({ status: 201, description: 'Pipeline created successfully' })
  @ApiResponse({ status: 400, description: 'Invalid pipeline definition' })
  async createPipeline(
    @Body() dto: CreatePipelineDto,
    @CurrentUser() user: any,
  ): Promise<Pipeline> {
    // Validate that trigger node exists in definition
    const triggerNode = dto.definition.nodes.find(
      (n) => n.id === dto.triggerNodeId,
    );
    
    if (!triggerNode) {
      throw new BadRequestException(
        `Trigger node ${dto.triggerNodeId} not found in definition`,
      );
    }

    if (!triggerNode.type.startsWith('TRIGGER_')) {
      throw new BadRequestException(
        `Node ${dto.triggerNodeId} is not a trigger type`,
      );
    }

    const pipeline = this.pipelineRepo.create({
      ...dto,
      ownerId: user.id,
    });

    return await this.pipelineRepo.save(pipeline);
  }

  @Get()
  @ApiOperation({ summary: 'List all pipelines' })
  @ApiResponse({ status: 200, description: 'List of pipelines' })
  async listPipelines(
    @Query() query: QueryPipelinesDto,
    @CurrentUser() user: any,
  ): Promise<PaginatedResponseDto<PipelineSummaryDto>> {
    const { page, limit, search, isActive, tags, sortBy, sortOrder } = query;

    const where: any = { ownerId: user.id };

    if (isActive !== undefined) {
      where.isActive = isActive;
    }

    if (search) {
      where.name = Like(`%${search}%`);
    }

    const [pipelines, total] = await this.pipelineRepo.findAndCount({
      where,
      order: { [sortBy]: sortOrder.toUpperCase() },
      take: limit,
      skip: (page - 1) * limit,
      select: [
        'id',
        'name',
        'description',
        'isActive',
        'totalExecutions',
        'successfulExecutions',
        'failedExecutions',
        'lastExecutedAt',
        'tags',
        'createdAt',
        'updatedAt',
      ],
    });

    // Filter by tags if provided (post-query filter for JSONB)
    let filteredPipelines = pipelines;
    if (tags?.length) {
      filteredPipelines = pipelines.filter((p) =>
        tags.some((tag) => p.tags?.includes(tag)),
      );
    }

    const totalPages = Math.ceil(total / limit);

    return {
      data: filteredPipelines as any,
      total,
      page,
      limit,
      totalPages,
      hasNext: page < totalPages,
      hasPrev: page > 1,
    };
  }

  @Get(':id')
  @ApiOperation({ summary: 'Get pipeline by ID' })
  @ApiParam({ name: 'id', type: 'string', format: 'uuid' })
  @ApiResponse({ status: 200, description: 'Pipeline details' })
  @ApiResponse({ status: 404, description: 'Pipeline not found' })
  async getPipeline(
    @Param('id', ParseUUIDPipe) id: string,
    @CurrentUser() user: any,
  ): Promise<Pipeline> {
    const pipeline = await this.pipelineRepo.findOne({
      where: { id, ownerId: user.id },
    });

    if (!pipeline) {
      throw new NotFoundException(`Pipeline ${id} not found`);
    }

    return pipeline;
  }

  @Put(':id')
  @ApiOperation({ summary: 'Update pipeline' })
  @ApiParam({ name: 'id', type: 'string', format: 'uuid' })
  @ApiResponse({ status: 200, description: 'Pipeline updated successfully' })
  @ApiResponse({ status: 404, description: 'Pipeline not found' })
  async updatePipeline(
    @Param('id', ParseUUIDPipe) id: string,
    @Body() dto: UpdatePipelineDto,
    @CurrentUser() user: any,
  ): Promise<Pipeline> {
    const pipeline = await this.pipelineRepo.findOne({
      where: { id, ownerId: user.id },
    });

    if (!pipeline) {
      throw new NotFoundException(`Pipeline ${id} not found`);
    }

    // Validate new definition if provided
    if (dto.definition && dto.triggerNodeId) {
      const triggerNode = dto.definition.nodes.find(
        (n) => n.id === dto.triggerNodeId,
      );
      if (!triggerNode) {
        throw new BadRequestException(
          `Trigger node ${dto.triggerNodeId} not found in definition`,
        );
      }
    }

    Object.assign(pipeline, dto);
    return await this.pipelineRepo.save(pipeline);
  }

  @Delete(':id')
  @HttpCode(HttpStatus.NO_CONTENT)
  @ApiOperation({ summary: 'Delete pipeline' })
  @ApiParam({ name: 'id', type: 'string', format: 'uuid' })
  @ApiResponse({ status: 204, description: 'Pipeline deleted successfully' })
  @ApiResponse({ status: 404, description: 'Pipeline not found' })
  async deletePipeline(
    @Param('id', ParseUUIDPipe) id: string,
    @CurrentUser() user: any,
  ): Promise<void> {
    const result = await this.pipelineRepo.delete({
      id,
      ownerId: user.id,
    });

    if (result.affected === 0) {
      throw new NotFoundException(`Pipeline ${id} not found`);
    }
  }

  // ═══════════════════════════════════════════════════════════════════════
  // EXECUTION
  // ═══════════════════════════════════════════════════════════════════════

  @Post(':id/execute')
  @ApiOperation({ summary: 'Execute a pipeline' })
  @ApiParam({ name: 'id', type: 'string', format: 'uuid' })
  @ApiResponse({ status: 201, description: 'Execution started' })
  @ApiResponse({ status: 404, description: 'Pipeline not found' })
  async executePipeline(
    @Param('id', ParseUUIDPipe) id: string,
    @Body() dto: ExecutePipelineDto,
    @CurrentUser() user: any,
  ): Promise<ExecutionStartedDto> {
    const result = await this.runnerService.startPipeline(
      id,
      user.id,
      dto.payload || {},
      {
        dryRun: dto.dryRun,
        priority: dto.priority,
      },
    );

    return {
      executionId: result.executionId,
      status: result.status,
      message:
        result.status === 'VALIDATED'
          ? 'Pipeline validated successfully (dry run)'
          : 'Pipeline queued for execution',
    };
  }

  @Get(':id/executions')
  @ApiOperation({ summary: 'List executions for a pipeline' })
  @ApiParam({ name: 'id', type: 'string', format: 'uuid' })
  @ApiResponse({ status: 200, description: 'List of executions' })
  async listExecutions(
    @Param('id', ParseUUIDPipe) id: string,
    @Query() query: QueryExecutionsDto,
    @CurrentUser() user: any,
  ): Promise<PaginatedResponseDto<ExecutionStatusDto>> {
    const { page, limit, status, startedAfter, startedBefore } = query;

    const qb = this.executionRepo
      .createQueryBuilder('exec')
      .where('exec.pipelineId = :pipelineId', { pipelineId: id })
      .andWhere('exec.ownerId = :ownerId', { ownerId: user.id });

    if (status) {
      qb.andWhere('exec.status = :status', { status });
    }

    if (startedAfter) {
      qb.andWhere('exec.startedAt >= :startedAfter', {
        startedAfter: new Date(startedAfter),
      });
    }

    if (startedBefore) {
      qb.andWhere('exec.startedAt <= :startedBefore', {
        startedBefore: new Date(startedBefore),
      });
    }

    const [executions, total] = await qb
      .orderBy('exec.startedAt', 'DESC')
      .take(limit)
      .skip((page - 1) * limit)
      .getManyAndCount();

    const totalPages = Math.ceil(total / limit);

    // Calculate progress for each execution
    const data = executions.map((exec) => {
      const pipeline = exec.pipeline;
      const totalSteps = pipeline?.definition?.nodes?.length || 1;
      const completedSteps = exec.stepLogs?.filter(
        (log) => log.status === 'completed',
      ).length || 0;
      const progress = Math.round((completedSteps / totalSteps) * 100);

      return {
        id: exec.id,
        pipelineId: exec.pipelineId,
        status: exec.status,
        currentStepId: exec.currentStepId,
        progress,
        stepLogs: exec.stepLogs,
        error: exec.error,
        startedAt: exec.startedAt,
        completedAt: exec.completedAt,
        durationMs: exec.durationMs,
      };
    });

    return {
      data,
      total,
      page,
      limit,
      totalPages,
      hasNext: page < totalPages,
      hasPrev: page > 1,
    };
  }

  @Get('executions/:executionId')
  @ApiOperation({ summary: 'Get execution status' })
  @ApiParam({ name: 'executionId', type: 'string', format: 'uuid' })
  @ApiResponse({ status: 200, description: 'Execution details' })
  @ApiResponse({ status: 404, description: 'Execution not found' })
  async getExecution(
    @Param('executionId', ParseUUIDPipe) executionId: string,
    @CurrentUser() user: any,
  ): Promise<ExecutionStatusDto> {
    const execution = await this.executionRepo.findOne({
      where: { id: executionId, ownerId: user.id },
      relations: ['pipeline'],
    });

    if (!execution) {
      throw new NotFoundException(`Execution ${executionId} not found`);
    }

    const totalSteps = execution.pipeline?.definition?.nodes?.length || 1;
    const completedSteps = execution.stepLogs?.filter(
      (log) => log.status === 'completed',
    ).length || 0;

    return {
      id: execution.id,
      pipelineId: execution.pipelineId,
      status: execution.status,
      currentStepId: execution.currentStepId,
      progress: Math.round((completedSteps / totalSteps) * 100),
      stepLogs: execution.stepLogs,
      error: execution.error,
      startedAt: execution.startedAt,
      completedAt: execution.completedAt,
      durationMs: execution.durationMs,
    };
  }

  @Post('executions/:executionId/cancel')
  @HttpCode(HttpStatus.OK)
  @ApiOperation({ summary: 'Cancel a running execution' })
  @ApiParam({ name: 'executionId', type: 'string', format: 'uuid' })
  @ApiResponse({ status: 200, description: 'Execution cancelled' })
  async cancelExecution(
    @Param('executionId', ParseUUIDPipe) executionId: string,
    @CurrentUser() user: any,
  ): Promise<{ message: string }> {
    const execution = await this.executionRepo.findOne({
      where: { id: executionId, ownerId: user.id },
    });

    if (!execution) {
      throw new NotFoundException(`Execution ${executionId} not found`);
    }

    if (['COMPLETED', 'FAILED', 'CANCELLED'].includes(execution.status)) {
      throw new BadRequestException(
        `Execution is already ${execution.status.toLowerCase()}`,
      );
    }

    await this.executionRepo.update(executionId, {
      status: 'CANCELLED' as any,
      completedAt: new Date(),
    });

    return { message: 'Execution cancelled successfully' };
  }

  // ═══════════════════════════════════════════════════════════════════════
  // TEMPLATES (Marcus: Pre-built workflows for onboarding)
  // ═══════════════════════════════════════════════════════════════════════

  @Get('templates')
  @ApiOperation({ summary: 'List available pipeline templates' })
  @ApiQuery({ name: 'category', required: false })
  @ApiResponse({ status: 200, description: 'List of templates' })
  async listTemplates(
    @Query('category') category?: string,
  ): Promise<PipelineTemplate[]> {
    const where: any = { isPublic: true };
    
    if (category) {
      where.category = category;
    }

    return await this.templateRepo.find({
      where,
      order: { usageCount: 'DESC' },
    });
  }

  @Post('templates/:templateId/use')
  @ApiOperation({ summary: 'Create a pipeline from a template' })
  @ApiParam({ name: 'templateId', type: 'string', format: 'uuid' })
  @ApiResponse({ status: 201, description: 'Pipeline created from template' })
  async useTemplate(
    @Param('templateId', ParseUUIDPipe) templateId: string,
    @Body() body: { name?: string },
    @CurrentUser() user: any,
  ): Promise<Pipeline> {
    const template = await this.templateRepo.findOne({
      where: { id: templateId },
    });

    if (!template) {
      throw new NotFoundException(`Template ${templateId} not found`);
    }

    // Create pipeline from template
    const pipeline = this.pipelineRepo.create({
      name: body.name || `${template.name} (Copy)`,
      description: template.description,
      definition: template.definition,
      triggerNodeId: template.definition.nodes.find((n) =>
        n.type.startsWith('TRIGGER_'),
      )?.id,
      ownerId: user.id,
      tags: [template.category],
    });

    const saved = await this.pipelineRepo.save(pipeline);

    // Increment template usage count
    await this.templateRepo.increment({ id: templateId }, 'usageCount', 1);

    return saved;
  }

  // ═══════════════════════════════════════════════════════════════════════
  // UTILITIES
  // ═══════════════════════════════════════════════════════════════════════

  @Post(':id/duplicate')
  @ApiOperation({ summary: 'Duplicate an existing pipeline' })
  @ApiParam({ name: 'id', type: 'string', format: 'uuid' })
  @ApiResponse({ status: 201, description: 'Pipeline duplicated' })
  async duplicatePipeline(
    @Param('id', ParseUUIDPipe) id: string,
    @CurrentUser() user: any,
  ): Promise<Pipeline> {
    const original = await this.pipelineRepo.findOne({
      where: { id, ownerId: user.id },
    });

    if (!original) {
      throw new NotFoundException(`Pipeline ${id} not found`);
    }

    const duplicate = this.pipelineRepo.create({
      name: `${original.name} (Copy)`,
      description: original.description,
      definition: original.definition,
      triggerNodeId: original.triggerNodeId,
      cronExpression: original.cronExpression,
      tags: original.tags,
      metadata: original.metadata,
      ownerId: user.id,
      isActive: false, // Duplicates start inactive
    });

    return await this.pipelineRepo.save(duplicate);
  }

  @Put(':id/toggle')
  @ApiOperation({ summary: 'Toggle pipeline active state' })
  @ApiParam({ name: 'id', type: 'string', format: 'uuid' })
  @ApiResponse({ status: 200, description: 'Pipeline toggled' })
  async togglePipeline(
    @Param('id', ParseUUIDPipe) id: string,
    @CurrentUser() user: any,
  ): Promise<{ isActive: boolean }> {
    const pipeline = await this.pipelineRepo.findOne({
      where: { id, ownerId: user.id },
    });

    if (!pipeline) {
      throw new NotFoundException(`Pipeline ${id} not found`);
    }

    pipeline.isActive = !pipeline.isActive;
    await this.pipelineRepo.save(pipeline);

    return { isActive: pipeline.isActive };
  }
}
