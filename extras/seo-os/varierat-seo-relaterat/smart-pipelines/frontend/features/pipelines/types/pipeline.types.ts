/**
 * @fileoverview Pipeline TypeScript Types (Shared Frontend Types)
 * 
 * APEX Generation Metadata:
 * - Signed by: Chen (Data Alchemist)
 * - Purpose: Single source of truth for frontend type definitions
 * 
 * These types mirror the backend entities and DTOs to ensure
 * type safety across the entire stack.
 */

// ═══════════════════════════════════════════════════════════════════════════
// ENUMS
// ═══════════════════════════════════════════════════════════════════════════

export enum NodeActionType {
  // Triggers
  TRIGGER_MANUAL = 'TRIGGER_MANUAL',
  TRIGGER_SCHEDULE = 'TRIGGER_SCHEDULE',
  TRIGGER_WEBHOOK = 'TRIGGER_WEBHOOK',
  TRIGGER_RSS = 'TRIGGER_RSS',
  
  // SEO Intelligence (SIE-X)
  ACTION_SIEX_ANALYZE = 'ACTION_SIEX_ANALYZE',
  ACTION_SIEX_EXTRACT_ENTITIES = 'ACTION_SIEX_EXTRACT_ENTITIES',
  ACTION_SIEX_COMPARE_SERP = 'ACTION_SIEX_COMPARE_SERP',
  ACTION_SERP_CHECK = 'ACTION_SERP_CHECK',
  
  // Content Generation (BACOWR)
  ACTION_BACOWR_GENERATE = 'ACTION_BACOWR_GENERATE',
  ACTION_BACOWR_REWRITE = 'ACTION_BACOWR_REWRITE',
  ACTION_BACOWR_PATCH = 'ACTION_BACOWR_PATCH',
  
  // Utilities
  ACTION_HTTP_REQUEST = 'ACTION_HTTP_REQUEST',
  ACTION_SEND_EMAIL = 'ACTION_SEND_EMAIL',
  ACTION_SLACK_NOTIFY = 'ACTION_SLACK_NOTIFY',
  ACTION_SAVE_TO_DB = 'ACTION_SAVE_TO_DB',
  
  // Logic
  LOGIC_CONDITION = 'LOGIC_CONDITION',
  LOGIC_DELAY = 'LOGIC_DELAY',
  LOGIC_LOOP = 'LOGIC_LOOP',
  LOGIC_SWITCH = 'LOGIC_SWITCH',
  LOGIC_MERGE = 'LOGIC_MERGE',
}

export enum PipelineExecutionStatus {
  PENDING = 'PENDING',
  QUEUED = 'QUEUED',
  RUNNING = 'RUNNING',
  PAUSED = 'PAUSED',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  CANCELLED = 'CANCELLED',
}

// ═══════════════════════════════════════════════════════════════════════════
// NODE CONFIGURATION TYPES
// ═══════════════════════════════════════════════════════════════════════════

export interface Position {
  x: number;
  y: number;
}

export interface RetryConfig {
  maxAttempts: number;
  backoffType: 'fixed' | 'exponential';
  backoffDelay: number;
}

export interface InputMapping {
  [key: string]: string | number | boolean | InputMapping;
}

export interface PipelineNode {
  id: string;
  type: NodeActionType;
  label: string;
  position: Position;
  inputs: InputMapping;
  config?: Record<string, any>;
  retryConfig?: RetryConfig;
  timeoutMs?: number;
  onError?: 'fail' | 'continue' | 'retry';
}

export interface PipelineEdge {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string;
  label?: string;
}

export interface PipelineDefinition {
  version: string;
  nodes: PipelineNode[];
  edges: PipelineEdge[];
  variables?: Record<string, any>;
}

// ═══════════════════════════════════════════════════════════════════════════
// PIPELINE TYPES
// ═══════════════════════════════════════════════════════════════════════════

