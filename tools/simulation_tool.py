def calculate_race_delta(strategy_name: str, pit_lap: int, tire_type: str) -> float:
    """
    Custom Tool: Simulates a potential pit stop strategy and calculates the time 
    difference (delta) in seconds versus a baseline strategy.

    This function represents the required 'Custom Tool' feature.
    
    Args:
        strategy_name (str): A name describing the strategy (e.g., 'Undercut', 'Overcut').
        pit_lap (int): The lap on which the pit stop is executed.
        tire_type (str): The compound used (e.g., 'Hard', 'Medium').

    Returns:
        float: Expected time gain in seconds. Positive is good, negative is a loss.
    """
    
    # --- Simplified Logic for Strategy Calculation ---
    
    base_gain = 0.0
    
    if "Aggressive" in strategy_name:
        base_gain += 1.5
    
    if pit_lap < 25 and tire_type == "Medium":
        # Aggressive undercut with soft tires provides a boost
        base_gain += 3.0
    elif pit_lap > 40 and tire_type == "Hard":
        # Long stint (overcut) provides a smaller but reliable gain
        base_gain += 1.0
    
    # Add a factor based on the lap number (later laps are riskier but can yield more gain)
    lap_factor = pit_lap / 50 
    
    return round(base_gain + lap_factor, 2)


if __name__ == '__main__':
    # Test cases:
    print(f"Aggressive Undercut (Lap 22, Medium): {calculate_race_delta('Undercut_Aggressive', 22, 'Medium')}s gain")
    print(f"Standard Strategy (Lap 35, Hard): {calculate_race_delta('Standard_Stint', 35, 'Hard')}s gain")
    print(f"Bad Strategy (Lap 55, Medium): {calculate_race_delta('Late_Stop_Soft', 55, 'Medium')}s gain")
