def calculate_race_delta(strategy_name: str, pit_lap: int, tire_type: str) -> float:
    """
    Custom Tool: Simulates a potential pit stop strategy and calculates the time 
    difference (delta) in seconds versus a baseline strategy.
    
    Args:
        strategy_name (str): A name describing the strategy (e.g., 'Undercut', 'Overcut').
        pit_lap (int): The lap on which the pit stop is executed.
        tire_type (str): The compound used (e.g., 'Hard', 'Medium', 'Soft').

    Returns:
        float: Expected time gain in seconds. Positive is good, negative is a loss.
    """
    
    base_gain = 0.0
    
    if "Aggressive" in strategy_name:
        base_gain += 1.5
    
    if pit_lap < 25 and tire_type == "Medium":
        base_gain += 3.0
    elif pit_lap > 40 and tire_type == "Hard":
        base_gain += 1.0
    
    lap_factor = pit_lap / 50 
    
    return round(base_gain + lap_factor, 2)