export interface Pipeline {
  id: string;
  name: string;
  description?: string;
  isActive: boolean;
  isTemplate: boolean;
  triggerNodeId: string;
  definition: PipelineDefinition;
  cronExpression?: string;
  ownerId: string;
  totalExecutions: number;
  successfulExecutions: number;
  failedExecutions: number;
  lastExecutedAt?: Date;
  metadata?: Record<string, any>;
  tags?: string[];
  createdAt: Date;
  updatedAt: Date;
}

export interface PipelineSummary {
  id: string;
  name: string;
  description?: string;
  isActive: boolean;
  totalExecutions: number;
  successfulExecutions: number;
  failedExecutions: number;
  lastExecutedAt?: Date;
  tags?: string[];
  createdAt: Date;
  updatedAt: Date;
}

// ═══════════════════════════════════════════════════════════════════════════
// EXECUTION TYPES
// ═══════════════════════════════════════════════════════════════════════════

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

export interface PipelineExecution {
  id: string;
  pipelineId: string;
  status: PipelineExecutionStatus;
  currentStepId?: string;
  context: Record<string, any>;
  stepLogs: StepExecutionLog[];
  error?: string;
  errorStepId?: string;
  retryCount: number;
  startedAt: Date;
  completedAt?: Date;
  durationMs?: number;
  usage?: {
    totalTokens?: number;
    estimatedCostUsd?: number;
    apiCalls?: number;
  };
}

export interface ExecutionStatus {
  id: string;
  pipelineId: string;
  status: PipelineExecutionStatus;
  currentStepId?: string;
  progress: number; // 0-100
  stepLogs: StepExecutionLog[];
  error?: string;
  startedAt: Date;
  completedAt?: Date;
  durationMs?: number;
}

// ═══════════════════════════════════════════════════════════════════════════
// TEMPLATE TYPES
// ═══════════════════════════════════════════════════════════════════════════

export interface PipelineTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  definition: PipelineDefinition;
  icon?: string;
  complexity: number; // 1-5
  estimatedDuration?: string;
  requiredIntegrations?: string[];
  isPublic: boolean;
  usageCount: number;
  createdAt: Date;
}

// ═══════════════════════════════════════════════════════════════════════════
// REQUEST/RESPONSE TYPES
// ═══════════════════════════════════════════════════════════════════════════

export interface CreatePipelineRequest {
  name: string;
  description?: string;
  triggerNodeId: string;
  definition: PipelineDefinition;
  cronExpression?: string;
  tags?: string[];
  metadata?: Record<string, any>;
}

export interface UpdatePipelineRequest {
  name?: string;
  description?: string;
  isActive?: boolean;
  triggerNodeId?: string;
  definition?: PipelineDefinition;
  cronExpression?: string;
  tags?: string[];
  metadata?: Record<string, any>;
}

export interface ExecutePipelineRequest {
  payload?: Record<string, any>;
  dryRun?: boolean;
  priority?: 'low' | 'normal' | 'high';
}

export interface ExecutionStartedResponse {
  executionId: string;
  status: string;
  message: string;
  queuePosition?: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
  hasNext: boolean;
  hasPrev: boolean;
}

// ═══════════════════════════════════════════════════════════════════════════
// NODE METADATA (For UI rendering)
// ═══════════════════════════════════════════════════════════════════════════

export interface NodeTypeMetadata {
  type: NodeActionType;
  label: string;
  description: string;
  category: 'trigger' | 'action' | 'logic';
  subcategory?: string;
  icon: string;
  color: string;
  inputs: NodeInputDefinition[];
  outputs: NodeOutputDefinition[];
}

export interface NodeInputDefinition {
  key: string;
  label: string;
  type: 'string' | 'number' | 'boolean' | 'json' | 'select' | 'template';
  required: boolean;
  defaultValue?: any;
  placeholder?: string;
  options?: { value: string; label: string }[];
  description?: string;
}

