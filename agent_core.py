# agent_core.py

import json
import os
from openai import OpenAI
from typing import Any, Dict

import tools
from tools import summarize_text, get_file_preview, run_file_workflow, create_directory, list_files_by_pattern, interpret_intent, open_website
from search import search_web, search_fandom_specific

# 1) JSON schema definitions for each tool
tool_schemas = [
    {
        "name": "list_files",
        "description": "List files in a directory matching a pattern.",
        "parameters": {
            "type": "object",
            "properties": {
                "directory": {"type": "string"},
                "pattern":   {"type": "string", "default": "*"},
                "recursive": {"type": "boolean", "default": False}
            },
            "required": ["directory"]
        }
    },
    {
        "name": "get_latest_file",
        "description": "Get the most recently modified file in a directory matching a pattern.",
        "parameters": {
            "type": "object",
            "properties": {
                "directory": {"type": "string"},
                "pattern": {"type": "string", "default": "*"}
            },
            "required": ["directory"]
        }
    },
    {
        "name": "get_latest_download",
        "description": "Get the most recent file from the user's Downloads folder. Perfect for 'what's the latest thing I downloaded'.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "read_file",
        "description": "Read and return the contents of a text file.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "write_file",
        "description": "Write text content to a file.",
        "parameters": {
            "type": "object",
            "properties": {
                "path":    {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "delete_file",
        "description": "Delete a file or directory.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "move_file",
        "description": "Move or rename a file or folder.",
        "parameters": {
            "type": "object",
            "properties": {
                "src": {"type": "string"},
                "dst": {"type": "string"}
            },
            "required": ["src", "dst"]
        }
    },
    {
        "name": "find_matching_files",
        "description": "Find files that match a natural language description. Use this before delete/move/open operations when the user gives a description rather than exact filename.",
        "parameters": {
            "type": "object",
            "properties": {
                "directory": {"type": "string"},
                "description": {"type": "string"},
                "limit": {"type": "integer", "default": 5}
            },
            "required": ["directory", "description"]
        }
    },
    {
        "name": "open_application",
        "description": "Run a shell command or open an application.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string"}
            },
            "required": ["command"]
        }
    },
    {
        "name": "search_files",
        "description": "Search your indexed files for content or filenames matching the query. Use this when users ask for files related to specific topics, classes, projects, or content.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Natural-language query to search file names and contents"},
                "top_k": {"type": "integer", "description": "Maximum number of results to return", "default": 5}
            },
            "required": ["query"]
        }
    },
    {
        "name": "interpret_file_intent",
        "description": "Analyze a user command to extract file operation intent and parameters. Returns structured data about the requested action.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The user command to analyze for file operation intent"}
            },
            "required": ["command"]
        }
    },
    {
        "name": "list_files_by_pattern",
        "description": "List files matching a specific pattern like *.py, *.json, test_*.py etc.",
        "parameters": {
            "type": "object",
            "properties": {
                "directory": {"type": "string", "default": "."},
                "pattern": {"type": "string"}
            },
            "required": ["pattern"]
        }
    },
    {
        "name": "create_directory",
        "description": "Create a new directory/folder at the specified path.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "run_file_workflow",
        "description": "Run a multi-step workflow of file operations. Use this for complex tasks that require multiple file operations in sequence.",
        "parameters": {
            "type": "object",
            "properties": {
                "steps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "tool": {"type": "string"},
                            "args": {"type": "object"}
                        },
                        "required": ["tool", "args"]
                    }
                }
            },
            "required": ["steps"]
        }
    },
    # Phase 5B: Docker-Based Sandboxed Web Automation
    {
        "name": "open_page_sandbox",
        "description": "Open a URL in the sandboxed browser. Use this for any web browsing or website interaction tasks.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The URL to open"}
            },
            "required": ["url"]
        }
    },
    {
        "name": "click_sandbox",
        "description": "Click a CSS selector in the sandboxed browser. Use after opening a page to interact with elements.",
        "parameters": {
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "CSS selector of the element to click"}
            },
            "required": ["selector"]
        }
    },
    {
        "name": "extract_text_sandbox",
        "description": "Extract inner text of a CSS selector in the sandboxed browser. Use to scrape content from web pages.",
        "parameters": {
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "CSS selector of the element to extract text from"}
            },
            "required": ["selector"]
        }
    },
    {
        "name": "fill_input_sandbox",
        "description": "Fill an input field with text in the sandboxed browser. Use for form interactions.",
        "parameters": {
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "CSS selector of the input element"},
                "text": {"type": "string", "description": "Text to fill in the input"}
            },
            "required": ["selector", "text"]
        }
    },
    {
        "name": "get_page_title_sandbox",
        "description": "Get the title of the current page in the sandboxed browser.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_page_url_sandbox",
        "description": "Get the current URL in the sandboxed browser.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "wait_for_element_sandbox",
        "description": "Wait for an element to appear in the sandboxed browser. Use when elements load dynamically.",
        "parameters": {
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "CSS selector of the element to wait for"},
                "timeout": {"type": "integer", "description": "Maximum seconds to wait", "default": 10}
            },
            "required": ["selector"]
        }
    },
    {
        "name": "get_element_attribute_sandbox",
        "description": "Get an attribute value of an element in the sandboxed browser.",
        "parameters": {
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "CSS selector of the element"},
                "attribute": {"type": "string", "description": "Attribute name to get (href, src, class, etc.)"}
            },
            "required": ["selector", "attribute"]
        }
    },
    {
        "name": "check_sandbox_health",
        "description": "Check if the sandbox is running properly.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "reset_sandbox",
        "description": "Reset the sandboxed browser session.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "open_website",
        "description": (
            "Enhanced AI-powered web content analysis. "
            "If query looks like a URL (http(s)://), opens it directly. "
            "Otherwise, searches the web for the query and opens the first result. "
            "Uses AI to intelligently summarize content or answer specific questions about it. "
            "Perfect for research tasks like 'get Leo Perlstein's profile' or 'summarize this article'."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search term or full URL"},
                "selector": {"type": "string", "description": "CSS selector to extract text (optional)"},
                "question": {"type": "string", "description": "Specific question to answer about the content (optional)"}
            },
            "required": ["query"]
        }
    }
]

# 2) Map schema names to Python callables
TOOL_MAP = {
    "list_files":      tools.list_files,
    "get_latest_file": tools.get_latest_file,
    "get_latest_download": tools.get_latest_download,
    "read_file":       tools.read_file,
    "write_file":      tools.write_file,
    "delete_file":     tools.delete_file,
    "move_file":       tools.move_file,
    "find_matching_files": tools.find_matching_files,
    "open_application":tools.open_application,
    "search_files":    tools.search_files,
    "interpret_file_intent": tools.interpret_file_intent,
    "list_files_by_pattern": tools.list_files_by_pattern,
    "create_directory": tools.create_directory,
    "run_file_workflow": tools.run_file_workflow,
    # Phase 5B: Docker-Based Sandboxed Web Automation
    "open_page_sandbox": tools.open_page_sandbox,
    "click_sandbox": tools.click_sandbox,
    "extract_text_sandbox": tools.extract_text_sandbox,
    "fill_input_sandbox": tools.fill_input_sandbox,
    "get_page_title_sandbox": tools.get_page_title_sandbox,
    "get_page_url_sandbox": tools.get_page_url_sandbox,
    "wait_for_element_sandbox": tools.wait_for_element_sandbox,
    "get_element_attribute_sandbox": tools.get_element_attribute_sandbox,
    "check_sandbox_health": tools.check_sandbox_health,
    "reset_sandbox": tools.reset_sandbox,
    "open_website": tools.open_website
}

