from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any, Optional

class A2AMessage(BaseModel):
    """
    Standardized message structure for Agent-to-Agent communication.
    This serves as the A2A Protocol for the F1 Strategist system.
    """
    
    # --- Metadata (A2A Headers) ---
    sender_agent: str = Field(description="The name of the agent sending the message (e.g., IntentAgent, LoopAgent).")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="ISO timestamp of message creation.")
    target_intent: str = Field(description="The intent or action this message triggers (e.g., DELETE_ENTRY, NEW_STRATEGY).")
    
    # --- Payload ---
    user_input: str = Field(description="The raw user input associated with this action.")
    payload: Optional[Any] = Field(default=None, description="The core data payload (e.g., Strategy details, optimization result).")
    status: str = Field(default="SUCCESS", description="The status of the originating agent's operation (e.g., SUCCESS, FAILURE).")