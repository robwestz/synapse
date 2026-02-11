"""
SEO Intelligence Platform - Tool Framework Core
================================================

A minimal, manifest-driven framework for the SEO platform's 100 standardized tools.

Architecture:
    Manifest (YAML) → Registry → Adapter → API → Frontend

Since ALL tools follow the same pattern (Config → Service → Result),
we need minimal adapter code - just dynamic loading and execution.

Usage:
    from framework import ToolFramework
    
    framework = ToolFramework("manifests/")
    result = await framework.execute("content_gap_discovery", {
        "domain": "example.com",
        "competitors": ["comp1.com", "comp2.com"]
    })
"""

import asyncio
import importlib
import inspect
import json
import logging
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Callable
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tool_framework")


# =============================================================================
# CORE DATA STRUCTURES
# =============================================================================

@dataclass
class ToolManifest:
    """Manifest definition for a tool."""
    id: str
    name: str
    description: str
    category: str
    archetype: str  # analyzer, generator, monitor, optimizer, discoverer
    
    # Backend mapping
    module: str
    service_class: str
    config_class: str
    result_class: str
    entry_method: str = "analyze"  # analyze, generate, optimize, monitor, etc.
    
    # UI metadata
    icon: str = "⚙️"
    color: str = "#3B82F6"
    
    # Input/Output schemas (for UI generation)
    inputs: List[Dict] = field(default_factory=list)
    outputs: Dict = field(default_factory=dict)
    
    # Optional: actions that can be performed on results
    actions: List[Dict] = field(default_factory=list)
    
    @classmethod
    def from_yaml(cls, path: Path) -> "ToolManifest":
        """Load manifest from YAML file."""
        data = yaml.safe_load(path.read_text(encoding='utf-8'))
        tool = data.get('tool', data)
        
        return cls(
            id=tool['id'],
            name=tool['name'],
            description=tool.get('description', ''),
            category=tool.get('category', 'general'),
            archetype=tool.get('archetype', 'analyzer'),
            module=tool['backend']['module'],
            service_class=tool['backend']['class'],
            config_class=tool['backend'].get('config_class', f"{tool['backend']['class']}Config"),
            result_class=tool['backend'].get('result_class', f"{tool['backend']['class']}Result"),
            entry_method=tool['backend'].get('method', 'analyze'),
            icon=tool.get('icon', '⚙️'),
            color=tool.get('color', '#3B82F6'),
            inputs=tool.get('inputs', []),
            outputs=tool.get('outputs', {}),
            actions=tool.get('actions', []),
        )
    
    @classmethod
    def auto_generate(cls, module_path: str, tool_id: str) -> "ToolManifest":
        """Auto-generate manifest from Python module (for tools without YAML)."""
        # Import module
        module = importlib.import_module(module_path)
        
        # Find classes following the pattern
        config_class = None
        service_class = None
        result_class = None
        
        for name, obj in inspect.getmembers(module, inspect.isclass):
            name_lower = name.lower()
            if 'config' in name_lower:
                config_class = name
            elif 'result' in name_lower:
                result_class = name
            elif 'service' in name_lower or 'engine' in name_lower:
                service_class = name
        
        if not service_class:
            raise ValueError(f"No Service/Engine class found in {module_path}")
        
        # Detect entry method
        entry_method = "analyze"
        service_cls = getattr(module, service_class)
        for method_name in ['analyze', 'generate', 'optimize', 'monitor', 'process', 'execute']:
            if hasattr(service_cls, method_name):
                entry_method = method_name
                break
        
        # Generate readable name from tool_id
        name = tool_id.replace('_', ' ').title()
        
        return cls(
            id=tool_id,
            name=name,
            description=f"Auto-generated manifest for {name}",
            category="auto",
            archetype="analyzer",
            module=module_path,
            service_class=service_class,
            config_class=config_class or f"{service_class}Config",
            result_class=result_class or f"{service_class}Result",
            entry_method=entry_method,
        )


@dataclass
class ExecutionResult:
    """Standardized execution result."""
    success: bool
    tool_id: str
    data: Any
    execution_time_ms: float
    error: Optional[str] = None
    metrics: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return asdict(self)


# =============================================================================
# TOOL REGISTRY
# =============================================================================