# Session state for conversation disambiguation (Step 3B)
pending_action = None

# Phase 4B: Advanced Context Understanding - Session State
_current_directory = None
_last_file = None
_last_action = None

def _update_context(action: str, fn_name: str, args: dict, result: Any):
    """
    Update session state after every file tool call.
    Tracks current directory, last file, and last action for context awareness.
    """
    global _current_directory, _last_file, _last_action
    
    # Determine what path or directory we just touched:
    if fn_name in ("list_files",):
        _current_directory = args.get("directory", ".")
    elif fn_name in ("get_latest_file", "get_latest_download"):
        _last_file = result  # result is the file path string or None
        _current_directory = os.path.dirname(result) if result else _current_directory
    elif fn_name in ("read_file", "delete_file", "move_file", "write_file", "open_application"):
        # Extract the actual file path from various possible argument names
        path_used = (args.get("target") or args.get("path") or args.get("src") or 
                    args.get("command") or args.get("choice") or args.get("file_path"))
        if path_used:
            _last_file = path_used
            # if it's a directory action, update current_directory:
            if fn_name == "open_application" and os.path.isdir(path_used):
                _current_directory = path_used
            else:
                _current_directory = os.path.dirname(path_used) if os.path.dirname(path_used) else _current_directory
    
    _last_action = action
    
    # Debug output to track state changes
    print(f"🧠 Context updated: action={_last_action}, file={_last_file}, dir={_current_directory}")

def _update_session_state(action: str, path: str = None, directory: str = None, file: str = None):
    """
    Update session state to track current directory, last file, and last action.
    This enables context-aware file operations and pronoun resolution.
    """
    global _current_directory, _last_file, _last_action
    
    _last_action = action
    
    # Handle both 'path' and 'file' parameters for compatibility
    if file:
        path = file
    
    if path:
        _last_file = path
        # Update current directory based on file path
        if os.path.isfile(path):
            _current_directory = os.path.dirname(path)
        elif os.path.isdir(path):
            _current_directory = path
    
    if directory:
        _current_directory = directory
    
    # Debug output to track state changes
    print(f"🧠 Context updated: action={_last_action}, file={_last_file}, dir={_current_directory}")

def _resolve_context_and_pronouns(intent: dict) -> dict:
    """
    Enhance intent with context awareness and pronoun resolution.
    Resolves vague targets like "this", "that", "it" using session state.
    """
    global _current_directory, _last_file, _last_action
    
    # Make a copy to avoid modifying the original
    enhanced_intent = intent.copy()
    
    # Resolve pronouns and implicit targets
    target = enhanced_intent.get("target", "").lower() if enhanced_intent.get("target") else ""
    pattern = enhanced_intent.get("pattern", "").lower() if enhanced_intent.get("pattern") else ""
    
    # Handle pronouns: "it", "this", "that" -> last file
    pronoun_words = ["it", "this", "that"]
    file_ref_phrases = ["this file", "that file", "the file", "same file", "previous file"]
    
    # Check if target or pattern contains pronouns or file references
    resolved = False
    for pronoun in pronoun_words:
        if (target == pronoun or pattern == pronoun) and _last_file:
            enhanced_intent["target"] = _last_file
            enhanced_intent["pattern"] = None
            print(f"🔗 Resolved pronoun '{target or pattern}' → {_last_file}")
            resolved = True
            break
    
    # Check for file reference phrases
    if not resolved:
        for phrase in file_ref_phrases:
            if (phrase in target or phrase in pattern) and _last_file:
                enhanced_intent["target"] = _last_file
                enhanced_intent["pattern"] = None
                print(f"🔗 Resolved file reference '{phrase}' → {_last_file}")
                resolved = True
                break
    
    # Handle implicit directory references
    if not resolved and target in ["here", "current folder", "this folder", "current directory"] and _current_directory:
        enhanced_intent["target"] = _current_directory
        print(f"🔗 Resolved location reference → {_current_directory}")
        resolved = True
    
    # Default directory context for list operations
    if not resolved and enhanced_intent.get("action") == "list" and not target and not pattern and _current_directory:
        enhanced_intent["target"] = _current_directory
        print(f"🔗 Applied directory context for list → {_current_directory}")
        resolved = True
    
    # Handle cases where action is clear but target/pattern is missing - use last file
    if not resolved and enhanced_intent.get("action") in ["read", "open"] and not target and not pattern and _last_file:
        enhanced_intent["target"] = _last_file
        print(f"🔗 Applied last file context for {enhanced_intent.get('action')} → {_last_file}")
        resolved = True
    
    return enhanced_intent

def _plan_and_execute_workflow(user_input: str) -> str:
    """
    Plan and execute a multi-step file workflow using LLM planning.
    """
    # Load API key and create OpenAI client
    with open("config.json") as f:
        config = json.load(f)
    api_key = config.get("openai_api_key")
    org_id = config.get("openai_organization")
    
    if org_id:
        client = OpenAI(api_key=api_key, organization=org_id)
    else:
        client = OpenAI(api_key=api_key)
    
    # Get available tools for the planning prompt
    available_tools = [s["name"] for s in tool_schemas if s["name"] != "run_file_workflow"]
    
    try:
        # Ask LLM to plan the workflow
        plan_response = client.chat.completions.create(
            model="gpt-4-0613",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You translate natural-language workflow requests into JSON lists of steps. "
                        "Each step is {\"tool\": \"tool_name\", \"args\": {\"param\": \"value\"}}. "
                        f"Available tools and their EXACT parameters:\n"
                        "- list_files: directory, pattern (optional), recursive (optional)\n"
                        "- list_files_by_pattern: pattern, directory (optional, defaults to current)\n"
                        "- find_matching_files: directory, description\n"
                        "- move_file: src, dst\n"
                        "- create_directory: path\n"
                        "- search_files: query\n"
                        "- read_file: path\n"
                        "- write_file: path, content\n"
                        "- delete_file: path\n"
                        "\nFor folders/directories, use these path mappings:\n"
                        "- 'python_files folder' → 'python_files'\n"
                        "- 'test folder' → 'test_files'\n"
                        "- 'log files' → use find_matching_files with description 'log files'\n"
                        "- 'config files' → use find_matching_files with description 'config json files'\n"
                        "- 'archive folder' → 'archive'\n"
                        "- 'backup directory' → 'backup'\n"
                        "\nWorkflow patterns:\n"
                        "1. Create folder + move files: create_directory first, then list_files_by_pattern, then move each file\n"
                        "2. Use list_files_by_pattern for file patterns like '*.py', '*.json', 'test_*.py'\n"
                        "3. Use find_matching_files for natural language descriptions\n"
                        "4. Use current directory '.' for searching\n"
                        "5. For moving multiple files: list_files_by_pattern to get files, then move_file for each\n"
                        "\nRespond with ONLY valid JSON, no other text."
                    )
                },
                {"role": "user", "content": user_input}
            ],
            temperature=0
        )
        
        plan_text = plan_response.choices[0].message.content.strip()
        
        # Try to extract JSON from the response
        try:
            if plan_text.startswith("```json"):
                plan_text = plan_text.split("```json")[1].split("```")[0].strip()
            elif plan_text.startswith("```"):
                plan_text = plan_text.split("```")[1].split("```")[0].strip()
            
            plan = json.loads(plan_text)
            
            # Ensure plan is a list of steps
            if isinstance(plan, dict) and "steps" in plan:
                steps = plan["steps"]
            elif isinstance(plan, list):
                steps = plan
            else:
                return f"❌ Invalid workflow plan format: {plan_text}"
            
        except json.JSONDecodeError as e:
            return f"❌ Failed to parse workflow plan as JSON: {e}\nPlan text: {plan_text}"
        
        # Execute the workflow
        print(f"🔄 Executing workflow with {len(steps)} steps...")
        result = run_file_workflow(steps)
        
        # Phase 4B-2: Update context after workflow execution
        _update_context("workflow", "run_file_workflow", {"steps": steps}, result)
        
        return f"🔄 **Workflow Execution Results:**\n{result}"
        
    except Exception as e:
        return f"❌ Error planning/executing workflow: {e}"

