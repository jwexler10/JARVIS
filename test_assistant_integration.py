# test_assistant_integration.py
from jarvis import process_command

def test_assistant_command():
    """Test Google Assistant integration through Jarvis"""
    
    print("Testing Google Assistant integration through Jarvis...")
    
    # Test a simple Assistant command
    command = "ask Google Assistant what's the weather in Philadelphia"
    result, should_exit = process_command(command, [], text_mode=True, speaker='Jason')
    
    print(f"\nCommand: {command}")
    print(f"Result: {result}")
    print(f"Should exit: {should_exit}")

if __name__ == "__main__":
    test_assistant_command()
