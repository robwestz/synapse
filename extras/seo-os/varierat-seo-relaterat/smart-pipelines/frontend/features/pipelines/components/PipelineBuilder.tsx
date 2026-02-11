/**
 * @fileoverview PipelineBuilder Component - The Visual Canvas
 * 
 * APEX Generation Metadata:
 * - Signed by: Marcus (UX), Leo (SEO Nodes)
 * 
 * This is the main component that renders:
 * - React Flow canvas for visual pipeline editing
 * - Sidebar with available nodes
 * - Toolbar with save/execute buttons
 */

'use client';

import React, { useCallback, useRef, useState } from 'react';
import ReactFlow, {
  addEdge,
  Background,
  Controls,
  MiniMap,
  Connection,
  Edge,
  Node,
  useNodesState,
  useEdgesState,
  ReactFlowProvider,
  ReactFlowInstance,
  MarkerType,
} from 'reactflow';
import 'reactflow/dist/style.css';

import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/use-toast';
import {
  Save,
  Play,
  Square,
  Undo,
  Redo,
  Settings,
  Download,
  Upload,
} from 'lucide-react';

// Custom nodes
import { TriggerNode } from './nodes/TriggerNode';
import { ActionNode } from './nodes/ActionNode';
import { LogicNode } from './nodes/LogicNode';

// Sidebar
import { PipelineSidebar } from './PipelineSidebar';

// Hook
import { usePipeline } from '../hooks/usePipeline';

// Types
import {
  PipelineNode,
  PipelineEdge,
  NodeActionType,
  getNodeMetadata,
} from '../types/pipeline.types';

// ═══════════════════════════════════════════════════════════════════════════
// NODE TYPE REGISTRATION
// ═══════════════════════════════════════════════════════════════════════════

const nodeTypes = {
  trigger: TriggerNode,
  action: ActionNode,
  logic: LogicNode,
};

// Map our node types to React Flow node types
function getReactFlowNodeType(actionType: NodeActionType): string {
  if (actionType.startsWith('TRIGGER_')) return 'trigger';
  if (actionType.startsWith('LOGIC_')) return 'logic';
  return 'action';
}

// ═══════════════════════════════════════════════════════════════════════════
// COMPONENT
// ═══════════════════════════════════════════════════════════════════════════

interface PipelineBuilderProps {
  pipelineId?: string;
}

