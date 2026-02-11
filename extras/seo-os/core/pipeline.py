"""
Project Nexus - Pipeline Engine
Handles automated workflows by chaining module tasks.
"""
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any, Callable
from core.database import save_asset, get_assets

logger = logging.getLogger(__name__)

class PipelineNode:
    def __init__(self, node_id: str, module_id: str, task_name: str, config: Dict = None):
        self.node_id = node_id
        self.module_id = module_id
        self.task_name = task_name
        self.config = config or {}

class PipelineRun:
    def __init__(self, pipeline_id: str, project_id: int = 1):
        self.run_id = str(uuid.uuid4())
        self.pipeline_id = pipeline_id
        self.project_id = project_id
        self.status = "Pending"
        self.logs = []
        self.results = {}

    def log(self, message: str):
        timestamp = datetime.now().isoformat()
        self.logs.append(f"[{timestamp}] {message}")
        logger.info(message)

class NexusPipelineEngine:
    def __init__(self):
        self.registry = {} # module_id -> {task_name: function}

    def register_task(self, module_id: str, task_name: str, func: Callable):
        if module_id not in self.registry:
            self.registry[module_id] = {}
        self.registry[module_id][task_name] = func
        logger.info(f"Registered task: {module_id}.{task_name}")

    async def run_pipeline(self, nodes: List[PipelineNode], project_id: int = 1) -> PipelineRun:
        run = PipelineRun("dynamic_pipeline", project_id)
        run.status = "Running"
        run.log(f"Starting pipeline run {run.run_id}")

        context = {} # Shared data between nodes

        for node in nodes:
            run.log(f"Executing Node: {node.node_id} ({node.module_id}.{node.task_name})")
            
            if node.module_id not in self.registry or node.task_name not in self.registry[node.module_id]:
                run.status = "Failed"
                run.log(f"Error: Task {node.module_id}.{node.task_name} not found in registry.")
                break

            try:
                task_func = self.registry[node.module_id][node.task_name]
                
                # Dynamic Recipe Injection
                # If config has 'recipe_id', fetch recipe and merge into config
                if 'recipe_id' in node.config:
                    recipe_assets = get_assets(project_id=project_id, asset_type="recipe")
                    # Find matching recipe
                    recipe = next((r for r in recipe_assets if r['id'] == node.config['recipe_id']), None)
                    if recipe:
                        run.log(f"Applying Data Recipe: {recipe['content']['name']}")
                        # Merge recipe config into node config (recipe takes precedence)
                        node.config.update(recipe['content']['config'])
                    else:
                        run.log(f"Warning: Recipe ID {node.config['recipe_id']} not found.")

                # Tasks receive (context, config, project_id)
                output = await task_func(context, node.config, project_id)
                
                # Update context with output
                context.update(output)
                run.log(f"Node {node.node_id} completed successfully.")
                
            except Exception as e:
                run.status = "Failed"
                run.log(f"Error in Node {node.node_id}: {str(e)}")
                break
        
        if run.status != "Failed":
            run.status = "Completed"
            run.log("Pipeline completed successfully.")
            
            # Save final state as a Nexus Asset
            save_asset(
                asset_id=run.run_id,
                project_id=project_id,
                module_id="pipeline_engine",
                asset_type="pipeline_run",
                content={"logs": run.logs, "final_context": context},
                metadata={"status": run.status, "pipeline_id": run.pipeline_id}
            )

        return run

# Global engine instance
nexus_engine = NexusPipelineEngine()
