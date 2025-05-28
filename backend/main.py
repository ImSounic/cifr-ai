from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

from backend.services.llm_service import LLMService
from backend.services.spotify_service import get_spotify_service

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="AI Voice Assistant")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
llm_service = LLMService()

# Function to execute tool calls
async def execute_tool_call(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Execute the actual tool call based on LLM response"""
    
    if tool_name == "control_spotify":
        spotify = get_spotify_service()
        action = arguments.get("action")
        
        if action in ["play", "pause", "skip", "previous"]:
            return spotify.control_playback(action)
        elif action == "search":
            query = arguments.get("query", "")
            search_type = arguments.get("type", "track")
            return spotify.search_and_play(query, search_type)
        elif action == "current":
            return spotify.get_current_track()
    
    elif tool_name == "manage_calendar":
        # We'll implement this later
        return {"status": "info", "message": "Calendar integration coming soon!"}
    
    elif tool_name == "general_query":
        return {"status": "success", "message": arguments.get("response", "")}
    
    return {"status": "error", "message": f"Unknown tool: {tool_name}"}

# Request models
class CommandRequest(BaseModel):
    text: str
    context: Optional[List[Dict]] = None

class CommandResponse(BaseModel):
    type: str
    tool: Optional[str] = None
    arguments: Optional[Dict] = None
    content: Optional[str] = None
    error: Optional[str] = None
    execution_result: Optional[Dict] = None  # Add this for tool execution results

@app.get("/")
async def root():
    return {"message": "AI Voice Assistant API", "status": "running"}

@app.post("/process", response_model=CommandResponse)
async def process_command(request: CommandRequest):
    """Process a voice command through the LLM"""
    logger.info(f"Processing command: {request.text}")
    
    # Get LLM response
    result = await llm_service.process_command(
        request.text,
        request.context
    )
    
    # If it's a tool call, execute it
    if result["type"] == "tool_call" and result.get("tool"):
        execution_result = await execute_tool_call(
            result["tool"], 
            result.get("arguments", {})
        )
        result["execution_result"] = execution_result
    
    return CommandResponse(**result)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time communication"""
    await websocket.accept()
    logger.info("WebSocket connection established")
    
    try:
        while True:
            # Receive text command
            data = await websocket.receive_text()
            logger.info(f"Received via WebSocket: {data}")
            
            # Process command
            result = await llm_service.process_command(data)
            
            # Execute tool if needed
            if result["type"] == "tool_call" and result.get("tool"):
                execution_result = await execute_tool_call(
                    result["tool"], 
                    result.get("arguments", {})
                )
                result["execution_result"] = execution_result
            
            # Send response
            await websocket.send_json(result)
            
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        logger.info("WebSocket connection closed")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "llm": "connected",
            "spotify": "checking...",
            "calendar": "not_configured"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)