# agents/intent_agent.py

from google import genai
from pydantic import BaseModel, Field
import json
from typing import Optional
from enum import Enum

# --- 1. Structured Output Schema (Pydantic) ---

class IntentType(str, Enum): 
    """Defines the restricted intent choices for Pydantic."""
    NEW_STRATEGY = "NEW_STRATEGY"
    REVIEW_HISTORY = "REVIEW_HISTORY"
    DELETE_ENTRY = "DELETE_ENTRY"
    OPTIMIZE_STRATEGY = "OPTIMIZE_STRATEGY" # <--- NEW INTENT ADDED
    EXIT = "EXIT"
    OTHER = "OTHER"

class IntentClassifier(BaseModel):
    """The final structured schema for the LLM output."""
    intent: IntentType = Field(description="The primary action the user is asking for.")
    argument: Optional[str] = Field(default=None, description="The specific argument needed for the action (e.g., the ID number for deletion).")


# --- 2. Classification Agent Function ---

def classify_intent(client: genai.Client, user_input: str) -> dict:
    """Uses the LLM to classify the user's input into a structured IntentClassifier model."""
    system_instruction = (
        "You are an expert User Intent Classifier for the F1 Strategist application. "
        "Analyze the user's input and classify its purpose using the provided JSON schema. "
        "If the user asks a question about pit strategy, racing, or tires, the intent is 'NEW_STRATEGY'. "
        "If the input matches a command like 'review', 'delete', 'optimize', or 'exit', use the corresponding intent."
    )
    
    prompt = f"Classify the following user input: '{user_input}'"

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={
                "system_instruction": system_instruction,
                "response_mime_type": "application/json",
                "response_schema": IntentClassifier,
            },
        )
        return json.loads(response.text)

    except Exception as e:
        return {"intent": "OTHER", "argument": None}