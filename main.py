import os
import json
from dotenv import load_dotenv
from google import genai
from typing import Optional
import logging 
from datetime import datetime

# Custom Project Imports
from tools.simulation_tool import calculate_race_delta 
from database import initialize_db, save_strategy_to_db, get_all_strategies_from_db, delete_strategy_by_id, get_all_strategies_from_db # Re-import get_all_strategies_from_db for context
from agents.intent_agent import classify_intent 
from agents.decision_loop_agent import run_optimization_loop
from agents.a2a_protocol import A2AMessage 

# Configure a robust logger that outputs to a file (for tracing) and the console
logging.basicConfig(
    level=logging.INFO, # Sets the minimum level to capture
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("agent_trace.log", mode='w'), # Logs to a file
        logging.StreamHandler() # Logs to the console
    ]
)
# Create a logger instance for the main application flow
logger = logging.getLogger('APW-STRATEGIST')


# --- 1. Memory Agent Helper Functions ---

def display_history():
    """Retrieves and prints all strategies from the database."""
    strategies = get_all_strategies_from_db()
    
    # We will still print the history, but the surrounding actions are logged.
    print("\n--- Strategy History (Long Term Memory) ---")
    if not strategies:
        print("No strategies saved yet.")
        return
        
    print("| ID | Date/Time         | Delta (s) | Topic")
    print("|----|-------------------|-----------|----------------------------------------------------")
    
    for s in strategies:
        topic_summary = s['topic'] 
        print(f"| {s['id']:<2} | {s['date'][0:16]:<17} | {s['delta']:<9.2f} | {topic_summary}")
        
    print("\nUse 'delete <ID>' to remove an entry.")


def get_context_compaction_data(limit: int = 3) -> str:
    """
    Retrieves the most recent strategies from memory and compacts them into
    a single string to be inserted into the LLM's context.
    """
    strategies = get_all_strategies_from_db()
    if not strategies:
        return "No prior strategies or optimizations are available in memory."
    
    # Sort by ID (newest first) and limit the list
    recent_strategies = sorted(strategies, key=lambda s: s['id'], reverse=True)[:limit]
    
    context_str = "Prior Race Strategy/Optimization History:\n---\n"
    
    for s in recent_strategies:
        delta = s['delta']
        topic = s['topic']
        
        # Format the context string for relevance
        if 'optimization' in topic.lower():
            advice = s.get('llm_advice', 'Optimization advice provided.')
            # Extract the first sentence of the advice for compaction
            summary = advice.split('.')[0] + '.' if advice and '.' in advice else advice
            context_str += f"- ID {s['id']}: OPTIMIZATION RUN (Gain: {delta:.2f}s). Result: {summary}\n"
        else:
            context_str += f"- ID {s['id']}: STANDARD STRATEGY (Delta: {delta:.2f}s). Topic: {topic[:50]}...\n"
            
    context_str += "---\nUse this information if the user's current query relates to previous results."
    return context_str


# --- 2. Simulation Agent Function (Core LLM Logic + Tool Use) ---

