import os
import json
from dotenv import load_dotenv
from google import genai
from typing import Optional

# Core Imports 
import os 
from dotenv import load_dotenv

# Custom Project Imports
from tools.simulation_tool import calculate_race_delta 
from database import initialize_db, save_strategy_to_db, get_all_strategies_from_db, delete_strategy_by_id 
from agents.intent_agent import classify_intent 
# --- NEW IMPORT ---
from agents.decision_loop_agent import run_optimization_loop
from datetime import datetime


# --- 1. Memory Agent Helper Functions ---

def display_history():
    """Retrieves and prints all strategies from the database."""
    strategies = get_all_strategies_from_db()
    
    print("\n--- Strategy History (Long Term Memory) ---")
    if not strategies:
        print("No strategies saved yet.")
        return
        
    print("| ID | Date/Time         | Delta (s) | Topic")
    print("|----|-------------------|-----------|----------------------------------------------------")
    
    for s in strategies:
        print(f"| {s['id']:<2} | {s['date']:<17} | {s['delta']:<9.2f} | {s['topic']}")
        
    print("\nUse 'delete <ID>' to remove an entry.")


# --- 2. Simulation Agent Function (Core LLM Logic + Tool Use) ---

def run_f1_strategist(client: genai.Client, prompt: str):
    """
    Runs the F1 strategist agent, using the Custom Tool and saving the result.
    This acts as the 'Simulation Agent' in the sequential flow.
    """
    
    system_instruction = (
        "You are an expert Formula 1 Race Strategist. Your goal is to analyze the "
        "user's request and determine the optimal pit stop strategy. "
        "You MUST use the available function `calculate_race_delta` whenever you need to quantify "
        "the time gain or loss of a potential pit stop strategy (Undercut, Overcut, etc.) "
        "before providing your final advice. "
        "The arguments for the tool must be precise and based on the user's prompt."
    )

    # First turn: Send the user's prompt to the model
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config={
            "system_instruction": system_instruction,
            "tools": [calculate_race_delta] 
        }
    )
    
    tool_output = None
    tool_args = None
    
    while response.function_calls:
        print("🤖 Simulation Agent: Decided to use the Custom Tool...")
        
        function_name = response.function_calls[0].name
        tool_args = dict(response.function_calls[0].args)
        
        if function_name == "calculate_race_delta":
            try:
                tool_output = calculate_race_delta(**tool_args)
                print(f"   -> Calling tool with: {tool_args}")
                print(f"   -> Simulation result: {tool_output:.2f} seconds gain/loss.")
            except TypeError as e:
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
        
        last_id = save_strategy_to_db(prompt, strategy_details)
        print(f"\n💾 Memory Agent: Strategy saved to database with ID: {last_id}")


# --- 3. Main Execution Block (The Dispatcher) ---

if __name__ == "__main__":
    load_dotenv() 
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("GEMINI_API_KEY not found. Please check your .env file.")

    client = genai.Client(api_key=api_key)
    initialize_db() 
    
    print("✅ F1 Strategist System Initialized! (Multi-Agent Running)")
    print("Commands: [exit], [review], [delete <ID>], or ask for a pit strategy.")
    
    while True:
        user_input = input("\n🏎️ Your Strategy Question: ").strip()
        
        if not user_input:
            continue

        # --- STEP 1: Intent Agent (Sequential Agent 1) ---
        print("\n🚦 Intent Agent: Classifying user request...")
        
        try:
            intent_result = classify_intent(client, user_input)
            
            intent = intent_result.get("intent", "OTHER").upper()
            argument = intent_result.get("argument")
            
            print(f"   -> Classified Intent: {intent} (Arg: {argument})")
            
        except Exception as e:
            print(f"⚠️ Critical Error during intent classification. Retrying input as NEW_STRATEGY. Error: {e}")
            intent = 'NEW_STRATEGY'
            argument = None


        # --- STEP 2: Dispatcher Logic ---
        
        if intent == 'EXIT':
            print("Race finished. Goodbye! 👋")
            break
        
        elif intent == 'REVIEW_HISTORY':
            display_history()
            
        elif intent == 'DELETE_ENTRY':
            if argument is None or not str(argument).isdigit():
                print("❌ Usage Error: The intent agent needs a valid ID (number) for deletion.")
                display_history()
            else:
                try:
                    strategy_id = int(argument)
                    rows = delete_strategy_by_id(strategy_id)
                    if rows > 0:
                        print(f"🗑️ Entry with ID {strategy_id} successfully deleted from memory.")
                    else:
                        print(f"⚠️ Strategy ID {strategy_id} not found.")
                except ValueError:
                    print("❌ Error: ID must be a number.")
        
        elif intent == 'OPTIMIZE_STRATEGY': # <--- NEW LOOP AGENT DISPATCH
            print("\n🔄 Calling Loop Agent for Optimization...")
            optimization_result = run_optimization_loop(client, user_input)
            
            # Save optimization result and display LLM summary
            print("\n--- Final Advice (LLM Response) ---")
            print(optimization_result['llm_advice'])
            
            # The entire result is saved as a single strategy entry
            last_id = save_strategy_to_db(user_input, optimization_result)
            print(f"\n💾 Memory Agent: Optimization saved to database with ID: {last_id}")

        elif intent == 'NEW_STRATEGY':
            run_f1_strategist(client, user_input)
            
        else:
            print("🤔 The system did not recognize the command. Please try again or ask a clear strategy question.")