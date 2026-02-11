/**
 * @fileoverview ActionNode Component - SEO Intelligence & Content Nodes
 * 
 * APEX Generation Metadata:
 * - Signed by: Leo (SEO Logic), Chen (Data Mapping)
 * 
 * This node represents actions like:
 * - SIE-X analysis and entity extraction
 * - BACOWR content generation
 * - HTTP requests, notifications, etc.
 */

'use client';

import React, { memo, useState } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import {
  Brain,
  GitCompare,
  BarChart3,
  FileText,
  FilePlus,
  RefreshCw,
  Globe,
  Mail,
  MessageSquare,
  Database,
  Settings,
  ChevronDown,
  ChevronRight,
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';

import {
  NodeActionType,
  PipelineNode,
  getNodeMetadata,
} from '../../types/pipeline.types';

// ═══════════════════════════════════════════════════════════════════════════
// ICON & COLOR MAPPING
// ═══════════════════════════════════════════════════════════════════════════

const actionIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  [NodeActionType.ACTION_SIEX_ANALYZE]: Brain,
  [NodeActionType.ACTION_SIEX_EXTRACT_ENTITIES]: Brain,
  [NodeActionType.ACTION_SIEX_COMPARE_SERP]: GitCompare,
  [NodeActionType.ACTION_SERP_CHECK]: BarChart3,
  [NodeActionType.ACTION_BACOWR_GENERATE]: FileText,
  [NodeActionType.ACTION_BACOWR_REWRITE]: RefreshCw,
  [NodeActionType.ACTION_BACOWR_PATCH]: FilePlus,
  [NodeActionType.ACTION_HTTP_REQUEST]: Globe,
  [NodeActionType.ACTION_SEND_EMAIL]: Mail,
  [NodeActionType.ACTION_SLACK_NOTIFY]: MessageSquare,
  [NodeActionType.ACTION_SAVE_TO_DB]: Database,
};

const actionColors: Record<string, { gradient: string; accent: string; bg: string }> = {
  intelligence: {
    gradient: 'from-purple-500 to-purple-600',
    accent: 'bg-purple-500',
    bg: 'bg-purple-50',
  },
  content: {
    gradient: 'from-green-500 to-green-600',
    accent: 'bg-green-500',
    bg: 'bg-green-50',
  },
  notification: {
    gradient: 'from-cyan-500 to-cyan-600',
    accent: 'bg-cyan-500',
    bg: 'bg-cyan-50',
  },
  default: {
    gradient: 'from-slate-500 to-slate-600',
    accent: 'bg-slate-500',
    bg: 'bg-slate-50',
  },
};

function getColorScheme(type: NodeActionType) {
  if (type.includes('SIEX') || type.includes('SERP')) {
    return actionColors.intelligence;
  }
  if (type.includes('BACOWR')) {
    return actionColors.content;
  }
  if (type.includes('EMAIL') || type.includes('SLACK')) {
    return actionColors.notification;
  }
  return actionColors.default;
}

// ═══════════════════════════════════════════════════════════════════════════
// COMPONENT
// ═══════════════════════════════════════════════════════════════════════════

interface ActionNodeData extends PipelineNode {
  onUpdate?: (updates: Partial<PipelineNode>) => void;
  executionStatus?: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
}

