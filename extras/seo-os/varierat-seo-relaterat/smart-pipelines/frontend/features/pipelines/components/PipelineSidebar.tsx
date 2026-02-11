/**
 * @fileoverview PipelineSidebar Component - The Node Toolbox
 * 
 * APEX Generation Metadata:
 * - Signed by: Leo (SEO Nodes), Marcus (UX)
 * 
 * This sidebar displays all available nodes grouped by category.
 * Users can drag nodes from here onto the canvas.
 */

'use client';

import React, { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import {
  Search,
  ChevronDown,
  ChevronRight,
  Play,
  Clock,
  Webhook,
  Rss,
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
  GitBranch,
  Timer,
  Repeat,
  Route,
  GitMerge,
} from 'lucide-react';

import {
  NODE_REGISTRY,
  NodeTypeMetadata,
  NodeActionType,
} from '../types/pipeline.types';

// ═══════════════════════════════════════════════════════════════════════════
// ICON MAPPING
// ═══════════════════════════════════════════════════════════════════════════

const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
  Play,
  Clock,
  Webhook,
  Rss,
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
  GitBranch,
  Timer,
  Repeat,
  Route,
  GitMerge,
};

// ═══════════════════════════════════════════════════════════════════════════
// CATEGORY CONFIGURATION
// ═══════════════════════════════════════════════════════════════════════════

interface CategoryConfig {
  label: string;
  description: string;
  color: string;
  bgColor: string;
  borderColor: string;
}

const categoryConfig: Record<string, CategoryConfig> = {
  trigger: {
    label: 'Triggers',
    description: 'Start your pipeline',
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
  },
  'action:intelligence': {
    label: 'SEO Intelligence (SIE-X)',
    description: 'Analyze and understand content',
    color: 'text-purple-600',
    bgColor: 'bg-purple-50',
    borderColor: 'border-purple-200',
  },
  'action:content': {
    label: 'Content Generation (BACOWR)',
    description: 'Create and modify content',
    color: 'text-green-600',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
  },
  'action:notification': {
    label: 'Notifications',
    description: 'Send alerts and messages',
    color: 'text-cyan-600',
    bgColor: 'bg-cyan-50',
    borderColor: 'border-cyan-200',
  },
  action: {
    label: 'Other Actions',
    description: 'Utility operations',
    color: 'text-slate-600',
    bgColor: 'bg-slate-50',
    borderColor: 'border-slate-200',
  },
  logic: {
    label: 'Logic',
    description: 'Control flow and branching',
    color: 'text-orange-600',
    bgColor: 'bg-orange-50',
    borderColor: 'border-orange-200',
  },
};

// ═══════════════════════════════════════════════════════════════════════════
// DRAGGABLE NODE ITEM
// ═══════════════════════════════════════════════════════════════════════════

interface NodeItemProps {
  node: NodeTypeMetadata;
  config: CategoryConfig;
}

function NodeItem({ node, config }: NodeItemProps) {
  const Icon = iconMap[node.icon] || Brain;

  const onDragStart = (event: React.DragEvent) => {
    event.dataTransfer.setData('actionType', node.type);
    event.dataTransfer.effectAllowed = 'move';
  };

  return (
    <div
      className={`
        p-3 rounded-lg border cursor-grab active:cursor-grabbing
        transition-all duration-150 hover:shadow-md hover:scale-[1.02]
        ${config.bgColor} ${config.borderColor}
      `}
      draggable
      onDragStart={onDragStart}
    >
      <div className="flex items-start gap-3">
        <div className={`p-2 rounded-md bg-white shadow-sm ${config.color}`}>
          <Icon className="w-4 h-4" />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="font-medium text-sm text-slate-800 truncate">
            {node.label}
          </h4>
          <p className="text-xs text-slate-500 mt-0.5 line-clamp-2">
            {node.description}
          </p>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// CATEGORY GROUP
// ═══════════════════════════════════════════════════════════════════════════

interface CategoryGroupProps {
  categoryKey: string;
  nodes: NodeTypeMetadata[];
  defaultOpen?: boolean;
}

function CategoryGroup({ categoryKey, nodes, defaultOpen = true }: CategoryGroupProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const config = categoryConfig[categoryKey] || categoryConfig.action;

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <CollapsibleTrigger className="w-full">
        <div className="flex items-center justify-between py-2 px-1 hover:bg-slate-50 rounded-md transition-colors">
          <div className="flex items-center gap-2">
            {isOpen ? (
              <ChevronDown className="w-4 h-4 text-slate-400" />
            ) : (
              <ChevronRight className="w-4 h-4 text-slate-400" />
            )}
            <span className={`font-semibold text-sm ${config.color}`}>
              {config.label}
            </span>
            <span className="text-xs text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">
              {nodes.length}
            </span>
          </div>
        </div>
      </CollapsibleTrigger>
      <CollapsibleContent>
        <div className="space-y-2 pl-6 pb-4">
          {nodes.map((node) => (
            <NodeItem key={node.type} node={node} config={config} />
          ))}
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ═══════════════════════════════════════════════════════════════════════════

export function PipelineSidebar() {
  const [searchQuery, setSearchQuery] = useState('');

  // Group nodes by category
  const groupedNodes = NODE_REGISTRY.reduce((acc, node) => {
    const key = node.subcategory
      ? `${node.category}:${node.subcategory}`
      : node.category;
    if (!acc[key]) acc[key] = [];
    acc[key].push(node);
    return acc;
  }, {} as Record<string, NodeTypeMetadata[]>);

  // Filter nodes by search query
  const filteredGroups = Object.entries(groupedNodes).reduce(
    (acc, [key, nodes]) => {
      if (!searchQuery) {
        acc[key] = nodes;
        return acc;
      }

      const filtered = nodes.filter(
        (node) =>
          node.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
          node.description.toLowerCase().includes(searchQuery.toLowerCase()),
      );

      if (filtered.length > 0) {
        acc[key] = filtered;
      }

      return acc;
    },
    {} as Record<string, NodeTypeMetadata[]>,
  );

  // Define category order
  const categoryOrder = [
    'trigger',
    'action:intelligence',
    'action:content',
    'action:notification',
    'action',
    'logic',
  ];

  const sortedCategories = categoryOrder.filter(
    (cat) => filteredGroups[cat]?.length > 0,
  );

  return (
    <Card className="w-72 h-full rounded-none border-r shadow-lg flex flex-col">
      {/* Header */}
      <div className="p-4 border-b bg-slate-50">
        <h2 className="font-bold text-lg text-slate-800 mb-1">Toolbox</h2>
        <p className="text-xs text-slate-500 mb-3">
          Drag nodes to the canvas to build your pipeline
        </p>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <Input
            placeholder="Search nodes..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 h-9 text-sm"
          />
        </div>
      </div>

      {/* Node List */}
      <ScrollArea className="flex-1 p-4">
        <div className="space-y-2">
          {sortedCategories.map((categoryKey) => (
            <CategoryGroup
              key={categoryKey}
              categoryKey={categoryKey}
              nodes={filteredGroups[categoryKey]}
              defaultOpen={categoryKey === 'trigger' || !!searchQuery}
            />
          ))}

          {sortedCategories.length === 0 && (
            <div className="text-center py-8 text-slate-400">
              <Search className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No nodes found</p>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Footer with tips */}
      <div className="p-4 border-t bg-slate-50">
        <div className="text-xs text-slate-500 space-y-1">
          <p>💡 <strong>Tip:</strong> Connect nodes by dragging from output to input handles.</p>
        </div>
      </div>
    </Card>
  );
}

export default PipelineSidebar;