def chat_with_agent(conversation_history: list, user_input: str) -> str:
    """
    Intelligent agent with intent parsing and autonomous web research capabilities.
    
    Flow:
    1. Parse user intent using LLM-driven intent classification
    2. For knowledge queries, detect if web research is needed
    3. Ask for permission before web research (if not previously granted)
    4. Execute appropriate tools based on intent
    5. Fall back to standard function calling if intent parsing fails
    """
    global pending_action
    
    # 0) If we're awaiting a yes/no on any tool (file or web), handle it first:
    if pending_action and pending_action.get("awaiting_confirmation"):
        reply = user_input.strip().lower()
        tool = pending_action["tool"]
        args = pending_action["args"]
        
        if reply in ("yes", "y", "sure", "go ahead", "ok", "okay", "proceed"):
            # Execute the pending tool
            try:
                if tool == "search_web":
                    result = search_web(**args)
                    response = f"🔍 Web search results:\n{result}"
                elif tool == "search_fandom_specific":
                    result = search_fandom_specific(**args)
                    response = f"🔍 VGHW Fandom search results:\n{result}"
                elif tool == "open_website":
                    result = open_website(**args)
                    # Check for disambiguation in confirmation result
                    if isinstance(result, dict) and result.get("needs_disambiguation"):
                        options = result["options"]
                        pending_action = {
                            "tool": "open_website",
                            # Always keep query as the original search, never a URL
                            "args": {"query": args.get("query"), "url": None},
                            "awaiting_disambiguation": True,
                            "candidates": options
                        }
                        response = "I found multiple pages:\n" + "\n".join(
                            f"{i+1}. {u}" for i, u in enumerate(options)
                        ) + "\nWhich one should I open? (Enter a number or 'all')"
                    else:
                        response = f"🌐 Web content:\n{result}"
                else:
                    # Handle other tools (file operations, etc.)
                    fn = TOOL_MAP.get(tool)
                    if fn:
                        result = fn(**args)
                        response = f"✅ {tool} result:\n{result}"
                    else:
                        response = f"❌ Error: Unknown tool {tool}"
            except Exception as e:
                response = f"❌ Error during {tool}: {e}"
        else:
            response = f"❎ {tool} cancelled."
        
        pending_action = None
        conversation_history.append({"role": "assistant", "content": response})
        return response
    
    # Handle disambiguation for web navigation
    if pending_action and pending_action.get("awaiting_disambiguation"):
        choice = user_input.strip().lower()
        candidates = pending_action.get("candidates", [])

        if choice in ("all", "every", "each", "all of them"):
            summaries = []
            for url_option in candidates:
                try:
                    content = open_website(query=None, url=url_option, summary_only=True)
                    summaries.append(f"{url_option}:\n{content}")
                except Exception as e:
                    summaries.append(f"{url_option}: Error {e}")
            pending_action = None
            combined = "\n\n".join(summaries)
            response = f"🌐 Web content:\n\n{combined}"
            conversation_history.append({"role": "assistant", "content": response})
            return response

        # Try to parse as number
        chosen_url = None
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(candidates):
                chosen_url = candidates[idx]
        # Try to match URL or keyword
        if not chosen_url and choice:
            for candidate in candidates:
                if choice in candidate.lower():
                    chosen_url = candidate
                    break
        # Default to first candidate if still unresolved
        if not chosen_url and candidates:
            chosen_url = candidates[0]

        # Execute with chosen URL (always as url=, never as query=)
        pending_action = None
        try:
            result = open_website(query=None, url=chosen_url, summary_only=True)
            response = f"🌐 Web content:\n\n{result}"
            conversation_history.append({"role": "assistant", "content": response})
            return response
        except Exception as e:
            response = f"❌ Error opening {chosen_url}: {e}"
            conversation_history.append({"role": "assistant", "content": response})
            return response
    
    # Load API key and create OpenAI client
    with open("config.json") as f:
        config = json.load(f)
    api_key = config.get("openai_api_key")
    org_id = config.get("openai_organization")
    
    if org_id:
        client = OpenAI(api_key=api_key, organization=org_id)
    else:
        client = OpenAI(api_key=api_key)
    
    # STEP 1: Intent Classification & Slot Extraction
    try:
        print("🧠 Analyzing user intent...")
        intent_result = interpret_intent(user_input)
        print(f"🎯 Intent analysis: {intent_result}")
        
        # Handle knowledge/research queries autonomously
        if intent_result.get("intent") == "knowledge_query":
            query = intent_result.get("slots", {}).get("query", user_input)
            specific_question = intent_result.get("slots", {}).get("question")
            
            # Check if this seems like something requiring web research
            needs_research = any(keyword in user_input.lower() for keyword in [
                "latest", "recent", "current", "news", "today", "2024", "2025",
                "who is", "what is", "tell me about", "research", "find information"
            ])
            
            if needs_research:
                # Check if confirmation is required
                if intent_result.get("requires_confirmation"):
                    pending_action = {
                        "tool": "open_website",
                        "args": {"query": query, "question": specific_question},
                        "awaiting_confirmation": True
                    }
                    prompt = f"🔍 I can research '{query}' for current information. Would you like me to proceed? (yes/no)"
                    conversation_history.append({"role": "user", "content": user_input})
                    conversation_history.append({"role": "assistant", "content": prompt})
                    return prompt
                
                # No confirmation needed - proceed directly
                print(f"🔍 This query may require web research for current/accurate information.")
                print(f"🤖 JARVIS: I don't have current information about '{query}' in my training data.")
                print("🤖 JARVIS: Proceeding with research...")
                
                # Perform web research
                try:
                    research_result = tools.open_website(query, question=specific_question)
                    if isinstance(research_result, dict) and research_result.get("needs_disambiguation"):
                        options = research_result["options"]
                        summaries = []
                        selected = options if "all" in user_input.lower() else [options[0]]
                        for opt in selected:
                            try:
                                content = tools.open_website(query=None, url=opt)
                                summaries.append(f"{opt}:\n{content}")
                            except Exception as e:
                                summaries.append(f"{opt}: Error {e}")
                        research_result = "\n\n".join(summaries)

                    # Return the research result directly
                    conversation_history.append({"role": "user", "content": user_input})
                    conversation_history.append({"role": "assistant", "content": f"I've researched '{query}' for you:\n\n{research_result}"})
                    return f"I've researched '{query}' for you:\n\n{research_result}"

                except Exception as e:
                    print(f"❌ Web research failed: {e}")
                    # Fall through to standard chat
        
        # Handle web search requests
        elif intent_result.get("intent") == "web_search":
            query = intent_result.get("slots", {}).get("query", user_input)
            
            # If flagged for confirmation, ask first
            if intent_result.get("requires_confirmation"):
                pending_action = {
                    "tool": "search_web",
                    "args": {"query": query},
                    "awaiting_confirmation": True
                }
                prompt = f"🔍 I can search the web for '{query}'. Would you like me to proceed? (yes/no)"
                conversation_history.append({"role": "user", "content": user_input})
                conversation_history.append({"role": "assistant", "content": prompt})
                return prompt
            
            # Otherwise, do it immediately
            print(f"🔍 Performing web search for: {query}")
            try:
                results = search_web(query)
                
                # Check if this might be a fandom query that got poor results
                original_query = intent_result.get("slots", {}).get("query", user_input).lower()
                if (("vghw" in original_query or "fandom" in user_input.lower()) and 
                    "wikipedia" in results.lower() and "fandom.com" not in results.lower()):
                    
                    # Offer clarification for better fandom results
                    pending_action = {
                        "tool": "search_fandom_specific", 
                        "args": {"query": original_query.replace("site:vghw.fandom.com", "").strip()},
                        "awaiting_confirmation": True
                    }
                    
                    prompt = f"🔍 I found results on Wikipedia, but you mentioned VGHW/fandom. Would you like me to search specifically on the VGHW fandom wiki instead? (yes/no)\n\nCurrent results:\n{results}"
                    conversation_history.append({"role": "user", "content": user_input})
                    conversation_history.append({"role": "assistant", "content": prompt})
                    return prompt
                
                conversation_history.append({"role": "user", "content": user_input})
                conversation_history.append({"role": "assistant", "content": f"🔍 Web search results:\n\n{results}"})
                return f"🔍 Web search results:\n\n{results}"
            except Exception as e:
                print(f"❌ Web search failed: {e}")
                # Fall through to standard chat
        
        # Handle web navigation requests
        elif intent_result.get("intent") == "web_navigation":
            query = intent_result.get("slots", {}).get("query", user_input)
            url = intent_result.get("slots", {}).get("url")
            
            # If flagged for confirmation, ask first
            if intent_result.get("requires_confirmation"):
                pending_action = {
                    "tool": "open_website",
                    "args": {"query": query, "url": url},
                    "awaiting_confirmation": True
                }
                prompt = f"🌐 I can navigate to '{query}' and extract data. Proceed? (yes/no)"
                conversation_history.append({"role": "user", "content": user_input})
                conversation_history.append({"role": "assistant", "content": prompt})
                return prompt
            
            # No confirmation needed: do it
            print(f"🌐 Navigating to: {query}")
            try:
                result = open_website(query=query, url=url)
                
                # Check for disambiguation
                if isinstance(result, dict) and result.get("needs_disambiguation"):
                    options = result["options"]
                    pending_action = {
                        "tool": "open_website",
                        "args": {"query": query, "url": None},
                        "awaiting_disambiguation": True,
                        "candidates": options
                    }
                    prompt = "I found multiple pages:\n" + "\n".join(
                        f"{i+1}. {u}" for i, u in enumerate(options)
                    ) + "\nWhich one should I open? (Enter a number or 'all')"
                    conversation_history.append({"role": "user", "content": user_input})
                    conversation_history.append({"role": "assistant", "content": prompt})
                    return prompt
                
                # Regular result
                conversation_history.append({"role": "user", "content": user_input})
                conversation_history.append({"role": "assistant", "content": f"🌐 Web content:\n\n{result}"})
                return f"🌐 Web content:\n\n{result}"
            except Exception as e:
                print(f"❌ Web navigation failed: {e}")
                # Fall through to standard chat
        
        # Handle web research requests
        elif intent_result.get("intent") == "web_research":
            query = intent_result.get("slots", {}).get("query", user_input)
            question = intent_result.get("slots", {}).get("question")
            
            # If flagged for confirmation, ask first
            if intent_result.get("requires_confirmation"):
                pending_action = {
                    "tool": "open_website",
                    "args": {"query": query, "question": question},
                    "awaiting_confirmation": True
                }
                prompt = f"🔍 I can research '{query}' for you. Would you like me to proceed? (yes/no)"
                conversation_history.append({"role": "user", "content": user_input})
                conversation_history.append({"role": "assistant", "content": prompt})
                return prompt
            
            # No confirmation needed: proceed directly
            print(f"🌐 Performing web research for: {query}")
            try:
                research_result = tools.open_website(query, question=question)
                if isinstance(research_result, dict) and research_result.get("needs_disambiguation"):
                    options = research_result["options"]
                    summaries = []
                    selected = options if "all" in user_input.lower() else [options[0]]
                    for opt in selected:
                        try:
                            content = tools.open_website(query=None, url=opt)
                            summaries.append(f"{opt}:\n{content}")
                        except Exception as e:
                            summaries.append(f"{opt}: Error {e}")
                    research_result = "\n\n".join(summaries)
                conversation_history.append({"role": "user", "content": user_input})
                conversation_history.append({"role": "assistant", "content": f"🔍 Web research results:\n\n{research_result}"})
                return f"🔍 Web research results:\n\n{research_result}"
            except Exception as e:
                print(f"❌ Web research failed: {e}")
                # Fall through to standard chat
        
        # Handle file operations with direct tool dispatch
        elif intent_result.get("intent") == "file_operation":
            operation = intent_result.get("slots", {}).get("operation")
            filename = intent_result.get("slots", {}).get("filename")
            content = intent_result.get("slots", {}).get("content")
            
            if operation and filename:
                print(f"📁 Executing file operation: {operation} on {filename}")
                
                # Map operations to tools
                if operation == "create" and content:
                    try:
                        result = tools.write_file(filename, content)
                        conversation_history.append({"role": "user", "content": user_input})
                        conversation_history.append({"role": "assistant", "content": f"✅ File created successfully: {result}"})
                        return f"✅ File created successfully: {result}"
                    except Exception as e:
                        print(f"❌ File operation failed: {e}")
                        # Fall through to standard chat
                
                elif operation == "read":
                    try:
                        result = tools.read_file(filename)
                        conversation_history.append({"role": "user", "content": user_input})
                        conversation_history.append({"role": "assistant", "content": f"📄 File contents:\n\n{result}"})
                        return f"📄 File contents:\n\n{result}"
                    except Exception as e:
                        print(f"❌ File operation failed: {e}")
                        # Fall through to standard chat
        
        # For other intents or if direct dispatch fails, fall through to standard chat
        print("💬 Using standard function calling...")
        
    except Exception as e:
        print(f"⚠️ Intent parsing failed: {e}")
        print("💬 Falling back to standard function calling...")
    
    # STEP 2: Standard Function Calling (fallback)
    # 1) Append user message
    conversation_history.append({"role": "user", "content": user_input})

    # Convert function schemas to new "tools" format
    tools_format = [{"type": "function", "function": func} for func in tool_schemas]

    # 2) First pass to let GPT decide on a function call
    response = client.chat.completions.create(
        model="gpt-4-0613",
        messages=conversation_history,
        tools=tools_format,
        tool_choice="auto"
    )
    message = response.choices[0].message

    # 3) If no tool_calls, return content
    if not message.tool_calls:
        assistant_reply = message.content
        conversation_history.append({"role": "assistant", "content": assistant_reply})
        return assistant_reply

    # 4) Add the assistant's message with tool calls to history
    conversation_history.append({
        "role": "assistant",
        "content": message.content,
        "tool_calls": [
            {
                "id": tool_call.id,
                "type": "function",
                "function": {
                    "name": tool_call.function.name,
                    "arguments": tool_call.function.arguments
                }
            } for tool_call in message.tool_calls
        ]
    })

    # 5) Process each tool call
    for tool_call in message.tool_calls:
        fn_name = tool_call.function.name
        args = json.loads(tool_call.function.arguments or "{}")
        fn = TOOL_MAP.get(fn_name)

        if not fn:
            result = f"[Error] No tool named {fn_name}"
        else:
            try:
                result = fn(**args)
            except Exception as e:
                result = f"[Error calling {fn_name}] {e}"

        # Add the result to the conversation
        conversation_history.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": str(result)
        })

    # 6) Send back to GPT for final reply
    follow_up = client.chat.completions.create(
        model="gpt-4-0613",
        messages=conversation_history
    )
    assistant_reply = follow_up.choices[0].message.content
    conversation_history.append({"role": "assistant", "content": assistant_reply})

    return assistant_reply