function PipelineBuilderInner({ pipelineId }: PipelineBuilderProps) {
  const { toast } = useToast();
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [reactFlowInstance, setReactFlowInstance] = useState<ReactFlowInstance | null>(null);

  // Use our custom hook for state management
  const {
    pipeline,
    nodes: pipelineNodes,
    edges: pipelineEdges,
    isLoading,
    isSaving,
    isExecuting,
    isDirty,
    currentExecution,
    savePipeline,
    addNode,
    updateNode,
    removeNode,
    setNodes: setPipelineNodes,
    addEdge: addPipelineEdge,
    removeEdge: removePipelineEdge,
    setEdges: setPipelineEdges,
    executePipeline,
    cancelExecution,
    undo,
    redo,
    validate,
  } = usePipeline(pipelineId);

  // Convert our pipeline nodes to React Flow nodes
  const initialNodes: Node[] = pipelineNodes.map((node) => ({
    id: node.id,
    type: getReactFlowNodeType(node.type),
    position: node.position,
    data: {
      ...node,
      onUpdate: (updates: Partial<PipelineNode>) => updateNode(node.id, updates),
      executionStatus: currentExecution?.stepLogs?.find((log) => log.stepId === node.id)?.status,
    },
  }));

  const initialEdges: Edge[] = pipelineEdges.map((edge) => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    sourceHandle: edge.sourceHandle,
    animated: currentExecution?.currentStepId === edge.source,
    markerEnd: {
      type: MarkerType.ArrowClosed,
      width: 20,
      height: 20,
    },
    style: {
      strokeWidth: 2,
    },
  }));

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Sync React Flow state back to our hook
  const onNodesChangeWrapper = useCallback(
    (changes: any) => {
      onNodesChange(changes);
      // Debounce sync to pipeline state
      const updatedNodes = changes.reduce((acc: PipelineNode[], change: any) => {
        if (change.type === 'position' && change.position) {
          const node = pipelineNodes.find((n) => n.id === change.id);
          if (node) {
            return [...acc, { ...node, position: change.position }];
          }
        }
        return acc;
      }, []);
      if (updatedNodes.length > 0) {
        // Batch position updates
      }
    },
    [onNodesChange, pipelineNodes],
  );

  // Handle new connections
  const onConnect = useCallback(
    (params: Connection) => {
      if (!params.source || !params.target) return;

      const newEdge: PipelineEdge = {
        id: `edge_${Date.now()}`,
        source: params.source,
        target: params.target,
        sourceHandle: params.sourceHandle || undefined,
      };

      addPipelineEdge(newEdge);
      setEdges((eds) =>
        addEdge(
          {
            ...params,
            id: newEdge.id,
            markerEnd: { type: MarkerType.ArrowClosed },
          },
          eds,
        ),
      );
    },
    [addPipelineEdge, setEdges],
  );

  // Handle drag and drop from sidebar
  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      if (!reactFlowWrapper.current || !reactFlowInstance) return;

      const actionType = event.dataTransfer.getData('actionType') as NodeActionType;
      if (!actionType) return;

      const bounds = reactFlowWrapper.current.getBoundingClientRect();
      const position = reactFlowInstance.project({
        x: event.clientX - bounds.left,
        y: event.clientY - bounds.top,
      });

      const metadata = getNodeMetadata(actionType);
      const newNode: PipelineNode = {
        id: `node_${Date.now()}`,
        type: actionType,
        label: metadata?.label || actionType,
        position,
        inputs: {},
      };

      addNode(newNode);

      // Add to React Flow
      setNodes((nds) => [
        ...nds,
        {
          id: newNode.id,
          type: getReactFlowNodeType(actionType),
          position,
          data: {
            ...newNode,
            onUpdate: (updates: Partial<PipelineNode>) => updateNode(newNode.id, updates),
          },
        },
      ]);
    },
    [reactFlowInstance, addNode, setNodes, updateNode],
  );

  // Handle node deletion
  const onNodesDelete = useCallback(
    (nodesToDelete: Node[]) => {
      nodesToDelete.forEach((node) => removeNode(node.id));
    },
    [removeNode],
  );

  // Handle edge deletion
  const onEdgesDelete = useCallback(
    (edgesToDelete: Edge[]) => {
      edgesToDelete.forEach((edge) => removePipelineEdge(edge.id));
    },
    [removePipelineEdge],
  );

  // Save handler
  const handleSave = useCallback(async () => {
    const { valid, errors } = validate();
    if (!valid) {
      toast({
        title: 'Validation Error',
        description: errors.join(', '),
        variant: 'destructive',
      });
      return;
    }
    await savePipeline();
  }, [validate, savePipeline, toast]);

  // Execute handler
  const handleExecute = useCallback(async () => {
    const { valid, errors } = validate();
    if (!valid) {
      toast({
        title: 'Cannot Execute',
        description: errors.join(', '),
        variant: 'destructive',
      });
      return;
    }
    await executePipeline();
  }, [validate, executePipeline, toast]);

  // Export pipeline as JSON
  const handleExport = useCallback(() => {
    const data = {
      name: pipeline?.name || 'Untitled Pipeline',
      definition: {
        version: '1.0.0',
        nodes: pipelineNodes,
        edges: pipelineEdges,
      },
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${data.name.replace(/\s+/g, '_')}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [pipeline, pipelineNodes, pipelineEdges]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="flex h-screen w-full bg-slate-50">
      {/* Sidebar */}
      <PipelineSidebar />

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Toolbar */}
        <div className="h-14 border-b bg-white flex items-center justify-between px-4 shadow-sm">
          <div className="flex items-center gap-2">
            <h1 className="font-semibold text-lg text-slate-800">
              {pipeline?.name || 'New Pipeline'}
            </h1>
            {isDirty && (
              <span className="text-xs text-orange-500 font-medium">
                (unsaved changes)
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            {/* Undo/Redo */}
            <Button variant="ghost" size="icon" onClick={undo} title="Undo">
              <Undo className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="icon" onClick={redo} title="Redo">
              <Redo className="h-4 w-4" />
            </Button>

            <div className="w-px h-6 bg-slate-200 mx-2" />

            {/* Export */}
            <Button variant="ghost" size="icon" onClick={handleExport} title="Export">
              <Download className="h-4 w-4" />
            </Button>

            <div className="w-px h-6 bg-slate-200 mx-2" />

            {/* Save */}
            <Button
              variant="outline"
              onClick={handleSave}
              disabled={isSaving || !isDirty}
            >
              <Save className="h-4 w-4 mr-2" />
              {isSaving ? 'Saving...' : 'Save'}
            </Button>

            {/* Execute */}
            {isExecuting ? (
              <Button variant="destructive" onClick={cancelExecution}>
                <Square className="h-4 w-4 mr-2" />
                Stop
              </Button>
            ) : (
              <Button onClick={handleExecute} disabled={!pipeline}>
                <Play className="h-4 w-4 mr-2" />
                Run
              </Button>
            )}
          </div>
        </div>

        {/* Execution Progress Bar */}
        {currentExecution && (
          <div className="h-2 bg-slate-100">
            <div
              className={`h-full transition-all duration-300 ${
                currentExecution.status === 'COMPLETED'
                  ? 'bg-green-500'
                  : currentExecution.status === 'FAILED'
                  ? 'bg-red-500'
                  : 'bg-blue-500'
              }`}
              style={{ width: `${currentExecution.progress}%` }}
            />
          </div>
        )}

        {/* Canvas */}
        <div className="flex-1" ref={reactFlowWrapper}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChangeWrapper}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onInit={setReactFlowInstance}
            onDrop={onDrop}
            onDragOver={onDragOver}
            onNodesDelete={onNodesDelete}
            onEdgesDelete={onEdgesDelete}
            nodeTypes={nodeTypes}
            fitView
            snapToGrid
            snapGrid={[15, 15]}
            defaultEdgeOptions={{
              type: 'smoothstep',
              markerEnd: {
                type: MarkerType.ArrowClosed,
              },
            }}
          >
            <Background color="#94a3b8" gap={20} />
            <Controls />
            <MiniMap
              nodeStrokeColor={(n) => {
                if (n.type === 'trigger') return '#3b82f6';
                if (n.type === 'logic') return '#f97316';
                return '#22c55e';
              }}
              nodeColor={(n) => {
                if (n.type === 'trigger') return '#dbeafe';
                if (n.type === 'logic') return '#ffedd5';
                return '#dcfce7';
              }}
            />
          </ReactFlow>
        </div>
      </div>
    </div>
  );
}

// Wrap with provider
export function PipelineBuilder(props: PipelineBuilderProps) {
  return (
    <ReactFlowProvider>
      <PipelineBuilderInner {...props} />
    </ReactFlowProvider>
  );
}

export default PipelineBuilder;