class ToolRegistry:
    """
    Registry for all available tools.
    
    Supports:
    - Loading from YAML manifests
    - Auto-discovery from Python modules
    - Hybrid approach (YAML overrides auto-generated)
    """
    
    def __init__(self):
        self._manifests: Dict[str, ToolManifest] = {}
        self._loaded_services: Dict[str, Any] = {}
    
    def register(self, manifest: ToolManifest) -> None:
        """Register a tool manifest."""
        self._manifests[manifest.id] = manifest
        logger.info(f"Registered tool: {manifest.id} ({manifest.name})")
    
    def get(self, tool_id: str) -> Optional[ToolManifest]:
        """Get a tool manifest by ID."""
        return self._manifests.get(tool_id)
    
    def list_all(self) -> List[ToolManifest]:
        """List all registered tools."""
        return list(self._manifests.values())
    
    def list_by_category(self, category: str) -> List[ToolManifest]:
        """List tools in a category."""
        return [m for m in self._manifests.values() if m.category == category]
    
    def list_by_archetype(self, archetype: str) -> List[ToolManifest]:
        """List tools by archetype."""
        return [m for m in self._manifests.values() if m.archetype == archetype]
    
    def load_manifests_from_directory(self, manifest_dir: Path) -> int:
        """Load all YAML manifests from a directory."""
        count = 0
        for yaml_file in manifest_dir.rglob("*.yaml"):
            try:
                manifest = ToolManifest.from_yaml(yaml_file)
                self.register(manifest)
                count += 1
            except Exception as e:
                logger.warning(f"Failed to load manifest {yaml_file}: {e}")
        return count
    
    def auto_discover_tools(self, tools_dir: Path, base_module: str) -> int:
        """
        Auto-discover tools from Python files.
        
        For each .py file, attempts to auto-generate a manifest.
        Skips files that already have a manifest registered.
        """
        count = 0
        for py_file in tools_dir.rglob("*.py"):
            if py_file.name.startswith("_"):
                continue
            
            tool_id = py_file.stem
            if tool_id in self._manifests:
                continue  # Already have manifest
            
            # Build module path
            relative = py_file.relative_to(tools_dir)
            module_parts = list(relative.with_suffix("").parts)
            module_path = f"{base_module}.{'.'.join(module_parts)}"
            
            try:
                manifest = ToolManifest.auto_generate(module_path, tool_id)
                self.register(manifest)
                count += 1
            except Exception as e:
                logger.debug(f"Could not auto-discover {py_file}: {e}")
        
        return count
    
    def get_categories(self) -> List[str]:
        """Get all unique categories."""
        return list(set(m.category for m in self._manifests.values()))
    
    def get_archetypes(self) -> List[str]:
        """Get all unique archetypes."""
        return list(set(m.archetype for m in self._manifests.values()))


# =============================================================================
# TOOL ADAPTER (The magic that makes it all work!)
# =============================================================================