export const ActionNode = memo(({ data, selected }: NodeProps<ActionNodeData>) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  const Icon = actionIcons[data.type] || Settings;
  const colors = getColorScheme(data.type);
  const metadata = getNodeMetadata(data.type);

  const getStatusBorder = () => {
    switch (data.executionStatus) {
      case 'running':
        return 'border-blue-500 animate-pulse';
      case 'completed':
        return 'border-green-500';
      case 'failed':
        return 'border-red-500';
      default:
        return selected ? 'border-slate-400' : 'border-slate-200';
    }
  };

  const handleInputChange = (key: string, value: any) => {
    if (data.onUpdate) {
      data.onUpdate({
        inputs: { ...data.inputs, [key]: value },
      });
    }
  };

  return (
    <div
      className={`
        w-72 rounded-xl border-2 bg-white shadow-md
        transition-all duration-200
        ${getStatusBorder()}
        ${selected ? 'shadow-lg' : ''}
      `}
    >
      {/* Input Handle */}
      <Handle
        type="target"
        position={Position.Top}
        className={`w-3 h-3 ${colors.accent} border-2 border-white`}
      />

      {/* Header */}
      <div className={`px-4 py-3 bg-gradient-to-r ${colors.gradient} rounded-t-lg`}>
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-white/20 rounded-md">
            <Icon className="w-4 h-4 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-sm text-white truncate">
              {data.label}
            </h3>
            <p className="text-xs text-white/70 truncate">
              {metadata?.description || 'Action'}
            </p>
          </div>
          {data.executionStatus && (
            <Badge
              variant={
                data.executionStatus === 'completed'
                  ? 'default'
                  : data.executionStatus === 'failed'
                  ? 'destructive'
                  : 'secondary'
              }
              className="text-xs"
            >
              {data.executionStatus}
            </Badge>
          )}
        </div>
      </div>

      {/* Configuration Panel */}
      <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
        <CollapsibleTrigger className="w-full">
          <div
            className={`
              px-4 py-2 flex items-center justify-between
              hover:bg-slate-50 transition-colors cursor-pointer
              border-b border-slate-100
            `}
          >
            <span className="text-xs font-medium text-slate-500">
              Configuration
            </span>
            {isExpanded ? (
              <ChevronDown className="w-4 h-4 text-slate-400" />
            ) : (
              <ChevronRight className="w-4 h-4 text-slate-400" />
            )}
          </div>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <div className="px-4 py-3 space-y-3 bg-slate-50/50">
            {metadata?.inputs.map((input) => (
              <div key={input.key} className="space-y-1">
                <Label className="text-xs text-slate-600">
                  {input.label}
                  {input.required && <span className="text-red-500 ml-1">*</span>}
                </Label>

                {input.type === 'select' ? (
                  <Select
                    value={data.inputs?.[input.key]?.toString() || ''}
                    onValueChange={(value) => handleInputChange(input.key, value)}
                  >
                    <SelectTrigger className="h-8 text-xs">
                      <SelectValue placeholder={input.placeholder || 'Select...'} />
                    </SelectTrigger>
                    <SelectContent>
                      {input.options?.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                ) : (
                  <Input
                    className="h-8 text-xs font-mono"
                    placeholder={input.placeholder || `{{step.${input.key}}}`}
                    value={data.inputs?.[input.key]?.toString() || ''}
                    onChange={(e) => handleInputChange(input.key, e.target.value)}
                  />
                )}

                {input.description && (
                  <p className="text-xs text-slate-400">{input.description}</p>
                )}
              </div>
            ))}

            {(!metadata?.inputs || metadata.inputs.length === 0) && (
              <p className="text-xs text-slate-400 italic">
                No configuration required
              </p>
            )}
          </div>
        </CollapsibleContent>
      </Collapsible>

      {/* Preview of current inputs */}
      {!isExpanded && Object.keys(data.inputs || {}).length > 0 && (
        <div className="px-4 py-2 border-t border-slate-100">
          <div className="flex flex-wrap gap-1">
            {Object.entries(data.inputs || {})
              .slice(0, 3)
              .map(([key, value]) => (
                <span
                  key={key}
                  className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded truncate max-w-[120px]"
                  title={`${key}: ${value}`}
                >
                  {key}: {String(value).substring(0, 15)}
                  {String(value).length > 15 ? '...' : ''}
                </span>
              ))}
            {Object.keys(data.inputs || {}).length > 3 && (
              <span className="text-xs text-slate-400">
                +{Object.keys(data.inputs).length - 3} more
              </span>
            )}
          </div>
        </div>
      )}

      {/* Output Handle */}
      <Handle
        type="source"
        position={Position.Bottom}
        className={`w-3 h-3 ${colors.accent} border-2 border-white`}
      />
    </div>
  );
});

ActionNode.displayName = 'ActionNode';

export default ActionNode;
