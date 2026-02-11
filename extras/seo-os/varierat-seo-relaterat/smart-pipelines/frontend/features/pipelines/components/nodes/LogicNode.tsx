/**
 * @fileoverview LogicNode Component - Control Flow & Branching
 * 
 * APEX Generation Metadata:
 * - Signed by: Aria (Agentic Architect)
 * 
 * This node handles:
 * - Conditional branching (If/Else)
 * - Delays
 * - Loops
 * - Switch/Case
 * - Merge points
 */

'use client';

import React, { memo, useState } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import {
  GitBranch,
  Timer,
  Repeat,
  Route,
  GitMerge,
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

import { NodeActionType, PipelineNode } from '../../types/pipeline.types';

// ═══════════════════════════════════════════════════════════════════════════
// ICON MAPPING
// ═══════════════════════════════════════════════════════════════════════════

const logicIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  [NodeActionType.LOGIC_CONDITION]: GitBranch,
  [NodeActionType.LOGIC_DELAY]: Timer,
  [NodeActionType.LOGIC_LOOP]: Repeat,
  [NodeActionType.LOGIC_SWITCH]: Route,
  [NodeActionType.LOGIC_MERGE]: GitMerge,
};

// Operators for condition node
const operators = [
  { value: 'equals', label: '= Equals' },
  { value: 'not_equals', label: '≠ Not Equals' },
  { value: 'contains', label: '∋ Contains' },
  { value: 'not_contains', label: '∌ Not Contains' },
  { value: 'gt', label: '> Greater Than' },
  { value: 'lt', label: '< Less Than' },
  { value: 'gte', label: '≥ Greater or Equal' },
  { value: 'lte', label: '≤ Less or Equal' },
  { value: 'is_empty', label: '∅ Is Empty' },
  { value: 'is_not_empty', label: '≢ Is Not Empty' },
  { value: 'regex', label: '~ Matches Regex' },
];

// ═══════════════════════════════════════════════════════════════════════════
// COMPONENT
// ═══════════════════════════════════════════════════════════════════════════

interface LogicNodeData extends PipelineNode {
  onUpdate?: (updates: Partial<PipelineNode>) => void;
  executionStatus?: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
}

