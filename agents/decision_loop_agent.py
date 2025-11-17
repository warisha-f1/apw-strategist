# agents/decision_loop_agent.py

from typing import Dict, Any
from google import genai
from tools.simulation_tool import calculate_race_delta

def run_optimization_loop(client: genai.Client, topic: str) -> Dict[str, Any]:
    """
    Implements the Loop Agent logic: iterates through a range of pit laps, 
    calls the simulation tool, and identifies the best strategy.
    """
    
    # 1. Configuration for the Loop (Hardcoded for Capstone Demo)
    START_LAP = 15
    END_LAP = 30
    TIRE_TYPE = "Medium" 
    STRATEGY_NAME = "Optimization Check"
    
    best_lap = 0
    max_delta = -float('inf')
    
    print("\n🔄 Loop Agent: Starting Optimization...")
    print(f"   Searching for optimal pit lap between Lap {START_LAP} and Lap {END_LAP} using {TIRE_TYPE} tires.")
    
    # 2. The Core Loop (Fulfills the "Loop Agents" Requirement)
    for lap in range(START_LAP, END_LAP + 1):
        
        # A. Call the Custom Tool
        try:
            current_delta = calculate_race_delta(
                strategy_name=STRATEGY_NAME,
                pit_lap=lap,
                tire_type=TIRE_TYPE
            )
        except Exception as e:
            print(f"   ⚠️ Loop failed to execute simulation for Lap {lap}. Error: {e}")
            continue

        # B. Decision/Evaluation (Finding the Maximum Gain)
        if current_delta > max_delta:
            max_delta = current_delta
            best_lap = lap
            print(f"   -> Lap {lap}: Delta = {current_delta:.2f}s. New MAX found!")
        else:
            print(f"   -> Lap {lap}: Delta = {current_delta:.2f}s.")
            
    print(f"\n✨ Loop Agent Complete: Optimal Pit Lap Found: {best_lap} (Gain: {max_delta:.2f}s)")

    # 3. Final LLM Reasoning
    prompt = (
        f"Based on the simulation loop you just ran, the calculated optimal pit lap "
        f"for a standard {TIRE_TYPE} stint is Lap {best_lap}, yielding a time gain of "
        f"{max_delta:.2f} seconds. Explain this result to the user, highlighting why "
        f"that specific lap is better than the others."
    )
    
   # agents/decision_loop_agent.py (From line 55 onwards)

    print(f"\n✨ Loop Agent Complete: Optimal Pit Lap Found: {best_lap} (Gain: {max_delta:.2f}s)")

    # 3. Final LLM Reasoning (Telling the user the result of the optimization)
    
    llm_advice = f"Optimal Lap Found: Lap {best_lap} with a time gain of {max_delta:.2f} seconds. The system recommends pitting on this lap."
    
    try:
        prompt = (
            f"Based on the simulation loop you just ran, the calculated optimal pit lap "
            f"for a standard {TIRE_TYPE} stint is Lap {best_lap}, yielding a time gain of "
            f"{max_delta:.2f} seconds. Explain this result to the user, highlighting why "
            f"that specific lap is better than the others."
        )
        
        # This is the line that was crashing due to 503
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        llm_advice = response.text
        
    except Exception as e:
        # If the server is down (503), print a warning but don't crash
        print(f"\n⚠️ API Warning: Could not get final LLM summary due to server error ({e}). Returning raw result.")
        
    # 4. Return the result in a structured format for saving to memory
    return {
        'llm_advice': llm_advice, # Uses the LLM advice OR the safe default text
        'strategy_name': STRATEGY_NAME,
        'pit_lap': best_lap,
        'tire_type': TIRE_TYPE,
        'calculated_delta': max_delta
    }