class ToolAdapter:
    """
    Universal adapter for executing tools.
    
    Since ALL tools follow the same pattern:
    - Config class for inputs
    - Service class with initialize/close/analyze
    - Result class with to_dict()
    
    This adapter can handle any tool with minimal code!
    """
    
    def __init__(self, manifest: ToolManifest):
        self.manifest = manifest
        self._module = None
        self._config_class = None
        self._service_class = None
        self._result_class = None
        self._service_instance = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Load and initialize the tool."""
        if self._initialized:
            return
        
        # Dynamic import
        try:
            self._module = importlib.import_module(self.manifest.module)
        except ImportError as e:
            raise RuntimeError(f"Failed to import module {self.manifest.module}: {e}")
        
        # Get classes
        self._config_class = getattr(self._module, self.manifest.config_class, None)
        self._service_class = getattr(self._module, self.manifest.service_class)
        self._result_class = getattr(self._module, self.manifest.result_class, None)
        
        # Instantiate service
        if self._config_class:
            config = self._config_class()
            self._service_instance = self._service_class(config)
        else:
            self._service_instance = self._service_class()
        
        # Initialize service (all tools have this!)
        if hasattr(self._service_instance, 'initialize'):
            await self._service_instance.initialize()
        
        self._initialized = True
        logger.info(f"Initialized tool: {self.manifest.id}")
    
    async def execute(self, data: Dict[str, Any]) -> ExecutionResult:
        """Execute the tool with given data."""
        if not self._initialized:
            await self.initialize()
        
        start_time = time.perf_counter()
        
        try:
            # Get the entry method
            method = getattr(self._service_instance, self.manifest.entry_method)
            
            # Execute
            if asyncio.iscoroutinefunction(method):
                result = await method(data)
            else:
                result = method(data)
            
            execution_time = (time.perf_counter() - start_time) * 1000
            
            # Convert result to dict if it has to_dict method
            if hasattr(result, 'to_dict'):
                result_data = result.to_dict()
            elif hasattr(result, '__dict__'):
                result_data = result.__dict__
            else:
                result_data = result
            
            # Get metrics if available
            metrics = {}
            if hasattr(self._service_instance, 'get_metrics'):
                metrics = self._service_instance.get_metrics()
            
            return ExecutionResult(
                success=True,
                tool_id=self.manifest.id,
                data=result_data,
                execution_time_ms=execution_time,
                metrics=metrics,
            )
            
        except Exception as e:
            execution_time = (time.perf_counter() - start_time) * 1000
            logger.error(f"Tool execution failed: {self.manifest.id} - {e}")
            return ExecutionResult(
                success=False,
                tool_id=self.manifest.id,
                data=None,
                execution_time_ms=execution_time,
                error=str(e),
            )
    
    async def close(self) -> None:
        """Clean up the tool."""
        if self._service_instance and hasattr(self._service_instance, 'close'):
            await self._service_instance.close()
        self._initialized = False


# =============================================================================
# TOOL FRAMEWORK (Main entry point)
# =============================================================================

class ToolFramework:
    """
    Main framework class - the single entry point for tool operations.
    
    Usage:
        framework = ToolFramework()
        framework.load_manifests("manifests/")
        framework.auto_discover("tools/", "tools")
        
        result = await framework.execute("content_gap_discovery", {
            "domain": "example.com"
        })
    """
    
    def __init__(self):
        self.registry = ToolRegistry()
        self._adapters: Dict[str, ToolAdapter] = {}
    
    def load_manifests(self, manifest_dir: str) -> int:
        """Load tool manifests from directory."""
        path = Path(manifest_dir)
        if not path.exists():
            logger.warning(f"Manifest directory not found: {manifest_dir}")
            return 0
        return self.registry.load_manifests_from_directory(path)
    
    def auto_discover(self, tools_dir: str, base_module: str) -> int:
        """Auto-discover tools from Python files."""
        path = Path(tools_dir)
        if not path.exists():
            logger.warning(f"Tools directory not found: {tools_dir}")
            return 0
        return self.registry.auto_discover_tools(path, base_module)
    
    def list_tools(self) -> List[Dict]:
        """List all available tools (for API/UI)."""
        return [
            {
                "id": m.id,
                "name": m.name,
                "description": m.description,
                "category": m.category,
                "archetype": m.archetype,
                "icon": m.icon,
                "color": m.color,
                "inputs": m.inputs,
                "outputs": m.outputs,
            }
            for m in self.registry.list_all()
        ]
    
    def get_tool(self, tool_id: str) -> Optional[Dict]:
        """Get tool details by ID."""
        manifest = self.registry.get(tool_id)
        if not manifest:
            return None
        return {
            "id": manifest.id,
            "name": manifest.name,
            "description": manifest.description,
            "category": manifest.category,
            "archetype": manifest.archetype,
            "icon": manifest.icon,
            "color": manifest.color,
            "inputs": manifest.inputs,
            "outputs": manifest.outputs,
            "actions": manifest.actions,
        }
    
    async def execute(self, tool_id: str, data: Dict[str, Any]) -> ExecutionResult:
        """Execute a tool."""
        manifest = self.registry.get(tool_id)
        if not manifest:
            return ExecutionResult(
                success=False,
                tool_id=tool_id,
                data=None,
                execution_time_ms=0,
                error=f"Tool not found: {tool_id}",
            )
        
        # Get or create adapter
        if tool_id not in self._adapters:
            self._adapters[tool_id] = ToolAdapter(manifest)
        
        adapter = self._adapters[tool_id]
        return await adapter.execute(data)
    
    async def execute_batch(
        self, 
        tool_id: str, 
        items: List[Dict[str, Any]],
        parallel: bool = True
    ) -> List[ExecutionResult]:
        """Execute a tool on multiple items."""
        if parallel:
            tasks = [self.execute(tool_id, item) for item in items]
            return await asyncio.gather(*tasks)
        else:
            results = []
            for item in items:
                result = await self.execute(tool_id, item)
                results.append(result)
            return results
    
    async def execute_pipeline(
        self,
        steps: List[Dict[str, Any]]
    ) -> List[ExecutionResult]:
        """
        Execute a pipeline of tools.
        
        Each step: {"tool_id": "...", "data": {...}, "pass_result_to_next": bool}
        """
        results = []
        previous_result = None
        
        for step in steps:
            tool_id = step["tool_id"]
            data = step.get("data", {})
            
            # Merge previous result if specified
            if step.get("pass_result_to_next") and previous_result:
                data = {**data, "previous_result": previous_result.data}
            
            result = await self.execute(tool_id, data)
            results.append(result)
            previous_result = result
            
            # Stop on error unless continue_on_error is set
            if not result.success and not step.get("continue_on_error"):
                break
        
        return results
    
    async def shutdown(self) -> None:
        """Shutdown all adapters."""
        for adapter in self._adapters.values():
            await adapter.close()
        self._adapters.clear()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

_default_framework: Optional[ToolFramework] = None


def get_framework() -> ToolFramework:
    """Get or create the default framework instance."""
    global _default_framework
    if _default_framework is None:
        _default_framework = ToolFramework()
    return _default_framework


async def execute_tool(tool_id: str, data: Dict[str, Any]) -> ExecutionResult:
    """Quick way to execute a tool."""
    return await get_framework().execute(tool_id, data)


# =============================================================================
# CLI FOR TESTING
# =============================================================================

if __name__ == "__main__":
    import sys
    
    async def main():
        framework = ToolFramework()
        
        # Example: load manifests and list tools
        if len(sys.argv) > 1:
            manifest_dir = sys.argv[1]
            count = framework.load_manifests(manifest_dir)
            print(f"Loaded {count} manifests from {manifest_dir}")
        
        if len(sys.argv) > 2:
            tools_dir = sys.argv[2]
            base_module = sys.argv[3] if len(sys.argv) > 3 else "tools"
            count = framework.auto_discover(tools_dir, base_module)
            print(f"Auto-discovered {count} tools from {tools_dir}")
        
        # List all tools
        tools = framework.list_tools()
        print(f"\nRegistered {len(tools)} tools:")
        for tool in tools:
            print(f"  - {tool['id']}: {tool['name']} ({tool['archetype']})")
    
    asyncio.run(main())
