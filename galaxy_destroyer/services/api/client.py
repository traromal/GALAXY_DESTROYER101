"""API service for AI communication - supports OpenCode.ai, Ollama, OpenAI, Anthropic"""

import os
import json
import asyncio
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from enum import Enum
import time


class Backend(Enum):
    OPENCODE = "opencode"
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class MessageRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


@dataclass
class Message:
    role: MessageRole
    content: str
    tool_calls: List[Dict] = field(default_factory=list)
    tool_call_id: Optional[str] = None
    name: Optional[str] = None


@dataclass 
class ToolUse:
    id: str
    name: str
    input: Dict[str, Any]


@dataclass
class Response:
    message: Message
    stop_reason: str
    usage: Dict[str, int]


class ApiClient:
    """AI API client with multi-backend support"""
    
    BACKEND_URLS = {
        Backend.OPENCODE: "https://opencode.ai/api",
        Backend.OLLAMA: "http://localhost:11434",
        Backend.OPENAI: "https://api.openai.com/v1",
        Backend.ANTHROPIC: "https://api.anthropic.com",
    }
    
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        backend: Backend = Backend.OPENCODE,
        model: Optional[str] = None
    ):
        self.api_key = api_key or os.environ.get("OPENCODE_API_KEY", "")
        self.backend = backend
        self.base_url = self.BACKEND_URLS[backend]
        
        self.default_models = {
            Backend.OPENCODE: "qwen2.5-coder",
            Backend.OLLAMA: "llama3",
            Backend.OPENAI: "gpt-4",
            Backend.ANTHROPIC: "claude-opus-4-5-20251114",
        }
        
        self.model = model or os.environ.get("MODEL", self.default_models[backend])
        self.max_tokens = 4096
        self._message_history: List[Message] = []
    
    def add_message(self, role: MessageRole, content: str, **kwargs):
        msg = Message(role=role, content=content, **kwargs)
        self._message_history.append(msg)
        return msg
    
    def add_tool_result(self, tool_call_id: str, content: str):
        msg = Message(
            role=MessageRole.USER,
            content=content,
            tool_call_id=tool_call_id
        )
        self._message_history.append(msg)
        return msg
    
    async def send_message(
        self,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[Dict] = None,
        max_tokens: Optional[int] = None,
        on_tool_use: Optional[Callable[[ToolUse], Any]] = None,
    ) -> Response:
        """Send a message to the AI API"""
        
        if self.backend == Backend.ANTHROPIC:
            return await self._send_anthropic(system_prompt, tools, tool_choice, max_tokens, on_tool_use)
        else:
            return await self._send_openai_compatible(system_prompt, tools, max_tokens, on_tool_use)
    
    async def _send_openai_compatible(
        self,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict]] = None,
        max_tokens: Optional[int] = None,
        on_tool_use: Optional[Callable[[ToolUse], Any]] = None,
    ) -> Response:
        """Send to OpenAI-compatible API (OpenCode, Ollama, OpenAI)"""
        
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        for msg in self._message_history:
            msg_dict = {"role": msg.role.value, "content": msg.content}
            if msg.name:
                msg_dict["name"] = msg.name
            messages.append(msg_dict)
        
        body = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
        }
        
        if max_tokens:
            body["max_tokens"] = max_tokens
        
        if tools:
            converted_tools = self._convert_tools(tools)
            if converted_tools:
                body["tools"] = converted_tools
                body["tool_choice"] = "auto"
        
        import urllib.request
        import urllib.error
        
        if self.backend == Backend.OLLAMA:
            url = f"{self.base_url}/api/chat"
        else:
            url = f"{self.base_url}/chat/completions"
        
        headers = {"Content-Type": "application/json"}
        if self.backend != Backend.OLLAMA and self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                data = json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else ""
            raise Exception(f"API error: {e.code} - {error_body}")
        
        choice = data["choices"][0]
        msg_data = choice["message"]
        
        assistant_message = Message(
            role=MessageRole.ASSISTANT,
            content=msg_data.get("content", "")
        )
        
        tool_uses = []
        if msg_data.get("tool_calls"):
            for tc in msg_data["tool_calls"]:
                tool_use = ToolUse(
                    id=tc.get("id", f"call_{len(tool_uses)}"),
                    name=tc["function"]["name"],
                    input=json.loads(tc["function"]["arguments"])
                )
                tool_uses.append(tool_use)
                if on_tool_use:
                    result = on_tool_use(tool_use)
                    if result is not None:
                        self.add_tool_result(tool_use.id, str(result))
        
        if tool_uses:
            assistant_message.tool_calls = [
                {"id": t.id, "name": t.name, "input": t.input}
                for t in tool_uses
            ]
        
        response = Response(
            message=assistant_message,
            stop_reason=choice.get("finish_reason", "stop"),
            usage=data.get("usage", {})
        )
        
        if tool_uses:
            self._message_history.append(assistant_message)
        
        return response
    
    def _convert_tools(self, tools: List[Dict]) -> List[Dict]:
        """Convert Claude tools to OpenAI format"""
        converted = []
        for tool in tools:
            if "description" in tool and "input" in tool:
                converted.append({
                    "type": "function",
                    "function": {
                        "name": tool.get("name", ""),
                        "description": tool["description"],
                        "parameters": tool["input"]
                    }
                })
        return converted
    
    async def _send_anthropic(
        self,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[Dict] = None,
        max_tokens: Optional[int] = None,
        on_tool_use: Optional[Callable[[ToolUse], Any]] = None,
    ) -> Response:
        """Send to Anthropic API"""
        
        if not self.api_key:
            raise ValueError("API key not set")
        
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        messages = []
        for msg in self._message_history:
            msg_dict = {"role": msg.role.value, "content": msg.content}
            if msg.tool_calls:
                msg_dict["tool_calls"] = msg.tool_calls
            if msg.tool_call_id:
                msg_dict["tool_call_id"] = msg.tool_call_id
            if msg.name:
                msg_dict["name"] = msg.name
            messages.append(msg_dict)
        
        body = {
            "model": self.model,
            "max_tokens": max_tokens or self.max_tokens,
            "messages": messages,
        }
        
        if system_prompt:
            body["system"] = system_prompt
        
        if tools:
            body["tools"] = tools
        
        if tool_choice:
            body["tool_choice"] = tool_choice
        
        import urllib.request
        import urllib.error
        
        req = urllib.request.Request(
            f"{self.base_url}/v1/messages",
            data=json.dumps(body).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                data = json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else ""
            raise Exception(f"API error: {e.code} - {error_body}")
        
        message_data = data["content"]
        
        assistant_message = Message(
            role=MessageRole.ASSISTANT,
            content=""
        )
        
        tool_uses = []
        for block in message_data:
            if block["type"] == "text":
                assistant_message.content = block["text"]
            elif block["type"] == "tool_use":
                tool_use = ToolUse(
                    id=block["id"],
                    name=block["name"],
                    input=block["input"]
                )
                tool_uses.append(tool_use)
                if on_tool_use:
                    result = on_tool_use(tool_use)
                    if result is not None:
                        self.add_tool_result(tool_use.id, str(result))
        
        if tool_uses:
            assistant_message.tool_calls = [
                {"id": t.id, "name": t.name, "input": t.input}
                for t in tool_uses
            ]
        
        response = Response(
            message=assistant_message,
            stop_reason=data.get("stop_reason", "end_turn"),
            usage=data.get("usage", {})
        )
        
        if response.stop_reason == "tool_use":
            self._message_history.append(assistant_message)
        
        return response
    
    def clear_history(self):
        """Clear message history"""
        self._message_history.clear()
    
    def get_history(self) -> List[Message]:
        """Get message history"""
        return self._message_history.copy()
    
    def set_model(self, model: str):
        """Set the model to use"""
        self.model = model
    
    def get_model(self) -> str:
        """Get current model"""
        return self.model
    
    def set_backend(self, backend: Backend):
        """Set the backend"""
        self.backend = backend
        self.base_url = self.BACKEND_URLS[backend]
        self.model = self.default_models[backend]


def create_client(
    api_key: Optional[str] = None, 
    backend: Backend = Backend.OPENCODE,
    model: Optional[str] = None
) -> ApiClient:
    """Create an API client"""
    return ApiClient(api_key=api_key, backend=backend, model=model)