def chat_with_agent_enhanced(conversation_history: list, user_input: str) -> str:
    """
    Enhanced version of chat_with_agent with intent interpretation for better file operation handling.
    Phase 3A: Intent Classification & Slot Extraction
    Phase 3B: Disambiguation & Conversational State
    """
    global pending_action
    
    # Load API key and create OpenAI client
    with open("config.json") as f:
        config = json.load(f)
    api_key = config.get("openai_api_key")
    org_id = config.get("openai_organization")
    
    if org_id:
        client = OpenAI(api_key=api_key, organization=org_id)
    else:
        client = OpenAI(api_key=api_key)
    
    # Enhanced system prompt with web research capabilities
    enhanced_prompt = {
        "role": "system",
        "content": (
            "You are JARVIS with enhanced file operation and web research capabilities. "
            "You have access to these tools:\n\n"
            "FILE OPERATIONS:\n"
            "• list_files, read_file, write_file, delete_file, move_file\n"
            "• search_files (semantic search through file contents)\n"
            "• find_matching_files (find files by description)\n\n"
            "WEB RESEARCH:\n"
            "• open_website(query, question=None) - Research any topic online and get AI summaries\n"
            "  - If query is a URL, opens it directly\n"
            "  - Otherwise searches web and opens first result\n"
            "  - Use 'question' parameter to ask specific questions about the content\n"
            "  - Returns intelligent AI summaries, not raw HTML\n\n"
            "COMBINED WORKFLOWS:\n"
            "When users ask to 'create a summary of [topic]' or 'research [topic] and save to file':\n"
            "1. First use open_website(query='[topic]', question='provide comprehensive summary') to research\n"
            "2. Then use write_file() to save the summary to the requested location\n\n"
            "EXAMPLES:\n"
            "• 'Create a summary of Leo Perlstein and save to jarvis folder'\n"
            "  → open_website('Leo Perlstein VGHW character', question='comprehensive character profile')\n"
            "  → write_file('C:\\\\Users\\\\jwexl\\\\Desktop\\\\jarvis\\\\Leo_Perlstein_Summary.txt', content)\n\n"
            "• 'Research latest AI news and create document'\n"
            "  → open_website('latest AI news 2025', question='summarize key developments')\n"
            "  → write_file(path, summary)\n\n"
            "Always provide clear status updates: 'Researching [topic]...', 'Creating document...', 'Done!'"
        )
    }
    
    # Insert enhanced prompt at the beginning if not already present
    if not any("enhanced file operation and web research capabilities" in str(msg.get("content", "")) for msg in conversation_history):
        conversation_history.insert(0, enhanced_prompt)
    
    # STEP 3A: Intent Classification & Slot Extraction
    # Before generic function calling, try to interpret file intent
    try:
        intent = tools.interpret_file_intent(user_input)
        print(f"🎯 Intent analysis: {intent}")
        
        if intent.get("is_file_command", False) and intent.get("confidence", 0) > 0.6:
            # Phase 4B-3: Pronoun & Implicit Target Resolution
            target = intent.get("target")
            pattern = intent.get("pattern")
            
            # Resolve pronouns in both target and pattern
            if target and target.lower() in ("this", "that", "it"):
                if _last_file:
                    intent["target"] = _last_file
                    intent["pattern"] = None  # Clear pattern when using pronoun
                    print(f"🔗 Resolved pronoun '{target}' → {_last_file}")
                    
            if pattern and pattern.lower() in ("this", "that", "it"):
                if _last_file:
                    intent["target"] = _last_file
                    intent["pattern"] = None  # Clear pattern when using pronoun
                    print(f"🔗 Resolved pronoun '{pattern}' → {_last_file}")
            
            # Resolve "current directory" to "."
            if target and target.lower() in ("current directory", "current folder", "here"):
                intent["target"] = "."
                print(f"🔗 Resolved directory reference '{target}' → .")
            
            # If no target but we have a current directory for list/search:
            if intent.get("action") in ("list", "search", "get_latest_file") and not intent.get("target"):
                if _current_directory:
                    intent["target"] = _current_directory
                    print(f"🔗 Applied directory context → {_current_directory}")
                else:
                    intent["target"] = "."
                    print(f"🔗 Applied default directory context → .")
            
            # Phase 4B: Apply context understanding and pronoun resolution
            enhanced_intent = _resolve_context_and_pronouns(intent)
            print(f"🧠 Enhanced intent: {enhanced_intent}")
            
            # Direct dispatch based on extracted intent
            result = _dispatch_file_operation(enhanced_intent, user_input)
            if result is not None:
                # Add both user input and result to conversation history
                conversation_history.append({"role": "user", "content": user_input})
                conversation_history.append({"role": "assistant", "content": result})
                return result
    except Exception as e:
        print(f"Intent analysis failed: {e}, falling back to generic function calling")
    
    # STEP 3B: Check for pending clarification after intent processing
    # Only treat as clarification if it's NOT a new file command
    if pending_action is not None:
        # If this is a new file command, clear pending action and continue with new command
        try:
            new_intent = tools.interpret_file_intent(user_input)
            if new_intent.get("is_file_command", False) and new_intent.get("confidence", 0) > 0.6:
                print(f"🔄 Clearing pending action for new file command")
                pending_action = None
                # Continue with normal processing below
            else:
                # This is clarification for pending action
                clarification_result = handle_clarification(user_input)
                if clarification_result:
                    conversation_history.append({"role": "user", "content": user_input})
                    conversation_history.append({"role": "assistant", "content": clarification_result})
                    return clarification_result
        except Exception as e:
            # If intent analysis fails, treat as clarification
            clarification_result = handle_clarification(user_input)
            if clarification_result:
                conversation_history.append({"role": "user", "content": user_input})
                conversation_history.append({"role": "assistant", "content": clarification_result})
                return clarification_result
    
    # Fallback to original chat_with_agent logic
    return chat_with_agent(conversation_history, user_input)

