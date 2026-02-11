/**
 * @fileoverview Pipeline Runner Service - The Brain of Execution
 * 
 * APEX Generation Metadata:
 * - Signed by: Leo (SEO Logic), Aria (Agentic Control), Chen (Data Mapping)
 * - This is the CORE of the entire system
 * 
 * Responsibilities:
 * 1. Execute pipeline steps in sequence
 * 2. Map data between nodes using {{path.syntax}}
 * 3. Handle conditional branching (If/Else)
 * 4. Integrate with SIE-X and BACOWR
 * 5. Manage execution state and persistence
 */

import { Injectable, Logger, BadRequestException, NotFoundException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { InjectQueue } from '@nestjs/bullmq';
import { Queue } from 'bullmq';
import { EventEmitter2 } from '@nestjs/event-emitter';
import { get, set } from 'lodash';

import {
  Pipeline,
  PipelineExecution,
  PipelineExecutionStatus,
  PipelineNode,
  NodeActionType,
  ExecutionContext,
  StepExecutionLog,
} from '../entities/pipeline.entity';

// External service imports (these should exist in your platform)
import { SieXClientService } from '../../integrations/sie-x/sie-x-client.service';
import { BacowrClientService } from '../../integrations/bacowr/bacowr-client.service';
import { HttpClientService } from '../../integrations/http/http-client.service';
import { NotificationService } from '../../notifications/notification.service';

// ═══════════════════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════════════════

export interface StepExecutionPayload {
  executionId: string;
  stepId: string;
  retryCount?: number;
}

export interface StepResult {
  success: boolean;
  output?: any;
  error?: string;
  nextStepId?: string | null;
  shouldRetry?: boolean;
}

// ═══════════════════════════════════════════════════════════════════════════
// SERVICE
// ═══════════════════════════════════════════════════════════════════════════

@Injectable()
export class PipelineRunnerService {
  private readonly logger = new Logger(PipelineRunnerService.name);

  constructor(
    @InjectRepository(Pipeline)
    private readonly pipelineRepo: Repository<Pipeline>,
    
    @InjectRepository(PipelineExecution)
    private readonly executionRepo: Repository<PipelineExecution>,
    
    @InjectQueue('pipeline-queue')
    private readonly pipelineQueue: Queue,
    
    private readonly eventEmitter: EventEmitter2,
    
    // External services-integrations-of-usp-features (Leo: These are the SEO muscles)
    private readonly siexService: SieXClientService,
    private readonly bacowrService: BacowrClientService,
    private readonly httpService: HttpClientService,
    private readonly notificationService: NotificationService,
  ) {}

  // ═══════════════════════════════════════════════════════════════════════
  // PUBLIC API
  // ═══════════════════════════════════════════════════════════════════════

  /**
   * Start a pipeline execution
   * Marcus: This is what the frontend calls when user clicks "Run"
   */
  async startPipeline(
    pipelineId: string,
    ownerId: string,
    initialPayload: Record<string, any> = {},
    options: { dryRun?: boolean; priority?: 'low' | 'normal' | 'high' } = {},
  ): Promise<{ executionId: string; status: string }> {
    // Validate pipeline exists and belongs to user
    const pipeline = await this.pipelineRepo.findOne({
      where: { id: pipelineId, ownerId },
    });

    if (!pipeline) {
      throw new NotFoundException(`Pipeline ${pipelineId} not found`);
    }

    // Validate pipeline structure
    this.validatePipelineStructure(pipeline);

    // Dry run mode - validate without executing
    if (options.dryRun) {
      return {
        executionId: 'dry-run',
        status: 'VALIDATED',
      };
    }

    // Create execution record
    const execution = await this.executionRepo.save({
      pipelineId: pipeline.id,
      ownerId,
      status: PipelineExecutionStatus.QUEUED,
      context: {
        trigger: initialPayload,
        _meta: {
          pipelineName: pipeline.name,
          startedAt: new Date().toISOString(),
        },
      },
      currentStepId: pipeline.triggerNodeId,
      stepLogs: [],
    });

    // Queue the first step
    const priority = options.priority === 'high' ? 1 : options.priority === 'low' ? 10 : 5;
    
    await this.pipelineQueue.add(
      'execute-step',
      {
        executionId: execution.id,
        stepId: pipeline.triggerNodeId,
        retryCount: 0,
      } as StepExecutionPayload,
      { priority },
    );

    // Update pipeline statistics
    await this.pipelineRepo.increment({ id: pipelineId }, 'totalExecutions', 1);
    await this.pipelineRepo.update(pipelineId, { lastExecutedAt: new Date() });

    // Emit event for real-time updates
    this.eventEmitter.emit('pipeline.started', {
      executionId: execution.id,
      pipelineId: pipeline.id,
      ownerId,
    });

    return {
      executionId: execution.id,
      status: 'QUEUED',
    };
  }

  /**
   * Execute a single step (called by BullMQ processor)
   * Aria: This is the heart of the agentic loop
   */
  async executeStep(payload: StepExecutionPayload): Promise<void> {
    const { executionId, stepId, retryCount = 0 } = payload;

    // Load execution with pipeline definition
    const execution = await this.executionRepo.findOne({
      where: { id: executionId },
      relations: ['pipeline'],
    });

    if (!execution) {
      this.logger.error(`Execution ${executionId} not found`);
      return;
    }

    // Check if execution was cancelled
    if (execution.status === PipelineExecutionStatus.CANCELLED) {
      this.logger.log(`Execution ${executionId} was cancelled, skipping step ${stepId}`);
      return;
    }

    // Find the node to execute
    const node = execution.pipeline.definition.nodes.find((n) => n.id === stepId);
    
    if (!node) {
      await this.failExecution(execution, `Node ${stepId} not found in pipeline definition`);
      return;
    }

    this.logger.log(`Executing step: ${node.type} (${node.id}) for execution ${executionId}`);

    // Update status
    await this.updateExecutionStatus(execution, PipelineExecutionStatus.RUNNING, stepId);

    // Log step start
    const stepLog: StepExecutionLog = {
      stepId: node.id,
      nodeType: node.type,
      status: 'running',
      startedAt: new Date(),
      retryCount,
    };

    try {
      // Chen: Resolve input mappings from context
      const resolvedInputs = this.resolveInputs(node.inputs, execution.context);
      stepLog.input = resolvedInputs;

      // Execute the action
      const result = await this.executeNodeAction(node, resolvedInputs, execution);

      // Handle result
      if (result.success) {
        stepLog.status = 'completed';
        stepLog.completedAt = new Date();
        stepLog.output = result.output;

        // Update context with step output
        const newContext = {
          ...execution.context,
          [node.id]: result.output,
        };

        await this.executionRepo.update(execution.id, {
          context: newContext,
          stepLogs: [...execution.stepLogs, stepLog],
        });

        // Queue next step if exists
        if (result.nextStepId) {
          await this.queueNextStep(executionId, result.nextStepId);
        } else {
          // No more steps - pipeline completed
          await this.completeExecution(execution);
        }
      } else {
        // Handle failure
        stepLog.status = 'failed';
        stepLog.completedAt = new Date();
        stepLog.error = result.error;

        // Check if we should retry
        const shouldRetry = result.shouldRetry && 
          node.retryConfig && 
          retryCount < node.retryConfig.maxAttempts;

        if (shouldRetry) {
          this.logger.warn(`Step ${stepId} failed, scheduling retry ${retryCount + 1}`);
          
          const delay = this.calculateBackoff(node.retryConfig, retryCount);
          
          await this.pipelineQueue.add(
            'execute-step',
            { executionId, stepId, retryCount: retryCount + 1 },
            { delay },
          );

          stepLog.status = 'pending'; // Will retry
          await this.executionRepo.update(execution.id, {
            stepLogs: [...execution.stepLogs, stepLog],
          });
        } else if (node.onError === 'continue') {
          // Continue despite failure
          this.logger.warn(`Step ${stepId} failed but continuing (onError=continue)`);
          
          stepLog.status = 'skipped';
          const nextStepId = this.getNextNodeId(execution.pipeline.definition, node, 'default');
          
          if (nextStepId) {
            await this.queueNextStep(executionId, nextStepId);
          } else {
            await this.completeExecution(execution);
          }
        } else {
          // Fail the execution
          await this.failExecution(execution, result.error, stepId);
        }

        await this.executionRepo.update(execution.id, {
          stepLogs: [...execution.stepLogs, stepLog],
        });
      }
    } catch (error) {
      this.logger.error(`Unhandled error in step ${stepId}: ${error.message}`, error.stack);
      stepLog.status = 'failed';
      stepLog.error = error.message;
      
      await this.executionRepo.update(execution.id, {
        stepLogs: [...execution.stepLogs, stepLog],
      });
      
      await this.failExecution(execution, error.message, stepId);
    }
  }

  // ═══════════════════════════════════════════════════════════════════════
  // NODE ACTION HANDLERS
  // Leo: This is where SEO magic happens
  // ═══════════════════════════════════════════════════════════════════════

  private async executeNodeAction(
    node: PipelineNode,
    inputs: Record<string, any>,
    execution: PipelineExecution,
  ): Promise<StepResult> {
    const definition = execution.pipeline.definition;

    switch (node.type) {
      // ─── Triggers ───
      case NodeActionType.TRIGGER_MANUAL:
      case NodeActionType.TRIGGER_SCHEDULE:
      case NodeActionType.TRIGGER_WEBHOOK:
      case NodeActionType.TRIGGER_RSS:
        // Triggers just pass through
        return {
          success: true,
          output: inputs,
          nextStepId: this.getNextNodeId(definition, node, 'default'),
        };

      // ─── SIE-X Actions (Intelligence) ───
      case NodeActionType.ACTION_SIEX_ANALYZE:
        return this.executeSieXAnalyze(node, inputs, definition);

      case NodeActionType.ACTION_SIEX_EXTRACT_ENTITIES:
        return this.executeSieXExtractEntities(node, inputs, definition);

      case NodeActionType.ACTION_SIEX_COMPARE_SERP:
        return this.executeSieXCompareSERP(node, inputs, definition);

      case NodeActionType.ACTION_SERP_CHECK:
        return this.executeSerpCheck(node, inputs, definition);

      // ─── BACOWR Actions (Content Generation) ───
      case NodeActionType.ACTION_BACOWR_GENERATE:
        return this.executeBacowrGenerate(node, inputs, definition, execution.context);

      case NodeActionType.ACTION_BACOWR_REWRITE:
        return this.executeBacowrRewrite(node, inputs, definition);

      case NodeActionType.ACTION_BACOWR_PATCH:
        return this.executeBacowrPatch(node, inputs, definition);

      // ─── Utility Actions ───
      case NodeActionType.ACTION_HTTP_REQUEST:
        return this.executeHttpRequest(node, inputs, definition);

      case NodeActionType.ACTION_SEND_EMAIL:
        return this.executeSendEmail(node, inputs, definition);

      case NodeActionType.ACTION_SLACK_NOTIFY:
        return this.executeSlackNotify(node, inputs, definition);

      case NodeActionType.ACTION_SAVE_TO_DB:
        return this.executeSaveToDb(node, inputs, definition);

      // ─── Logic Nodes (Aria) ───
      case NodeActionType.LOGIC_CONDITION:
        return this.executeCondition(node, inputs, definition);

      case NodeActionType.LOGIC_DELAY:
        return this.executeDelay(node, inputs, definition);

      case NodeActionType.LOGIC_LOOP:
        return this.executeLoop(node, inputs, definition, execution);

      case NodeActionType.LOGIC_SWITCH:
        return this.executeSwitch(node, inputs, definition);

      case NodeActionType.LOGIC_MERGE:
        return this.executeMerge(node, inputs, definition);

      default:
        return {
          success: false,
          error: `Unknown node type: ${node.type}`,
        };
    }
  }

  // ─── SIE-X Implementations ───

  private async executeSieXAnalyze(
    node: PipelineNode,
    inputs: Record<string, any>,
    definition: any,
  ): Promise<StepResult> {
    try {
      const result = await this.siexService.analyze({
        url: inputs.url,
        text: inputs.text,
        options: inputs.options || {},
      });

      return {
        success: true,
        output: {
          entities: result.entities,
          intent: result.intent,
          score: result.score,
          suggestions: result.suggestions,
        },
        nextStepId: this.getNextNodeId(definition, node, 'default'),
      };
    } catch (error) {
      return {
        success: false,
        error: `SIE-X analysis failed: ${error.message}`,
        shouldRetry: true,
      };
    }
  }

  private async executeSieXExtractEntities(
    node: PipelineNode,
    inputs: Record<string, any>,
    definition: any,
  ): Promise<StepResult> {
    try {
      const result = await this.siexService.extractEntities({
        text: inputs.text || inputs.content,
        entityTypes: inputs.entityTypes || ['all'],
      });

      return {
        success: true,
        output: {
          entities: result.entities,
          relationships: result.relationships,
        },
        nextStepId: this.getNextNodeId(definition, node, 'default'),
      };
    } catch (error) {
      return {
        success: false,
        error: `Entity extraction failed: ${error.message}`,
        shouldRetry: true,
      };
    }
  }

  private async executeSieXCompareSERP(
    node: PipelineNode,
    inputs: Record<string, any>,
    definition: any,
  ): Promise<StepResult> {
    try {
      // Leo: The "Semantic Gap Eraser" logic
      const targetAnalysis = await this.siexService.analyze({ url: inputs.targetUrl });
      const serpResults = await this.siexService.analyzeSERP({
        keyword: inputs.keyword,
        limit: inputs.limit || 5,
      });

      // Calculate entity gaps
      const targetEntities = new Set(targetAnalysis.entities.map((e) => e.name));
      const serpEntities = new Set(
        serpResults.flatMap((r) => r.entities.map((e) => e.name)),
      );

      const missingEntities = [...serpEntities].filter((e) => !targetEntities.has(e));
      const coverageScore = targetEntities.size / serpEntities.size;

      return {
        success: true,
        output: {
          targetUrl: inputs.targetUrl,
          keyword: inputs.keyword,
          missingEntities,
          coverageScore,
          serpComparison: serpResults,
          targetAnalysis,
        },
        nextStepId: this.getNextNodeId(definition, node, 'default'),
      };
    } catch (error) {
      return {
        success: false,
        error: `SERP comparison failed: ${error.message}`,
        shouldRetry: true,
      };
    }
  }

  private async executeSerpCheck(
    node: PipelineNode,
    inputs: Record<string, any>,
    definition: any,
  ): Promise<StepResult> {
    try {
      const result = await this.siexService.checkRankings({
        keywords: inputs.keywords,
        domain: inputs.domain,
      });

      return {
        success: true,
        output: result,
        nextStepId: this.getNextNodeId(definition, node, 'default'),
      };
    } catch (error) {
      return {
        success: false,
        error: `SERP check failed: ${error.message}`,
        shouldRetry: true,
      };
    }
  }

  // ─── BACOWR Implementations ───

  private async executeBacowrGenerate(
    node: PipelineNode,
    inputs: Record<string, any>,
    definition: any,
    context: ExecutionContext,
  ): Promise<StepResult> {
    try {
      // Leo: Full BACOWR integration with feedback loop support (Aria)
      const result = await this.bacowrService.generateContent({
        topic: inputs.topic,
        targetUrl: inputs.targetUrl,
        anchorText: inputs.anchorText,
        tone: inputs.tone || 'professional',
        wordCount: inputs.wordCount || 1500,
        // Aria: Pass feedback if this is a retry/refinement
        feedback: context._lastError || inputs.feedback,
        // Additional SEO context
        entities: inputs.entities,
        intent: inputs.intent,
      });

      return {
        success: true,
        output: {
          title: result.title,
          content: result.content,
          metaDescription: result.metaDescription,
          wordCount: result.wordCount,
          readabilityScore: result.readabilityScore,
          seoScore: result.seoScore,
        },
        nextStepId: this.getNextNodeId(definition, node, 'default'),
      };
    } catch (error) {
      return {
        success: false,
        error: `BACOWR generation failed: ${error.message}`,
        shouldRetry: true,
      };
    }
  }

  private async executeBacowrRewrite(
    node: PipelineNode,
    inputs: Record<string, any>,
    definition: any,
  ): Promise<StepResult> {
    try {
      const result = await this.bacowrService.rewriteContent({
        originalContent: inputs.content,
        instructions: inputs.instructions,
        targetTone: inputs.tone,
        preserveSections: inputs.preserveSections,
      });

      return {
        success: true,
        output: result,
        nextStepId: this.getNextNodeId(definition, node, 'default'),
      };
    } catch (error) {
      return {
        success: false,
        error: `BACOWR rewrite failed: ${error.message}`,
        shouldRetry: true,
      };
    }
  }

  private async executeBacowrPatch(
    node: PipelineNode,
    inputs: Record<string, any>,
    definition: any,
  ): Promise<StepResult> {
    try {
      // Leo: Surgical content patching
      const result = await this.bacowrService.patchContent({
        originalContent: inputs.content,
        missingEntities: inputs.missingEntities,
        targetTone: inputs.tone,
        patchType: inputs.patchType || 'insert', // 'insert' | 'replace' | 'append'
      });

      return {
        success: true,
        output: {
          patchedContent: result.content,
          patchLocations: result.patchLocations,
          addedEntities: result.addedEntities,
        },
        nextStepId: this.getNextNodeId(definition, node, 'default'),
      };
    } catch (error) {
      return {
        success: false,
        error: `BACOWR patch failed: ${error.message}`,
        shouldRetry: true,
      };
    }
  }

  // ─── Utility Actions ───

  private async executeHttpRequest(
    node: PipelineNode,
    inputs: Record<string, any>,
    definition: any,
  ): Promise<StepResult> {
    try {
      const response = await this.httpService.request({
        method: inputs.method || 'GET',
        url: inputs.url,
        headers: inputs.headers,
        body: inputs.body,
        timeout: inputs.timeout || 30000,
      });

      return {
        success: true,
        output: {
          status: response.status,
          data: response.data,
          headers: response.headers,
        },
        nextStepId: this.getNextNodeId(definition, node, 'default'),
      };
    } catch (error) {
      return {
        success: false,
        error: `HTTP request failed: ${error.message}`,
        shouldRetry: true,
      };
    }
  }

  private async executeSendEmail(
    node: PipelineNode,
    inputs: Record<string, any>,
    definition: any,
  ): Promise<StepResult> {
    try {
      await this.notificationService.sendEmail({
        to: inputs.to,
        subject: inputs.subject,
        body: inputs.body,
        attachments: inputs.attachments,
      });

      return {
        success: true,
        output: { sent: true, to: inputs.to },
        nextStepId: this.getNextNodeId(definition, node, 'default'),
      };
    } catch (error) {
      return {
        success: false,
        error: `Email send failed: ${error.message}`,
        shouldRetry: true,
      };
    }
  }

  private async executeSlackNotify(
    node: PipelineNode,
    inputs: Record<string, any>,
    definition: any,
  ): Promise<StepResult> {
    try {
      await this.notificationService.sendSlack({
        channel: inputs.channel,
        message: inputs.message,
        blocks: inputs.blocks,
      });

      return {
        success: true,
        output: { sent: true, channel: inputs.channel },
        nextStepId: this.getNextNodeId(definition, node, 'default'),
      };
    } catch (error) {
      return {
        success: false,
        error: `Slack notification failed: ${error.message}`,
        shouldRetry: true,
      };
    }
  }

  private async executeSaveToDb(
    node: PipelineNode,
    inputs: Record<string, any>,
    definition: any,
  ): Promise<StepResult> {
    // This would save to a user-defined table or content store
    return {
      success: true,
      output: { saved: true, data: inputs },
      nextStepId: this.getNextNodeId(definition, node, 'default'),
    };
  }

  // ─── Logic Nodes (Aria) ───

  private async executeCondition(
    node: PipelineNode,
    inputs: Record<string, any>,
    definition: any,
  ): Promise<StepResult> {
    const { value, operator, compareValue } = inputs;
    let result: boolean;

    switch (operator) {
      case 'equals':
      case 'eq':
        result = value == compareValue;
        break;
      case 'not_equals':
      case 'neq':
        result = value != compareValue;
        break;
      case 'contains':
        result = String(value).includes(String(compareValue));
        break;
      case 'not_contains':
        result = !String(value).includes(String(compareValue));
        break;
      case 'greater_than':
      case 'gt':
        result = Number(value) > Number(compareValue);
        break;
      case 'less_than':
      case 'lt':
        result = Number(value) < Number(compareValue);
        break;
      case 'greater_equal':
      case 'gte':
        result = Number(value) >= Number(compareValue);
        break;
      case 'less_equal':
      case 'lte':
        result = Number(value) <= Number(compareValue);
        break;
      case 'is_empty':
        result = !value || (Array.isArray(value) && value.length === 0);
        break;
      case 'is_not_empty':
        result = !!value && (!Array.isArray(value) || value.length > 0);
        break;
      case 'regex':
        result = new RegExp(compareValue).test(String(value));
        break;
      default:
        result = !!value;
    }

    // Get the appropriate branch
    const branch = result ? 'true' : 'false';
    const nextStepId = this.getNextNodeId(definition, node, branch);

    return {
      success: true,
      output: { condition: result, branch },
      nextStepId,
    };
  }

  private async executeDelay(
    node: PipelineNode,
    inputs: Record<string, any>,
    definition: any,
  ): Promise<StepResult> {
    const delayMs = inputs.delayMs || inputs.delay * 1000 || 1000;
    
    // Actually delay
    await new Promise((resolve) => setTimeout(resolve, delayMs));

    return {
      success: true,
      output: { delayed: true, delayMs },
      nextStepId: this.getNextNodeId(definition, node, 'default'),
    };
  }

  private async executeLoop(
    node: PipelineNode,
    inputs: Record<string, any>,
    definition: any,
    execution: PipelineExecution,
  ): Promise<StepResult> {
    // Aria: Loop iteration tracking
    const loopKey = `_loop_${node.id}`;
    const currentIndex = execution.context[loopKey]?.index || 0;
    const items = inputs.items || [];
    const maxIterations = inputs.maxIterations || 100;

    if (currentIndex >= items.length || currentIndex >= maxIterations) {
      // Loop complete
      return {
        success: true,
        output: { loopCompleted: true, totalIterations: currentIndex },
        nextStepId: this.getNextNodeId(definition, node, 'complete'),
      };
    }

    // Continue loop
    return {
      success: true,
      output: {
        currentItem: items[currentIndex],
        currentIndex,
        totalItems: items.length,
        [loopKey]: { index: currentIndex + 1 },
      },
      nextStepId: this.getNextNodeId(definition, node, 'iteration'),
    };
  }

  private async executeSwitch(
    node: PipelineNode,
    inputs: Record<string, any>,
    definition: any,
  ): Promise<StepResult> {
    const value = inputs.value;
    const cases = inputs.cases || {};

    // Find matching case or default
    const matchedCase = cases[value] || 'default';
    const nextStepId = this.getNextNodeId(definition, node, matchedCase);

    return {
      success: true,
      output: { matched: matchedCase, value },
      nextStepId,
    };
  }

  private async executeMerge(
    node: PipelineNode,
    inputs: Record<string, any>,
    definition: any,
  ): Promise<StepResult> {
    // Merge multiple inputs into one output
    return {
      success: true,
      output: { merged: inputs },
      nextStepId: this.getNextNodeId(definition, node, 'default'),
    };
  }

  // ═══════════════════════════════════════════════════════════════════════
  // HELPER METHODS
  // ═══════════════════════════════════════════════════════════════════════

  /**
   * Chen: Resolve input mappings like {{trigger.url}} to actual values
   */
  private resolveInputs(
    inputConfig: Record<string, any>,
    context: ExecutionContext,
  ): Record<string, any> {
    if (!inputConfig) return {};

    const resolved: Record<string, any> = {};

    for (const [key, value] of Object.entries(inputConfig)) {
      if (typeof value === 'string') {
        // Check for template syntax {{path.to.value}}
        const templateRegex = /\{\{([^}]+)\}\}/g;
        let resolvedValue = value;
        let match;

        while ((match = templateRegex.exec(value)) !== null) {
          const path = match[1].trim();
          const contextValue = get(context, path);
          
          if (value === match[0]) {
            // Entire value is a template - preserve type
            resolvedValue = contextValue;
          } else {
            // Part of a string - stringify
            resolvedValue = resolvedValue.replace(match[0], String(contextValue ?? ''));
          }
        }

        resolved[key] = resolvedValue;
      } else if (typeof value === 'object' && value !== null) {
        // Recursively resolve nested objects
        resolved[key] = this.resolveInputs(value, context);
      } else {
        resolved[key] = value;
      }
    }

    return resolved;
  }

  /**
   * Get the next node ID based on edge handle
   */
  private getNextNodeId(
    definition: any,
    currentNode: PipelineNode,
    handle: string = 'default',
  ): string | null {
    const edge = definition.edges.find(
      (e) => e.source === currentNode.id && 
             (e.sourceHandle === handle || (!e.sourceHandle && handle === 'default')),
    );

    return edge?.target || null;
  }

  /**
   * Calculate backoff delay for retries
   */
  private calculateBackoff(
    retryConfig: { backoffType: string; backoffDelay: number },
    retryCount: number,
  ): number {
    if (retryConfig.backoffType === 'exponential') {
      return retryConfig.backoffDelay * Math.pow(2, retryCount);
    }
    return retryConfig.backoffDelay;
  }

  /**
   * Queue the next step for execution
   */
  private async queueNextStep(executionId: string, stepId: string): Promise<void> {
    await this.pipelineQueue.add('execute-step', {
      executionId,
      stepId,
      retryCount: 0,
    });
  }

  /**
   * Validate pipeline structure before execution
   */
  private validatePipelineStructure(pipeline: Pipeline): void {
    const { definition, triggerNodeId } = pipeline;

    if (!definition?.nodes?.length) {
      throw new BadRequestException('Pipeline has no nodes defined');
    }

    if (!definition.edges) {
      throw new BadRequestException('Pipeline has no edges defined');
    }

    const nodeIds = new Set(definition.nodes.map((n) => n.id));
    
    if (!nodeIds.has(triggerNodeId)) {
      throw new BadRequestException(`Trigger node ${triggerNodeId} not found in pipeline`);
    }

    // Validate all edges reference existing nodes
    for (const edge of definition.edges) {
      if (!nodeIds.has(edge.source)) {
        throw new BadRequestException(`Edge source node ${edge.source} not found`);
      }
      if (!nodeIds.has(edge.target)) {
        throw new BadRequestException(`Edge target node ${edge.target} not found`);
      }
    }
  }

  /**
   * Update execution status and emit events
   */
  private async updateExecutionStatus(
    execution: PipelineExecution,
    status: PipelineExecutionStatus,
    currentStepId?: string,
  ): Promise<void> {
    const updates: Partial<PipelineExecution> = { status };
    if (currentStepId) {
      updates.currentStepId = currentStepId;
    }

    await this.executionRepo.update(execution.id, updates);

    this.eventEmitter.emit('pipeline.status', {
      executionId: execution.id,
      pipelineId: execution.pipelineId,
      status,
      currentStepId,
    });
  }

  /**
   * Mark execution as completed
   */
  private async completeExecution(execution: PipelineExecution): Promise<void> {
    const completedAt = new Date();
    const durationMs = completedAt.getTime() - execution.startedAt.getTime();

    await this.executionRepo.update(execution.id, {
      status: PipelineExecutionStatus.COMPLETED,
      completedAt,
      durationMs,
    });

    // Update pipeline success stats
    await this.pipelineRepo.increment(
      { id: execution.pipelineId },
      'successfulExecutions',
      1,
    );

    this.eventEmitter.emit('pipeline.completed', {
      executionId: execution.id,
      pipelineId: execution.pipelineId,
      durationMs,
    });

    this.logger.log(`Pipeline execution ${execution.id} completed in ${durationMs}ms`);
  }

  /**
   * Mark execution as failed
   */
  private async failExecution(
    execution: PipelineExecution,
    error: string,
    errorStepId?: string,
  ): Promise<void> {
    const completedAt = new Date();
    const durationMs = completedAt.getTime() - execution.startedAt.getTime();

    await this.executionRepo.update(execution.id, {
      status: PipelineExecutionStatus.FAILED,
      error,
      errorStepId,
      completedAt,
      durationMs,
    });

    // Update pipeline failure stats
    await this.pipelineRepo.increment(
      { id: execution.pipelineId },
      'failedExecutions',
      1,
    );

    this.eventEmitter.emit('pipeline.failed', {
      executionId: execution.id,
      pipelineId: execution.pipelineId,
      error,
      errorStepId,
    });

    this.logger.error(`Pipeline execution ${execution.id} failed: ${error}`);
  }
}
