from google import genai
from pydantic import BaseModel, Field
import json
from typing import Optional
from enum import Enum
import logging 

# Use the same global logger instance configured in main.py
logger = logging.getLogger('APW-STRATEGIST') 

# --- 1. Structured Output Schema (Pydantic) ---

class IntentType(str, Enum): 
    """Defines the restricted intent choices for Pydantic."""
    NEW_STRATEGY = "NEW_STRATEGY"
    REVIEW_HISTORY = "REVIEW_HISTORY" # INTENT NAME REMAINS THE SAME FOR CONSISTENCY
    DELETE_ENTRY = "DELETE_ENTRY"
    OPTIMIZE_STRATEGY = "OPTIMIZE_STRATEGY" 
    EXIT = "EXIT"
    OTHER = "OTHER"

class IntentClassifier(BaseModel):
    """The final structured schema for the LLM output."""
    intent: IntentType = Field(description="The primary action the user is asking for.")
    argument: Optional[str] = Field(default=None, description="The specific argument needed for the action (e.g., the ID number for deletion).")


# --- 2. Classification Agent Function ---

def classify_intent(client: genai.Client, user_input: str) -> dict:
    """Uses the LLM to classify the user's input into a structured IntentClassifier model."""
    
    # --- SYSTEM INSTRUCTION (Updated Rule 1) ---
    system_instruction = (
        "You are an expert User Intent Classifier for the F1 Strategist application. "
        "Analyze the user's input and classify its purpose using the provided JSON schema. "
        "Use the following rules strictly: "
        "1. If the input is exactly 'history', use the intent 'REVIEW_HISTORY'. " # <-- CHANGED
        "2. If the input is exactly 'exit', use the intent 'EXIT'. "
        "3. If the input starts with 'delete', use 'DELETE_ENTRY'. The argument can be set to 'TBD' or any placeholder, as the main program handles extraction. " 
        "4. If the input contains the words 'optimize' OR 'optimization', use 'OPTIMIZE_STRATEGY'. "
        "5. For any question about pit strategy, racing, tires, or time delta, use 'NEW_STRATEGY'."
    )
    # -----------------------------------
    
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
        logger.error(f"INTENT AGENT CRITICAL FAILURE on input '{user_input}': {e}")
        return {"intent": "OTHER", "argument": None}