def run_f1_strategist(client: genai.Client, prompt: str):
    """
    Runs the F1 strategist agent, using the Custom Tool and saving the result.
    This acts as the 'Simulation Agent' in the sequential flow.
    """
    logger.info("ACTION: Running Sequential Agent (Simulation Agent).")
    
    system_instruction = (
        "You are an expert Formula 1 Race Strategist. Your goal is to analyze the "
        "user's request and determine the optimal pit stop strategy. "
        "You MUST use the available function `calculate_race_delta` whenever you need to quantify "
        "the time gain or loss of a potential pit stop strategy (Undercut, Overcut, etc.) "
        "before providing your final advice. "
        "The arguments for the tool must be precise and based on the user's prompt."
    )

    # --- CONTEXT ENGINEERING: Compacting Long-Term Memory ---
    compaction_context = get_context_compaction_data(limit=3)
    logger.info(f"CONTEXT: Compaction successful. Using context for 3 recent entries.")
    
    full_prompt = (
        f"{compaction_context}\n\n"
        f"USER'S CURRENT REQUEST: {prompt}"
    )
    # ---------------------------------------------------------

    # First turn: Send the user's prompt to the model
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=full_prompt, # <-- USING full_prompt
        config={
            "system_instruction": system_instruction,
            "tools": [calculate_race_delta] 
        }
    )
    
    tool_output = None
    tool_args = None
    
    while response.function_calls:
        logger.info("AGENT FLOW: Simulation Agent decided to use the Custom Tool.")
        print("🤖 Simulation Agent: Decided to use the Custom Tool...")
        
        function_name = response.function_calls[0].name
        tool_args = dict(response.function_calls[0].args)
        
        if function_name == "calculate_race_delta":
            try:
                tool_output = calculate_race_delta(**tool_args)
                logger.info(f"TOOL CALL: Calling tool with arguments: {tool_args}")
                print(f"   -> Calling tool with: {tool_args}")
                print(f"   -> Simulation result: {tool_output:.2f} seconds gain/loss.")
            except TypeError as e:
                 logger.error(f"TOOL ERROR: Missing or invalid argument in tool call: {e}")
                 print(f"⚠️ Error executing tool: Missing or invalid argument in tool call: {e}")
                 tool_output = None 
                 break
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[], 
                config={
                    "system_instruction": system_instruction,
                    "tools": [calculate_race_delta]
                },
                history=[
                    response.candidates[0].content,
                    {"role": "tool", "parts": [{"functionResponse": {"name": function_name, "response": {"calculated_delta": tool_output}}}]}
                ]
            )
        else:
            raise NotImplementedError(f"Unknown tool requested: {function_name}")
            
    print("\n--- Final Advice (LLM Response) ---")
    print(response.text)
    
    if tool_output is not None:
        strategy_details = {
            'calculated_delta': tool_output,
            'strategy_name': tool_args.get('strategy_name', 'N/A'),
            'pit_lap': tool_args.get('pit_lap', 0),
            'tire_type': tool_args.get('tire_type', 'N/A')
        }
        
        # --- A2A Protocol Implementation for Memory Save ---
        message = A2AMessage(
            sender_agent="SimulationAgent",
            target_intent="NEW_STRATEGY_SAVE",
            user_input=prompt,
            payload=strategy_details,
            status="SUCCESS"
        )
        last_id = save_strategy_to_db(message.user_input, message.payload)
        logger.info(f"A2A PROTOCOL: SimulationAgent sent message to Memory. ID: {last_id}, Delta: {tool_output:.2f}")
        print(f"\n💾 Memory Agent: Strategy saved to database with ID: {last_id}")
        # --- END A2A Protocol Implementation ---


# --- 3. Main Execution Block (The Dispatcher) ---

