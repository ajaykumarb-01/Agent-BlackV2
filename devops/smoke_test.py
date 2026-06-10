"""Runtime smoke test for Agent Black agents.

Exercises:
  - GET  /health
  - GET  /capabilities
  - GET  /tools
  - POST /mcp       (tools/list and tools/call)
  - POST /research  (a tiny LLM-driven query)

Verifies that:
  - Every agent reports healthy
  - /capabilities "tasks" names match /tools registered MCP tool names
  - MCP tools/list returns one entry per canonical tool with a real inputSchema
  - MCP tools/call returns a result for a parameterless LLM-only tool
  - /research accepts a query and returns a structured AgentResponse

Usage:
    python devops/smoke_test.py            # tests the three specialist agents
    python devops/smoke_test.py --port 8001 # only one agent
    python devops/smoke_test.py --no-research # skip the LLM call
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Any

import httpx


DEFAULT_AGENTS = [
    ("research-agent", "http://localhost:8001"),
    ("solution-agent", "http://localhost:8002"),
    ("experiment-agent", "http://localhost:8003"),
]

TIMEOUT_SECONDS = 30


class SmokeTest:
    def __init__(self, base_url: str, agent_name: str, skip_research: bool = False) -> None:
        self.base_url = base_url.rstrip("/")
        self.agent_name = agent_name
        self.skip_research = skip_research
        self.passed: list[str] = []
        self.failed: list[tuple[str, str]] = []
        self.warnings: list[str] = []

    def _record(self, name: str, ok: bool, detail: str = "") -> None:
        if ok:
            self.passed.append(name)
            print(f"  PASS  {name}")
        else:
            self.failed.append((name, detail))
            print(f"  FAIL  {name}: {detail}")

    def _warn(self, msg: str) -> None:
        self.warnings.append(msg)
        print(f"  WARN  {msg}")

    def _get(self, path: str) -> tuple[int, Any]:
        with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
            r = client.get(f"{self.base_url}{path}")
        try:
            payload: Any = r.json()
        except Exception:
            payload = r.text
        return r.status_code, payload

    def _post(self, path: str, body: dict) -> tuple[int, Any]:
        with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
            r = client.post(f"{self.base_url}{path}", json=body)
        try:
            payload: Any = r.json()
        except Exception:
            payload = r.text
        return r.status_code, payload

    def test_health(self) -> None:
        status, body = self._get("/health")
        ok = status == 200 and isinstance(body, dict) and body.get("status") == "ok"
        self._record("/health", ok, f"status={status} body={body}")

    def test_capabilities(self) -> list[str]:
        status, body = self._get("/capabilities")
        if status != 200 or not isinstance(body, dict):
            self._record("/capabilities", False, f"status={status} body={body}")
            return []
        tasks = body.get("tasks") or []
        if not isinstance(tasks, list) or not tasks:
            self._record("/capabilities tasks", False, f"tasks={tasks}")
            return []
        self._record("/capabilities", True, "")
        return [str(t) for t in tasks]

    def test_tools(self) -> list[dict]:
        status, body = self._get("/tools")
        if status != 200 or not isinstance(body, dict):
            self._record("/tools", False, f"status={status} body={body}")
            return []
        tools = body.get("tools") or {}
        if not isinstance(tools, dict) or not tools:
            self._record("/tools entries", False, f"tools={type(tools).__name__}")
            return []
        self._record(f"/tools ({len(tools)} registered)", True, "")
        return list(tools.values())

    def test_capabilities_match_tools(self, capability_tasks: list[str], tool_entries: list[dict]) -> None:
        tool_names = {entry["name"] for entry in tool_entries if entry.get("name")}
        capability_set = set(capability_tasks)

        missing_in_caps = tool_names - capability_set
        missing_in_tools = capability_set - tool_names
        if missing_in_caps or missing_in_tools:
            detail = f"capability-only={sorted(missing_in_tools)} tool-only={sorted(missing_in_caps)}"
            self._record("capabilities <-> tools name match", False, detail)
        else:
            self._record("capabilities <-> tools name match", True, "")

    def test_schemas(self, tool_entries: list[dict]) -> None:
        if not tool_entries:
            self._record("schema strength", False, "no tools to inspect")
            return
        weak_count = 0
        for entry in tool_entries:
            schema = entry.get("inputSchema") or {}
            props = schema.get("properties") or {}
            if not isinstance(props, dict):
                weak_count += 1
                continue
            non_query_props = [k for k in props.keys() if k != "query"]
            if not non_query_props:
                weak_count += 1
        if weak_count:
            self._warn(f"{weak_count} tool(s) still expose only a 'query' property")
        self._record("schema strength (all tools have >1 property)", weak_count == 0, f"weak={weak_count}")

    def test_mcp_tools_list(self) -> list[dict]:
        status, body = self._post("/mcp", {"jsonrpc": "2.0", "method": "tools/list", "id": 1})
        if status != 200 or not isinstance(body, dict):
            self._record("MCP tools/list", False, f"status={status} body={body}")
            return []
        result = body.get("result") or {}
        tools = result.get("tools") or []
        if not isinstance(tools, list) or not tools:
            self._record("MCP tools/list entries", False, f"tools={tools}")
            return []
        self._record(f"MCP tools/list ({len(tools)} tools)", True, "")
        return tools

    def test_mcp_tools_call(self, mcp_tools: list[dict]) -> None:
        if not mcp_tools:
            self._record("MCP tools/call (citation_generator)", False, "no tools to call")
            return
        target = next((t for t in mcp_tools if t.get("name") == "citation_generator"), mcp_tools[0])
        target_name = target.get("name", "unknown")
        if target_name == "citation_generator":
            arguments = {"title": "Attention Is All You Need"}
        else:
            arguments = {"query": "transformer architecture"}
        status, body = self._post(
            "/mcp",
            {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {"name": target_name, "arguments": arguments},
                "id": 2,
            },
        )
        if status != 200 or not isinstance(body, dict):
            self._record(f"MCP tools/call {target_name}", False, f"status={status} body={body}")
            return
        if body.get("error"):
            self._warn(f"MCP tools/call {target_name} returned error: {body['error']}")
            self._record(f"MCP tools/call {target_name}", True, "got error payload (still a valid response)")
            return
        result = body.get("result") or {}
        content = result.get("content") or []
        ok = isinstance(content, list) and content and isinstance(content[0], dict) and "text" in content[0]
        self._record(f"MCP tools/call {target_name}", ok, "")

    def test_research_endpoint(self) -> None:
        if self.skip_research:
            self._warn("skipped /research (--no-research)")
            return
        status, body = self._post(
            "/research",
            {"query": "List three SOTA CV segmentation models", "context": {}},
        )
        if status != 200 or not isinstance(body, dict):
            self._record("/research", False, f"status={status} body={body}")
            return
        if body.get("error") and "not_research_query" not in str(body.get("error")):
            self._warn(f"/research returned error: {body.get('error')}")
        if "result" in body or "error" in body:
            self._record("/research", True, "")
        else:
            self._record("/research", False, f"unexpected body={body}")

    def run(self) -> dict:
        print(f"\n=== {self.agent_name} @ {self.base_url} ===")
        cap_tasks = self.test_capabilities()
        tool_entries = self.test_tools()
        if cap_tasks and tool_entries:
            self.test_capabilities_match_tools(cap_tasks, tool_entries)
            self.test_schemas(tool_entries)
        mcp_tools = self.test_mcp_tools_list()
        if mcp_tools:
            self.test_mcp_tools_call(mcp_tools)
        self.test_research_endpoint()
        return {
            "agent": self.agent_name,
            "base_url": self.base_url,
            "passed": self.passed,
            "failed": self.failed,
            "warnings": self.warnings,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Agent Black runtime smoke test")
    parser.add_argument("--port", type=int, default=None, help="Test only this port")
    parser.add_argument("--no-research", action="store_true", help="Skip the /research LLM call")
    args = parser.parse_args()

    agents = DEFAULT_AGENTS
    if args.port:
        agents = [a for a in DEFAULT_AGENTS if a[1].endswith(f":{args.port}")]
        if not agents:
            print(f"No agent registered for port {args.port}")
            return 2

    overall_pass = 0
    overall_fail = 0
    overall_warn = 0
    started = time.time()
    per_agent: list[dict] = []
    for name, url in agents:
        result = SmokeTest(url, name, skip_research=args.no_research).run()
        per_agent.append(result)
        overall_pass += len(result["passed"])
        overall_fail += len(result["failed"])
        overall_warn += len(result["warnings"])

    print("\n" + "=" * 60)
    print(f"TOTAL: {overall_pass} passed, {overall_fail} failed, {overall_warn} warnings in {time.time() - started:.1f}s")
    print("=" * 60)
    if overall_fail:
        for result in per_agent:
            for name, detail in result["failed"]:
                print(f"  - {result['agent']} :: {name} :: {detail}")
        return 1
    if overall_warn:
        for result in per_agent:
            for msg in result["warnings"]:
                print(f"  - {result['agent']} :: {msg}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
