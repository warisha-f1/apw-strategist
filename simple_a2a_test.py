from agents.a2a_protocol import A2AMessage
from pydantic import ValidationError

def run_a2a_test():
    print("\n--- Running Isolated A2A Protocol Test (Agent Evaluation) ---")
    
    # 1. Test a successful message creation
    try:
        valid_message = A2AMessage(
            sender_agent="LoopAgent",
            target_intent="OPTIMIZATION_SAVE",
            user_input="Find best pit lap.",
            payload={"best_lap": 23, "delta": 3.45},
            status="SUCCESS"
        )
        print("A2A Test 1: Valid message creation successful.")
        print(f"   Payload verified: {valid_message.payload}")

    except Exception as e:
        print(f"A2A Test 1 FAILED: {e}")
        
    # 2. Test failure case (Validation Error - 'status' is missing)
    try:
        # This MUST fail because 'status' is a required field in the A2AMessage class
        A2AMessage(
            sender_agent="Dispatcher",
            target_intent="DELETE_ENTRY",
            user_input="delete 10",
            payload={"strategy_id": 10}
        )
        print("A2A Test 2 FAILED: Missing required field did NOT raise an error.")
    
    except ValidationError:
        # This is the expected, successful outcome for Test 2
        print("A2A Test 2: Validation Error successfully caught (Proves Pydantic works).")
    
    print("---------------------------------------------------------------")

if __name__ == "__main__":
    run_a2a_test()