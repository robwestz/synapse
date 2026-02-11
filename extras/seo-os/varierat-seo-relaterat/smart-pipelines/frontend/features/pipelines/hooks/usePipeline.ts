/**
 * @fileoverview usePipeline Hook - React State Management
 * 
 * APEX Generation Metadata:
 * - Signed by: Roxanne (State Management), Marcus (UX)
 * 
 * This hook manages:
 * - Pipeline definition state (nodes, edges)
 * - Saving/loading pipelines
 * - Execution triggers and status
 * - Undo/redo functionality
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import { useToast } from '@/components/ui/use-toast';
import { pipelineApi, ApiError } from '../api/pipelineService';
import {
  Pipeline,
  PipelineDefinition,
  PipelineNode,
  PipelineEdge,
  ExecutionStatus,
  PipelineExecutionStatus,
  NodeActionType,
} from '../types/pipeline.types';

// ═══════════════════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════════════════

interface UsePipelineState {
  // Pipeline data
  pipeline: Pipeline | null;
  nodes: PipelineNode[];
  edges: PipelineEdge[];
  
  // UI state
  isLoading: boolean;
  isSaving: boolean;
  isExecuting: boolean;
  isDirty: boolean;
  
  // Execution state
  currentExecution: ExecutionStatus | null;
  
  // History for undo/redo
  history: PipelineDefinition[];
  historyIndex: number;
}

interface UsePipelineActions {
  // Pipeline CRUD
  loadPipeline: (id: string) => Promise<void>;
  savePipeline: () => Promise<void>;
  createPipeline: (name: string, description?: string) => Promise<string>;
  
  // Node operations
  addNode: (node: PipelineNode) => void;
  updateNode: (id: string, updates: Partial<PipelineNode>) => void;
  removeNode: (id: string) => void;
  
  // Edge operations
  addEdge: (edge: PipelineEdge) => void;
  removeEdge: (id: string) => void;
  
  // Bulk operations
  setNodes: (nodes: PipelineNode[]) => void;
  setEdges: (edges: PipelineEdge[]) => void;
  
  // Execution
  executePipeline: (payload?: Record<string, any>) => Promise<void>;
  cancelExecution: () => Promise<void>;
  
  // History
  undo: () => void;
  redo: () => void;
  
  // Utilities
  reset: () => void;
  validate: () => { valid: boolean; errors: string[] };
}

// ═══════════════════════════════════════════════════════════════════════════
// DEFAULT STATE
// ═══════════════════════════════════════════════════════════════════════════

const defaultNode: PipelineNode = {
  id: 'trigger-1',
  type: NodeActionType.TRIGGER_MANUAL,
  label: 'Manual Trigger',
  position: { x: 250, y: 50 },
  inputs: {},
};

const initialState: UsePipelineState = {
  pipeline: null,
  nodes: [defaultNode],
  edges: [],
  isLoading: false,
  isSaving: false,
  isExecuting: false,
  isDirty: false,
  currentExecution: null,
  history: [],
  historyIndex: -1,
};

// ═══════════════════════════════════════════════════════════════════════════
// HOOK
// ═══════════════════════════════════════════════════════════════════════════

export function usePipeline(pipelineId?: string): UsePipelineState & UsePipelineActions {
  const [state, setState] = useState<UsePipelineState>(initialState);
  const { toast } = useToast();
  
  // Polling ref for execution status
  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  // ═══════════════════════════════════════════════════════════════════════
  // HISTORY MANAGEMENT
  // ═══════════════════════════════════════════════════════════════════════

  const pushHistory = useCallback((definition: PipelineDefinition) => {
    setState((prev) => ({
      ...prev,
      history: [...prev.history.slice(0, prev.historyIndex + 1), definition],
      historyIndex: prev.historyIndex + 1,
    }));
  }, []);

  const undo = useCallback(() => {
    setState((prev) => {
      if (prev.historyIndex <= 0) return prev;
      
      const newIndex = prev.historyIndex - 1;
      const historicState = prev.history[newIndex];
      
      return {
        ...prev,
        nodes: historicState.nodes,
        edges: historicState.edges,
        historyIndex: newIndex,
        isDirty: true,
      };
    });
  }, []);

  const redo = useCallback(() => {
    setState((prev) => {
      if (prev.historyIndex >= prev.history.length - 1) return prev;
      
      const newIndex = prev.historyIndex + 1;
      const historicState = prev.history[newIndex];
      
      return {
        ...prev,
        nodes: historicState.nodes,
        edges: historicState.edges,
        historyIndex: newIndex,
        isDirty: true,
      };
    });
  }, []);

  // ═══════════════════════════════════════════════════════════════════════
  // PIPELINE CRUD
  // ═══════════════════════════════════════════════════════════════════════

  const loadPipeline = useCallback(async (id: string) => {
    setState((prev) => ({ ...prev, isLoading: true }));

    try {
      const pipeline = await pipelineApi.getPipeline(id);
      
      setState((prev) => ({
        ...prev,
        pipeline,
        nodes: pipeline.definition.nodes,
        edges: pipeline.definition.edges,
        isLoading: false,
        isDirty: false,
        history: [pipeline.definition],
        historyIndex: 0,
      }));
    } catch (error) {
      const apiError = error as ApiError;
      toast({
        title: 'Error loading pipeline',
        description: apiError.message,
        variant: 'destructive',
      });
      setState((prev) => ({ ...prev, isLoading: false }));
    }
  }, [toast]);

  const savePipeline = useCallback(async () => {
    if (!state.pipeline) return;

    setState((prev) => ({ ...prev, isSaving: true }));

    const definition: PipelineDefinition = {
      version: state.pipeline.definition.version || '1.0.0',
      nodes: state.nodes,
      edges: state.edges,
    };

    // Find trigger node
    const triggerNode = state.nodes.find((n) => n.type.startsWith('TRIGGER_'));

    try {
      await pipelineApi.updatePipeline(state.pipeline.id, {
        definition,
        triggerNodeId: triggerNode?.id,
      });

      setState((prev) => ({
        ...prev,
        isSaving: false,
        isDirty: false,
        pipeline: prev.pipeline
          ? { ...prev.pipeline, definition }
          : null,
      }));

      toast({
        title: 'Pipeline saved',
        description: 'Your changes have been saved successfully.',
      });
    } catch (error) {
      const apiError = error as ApiError;
      toast({
        title: 'Error saving pipeline',
        description: apiError.message,
        variant: 'destructive',
      });
      setState((prev) => ({ ...prev, isSaving: false }));
    }
  }, [state.pipeline, state.nodes, state.edges, toast]);

  const createPipeline = useCallback(async (name: string, description?: string): Promise<string> => {
    setState((prev) => ({ ...prev, isSaving: true }));

    const definition: PipelineDefinition = {
      version: '1.0.0',
      nodes: state.nodes,
      edges: state.edges,
    };

    const triggerNode = state.nodes.find((n) => n.type.startsWith('TRIGGER_'));

    try {
      const pipeline = await pipelineApi.createPipeline({
        name,
        description,
        definition,
        triggerNodeId: triggerNode?.id || 'trigger-1',
      });

      setState((prev) => ({
        ...prev,
        pipeline,
        isSaving: false,
        isDirty: false,
      }));

      toast({
        title: 'Pipeline created',
        description: `"${name}" has been created successfully.`,
      });

      return pipeline.id;
    } catch (error) {
      const apiError = error as ApiError;
      toast({
        title: 'Error creating pipeline',
        description: apiError.message,
        variant: 'destructive',
      });
      setState((prev) => ({ ...prev, isSaving: false }));
      throw error;
    }
  }, [state.nodes, state.edges, toast]);

  // ═══════════════════════════════════════════════════════════════════════
  // NODE OPERATIONS
  // ═══════════════════════════════════════════════════════════════════════

  const addNode = useCallback((node: PipelineNode) => {
    setState((prev) => {
      const newNodes = [...prev.nodes, node];
      const definition = { version: '1.0.0', nodes: newNodes, edges: prev.edges };
      return {
        ...prev,
        nodes: newNodes,
        isDirty: true,
        history: [...prev.history.slice(0, prev.historyIndex + 1), definition],
        historyIndex: prev.historyIndex + 1,
      };
    });
  }, []);

  const updateNode = useCallback((id: string, updates: Partial<PipelineNode>) => {
    setState((prev) => {
      const newNodes = prev.nodes.map((node) =>
        node.id === id ? { ...node, ...updates } : node,
      );
      const definition = { version: '1.0.0', nodes: newNodes, edges: prev.edges };
      return {
        ...prev,
        nodes: newNodes,
        isDirty: true,
        history: [...prev.history.slice(0, prev.historyIndex + 1), definition],
        historyIndex: prev.historyIndex + 1,
      };
    });
  }, []);

  const removeNode = useCallback((id: string) => {
    setState((prev) => {
      const newNodes = prev.nodes.filter((node) => node.id !== id);
      // Also remove connected edges
      const newEdges = prev.edges.filter(
        (edge) => edge.source !== id && edge.target !== id,
      );
      const definition = { version: '1.0.0', nodes: newNodes, edges: newEdges };
      return {
        ...prev,
        nodes: newNodes,
        edges: newEdges,
        isDirty: true,
        history: [...prev.history.slice(0, prev.historyIndex + 1), definition],
        historyIndex: prev.historyIndex + 1,
      };
    });
  }, []);

  const setNodes = useCallback((nodes: PipelineNode[]) => {
    setState((prev) => ({
      ...prev,
      nodes,
      isDirty: true,
    }));
  }, []);

  // ═══════════════════════════════════════════════════════════════════════
  // EDGE OPERATIONS
  // ═══════════════════════════════════════════════════════════════════════

  const addEdge = useCallback((edge: PipelineEdge) => {
    setState((prev) => {
      // Prevent duplicate edges
      const exists = prev.edges.some(
        (e) => e.source === edge.source && e.target === edge.target,
      );
      if (exists) return prev;

      const newEdges = [...prev.edges, edge];
      const definition = { version: '1.0.0', nodes: prev.nodes, edges: newEdges };
      return {
        ...prev,
        edges: newEdges,
        isDirty: true,
        history: [...prev.history.slice(0, prev.historyIndex + 1), definition],
        historyIndex: prev.historyIndex + 1,
      };
    });
  }, []);

  const removeEdge = useCallback((id: string) => {
    setState((prev) => {
      const newEdges = prev.edges.filter((edge) => edge.id !== id);
      const definition = { version: '1.0.0', nodes: prev.nodes, edges: newEdges };
      return {
        ...prev,
        edges: newEdges,
        isDirty: true,
        history: [...prev.history.slice(0, prev.historyIndex + 1), definition],
        historyIndex: prev.historyIndex + 1,
      };
    });
  }, []);

  const setEdges = useCallback((edges: PipelineEdge[]) => {
    setState((prev) => ({
      ...prev,
      edges,
      isDirty: true,
    }));
  }, []);

  // ═══════════════════════════════════════════════════════════════════════
  // EXECUTION
  // ═══════════════════════════════════════════════════════════════════════

  const executePipeline = useCallback(async (payload?: Record<string, any>) => {
    if (!state.pipeline) {
      toast({
        title: 'Cannot execute',
        description: 'Please save the pipeline first.',
        variant: 'destructive',
      });
      return;
    }

    // Save first if dirty
    if (state.isDirty) {
      await savePipeline();
    }

    setState((prev) => ({ ...prev, isExecuting: true }));

    try {
      const result = await pipelineApi.executePipeline(state.pipeline.id, {
        payload,
      });

      // Start polling for status
      startPolling(result.executionId);

      toast({
        title: 'Pipeline started',
        description: 'Execution has been queued.',
      });
    } catch (error) {
      const apiError = error as ApiError;
      toast({
        title: 'Execution failed',
        description: apiError.message,
        variant: 'destructive',
      });
      setState((prev) => ({ ...prev, isExecuting: false }));
    }
  }, [state.pipeline, state.isDirty, savePipeline, toast]);

  const startPolling = useCallback((executionId: string) => {
    // Clear any existing polling
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
    }

    const poll = async () => {
      try {
        const status = await pipelineApi.getExecution(executionId);
        
        setState((prev) => ({
          ...prev,
          currentExecution: status,
          isExecuting: ![
            PipelineExecutionStatus.COMPLETED,
            PipelineExecutionStatus.FAILED,
            PipelineExecutionStatus.CANCELLED,
          ].includes(status.status as PipelineExecutionStatus),
        }));

        // Stop polling if execution is done
        if (
          [
            PipelineExecutionStatus.COMPLETED,
            PipelineExecutionStatus.FAILED,
            PipelineExecutionStatus.CANCELLED,
          ].includes(status.status as PipelineExecutionStatus)
        ) {
          if (pollingRef.current) {
            clearInterval(pollingRef.current);
            pollingRef.current = null;
          }

          // Show completion toast
          const isSuccess = status.status === PipelineExecutionStatus.COMPLETED;
          toast({
            title: isSuccess ? 'Execution completed' : 'Execution failed',
            description: isSuccess
              ? `Completed in ${status.durationMs}ms`
              : status.error || 'Unknown error',
            variant: isSuccess ? 'default' : 'destructive',
          });
        }
      } catch (error) {
        console.error('Polling error:', error);
      }
    };

    // Initial poll
    poll();

    // Continue polling every 2 seconds
    pollingRef.current = setInterval(poll, 2000);
  }, [toast]);

  const cancelExecution = useCallback(async () => {
    if (!state.currentExecution) return;

    try {
      await pipelineApi.cancelExecution(state.currentExecution.id);
      
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }

      setState((prev) => ({
        ...prev,
        isExecuting: false,
        currentExecution: prev.currentExecution
          ? { ...prev.currentExecution, status: PipelineExecutionStatus.CANCELLED }
          : null,
      }));

      toast({
        title: 'Execution cancelled',
        description: 'The pipeline execution has been stopped.',
      });
    } catch (error) {
      const apiError = error as ApiError;
      toast({
        title: 'Cancel failed',
        description: apiError.message,
        variant: 'destructive',
      });
    }
  }, [state.currentExecution, toast]);

  // ═══════════════════════════════════════════════════════════════════════
  // VALIDATION
  // ═══════════════════════════════════════════════════════════════════════

  const validate = useCallback((): { valid: boolean; errors: string[] } => {
    const errors: string[] = [];

    // Must have at least one trigger
    const triggers = state.nodes.filter((n) => n.type.startsWith('TRIGGER_'));
    if (triggers.length === 0) {
      errors.push('Pipeline must have at least one trigger node');
    }
    if (triggers.length > 1) {
      errors.push('Pipeline can only have one trigger node');
    }

    // All edges must reference existing nodes
    const nodeIds = new Set(state.nodes.map((n) => n.id));
    for (const edge of state.edges) {
      if (!nodeIds.has(edge.source)) {
        errors.push(`Edge source "${edge.source}" not found`);
      }
      if (!nodeIds.has(edge.target)) {
        errors.push(`Edge target "${edge.target}" not found`);
      }
    }

    // Check for orphan nodes (except trigger)
    for (const node of state.nodes) {
      if (node.type.startsWith('TRIGGER_')) continue;
      
      const hasIncoming = state.edges.some((e) => e.target === node.id);
      if (!hasIncoming) {
        errors.push(`Node "${node.label}" has no incoming connections`);
      }
    }

    return {
      valid: errors.length === 0,
      errors,
    };
  }, [state.nodes, state.edges]);

  // ═══════════════════════════════════════════════════════════════════════
  // RESET
  // ═══════════════════════════════════════════════════════════════════════

  const reset = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
    setState(initialState);
  }, []);

  // ═══════════════════════════════════════════════════════════════════════
  // EFFECTS
  // ═══════════════════════════════════════════════════════════════════════

  // Load pipeline on mount if ID provided
  useEffect(() => {
    if (pipelineId) {
      loadPipeline(pipelineId);
    }
  }, [pipelineId, loadPipeline]);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, []);

  // ═══════════════════════════════════════════════════════════════════════
  // RETURN
  // ═══════════════════════════════════════════════════════════════════════

  return {
    // State
    ...state,

    // Actions
    loadPipeline,
    savePipeline,
    createPipeline,
    addNode,
    updateNode,
    removeNode,
    setNodes,
    addEdge,
    removeEdge,
    setEdges,
    executePipeline,
    cancelExecution,
    undo,
    redo,
    reset,
    validate,
  };
}
