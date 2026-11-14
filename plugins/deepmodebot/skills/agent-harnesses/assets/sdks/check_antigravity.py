"""Exercise installed SDK configuration and tool dispatch without a model call."""
import asyncio
from importlib.metadata import distribution
from pathlib import Path

from google.antigravity import CapabilitiesConfig, LocalAgentConfig
from google.antigravity.tools.tool_runner import ToolRunner
from google.antigravity.types import BuiltinTools


def character_count(text: str) -> int:
    """Count Unicode code points in the supplied text."""
    return len(text)


async def main():
    package = distribution("google-antigravity")
    config = LocalAgentConfig(
        workspaces=[str(Path.cwd())],
        tools=[character_count],
        capabilities=CapabilitiesConfig(enabled_tools=[BuiltinTools.VIEW_FILE]),
    )
    runner = ToolRunner(tools=config.tools)
    result = await runner.execute("character_count", text="SDK check")
    if result != 9:
        raise RuntimeError(f"Custom tool returned {result!r}, expected 9")
    binaries = [
        package.locate_file(path) for path in package.files or []
        if path.name in {"localharness", "localharness.exe"}
    ]
    if not binaries or not all(path.is_file() for path in binaries):
        raise RuntimeError("Platform wheel has no installed localharness binary")
    print(f"google-antigravity {package.version}: config + custom tool dispatch PASS")
    print("Bundled runtime present; runtime startup and inference not exercised")


if __name__ == "__main__":
    asyncio.run(main())
