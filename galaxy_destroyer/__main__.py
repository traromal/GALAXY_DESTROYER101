"""Main entry point - ties everything together"""

import os
import sys
import asyncio

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)

from core.app import GalaxyApp
from core.state import Context, State, AppMode
from commands import get_commands, execute_command

import commands.builtin
import commands.git
import services.tools.builtin


class GalaxyCLI(GalaxyApp):
    """Full-featured CLI with AI integration"""
    
    def __init__(self):
        super().__init__()
        self._setup_handlers()
        self._load_tools()
    
    def _setup_handlers(self):
        self.on("command", self._handle_command)
        self.on("complete", self._handle_completion)
        self.on("mode_changed", self._handle_mode_change)
    
    def _load_tools(self):
        """Load all tools"""
        from services.tools import get_executor
        executor = get_executor()
        self._tool_executor = executor
    
    def _handle_command(self, cmd: str):
        parts = cmd.split()
        
        if not parts:
            return
        
        cmd_name = parts[0]
        args = parts[1:]
        
        if cmd_name == "ai" or cmd_name == "ask":
            self._handle_ai_command(args)
            return
        
        if cmd_name == "tool":
            self._handle_tool_command(args)
            return
        
        if cmd_name == "tools":
            self._list_tools()
            return
        
        if cmd_name.startswith("/"):
            cmd_name = cmd_name[1:]
        
        result = execute_command(cmd_name, args, app=self)
        
        if result:
            self.add_output(result)
        else:
            self.mark_dirty()
    
    def _handle_ai_command(self, args):
        """Handle AI ask command"""
        if not args:
            self.add_output("Usage: ask <question>")
            return
        
        question = " ".join(args)
        self.add_output(f"[AI] Processing: {question}")
        self.context.add_message("user", question)
        
        self.show_loading(True)
        
        asyncio.create_task(self._call_ai(question))
    
    async def _call_ai(self, question: str):
        """Call AI API"""
        try:
            from services.api import create_client
            
            client = create_client()
            
            tools_schema = self._tool_executor.get_tools_schema()
            
            async def on_tool(tool_use):
                result = await self._tool_executor.execute_tool(
                    name=tool_use.name,
                    tool_use_id=tool_use.id,
                    input_data=tool_use.input,
                    context=self.context
                )
                return result
            
            response = await client.send_message(
                system_prompt="You are a helpful AI assistant.",
                tools=tools_schema,
                on_tool_use=on_tool
            )
            
            self.context.add_message("assistant", response.message.content)
            self.add_output(f"[AI] {response.message.content}")
            
        except Exception as e:
            self.add_output(f"[AI Error] {str(e)}")
        
        finally:
            self.show_loading(False)
            self.mark_dirty()
    
    def _handle_tool_command(self, args):
        """Handle direct tool calls"""
        if not args:
            self.add_output("Usage: tool <name> [args...]")
            return
        
        tool_name = args[0]
        tool_args = args[1:]
        
        import json
        input_dict = {}
        for arg in tool_args:
            if '=' in arg:
                key, value = arg.split('=', 1)
                input_dict[key] = value
        
        result = asyncio.run(
            self._tool_executor.execute_tool(
                name=tool_name,
                tool_use_id="cli",
                input_data=input_dict,
                context=self.context
            )
        )
        
        if result.status.value == "success":
            self.add_output(f"[Tool] {result.content}")
        else:
            self.add_output(f"[Tool Error] {result.error}")
    
    def _list_tools(self):
        """List available tools"""
        tools = self._tool_executor.list_tools()
        self.add_output("Available tools:")
        for tool in tools:
            self.add_output(f"  - {tool}")
    
    def _handle_completion(self, partial: str):
        """Handle tab completion"""
        registry = get_commands()
        
        if partial.startswith('/'):
            partial = partial[1:]
        
        cmds = registry.search(partial)
        if cmds:
            suggestions = ", ".join(c.name for c in cmds[:8])
            self.add_output(f"Suggestions: {suggestions}")
    
    def _handle_mode_change(self, mode: str):
        """Handle mode change"""
        if mode == "vim":
            self.set_mode("insert")
        elif mode == "normal":
            self.set_mode("normal")
    
    def show_welcome(self):
        """Show welcome message"""
        welcome = [
            "=" * 60,
            "  Galaxy Destroyer v0.1.0",
            "  AI-Powered Terminal Assistant",
            "=" * 60,
            "",
            "Commands:",
            "  help          - Show help",
            "  ask <prompt>  - Ask AI",
            "  tool <name>   - Run a tool",
            "  tools         - List tools",
            "  status        - Show status",
            "  git           - Git commands",
            "",
            "Type 'help' for more commands.",
            ""
        ]
        for line in welcome:
            self.add_output(line)


def main():
    """Main entry point"""
    cli = GalaxyCLI()
    cli.show_welcome()
    cli.run()


if __name__ == "__main__":
    main()