def _dispatch_file_operation(intent: dict, user_input: str) -> str:
    """
    Directly dispatch file operations based on extracted intent.
    Returns None if operation couldn't be handled directly.
    Phase 5A: Check for requires_confirmation flag for destructive operations.
    """
    global pending_action
    
    action = intent.get("action")
    target = intent.get("target")
    pattern = intent.get("pattern")
    query = intent.get("query")
    src = intent.get("src")
    dst = intent.get("dst")
    requires_confirmation = intent.get("requires_confirmation", False)
    
    try:
        if action == "list":
            # List files operation
            directory = target or "."
            files = tools.list_files(directory, pattern or "*", recursive=False)
            
            # Phase 4B-2: Update context after tool call
            _update_context("list", "list_files", {"directory": directory, "pattern": pattern}, files)
            
            if isinstance(files, list) and len(files) > 0:
                file_list = "\n".join(f"• {f}" for f in files[:20])  # Limit to 20 files
                more_text = f"\n... and {len(files) - 20} more files" if len(files) > 20 else ""
                return f"📁 Files in {directory}:\n{file_list}{more_text}"
            else:
                return f"📁 No files found in {directory} matching pattern '{pattern or '*'}'"
        
        elif action == "search" and query:
            # Semantic search operation
            results = tools.search_files(query, top_k=5)
            if results:
                file_list = []
                for i, result in enumerate(results, 1):
                    filename = result.get('filename', 'Unknown')
                    score = result.get('score', 0.0)
                    file_list.append(f"{i}. {filename} (relevance: {score:.2f})")
                return f"🔍 Search results for '{query}':\n" + "\n".join(file_list)
            else:
                return f"🔍 No files found matching '{query}'"
        
        elif action == "open" and (target or pattern):
            # Use target if available, otherwise use pattern
            search_term = target or pattern
            
            # If the search_term isn't an absolute path or doesn't exist, semantic-search for it
            if not os.path.isabs(search_term) or not os.path.exists(search_term):
                # find matching files
                candidates = tools.search_files(search_term, top_k=5)
                if len(candidates) == 0:
                    return f"📂 I couldn't find any files matching '{search_term}'."
                elif len(candidates) == 1:
                    # resolve to the single file
                    target = candidates[0].get("path", candidates[0].get("filename", str(candidates[0])))
                else:
                    # multiple matches → ask for clarification with summaries
                    # Convert search results to the format expected by handle_clarification
                    file_paths = []
                    file_descriptions = []
                    
                    for i, candidate in enumerate(candidates, 1):
                        if isinstance(candidate, dict):
                            path = candidate.get("path", candidate.get("filename", str(candidate)))
                        else:
                            path = str(candidate)
                        file_paths.append(path)
                        
                        # Generate summary for this file
                        try:
                            preview = get_file_preview(path, max_chars=500)
                            summary = summarize_text(preview, max_sentences=1)
                            filename = os.path.basename(path)
                            file_descriptions.append(f"{i}. {filename} — {summary}")
                        except Exception as e:
                            filename = os.path.basename(path)
                            file_descriptions.append(f"{i}. {filename} — (Summary unavailable)")
                    
                    pending_action = {
                        "action": "open",
                        "tool_name": "open_application",
                        "candidates": file_paths,
                        "original_command": user_input
                    }
                    
                    prompt = (
                        f"📂 I found {len(candidates)} files matching '{search_term}':\n\n" +
                        "\n".join(file_descriptions) +
                        "\n\nWhich one would you like to open? (Reply with number, filename, or keyword)"
                    )
                    return prompt
            else:
                target = search_term
            result = tools.open_application(target)
            
            # Phase 4B-2: Update context after tool call
            _update_context("open", "open_application", {"target": target}, result)
            
            return f"📂 Opening {os.path.basename(target)}\n{result}"
        
        elif action == "read" and (target or pattern):
            # Use target if available, otherwise use pattern
            search_term = target or pattern
            
            # If the search_term isn't an absolute path or doesn't exist, semantic-search for it
            if not os.path.isabs(search_term) or not os.path.exists(search_term):
                # find matching files
                candidates = tools.search_files(search_term, top_k=5)
                if len(candidates) == 0:
                    return f"📄 I couldn't find any files matching '{search_term}'."
                elif len(candidates) == 1:
                    # resolve to the single file
                    target = candidates[0].get("path", candidates[0].get("filename", str(candidates[0])))
                else:
                    # multiple matches → ask for clarification with summaries
                    # Convert search results to the format expected by handle_clarification
                    file_paths = []
                    file_descriptions = []
                    
                    for i, candidate in enumerate(candidates, 1):
                        if isinstance(candidate, dict):
                            path = candidate.get("path", candidate.get("filename", str(candidate)))
                        else:
                            path = str(candidate)
                        file_paths.append(path)
                        
                        # Generate summary for this file
                        try:
                            preview = get_file_preview(path, max_chars=500)
                            summary = summarize_text(preview, max_sentences=1)
                            filename = os.path.basename(path)
                            file_descriptions.append(f"{i}. {filename} — {summary}")
                        except Exception as e:
                            filename = os.path.basename(path)
                            file_descriptions.append(f"{i}. {filename} — (Summary unavailable)")
                    
                    pending_action = {
                        "action": "read",
                        "tool_name": "read_file",
                        "candidates": file_paths,
                        "original_command": user_input
                    }
                    
                    prompt = (
                        f"📄 I found {len(candidates)} files matching '{search_term}':\n\n" +
                        "\n".join(file_descriptions) +
                        "\n\nWhich one would you like to read? (Reply with number, filename, or keyword)"
                    )
                    return prompt
            else:
                target = search_term
            content = tools.read_file(target)
            
            # Phase 4B-2: Update context after tool call
            _update_context("read", "read_file", {"target": target}, content)
            
            if len(content) > 1000:
                content = content[:1000] + "...\n[Content truncated]"
            return f"📄 Content of {os.path.basename(target)}:\n\n{content}"
        
        elif action == "delete" and (target or pattern):
            # Use target if available, otherwise use pattern
            search_term = target or pattern
            
            # First, try to find the file locally in current directory
            local_path = None
            if not os.path.isabs(search_term):
                # Check if file exists in current directory
                if os.path.exists(search_term):
                    local_path = os.path.abspath(search_term)
                # Also check common variations
                elif os.path.exists(f"./{search_term}"):
                    local_path = os.path.abspath(f"./{search_term}")
            else:
                # It's already an absolute path
                if os.path.exists(search_term):
                    local_path = search_term
            
            if local_path:
                # Found file locally - proceed with confirmation
                if requires_confirmation:
                    # Phase 5A: Request confirmation for destructive delete operation
                    pending_action = {
                        "action": "delete",
                        "tool_name": "delete_file",
                        "candidates": [local_path],
                        "original_command": user_input
                    }
                    filename = os.path.basename(local_path)
                    return f"🗑️ Are you sure you want to delete '{filename}'? Reply 'yes' to confirm or 'no' to cancel."
                else:
                    # Execute delete directly (shouldn't happen with safe_roots)
                    result = tools.delete_file(local_path)
                    _update_context("delete", "delete_file", {"file_path": local_path}, result)
                    return f"🗑️ Deleted {os.path.basename(local_path)}\n{result}"
            else:
                # File not found locally, fall back to semantic search
                candidates = tools.search_files(search_term, top_k=5)
                if len(candidates) == 0:
                    return f"🗑️ I couldn't find any files matching '{search_term}'."
                elif len(candidates) == 1:
                    # resolve to the single file
                    target = candidates[0].get("path", candidates[0].get("filename", str(candidates[0])))
                else:
                    # multiple matches → ask for clarification with summaries
                    # Convert search results to the format expected by handle_clarification
                    file_paths = []
                    file_descriptions = []
                    
                    for i, candidate in enumerate(candidates, 1):
                        if isinstance(candidate, dict):
                            path = candidate.get("path", candidate.get("filename", str(candidate)))
                        else:
                            path = str(candidate)
                        file_paths.append(path)
                        
                        # Generate summary for this file
                        try:
                            preview = get_file_preview(path, max_chars=500)
                            summary = summarize_text(preview, max_sentences=1)
                            filename = os.path.basename(path)
                            file_descriptions.append(f"{i}. {filename} — {summary}")
                        except Exception as e:
                            filename = os.path.basename(path)
                            file_descriptions.append(f"{i}. {filename} — (Summary unavailable)")
                    
                    pending_action = {
                        "action": "delete",
                        "tool_name": "delete_file",
                        "candidates": file_paths,
                        "original_command": user_input
                    }
                    
                    prompt = (
                        f"🗑️ I found {len(candidates)} files matching '{search_term}':\n\n" +
                        "\n".join(file_descriptions) +
                        "\n\nWhich one would you like to delete? (Reply with number, filename, or keyword)"
                    )
                    return prompt
            
            # For single file deletion, ask for confirmation
            if requires_confirmation:
                pending_action = {
                    "action": "delete",
                    "tool_name": "delete_file", 
                    "candidates": [target],
                    "original_command": user_input
                }
                filename = os.path.basename(target)
                return f"🗑️ Are you sure you want to delete '{filename}'? Reply 'yes' to confirm or 'no' to cancel."
            else:
                # Execute delete directly (shouldn't happen with safe_roots)
                result = tools.delete_file(target)
                _update_context("delete", "delete_file", {"file_path": target}, result)
                return f"🗑️ Deleted {os.path.basename(target)}\n{result}"
        
        elif action == "move" and pattern and dst:
            # Find and move file
            matches = tools.find_matching_files(pattern)
            if isinstance(matches, list) and len(matches) > 0:
                if len(matches) == 1:
                    # Single match - check if confirmation is required
                    src_file = matches[0]
                    if requires_confirmation:
                        # Phase 5A: Request confirmation for destructive move operation
                        pending_action = {
                            "action": "move",
                            "tool_name": "move_file",
                            "candidates": [src_file],
                            "original_command": user_input,
                            "dst": dst
                        }
                        filename = os.path.basename(src_file)
                        return f"📦 Are you sure you want to move '{filename}' to '{dst}'? Reply 'yes' to confirm or 'no' to cancel."
                    else:
                        # Execute move directly
                        result = tools.move_file(src_file, dst)
                        # Phase 4B-2: Update context after tool call
                        _update_context("move", "move_file", {"src": src_file, "dst": dst}, result)
                        return f"📦 Moving {src_file} to {dst}\n{result}"
                else:
                    # Multiple matches - ask for clarification
                    pending_action = {
                        "action": "move",
                        "tool_name": "move_file",
                        "candidates": matches[:10],
                        "original_command": user_input,
                        "dst": dst
                    }
                    names = [f"{i+1}. {os.path.basename(path)}" for i, path in enumerate(matches[:10])]
                    return (f"📦 I found {len(matches)} files matching '{pattern}':\n" +
                            "\n".join(names) +
                            f"\nWhich one would you like to move to {dst}?")
            else:
                return f"📦 No files found matching '{pattern}'"
        
        elif action == "write" and target:
            # Write file operation
            content = intent.get("content", "")
            if requires_confirmation:
                # Phase 5A: Request confirmation for destructive write operation
                pending_action = {
                    "action": "write",
                    "tool_name": "write_file",
                    "candidates": [target],
                    "original_command": user_input,
                    "content": content
                }
                filename = os.path.basename(target)
                file_exists = os.path.exists(target)
                action_verb = "overwrite" if file_exists else "create"
                return f"✏️ Are you sure you want to {action_verb} '{filename}'? Reply 'yes' to confirm or 'no' to cancel."
            else:
                # Execute write directly
                result = tools.write_file(target, content)
                # Phase 4B-2: Update context after tool call
                _update_context("write", "write_file", {"target": target, "content": content}, result)
                return f"✏️ Writing to {os.path.basename(target)}\n{result}"
        
        elif action == "workflow":
            # Multi-step workflow planning and execution
            return _plan_and_execute_workflow(user_input)
        
        # If we get here, the intent couldn't be handled directly
        return None
        
    except Exception as e:
        print(f"Error in direct file operation dispatch: {e}")
        return None