if __name__ == "__main__":
    load_dotenv() 
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        logger.critical("SETUP ERROR: GEMINI_API_KEY not found.")
        raise ValueError("GEMINI_API_KEY not found. Please check your .env file.")

    client = genai.Client(api_key=api_key)
    initialize_db() 
    
    logger.info("SYSTEM STARTUP: F1 Strategist System Initialized.")
    print("✅ F1 Strategist System Initialized! (Multi-Agent Running)")
    print("Commands: [exit], [history], [delete <ID>], or ask for a pit strategy.")
    
    while True:
        user_input = input("\n🏎️ Your Strategy Question: ").strip()
        
        if not user_input:
            continue

        # --- STEP 1: Intent Agent (Sequential Agent 1) ---
        print("\n🚦 Intent Agent: Classifying user request...")
        logger.info(f"INTENT: Classifying input: '{user_input}'")
        
        try:
            intent_result = classify_intent(client, user_input)
            
            intent = intent_result.get("intent", "OTHER").upper()
            argument = intent_result.get("argument") 
            
            print(f"   -> Classified Intent: {intent} (Arg: {argument})")
            logger.info(f"INTENT RESULT: Classified as {intent} (Arg: {argument})")
            
        except Exception as e:
            logger.error(f"INTENT AGENT CRITICAL FAILURE: {e}")
            print(f"⚠️ Critical Error during intent classification. Retrying input as NEW_STRATEGY. Error: {e}")
            intent = 'NEW_STRATEGY'
            argument = None


        # --- STEP 2: Dispatcher Logic ---
        
        if intent == 'EXIT':
            logger.info("ACTION: Exit command received. System shutting down.")
            print("Race finished. Goodbye! 👋")
            break
        
        # --- ROBUST HISTORY LOGIC ---
        elif intent == 'REVIEW_HISTORY' or user_input.lower() == 'history': 
            logger.info("ACTION: Reviewing strategy history.")
            display_history()
        # --- END ROBUST HISTORY LOGIC ---
            
        # --- ROBUST DELETE LOGIC ---
        elif intent == 'DELETE_ENTRY' or user_input.lower().startswith('delete '): 
            
            # Use the raw input to reliably extract the ID, bypassing the inconsistent LLM extraction
            parts = user_input.split()
            if len(parts) < 2 or not parts[1].isdigit():
                logger.warning("VALIDATION ERROR: Delete command missing valid ID.")
                print("❌ Usage Error: The delete command must be followed by a valid ID (e.g., delete 2).")
                display_history()
            else:
                try:
                    strategy_id = int(parts[1]) # Extracts the number directly from the raw input
                    
                    # --- A2A Protocol Implementation for Delete ---
                    message = A2AMessage(
                        sender_agent="Dispatcher",
                        target_intent="DELETE_ENTRY",
                        user_input=user_input,
                        payload={"strategy_id": strategy_id},
                        status="SUCCESS" 
                    )
                    rows = delete_strategy_by_id(message.payload['strategy_id'])
                    # --- END A2A Protocol Implementation ---
                    
                    if rows > 0:
                        logger.info(f"ACTION: Entry deleted from memory. ID: {strategy_id}")
                        print(f"🗑️ Entry with ID {strategy_id} successfully deleted from memory.")
                    else:
                        logger.warning(f"DATABASE ERROR: Attempted to delete non-existent ID: {strategy_id}")
                        print(f"⚠️ Strategy ID {strategy_id} not found.")
                except ValueError:
                    logger.error("VALIDATION ERROR: Delete ID was not a number.")
                    print("❌ Error: ID must be a number.")
        # --- END ROBUST DELETE LOGIC ---
        
        # --- ROBUST OPTIMIZE LOGIC ---
        elif intent == 'OPTIMIZE_STRATEGY' or 'optimize' in user_input.lower():
            
            logger.info("DISPATCH: Calling Loop Agent (Optimization).")
            print("\n🔄 Calling Loop Agent for Optimization...")
            optimization_result = run_optimization_loop(client, user_input)
            
            # Save optimization result and display LLM summary
            print("\n--- Final Advice (LLM Response) ---")
            print(optimization_result['llm_advice'])
            
            # --- A2A Protocol Implementation for Memory Save ---
            message = A2AMessage(
                sender_agent="LoopAgent",
                target_intent="OPTIMIZATION_SAVE",
                user_input=user_input,
                payload=optimization_result,
                status="SUCCESS"
            )
            last_id = save_strategy_to_db(message.user_input, message.payload)
            logger.info(f"A2A PROTOCOL: LoopAgent sent message to Memory. ID: {last_id}")
            print(f"\n💾 Memory Agent: Optimization saved to database with ID: {last_id}")
            # --- END A2A Protocol Implementation ---

        # --- END ROBUST OPTIMIZE LOGIC ---

        elif intent == 'NEW_STRATEGY':
            run_f1_strategist(client, user_input)
            
        else:
            logger.warning(f"DISPATCH ERROR: Input '{user_input}' classified as OTHER and not handled.")
            print("🤔 The system did not recognize the command. Please try again or ask a clear strategy question.")