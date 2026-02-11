/**
 * @fileoverview TriggerNode Component - Pipeline Entry Point
 * 
 * APEX Generation Metadata:
 * - Signed by: Aria (Orchestrator)
 * 
 * This node represents the starting point of a pipeline.
 * Only one trigger node is allowed per pipeline.
 */

'use client';

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Play, Clock, Webhook, Rss } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { NodeActionType, PipelineNode } from '../../types/pipeline.types';

// ═══════════════════════════════════════════════════════════════════════════
// ICON MAPPING
// ═══════════════════════════════════════════════════════════════════════════

const triggerIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  [NodeActionType.TRIGGER_MANUAL]: Play,
  [NodeActionType.TRIGGER_SCHEDULE]: Clock,
  [NodeActionType.TRIGGER_WEBHOOK]: Webhook,
  [NodeActionType.TRIGGER_RSS]: Rss,
};

// ═══════════════════════════════════════════════════════════════════════════
// COMPONENT
// ═══════════════════════════════════════════════════════════════════════════

interface TriggerNodeData extends PipelineNode {
  onUpdate?: (updates: Partial<PipelineNode>) => void;
  executionStatus?: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
}

export const TriggerNode = memo(({ data, selected }: NodeProps<TriggerNodeData>) => {
  const Icon = triggerIcons[data.type] || Play;

  const getStatusColor = () => {
    switch (data.executionStatus) {
      case 'running':
        return 'border-blue-500 bg-blue-50';
      case 'completed':
        return 'border-green-500 bg-green-50';
      case 'failed':
        return 'border-red-500 bg-red-50';
      default:
        return selected ? 'border-blue-500' : 'border-blue-200';
    }
  };

  return (
    <div
      className={`
        w-56 rounded-xl border-2 bg-white shadow-md
        transition-all duration-200
        ${getStatusColor()}
        ${selected ? 'shadow-lg ring-2 ring-blue-200' : ''}
      `}
    >
      {/* Header */}
      <div className="px-4 py-3 bg-gradient-to-r from-blue-500 to-blue-600 rounded-t-lg">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-white/20 rounded-md">
            <Icon className="w-4 h-4 text-white" />
          </div>
          <div className="flex-1">
            <h3 className="font-semibold text-sm text-white truncate">
              {data.label}
            </h3>
            <p className="text-xs text-blue-100">Trigger</p>
          </div>
          {data.executionStatus && (
            <Badge
              variant={data.executionStatus === 'completed' ? 'default' : 'secondary'}
              className="text-xs"
            >
              {data.executionStatus}
            </Badge>
          )}
        </div>
      </div>

      {/* Body */}
      <div className="px-4 py-3">
        {data.type === NodeActionType.TRIGGER_SCHEDULE && data.inputs?.cron && (
          <div className="text-xs text-slate-600">
            <span className="font-medium">Schedule:</span>{' '}
            <code className="bg-slate-100 px-1 py-0.5 rounded">
              {data.inputs.cron}
            </code>
          </div>
        )}
        
        {data.type === NodeActionType.TRIGGER_MANUAL && (
          <p className="text-xs text-slate-500">
            Click "Run" to start this pipeline manually
          </p>
        )}

        {data.type === NodeActionType.TRIGGER_WEBHOOK && (
          <p className="text-xs text-slate-500">
            Triggered by external HTTP POST request
          </p>
        )}

        {data.type === NodeActionType.TRIGGER_RSS && (
          <p className="text-xs text-slate-500">
            Triggered when new RSS feed items appear
          </p>
        )}
      </div>

      {/* Output Handle */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3 bg-blue-500 border-2 border-white"
      />
    </div>
  );
});

TriggerNode.displayName = 'TriggerNode';

export default TriggerNode;
