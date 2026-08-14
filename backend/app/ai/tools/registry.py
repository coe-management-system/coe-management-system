from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    success: bool
    data: dict | list | None = None
    error: str | None = None
    metadata: dict = Field(default_factory=dict)


class Tool(BaseModel):
    name: str
    description: str
    parameters: dict
    required_parameters: List[str]
    permission: str
    executor: Callable


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register_tool(self, tool: Tool):
        """Registers a new tool in the registry."""
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[Tool]:
        """Retrieves a tool by name."""
        return self._tools.get(name)

    def is_authorized(self, required_permission: str, user_role: str) -> bool:
        """Checks if user_role has sufficient authorization for required_permission."""
        role = user_role.upper()
        perm = required_permission.upper()

        if perm in ("READ", "STUDENT", "ALL", "PUBLIC"):
            return True
        if perm in ("FACULTY", "SIMULATION"):
            return role in ("FACULTY", "ADMIN")
        if perm == "ADMIN":
            return role == "ADMIN"
        return True

    def execute(self, name: str, user_role: str = "FACULTY", **kwargs) -> ToolResult:
        """
        Executes a registered tool by name with the given arguments.
        Handles parameter validation, RBAC checks, and catches exceptions to return a structured ToolResult.
        """
        tool = self.get_tool(name)
        if not tool:
            return ToolResult(
                success=False,
                data=None,
                error=f"Tool '{name}' not found in registry.",
            )

        # RBAC Check
        if not self.is_authorized(tool.permission, user_role):
            return ToolResult(
                success=False,
                data=None,
                error=f"Permission Denied: User role '{user_role}' is not authorized to execute tool '{name}'. Required permission level: '{tool.permission}'.",
                metadata={"tool": tool.name, "rbac_status": "DENIED", "user_role": user_role}
            )

        # Validate required parameters
        for req_param in tool.required_parameters:
            if req_param not in kwargs:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Missing required parameter: {req_param}",
                    metadata={"tool": tool.name}
                )

        # Execute tool
        try:
            result = tool.executor(**kwargs)
            # Ensure the result is a ToolResult
            if isinstance(result, dict) and "success" in result:
                tr = ToolResult(**result)
            elif isinstance(result, ToolResult):
                tr = result
            else:
                tr = ToolResult(
                    success=True,
                    data=result,
                )
            
            # Inject tool name into metadata
            if "tool" not in tr.metadata:
                tr.metadata["tool"] = tool.name
            return tr
        except ValueError as e:
            # Handle specific known errors (like invalid ID formats) without stack traces
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
                metadata={"tool": tool.name}
            )
        except Exception as e:
            # Catch-all for backend failures to prevent stack trace leaks to AI
            return ToolResult(
                success=False,
                data=None,
                error="Backend service unavailable or encountered an error.",
                metadata={"tool": tool.name}
            )

registry = ToolRegistry()