def handle_clarification(user_input: str) -> str:
    """
    Handle clarification responses when pending_action exists (Step 3B).
    """
    global pending_action
    
    if not pending_action:
        return None  # No pending action to clarify
    
    action = pending_action["action"]
    tool_name = pending_action.get("tool_name")
    candidates = pending_action["candidates"]
    dst = pending_action.get("dst")
    
    user_lower = user_input.lower().strip()
    
    # Phase 5A: Handle simple confirmations for destructive operations
    if action == "delete":
        if user_lower in ["yes", "y", "confirm", "ok", "sure", "delete it"]:
            file_path = candidates[0]
            result = tools.delete_file(file_path)
            # Phase 4B-2: Update context after tool call
            _update_context("delete", "delete_file", {"file_path": file_path}, result)
            pending_action = None  # Clear pending action
            return f"🗑️ Deleted {os.path.basename(file_path)}\n{result}"
        elif user_lower in ["no", "n", "cancel", "abort", "don't", "stop"]:
            pending_action = None  # Clear pending action
            return "🚫 Delete operation cancelled."
    
    elif action == "move":
        if user_lower in ["yes", "y", "confirm", "ok", "sure", "move it"]:
            src_file = candidates[0]
            result = tools.move_file(src_file, dst)
            # Phase 4B-2: Update context after tool call
            _update_context("move", "move_file", {"src": src_file, "dst": dst}, result)
            pending_action = None  # Clear pending action
            return f"📦 Moved {os.path.basename(src_file)} to {dst}\n{result}"
        elif user_lower in ["no", "n", "cancel", "abort", "don't", "stop"]:
            pending_action = None  # Clear pending action
            return "🚫 Move operation cancelled."
    
    elif action == "write":
        if user_lower in ["yes", "y", "confirm", "ok", "sure", "write it", "save it"]:
            target = candidates[0]
            content = pending_action.get("content", "")
            result = tools.write_file(target, content)
            # Phase 4B-2: Update context after tool call
            _update_context("write", "write_file", {"target": target, "content": content}, result)
            pending_action = None  # Clear pending action
            return f"✏️ Wrote to {os.path.basename(target)}\n{result}"
        elif user_lower in ["no", "n", "cancel", "abort", "don't", "stop"]:
            pending_action = None  # Clear pending action
            return "🚫 Write operation cancelled."
    
    # Handle number selection
    if user_input.strip().isdigit():
        selection = int(user_input.strip())
        if 1 <= selection <= len(candidates):
            choice = candidates[selection - 1]
            
            # Execute the tool using TOOL_MAP
            if tool_name and tool_name in TOOL_MAP:
                fn = TOOL_MAP[tool_name]
                try:
                    if action == "open":
                        result = fn(choice)
                        # Phase 4B-2: Update context after tool call
                        _update_context("open", tool_name, {"choice": choice}, result)
                    elif action == "read":
                        result = fn(choice)
                        # Phase 4B-2: Update context after tool call
                        _update_context("read", tool_name, {"choice": choice}, result)
                    elif action == "delete":
                        # Phase 5A: For destructive operations selected from list, ask for confirmation
                        pending_action = {
                            "action": "delete",
                            "tool_name": tool_name,
                            "candidates": [choice],
                            "original_command": pending_action.get("original_command", "")
                        }
                        filename = os.path.basename(choice)
                        return f"🗑️ Are you sure you want to delete '{filename}'? Reply 'yes' to confirm or 'no' to cancel."
                    elif action == "move":
                        # Phase 5A: For destructive operations selected from list, ask for confirmation
                        pending_action = {
                            "action": "move", 
                            "tool_name": tool_name,
                            "candidates": [choice],
                            "original_command": pending_action.get("original_command", ""),
                            "dst": dst
                        }
                        filename = os.path.basename(choice)
                        return f"� Are you sure you want to move '{filename}' to '{dst}'? Reply 'yes' to confirm or 'no' to cancel."
                    elif action == "write":
                        # Phase 5A: For destructive operations selected from list, ask for confirmation
                        content = pending_action.get("content", "")
                        pending_action = {
                            "action": "write",
                            "tool_name": tool_name, 
                            "candidates": [choice],
                            "original_command": pending_action.get("original_command", ""),
                            "content": content
                        }
                        filename = os.path.basename(choice)
                        file_exists = os.path.exists(choice)
                        action_verb = "overwrite" if file_exists else "create"
                        return f"✏️ Are you sure you want to {action_verb} '{filename}'? Reply 'yes' to confirm or 'no' to cancel."
                    
                    pending_action = None  # Clear pending action
                    
                    if action == "open":
                        return f"� Opened {os.path.basename(choice)}. {result}"
                    elif action == "read":
                        if len(str(result)) > 1000:
                            result = str(result)[:1000] + "...\n[Content truncated]"
                        return f"📄 Content of {os.path.basename(choice)}:\n\n{result}"
                except Exception as e:
                    pending_action = None  # Clear pending action
                    return f"❌ Error executing {action}: {e}"
            else:
                # Fallback to direct function calls if tool_name not found
                if action == "open":
                    result = tools.open_application(choice)
                    _update_session_state("open", file=choice)
                    pending_action = None  # Clear pending action
                    return f"📂 Opening {os.path.basename(choice)}\n{result}"
                elif action == "read":
                    content = tools.read_file(choice)
                    _update_session_state("read", file=choice)
                    pending_action = None  # Clear pending action
                    if len(content) > 1000:
                        content = content[:1000] + "...\n[Content truncated]"
                    return f"📄 Content of {os.path.basename(choice)}:\n\n{content}"
                elif action == "delete":
                    # Phase 5A: For destructive operations selected from list, ask for confirmation
                    pending_action = {
                        "action": "delete",
                        "tool_name": "delete_file",
                        "candidates": [choice],
                        "original_command": pending_action.get("original_command", "")
                    }
                    filename = os.path.basename(choice)
                    return f"🗑️ Are you sure you want to delete '{filename}'? Reply 'yes' to confirm or 'no' to cancel."
                elif action == "move" and dst:
                    # Phase 5A: For destructive operations selected from list, ask for confirmation
                    pending_action = {
                        "action": "move",
                        "tool_name": "move_file",
                        "candidates": [choice],
                        "original_command": pending_action.get("original_command", ""),
                        "dst": dst
                    }
                    filename = os.path.basename(choice)
                    return f"📦 Are you sure you want to move '{filename}' to '{dst}'? Reply 'yes' to confirm or 'no' to cancel."
        else:
            return f"❌ Please choose a number between 1 and {len(candidates)}"
    
    # Handle keyword-based clarification
    best_match = None
    best_score = 0
    
    for candidate in candidates:
        # Handle both Windows and Unix path separators
        if "\\" in candidate:
            filename = candidate.split("\\")[-1].lower()
        else:
            filename = candidate.split("/")[-1].lower()
        score = 0
        
        # Check for keyword matches in the filename
        for word in user_lower.split():
            if word in filename:
                score += 1
        
        if score > best_score:
            best_score = score
            best_match = candidate
    
    if best_match and best_score > 0:
        pending_action = None  # Clear pending action
        
        # Execute the action on matched file
        if action == "open":
            result = tools.open_application(best_match)
            return f"📂 Opening {os.path.basename(best_match)}\n{result}"
        elif action == "read":
            content = tools.read_file(best_match)
            if len(content) > 1000:
                content = content[:1000] + "...\n[Content truncated]"
            return f"📄 Content of {os.path.basename(best_match)}:\n\n{content}"
        elif action == "delete":
            # Phase 5A: For destructive operations matched by fuzzy search, ask for confirmation
            pending_action = {
                "action": "delete",
                "tool_name": "delete_file",
                "candidates": [best_match],
                "original_command": pending_action.get("original_command", "")
            }
            filename = os.path.basename(best_match)
            return f"🗑️ Are you sure you want to delete '{filename}'? Reply 'yes' to confirm or 'no' to cancel."
        elif action == "move" and dst:
            # Phase 5A: For destructive operations matched by fuzzy search, ask for confirmation
            pending_action = {
                "action": "move",
                "tool_name": "move_file",
                "candidates": [best_match],
                "original_command": pending_action.get("original_command", ""),
                "dst": dst
            }
            filename = os.path.basename(best_match)
            return f"📦 Are you sure you want to move '{filename}' to '{dst}'? Reply 'yes' to confirm or 'no' to cancel."
            return f"📦 Moving {os.path.basename(best_match)} to {dst}\n{result}"
    
    # Handle cancel requests and "none of these" responses
    if user_lower in ["cancel", "abort", "stop", "quit", "no", "none", "none of those", "none of these", "not these", "not those"]:
        pending_action = None
        return "🚫 Operation cancelled."
    
    # If we can't understand the clarification, ask again
    return ("🤔 I didn't understand your choice. Please reply with:\n"
            "• A number (1, 2, 3, etc.)\n"
            "• Keywords from the filename you want\n"
            "• 'cancel' to abort the operation")