export interface NodeOutputDefinition {
  key: string;
  label: string;
  type: string;
  description?: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// NODE REGISTRY (All available nodes with their metadata)
// ═══════════════════════════════════════════════════════════════════════════

export const NODE_REGISTRY: NodeTypeMetadata[] = [
  // Triggers
  {
    type: NodeActionType.TRIGGER_MANUAL,
    label: 'Manual Trigger',
    description: 'Start the pipeline manually from the UI',
    category: 'trigger',
    icon: 'Play',
    color: 'blue',
    inputs: [],
    outputs: [{ key: 'payload', label: 'Trigger Payload', type: 'object' }],
  },
  {
    type: NodeActionType.TRIGGER_SCHEDULE,
    label: 'Scheduled Trigger',
    description: 'Run on a schedule (cron)',
    category: 'trigger',
    icon: 'Clock',
    color: 'blue',
    inputs: [
      { key: 'cron', label: 'Cron Expression', type: 'string', required: true, placeholder: '0 9 * * 1' },
    ],
    outputs: [{ key: 'scheduledAt', label: 'Scheduled Time', type: 'date' }],
  },
  {
    type: NodeActionType.TRIGGER_WEBHOOK,
    label: 'Webhook Trigger',
    description: 'Triggered by an external HTTP request',
    category: 'trigger',
    icon: 'Webhook',
    color: 'blue',
    inputs: [],
    outputs: [
      { key: 'body', label: 'Request Body', type: 'object' },
      { key: 'headers', label: 'Request Headers', type: 'object' },
    ],
  },
  
  // SIE-X Actions
  {
    type: NodeActionType.ACTION_SIEX_ANALYZE,
    label: 'Analyze Content',
    description: 'Use SIE-X to analyze a URL or text',
    category: 'action',
    subcategory: 'intelligence',
    icon: 'Brain',
    color: 'purple',
    inputs: [
      { key: 'url', label: 'URL to Analyze', type: 'template', required: false, placeholder: '{{trigger.url}}' },
      { key: 'text', label: 'Or Text Content', type: 'template', required: false },
    ],
    outputs: [
      { key: 'entities', label: 'Extracted Entities', type: 'array' },
      { key: 'intent', label: 'Search Intent', type: 'string' },
      { key: 'score', label: 'Quality Score', type: 'number' },
    ],
  },
  {
    type: NodeActionType.ACTION_SIEX_COMPARE_SERP,
    label: 'Compare with SERP',
    description: 'Find content gaps by comparing to top search results',
    category: 'action',
    subcategory: 'intelligence',
    icon: 'GitCompare',
    color: 'purple',
    inputs: [
      { key: 'targetUrl', label: 'Your URL', type: 'template', required: true },
      { key: 'keyword', label: 'Target Keyword', type: 'template', required: true },
      { key: 'limit', label: 'Compare Top N', type: 'number', required: false, defaultValue: 5 },
    ],
    outputs: [
      { key: 'missingEntities', label: 'Missing Entities', type: 'array' },
      { key: 'coverageScore', label: 'Coverage Score', type: 'number' },
    ],
  },
  
  // BACOWR Actions
  {
    type: NodeActionType.ACTION_BACOWR_GENERATE,
    label: 'Generate Article',
    description: 'Use BACOWR to generate SEO content',
    category: 'action',
    subcategory: 'content',
    icon: 'FileText',
    color: 'green',
    inputs: [
      { key: 'topic', label: 'Topic/Keyword', type: 'template', required: true },
      { key: 'targetUrl', label: 'Link Target URL', type: 'template', required: false },
      { key: 'anchorText', label: 'Anchor Text', type: 'template', required: false },
      { key: 'tone', label: 'Writing Tone', type: 'select', required: false, options: [
        { value: 'professional', label: 'Professional' },
        { value: 'casual', label: 'Casual' },
        { value: 'academic', label: 'Academic' },
      ]},
      { key: 'wordCount', label: 'Target Word Count', type: 'number', required: false, defaultValue: 1500 },
    ],
    outputs: [
      { key: 'title', label: 'Article Title', type: 'string' },
      { key: 'content', label: 'Article Content', type: 'string' },
      { key: 'metaDescription', label: 'Meta Description', type: 'string' },
    ],
  },
  {
    type: NodeActionType.ACTION_BACOWR_PATCH,
    label: 'Patch Content',
    description: 'Add missing entities to existing content',
    category: 'action',
    subcategory: 'content',
    icon: 'FilePlus',
    color: 'green',
    inputs: [
      { key: 'content', label: 'Original Content', type: 'template', required: true },
      { key: 'missingEntities', label: 'Entities to Add', type: 'template', required: true },
      { key: 'tone', label: 'Match Tone', type: 'template', required: false },
    ],
    outputs: [
      { key: 'patchedContent', label: 'Updated Content', type: 'string' },
      { key: 'addedEntities', label: 'Added Entities', type: 'array' },
    ],
  },
  
  // Logic Nodes
  {
    type: NodeActionType.LOGIC_CONDITION,
    label: 'If/Else',
    description: 'Branch based on a condition',
    category: 'logic',
    icon: 'GitBranch',
    color: 'orange',
    inputs: [
      { key: 'value', label: 'Value to Check', type: 'template', required: true },
      { key: 'operator', label: 'Operator', type: 'select', required: true, options: [
        { value: 'equals', label: 'Equals' },
        { value: 'not_equals', label: 'Not Equals' },
        { value: 'contains', label: 'Contains' },
        { value: 'gt', label: 'Greater Than' },
        { value: 'lt', label: 'Less Than' },
        { value: 'is_empty', label: 'Is Empty' },
      ]},
      { key: 'compareValue', label: 'Compare To', type: 'template', required: false },
    ],
    outputs: [
      { key: 'result', label: 'Condition Result', type: 'boolean' },
    ],
  },
  {
    type: NodeActionType.LOGIC_DELAY,
    label: 'Delay',
    description: 'Wait before continuing',
    category: 'logic',
    icon: 'Timer',
    color: 'orange',
    inputs: [
      { key: 'delay', label: 'Delay (seconds)', type: 'number', required: true, defaultValue: 5 },
    ],
    outputs: [],
  },
  
  // Utility Actions
  {
    type: NodeActionType.ACTION_SEND_EMAIL,
    label: 'Send Email',
    description: 'Send an email notification',
    category: 'action',
    subcategory: 'notification',
    icon: 'Mail',
    color: 'cyan',
    inputs: [
      { key: 'to', label: 'Recipient Email', type: 'template', required: true },
      { key: 'subject', label: 'Subject', type: 'template', required: true },
      { key: 'body', label: 'Email Body', type: 'template', required: true },
    ],
    outputs: [{ key: 'sent', label: 'Sent Successfully', type: 'boolean' }],
  },
  {
    type: NodeActionType.ACTION_SLACK_NOTIFY,
    label: 'Slack Message',
    description: 'Send a Slack notification',
    category: 'action',
    subcategory: 'notification',
    icon: 'MessageSquare',
    color: 'cyan',
    inputs: [
      { key: 'channel', label: 'Channel', type: 'string', required: true, placeholder: '#seo-alerts' },
      { key: 'message', label: 'Message', type: 'template', required: true },
    ],
    outputs: [{ key: 'sent', label: 'Sent Successfully', type: 'boolean' }],
  },
];

// Helper to get node metadata by type
export function getNodeMetadata(type: NodeActionType): NodeTypeMetadata | undefined {
  return NODE_REGISTRY.find((n) => n.type === type);
}

// Group nodes by category for sidebar
export function getNodesByCategory(): Record<string, NodeTypeMetadata[]> {
  return NODE_REGISTRY.reduce((acc, node) => {
    const key = node.subcategory ? `${node.category}:${node.subcategory}` : node.category;
    if (!acc[key]) acc[key] = [];
    acc[key].push(node);
    return acc;
  }, {} as Record<string, NodeTypeMetadata[]>);
}