export const LogicNode = memo(({ data, selected }: NodeProps<LogicNodeData>) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  const Icon = logicIcons[data.type] || GitBranch;
  const isCondition = data.type === NodeActionType.LOGIC_CONDITION;
  const isSwitch = data.type === NodeActionType.LOGIC_SWITCH;

  const getStatusBorder = () => {
    switch (data.executionStatus) {
      case 'running':
        return 'border-orange-500 animate-pulse';
      case 'completed':
        return 'border-green-500';
      case 'failed':
        return 'border-red-500';
      default:
        return selected ? 'border-orange-400' : 'border-orange-200';
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
        w-64 rounded-xl border-2 bg-white shadow-md
        transition-all duration-200
        ${getStatusBorder()}
        ${selected ? 'shadow-lg' : ''}
      `}
    >
      {/* Input Handle */}
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 bg-orange-500 border-2 border-white"
      />

      {/* Header */}
      <div className="px-4 py-3 bg-gradient-to-r from-orange-500 to-orange-600 rounded-t-lg">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-white/20 rounded-md">
            <Icon className="w-4 h-4 text-white" />
          </div>
          <div className="flex-1">
            <h3 className="font-semibold text-sm text-white truncate">
              {data.label}
            </h3>
            <p className="text-xs text-orange-100">Logic</p>
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
          <div className="px-4 py-2 flex items-center justify-between hover:bg-slate-50 transition-colors cursor-pointer border-b border-slate-100">
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
          <div className="px-4 py-3 space-y-3 bg-orange-50/30">
            {/* Condition Node Config */}
            {isCondition && (
              <>
                <div className="space-y-1">
                  <Label className="text-xs text-slate-600">
                    Value to Check <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    className="h-8 text-xs font-mono"
                    placeholder="{{step_1.score}}"
                    value={data.inputs?.value?.toString() || ''}
                    onChange={(e) => handleInputChange('value', e.target.value)}
                  />
                </div>

                <div className="space-y-1">
                  <Label className="text-xs text-slate-600">
                    Operator <span className="text-red-500">*</span>
                  </Label>
                  <Select
                    value={data.inputs?.operator?.toString() || ''}
                    onValueChange={(value) => handleInputChange('operator', value)}
                  >
                    <SelectTrigger className="h-8 text-xs">
                      <SelectValue placeholder="Select operator..." />
                    </SelectTrigger>
                    <SelectContent>
                      {operators.map((op) => (
                        <SelectItem key={op.value} value={op.value}>
                          {op.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {!['is_empty', 'is_not_empty'].includes(
                  data.inputs?.operator?.toString() || '',
                ) && (
                  <div className="space-y-1">
                    <Label className="text-xs text-slate-600">Compare To</Label>
                    <Input
                      className="h-8 text-xs font-mono"
                      placeholder="0.5"
                      value={data.inputs?.compareValue?.toString() || ''}
                      onChange={(e) =>
                        handleInputChange('compareValue', e.target.value)
                      }
                    />
                  </div>
                )}
              </>
            )}

            {/* Delay Node Config */}
            {data.type === NodeActionType.LOGIC_DELAY && (
              <div className="space-y-1">
                <Label className="text-xs text-slate-600">
                  Delay (seconds) <span className="text-red-500">*</span>
                </Label>
                <Input
                  type="number"
                  className="h-8 text-xs"
                  placeholder="5"
                  value={data.inputs?.delay?.toString() || ''}
                  onChange={(e) =>
                    handleInputChange('delay', parseInt(e.target.value) || 0)
                  }
                />
              </div>
            )}

            {/* Loop Node Config */}
            {data.type === NodeActionType.LOGIC_LOOP && (
              <>
                <div className="space-y-1">
                  <Label className="text-xs text-slate-600">
                    Items Array <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    className="h-8 text-xs font-mono"
                    placeholder="{{step_1.results}}"
                    value={data.inputs?.items?.toString() || ''}
                    onChange={(e) => handleInputChange('items', e.target.value)}
                  />
                </div>

                <div className="space-y-1">
                  <Label className="text-xs text-slate-600">Max Iterations</Label>
                  <Input
                    type="number"
                    className="h-8 text-xs"
                    placeholder="100"
                    value={data.inputs?.maxIterations?.toString() || ''}
                    onChange={(e) =>
                      handleInputChange(
                        'maxIterations',
                        parseInt(e.target.value) || 100,
                      )
                    }
                  />
                </div>
              </>
            )}

            {/* Switch Node Config */}
            {isSwitch && (
              <div className="space-y-1">
                <Label className="text-xs text-slate-600">
                  Value to Switch On <span className="text-red-500">*</span>
                </Label>
                <Input
                  className="h-8 text-xs font-mono"
                  placeholder="{{step_1.intent}}"
                  value={data.inputs?.value?.toString() || ''}
                  onChange={(e) => handleInputChange('value', e.target.value)}
                />
                <p className="text-xs text-slate-400">
                  Create output handles for each case value
                </p>
              </div>
            )}

            {/* Merge Node */}
            {data.type === NodeActionType.LOGIC_MERGE && (
              <p className="text-xs text-slate-500 italic">
                Merges multiple inputs into one output. Connect multiple nodes
                to this merge point.
              </p>
            )}
          </div>
        </CollapsibleContent>
      </Collapsible>

      {/* Preview of condition */}
      {!isExpanded && isCondition && data.inputs?.operator && (
        <div className="px-4 py-2 border-t border-slate-100">
          <div className="text-xs text-slate-600 font-mono bg-slate-50 px-2 py-1 rounded">
            {data.inputs.value || '?'} {data.inputs.operator}{' '}
            {data.inputs.compareValue || '?'}
          </div>
        </div>
      )}

      {/* Output Handles */}
      {isCondition ? (
        // Two handles for true/false branches
        <>
          <Handle
            type="source"
            position={Position.Bottom}
            id="true"
            className="w-3 h-3 bg-green-500 border-2 border-white"
            style={{ left: '30%' }}
          />
          <div
            className="absolute text-xs text-green-600 font-medium"
            style={{ bottom: -20, left: '25%' }}
          >
            True
          </div>
          <Handle
            type="source"
            position={Position.Bottom}
            id="false"
            className="w-3 h-3 bg-red-500 border-2 border-white"
            style={{ left: '70%' }}
          />
          <div
            className="absolute text-xs text-red-600 font-medium"
            style={{ bottom: -20, left: '65%' }}
          >
            False
          </div>
        </>
      ) : data.type === NodeActionType.LOGIC_LOOP ? (
        // Two handles for iteration/complete
        <>
          <Handle
            type="source"
            position={Position.Bottom}
            id="iteration"
            className="w-3 h-3 bg-blue-500 border-2 border-white"
            style={{ left: '30%' }}
          />
          <div
            className="absolute text-xs text-blue-600 font-medium"
            style={{ bottom: -20, left: '20%' }}
          >
            Each
          </div>
          <Handle
            type="source"
            position={Position.Bottom}
            id="complete"
            className="w-3 h-3 bg-green-500 border-2 border-white"
            style={{ left: '70%' }}
          />
          <div
            className="absolute text-xs text-green-600 font-medium"
            style={{ bottom: -20, left: '60%' }}
          >
            Done
          </div>
        </>
      ) : (
        // Single output handle
        <Handle
          type="source"
          position={Position.Bottom}
          className="w-3 h-3 bg-orange-500 border-2 border-white"
        />
      )}
    </div>
  );
});

LogicNode.displayName = 'LogicNode';

export default LogicNode;
