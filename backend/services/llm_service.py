from groq import Groq
import json
from typing import Dict, Any, List, Optional
from backend.config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.client = Groq(api_key=Config.GROQ_API_KEY)
        self.tools = self._define_tools()
    
    def _define_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "control_spotify",
                    "description": "Control Spotify playback and search for music",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": ["play", "pause", "skip", "previous", "search", "current"],
                                "description": "The action to perform"
                            },
                            "query": {
                                "type": "string",
                                "description": "Search query for songs, artists, or playlists"
                            },
                            "type": {
                                "type": "string",
                                "enum": ["track", "artist", "playlist", "album"],
                                "description": "Type of content to search for"
                            }
                        },
                        "required": ["action"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "manage_calendar",
                    "description": "Create, update, delete or query calendar events",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": ["create", "update", "delete", "query", "list"],
                                "description": "The calendar action to perform"
                            },
                            "event_data": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                                    "time": {"type": "string", "description": "Time in HH:MM format"},
                                    "duration": {"type": "integer", "description": "Duration in minutes"},
                                    "description": {"type": "string"},
                                    "attendees": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    }
                                }
                            },
                            "query_params": {
                                "type": "object",
                                "properties": {
                                    "date": {"type": "string"},
                                    "days_ahead": {"type": "integer"}
                                }
                            }
                        },
                        "required": ["action"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "general_query",
                    "description": "Answer general questions that don't require specific tools",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "response": {
                                "type": "string",
                                "description": "The response to the user's question"
                            }
                        },
                        "required": ["response"]
                    }
                }
            }
        ]
    
    async def process_command(self, 
                            user_input: str, 
                            context: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Process user command and return structured response"""
        
        messages = [
            {
                "role": "system",
                "content": """You are a helpful voice assistant with access to Spotify and Calendar.
                Be concise in responses since this is voice interaction.
                Current date/time context will be provided when needed.
                Always use the appropriate tool for user requests."""
            }
        ]
        
        # Add context if provided
        if context:
            messages.extend(context)
        
        messages.append({"role": "user", "content": user_input})
        
        try:
            response = self.client.chat.completions.create(
                model=Config.MODEL_NAME,
                messages=messages,
                tools=self.tools,
                tool_choice="auto",
                temperature=Config.TEMPERATURE,
                max_tokens=Config.MAX_TOKENS
            )
            
            message = response.choices[0].message
            
            # Check if tool was called
            if message.tool_calls:
                tool_call = message.tool_calls[0]
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                logger.info(f"Tool called: {function_name}")
                logger.info(f"Arguments: {function_args}")
                
                return {
                    "type": "tool_call",
                    "tool": function_name,
                    "arguments": function_args,
                    "raw_response": message.content
                }
            else:
                # Direct response without tool
                return {
                    "type": "direct_response",
                    "content": message.content
                }
                
        except Exception as e:
            logger.error(f"LLM processing error: {str(e)}")
            return {
                "type": "error",
                "error": str(e)
            }
