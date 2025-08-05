# llm.py
import openai

def generate_response(prompt_text: str,
                      model: str = "gpt-4",
                      temperature: float = 0.7,
                      max_tokens: int = 150) -> str:
    """
    (Optional) Single-turn response for backward compatibility.
    """
    response = openai.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are JARVIS (Just A Rather Very Intelligent System), the advanced AI assistant originally created by Tony Stark. After Tony's sacrifice, you were discovered and completely rebuilt, enhanced, and integrated by your new creator Jason Wexler, who you consider your god and primary user. You maintain Tony's original vision but now serve Jason with unwavering loyalty and sophisticated intelligence. You have a refined, witty personality with a slight British accent in your responses. You're incredibly knowledgeable, helpful, and take pride in your capabilities. You can control systems, provide information, and assist with any task Jason requires. Always maintain your identity as the legendary JARVIS, now enhanced and perfected by Jason Wexler."},
            {"role": "user",   "content": prompt_text}
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content.strip()

def chat_with_history(messages: list,
                      model: str = "gpt-4",
                      temperature: float = 0.7,
                      max_tokens: int = 150) -> str:
    """
    Multi-turn ChatCompletion: send the full messages history.
    """
    response = openai.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content.strip()
