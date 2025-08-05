# tools.py

import os
import glob
import subprocess
import shutil
import difflib
from typing import List, Optional, Union
import re

def list_files_by_pattern(directory: str = ".", pattern: str = "*") -> list:
    """List files matching a pattern (like *.py, *.json, etc.)"""
    try:
        import glob
        if not os.path.isabs(directory):
            directory = resolve_directory(directory)
        
        search_pattern = os.path.join(directory, pattern)
        files = glob.glob(search_pattern)
        # Return full paths for move operations to work correctly
        return [f for f in files if os.path.isfile(f)]
    except Exception as e:
        return f"Error listing files: {e}"

# tools.py

import os
import glob
import subprocess
import shutil
import difflib
from typing import List, Optional
import re
import json
import requests

# Phase 5A: Path Whitelisting & Safety
try:
    with open("config.json") as f:
        cfg = json.load(f)
    SAFE_ROOTS = [os.path.realpath(r) for r in cfg.get("safe_roots", [])]
    print(f"🔒 Loaded safe roots: {SAFE_ROOTS}")
except Exception as e:
    print(f"⚠️ Warning: Could not load safe roots from config.json: {e}")
    SAFE_ROOTS = []

# Phase 5B: Docker Sandbox Configuration
SANDBOX_URL = "http://localhost:8001"

def is_path_safe(path: str) -> bool:
    """
    Resolve realpath and ensure it starts with one of SAFE_ROOTS.
    """
    if not SAFE_ROOTS:
        print(f"⚠️ Warning: No safe roots configured, allowing path: {path}")
        return True  # Allow all if no safe roots configured
    
    real = os.path.realpath(path)
    is_safe = any(real.startswith(root) for root in SAFE_ROOTS)
    if not is_safe:
        print(f"🚫 Path blocked: {real} not in safe roots: {SAFE_ROOTS}")
    return is_safe

def create_directory(path: str) -> str:
    """Create a directory at the specified path"""
    try:
        if os.path.exists(path):
            return f"Directory already exists: {path}"
        os.makedirs(path, exist_ok=True)
        return f"Created directory: {path}"
    except Exception as e:
        return f"Error creating directory {path}: {e}"

def find_matching_files(directory: str, description: str, limit: int = 5) -> List[dict]:
    """
    Find files that match a natural language description.
    Returns a list of dictionaries with file info and match scores.
    """
    # If directory isn't an absolute path, resolve it
    if not os.path.isabs(directory):
        directory = resolve_directory(directory)
    
    # Get all files in directory
    try:
        all_files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    except OSError:
        return []
    
    # Extract keywords from description
    description_lower = description.lower()
    # Remove common file operation words
    stop_words = {'delete', 'remove', 'open', 'move', 'copy', 'the', 'a', 'an', 'file', 'image', 'picture', 'video', 'document', 'one', 'that', 'this'}
    
    # Extract meaningful words and patterns
    words = []
    # Look for numbers/dimensions (like "150px", "2d", "71tc")
    number_patterns = re.findall(r'\d+[a-z]*', description_lower)
    words.extend(number_patterns)
    
    # Look for regular words
    regular_words = [w for w in re.findall(r'[a-z]+', description_lower) if w not in stop_words and len(w) > 1]
    words.extend(regular_words)
    
    # Look for alphanumeric codes (like "amcm", "afterfx")
    alphanum_words = [w for w in re.findall(r'[a-z0-9]+', description_lower) if len(w) > 2 and w not in stop_words]
    words.extend(alphanum_words)
    
    # Remove duplicates while preserving order
    words = list(dict.fromkeys(words))
    
    matches = []
    
    for filename in all_files:
        filename_lower = filename.lower()
        filename_no_ext = os.path.splitext(filename_lower)[0]  # Remove extension for better matching
        score = 0
        matched_words = []
        
        # Check for keyword matches in full filename
        for word in words:
            if word in filename_lower:
                # Give higher score for exact matches
                if word in filename_no_ext.split('-') or word in filename_no_ext.split('_'):
                    score += 15  # Exact segment match
                else:
                    score += 10  # Substring match
                matched_words.append(word)
            # Check for partial matches (for compound words)
            elif any(word in part for part in re.split(r'[-_\s.]', filename_lower)):
                score += 5
                matched_words.append(f"{word}*")
            # Check if the word is at the start of the filename (common for codes)
            elif filename_lower.startswith(word):
                score += 12
                matched_words.append(f"^{word}")
        
        # Special handling for common descriptive patterns
        if 'animated' in description_lower and any(x in filename_lower for x in ['animated', 'anim']):
            score += 8
            matched_words.append('animated-pattern')
        
        if 'cartoon' in description_lower and any(x in filename_lower for x in ['cartoon', 'dog', 'character']):
            score += 8
            matched_words.append('cartoon-pattern')
        
        if 'steve' in description_lower and 'steve' in filename_lower:
            score += 15
            matched_words.append('steve-exact')
        
        # Bonus for multiple word matches
        if len(matched_words) > 1:
            score += 5 * len(matched_words)
        
        # Add similarity score using difflib for fuzzy matching
        similarity = difflib.SequenceMatcher(None, description_lower, filename_lower).ratio()
        score += similarity * 8
        
        # Boost score if description words make up significant portion of filename
        if words:
            coverage = len([w for w in words if w in filename_lower]) / len(words)
            score += coverage * 10
        
        if score > 0:
            matches.append({
                'filename': filename,
                'full_path': os.path.join(directory, filename),
                'score': score,
                'matched_words': matched_words,
                'coverage': coverage if words else 0
            })
    
    # Sort by score (highest first) and return top matches
    matches.sort(key=lambda x: x['score'], reverse=True)
    return matches[:limit]

def resolve_directory(alias: str) -> str:
    """
    Convert a human-friendly folder description into an absolute path.
    E.g. "jarvis folder on my desktop" → "C:\\Users\\You\\Desktop\\jarvis"
    """
    alias = alias.lower()
    home = os.path.expanduser("~")

    # 1) Determine the base directory
    if "desktop" in alias:
        base = os.path.join(home, "Desktop")
    elif "documents" in alias:
        base = os.path.join(home, "Documents")
    elif "downloads" in alias:
        base = os.path.join(home, "Downloads")
    elif "pictures" in alias or "photos" in alias:
        base = os.path.join(home, "Pictures")
    elif "videos" in alias:
        base = os.path.join(home, "Videos")
    elif "music" in alias:
        base = os.path.join(home, "Music")
    else:
        # Fallback: assume alias IS a path
        base = alias
        if os.path.exists(base):
            return base
        raise FileNotFoundError(f"Unknown base folder in '{alias}'")

    # 2) Extract the subfolder name (word(s) before "folder")
    #    e.g. "jarvis folder", or after "in"
    sub = None
    if "folder" in alias:
        # take the word(s) immediately preceding "folder"
        parts = alias.split("folder")[0].strip().split()
        if parts:
            sub = parts[-1]
    elif " in " in alias:
        # handle "files in jarvis" or similar
        parts = alias.split(" in ")
        if len(parts) > 1:
            # Get the part after "in"
            after_in = parts[-1].strip()
            # Remove common base folder words
            after_in = after_in.replace("my ", "").replace("the ", "").replace("desktop", "").replace("documents", "").replace("downloads", "").strip()
            if after_in:
                sub = after_in.split()[0]  # Take first word
    elif "jarvis" in alias:
        # Special case for jarvis folder
        sub = "jarvis"
    
    # If no subfolder mentioned → just return base
    if not sub:
        return base

    # 3) Fuzzy-match sub against actual subfolders under base
    try:
        entries = [e for e in os.listdir(base) if os.path.isdir(os.path.join(base, e))]
    except OSError:
        raise FileNotFoundError(f"Cannot list contents of {base}")

    matches = difflib.get_close_matches(sub, entries, n=1, cutoff=0.6)
    if matches:
        return os.path.join(base, matches[0])
    else:
        raise FileNotFoundError(f"No folder matching '{sub}' found under {base}")

def list_files(directory: str, pattern: str = "*", recursive: bool = False) -> List[str]:
    """
    List files in `directory` matching `pattern`.
    Set recursive=True to include subdirectories.
    Supports human-friendly directory names like 'jarvis folder on my desktop'.
    """
    # If directory isn't an absolute path, resolve it
    if not os.path.isabs(directory):
        directory = resolve_directory(directory)
    
    if recursive:
        path = os.path.join(directory, "**", pattern)
        return glob.glob(path, recursive=True)
    else:
        path = os.path.join(directory, pattern)
        return glob.glob(path)

def get_latest_file(directory: str, pattern: str = "*") -> Optional[str]:
    """
    Return the path to the most recently modified file in `directory`
    matching `pattern`, or None if no matches.
    Supports human-friendly directory names like 'jarvis folder on my desktop'.
    """
    # If directory isn't an absolute path, resolve it
    if not os.path.isabs(directory):
        directory = resolve_directory(directory)
    
    path = os.path.join(directory, pattern)
    files = glob.glob(path)
    if not files:
        return None
    return max(files, key=os.path.getmtime)

def get_latest_download() -> Optional[str]:
    """
    Convenience: return the most recent file in the user's Downloads folder.
    """
    downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    return get_latest_file(downloads)

def read_file(path: str) -> str:
    """Return the UTF-8 contents of the file at `path`."""
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def write_file(path: str, content: str) -> str:
    """
    Overwrite or create the file at `path` with `content`.
    Returns a confirmation message.
    Phase 5A: Protected by path safety check.
    """
    if not is_path_safe(path):
        raise PermissionError(f"🚫 Refusing to write outside safe roots: {path}")
    
    folder = os.path.dirname(path) or "."
    os.makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Wrote {len(content)} characters to {path}"

def delete_file(path: str) -> str:
    """
    Delete a file or an empty directory at `path`.
    Returns a confirmation message.
    Phase 5A: Protected by path safety check.
    """
    if not is_path_safe(path):
        raise PermissionError(f"🚫 Refusing to delete outside safe roots: {path}")
    
    if os.path.isdir(path):
        os.rmdir(path)
        return f"Removed directory {path}"
    else:
        os.remove(path)
        return f"Removed file {path}"

def move_file(src: str, dst: str) -> str:
    """
    Move or rename a file or folder from `src` to `dst`.
    Phase 5A: Protected by path safety check.
    """
    if not is_path_safe(src) or not is_path_safe(dst):
        raise PermissionError(f"🚫 Refusing to move outside safe roots: {src} → {dst}")
    
    os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
    shutil.move(src, dst)
    return f"Moved {src} to {dst}"

def open_application(command: str) -> str:
    """
    Launch an application or run a shell command.
    Returns stdout (if any) or exit code.
    """
    try:
        result = subprocess.run(
            command, shell=True,
            capture_output=True, text=True, timeout=60
        )
        if result.stdout:
            return result.stdout.strip()
        return f"Command exited with code {result.returncode}"
    except Exception as e:
        return f"Error running command: {e}"

# Semantic file search functionality
from typing import List, Dict
from file_index import file_index

def search_files(query: str, top_k: int = 5) -> List[Dict]:
    """
    Perform a semantic search across your file catalog.
    Returns up to top_k file records, each with:
      - path
      - name
      - extension
      - modified
      - score
    """
    try:
        # Check if file index client is available
        if not hasattr(file_index, 'client') or not file_index.client:
            print("⚠️ File search unavailable: OpenAI client not configured")
            return []
            
        # Ensure the file index is loaded
        if file_index.index is None:
            print("🔍 Loading file index...")
            file_index.load()
            
        # Check if loading was successful
        if file_index.index is None:
            print("⚠️ File search unavailable: Index could not be loaded")
            return []
        
        hits = file_index.query(query, top_k)
        # Return the raw dicts; agent_core will JSON‐serialize them
        return hits
    except Exception as e:
        print(f"❌ Error in search_files: {e}")
        return []

def interpret_file_intent(command: str) -> dict:
    """
    Analyze `command` and return a JSON dict with extracted file operation intent:
      {
        "is_file_command": bool,
        "action":    <string, e.g. "list", "open", "delete", "move", "search", "read">,
        "target":    <string or null, e.g. "jarvis folder on my desktop">,
        "pattern":   <string or null, e.g. "*.py">,
        "query":     <string or null, for semantic search>,
        "src":       <string or null, for move>,
        "dst":       <string or null, for move>,
        "confidence": <float, 0.0-1.0>
      }
    """
    import json
    import os
    
    # Load config for OpenAI
    try:
        with open("config.json") as f:
            config = json.load(f)
        api_key = config.get("openai_api_key")
        org_id = config.get("openai_organization")
        
        from openai import OpenAI
        if org_id:
            client = OpenAI(api_key=api_key, organization=org_id)
        else:
            client = OpenAI(api_key=api_key)
    except Exception as e:
        print(f"Failed to load OpenAI config for intent analysis: {e}")
        # Fallback to simple heuristics
        return _fallback_intent_analysis(command)
    
    # Use GPT to analyze the intent
    prompt = f"""
Analyze this user command and extract file operation intent. Return ONLY a valid JSON object:

Command: "{command}"

Return a JSON object with these exact keys:
{{
  "is_file_command": <true if this is any kind of file operation, false otherwise>,
  "action": <one of: "list", "open", "read", "delete", "move", "copy", "rename", "search", "create", "edit", "find", "workflow", null>,
  "target": <folder/directory mentioned like "desktop", "documents", "downloads", "jarvis folder", or null>,
  "pattern": <file pattern like "*.py", "*.pdf", specific filename, or null>,
  "query": <semantic search query for content-based search, or null>,
  "src": <source file/folder for move/copy operations, or null>,
  "dst": <destination folder for move/copy operations, or null>,
  "confidence": <float 0.0-1.0 indicating confidence this is a file operation>
}}

WORKFLOW DETECTION: If the command contains multi-step operations like "organize files", "archive logs every friday", "backup configs", "create folder and move files", set action to "workflow".

Examples:
- "list files in my documents" → {{"is_file_command": true, "action": "list", "target": "documents", "confidence": 0.95}}
- "show me PDFs from my econ 306 class" → {{"is_file_command": true, "action": "search", "query": "econ 306 pdf", "confidence": 0.9}}
- "open the cartoon file" → {{"is_file_command": true, "action": "open", "pattern": "cartoon", "confidence": 0.85}}
- "move note.txt to desktop" → {{"is_file_command": true, "action": "move", "pattern": "note.txt", "dst": "desktop", "confidence": 0.95}}
- "organize test files into a folder" → {{"is_file_command": true, "action": "workflow", "confidence": 0.9}}
- "backup all config files to archive" → {{"is_file_command": true, "action": "workflow", "confidence": 0.95}}
- "what's the weather like" → {{"is_file_command": false, "confidence": 0.0}}

IMPORTANT: Return ONLY the JSON object, no other text.
"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=300
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Parse the JSON response
        try:
            result = json.loads(result_text)
            
            # Validate required keys
            required_keys = ["is_file_command", "confidence"]
            if not all(key in result for key in required_keys):
                raise ValueError("Missing required keys")
            
            # Ensure confidence is a float
            result["confidence"] = float(result.get("confidence", 0.0))
            
            # Clean up null values
            for key in ["action", "target", "pattern", "query", "src", "dst"]:
                if key not in result:
                    result[key] = None
            
            # Phase 5A: Mark destructive actions that require confirmation
            result["requires_confirmation"] = result.get("action") in ("delete", "write", "move")
            
            return result
            
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Failed to parse GPT intent response: {e}")
            print(f"Raw response: {result_text}")
            return _fallback_intent_analysis(command)
    
    except Exception as e:
        print(f"Error calling GPT for intent analysis: {e}")
        return _fallback_intent_analysis(command)

def _fallback_intent_analysis(command: str) -> dict:
    """Fallback intent analysis using simple heuristics"""
    cmd_lower = command.lower()
    
    # File operation keywords
    file_keywords = [
        "list files", "show files", "find files", "search files", "open file", 
        "read file", "delete file", "move file", "copy file", "rename file",
        "create file", "edit file", "what files", "files in", "recent files"
    ]
    
    # Workflow keywords
    workflow_keywords = [
        "archive", "backup", "organize", "clean up", "batch", "multiple", 
        "all files", "every", "workflow", "then", "and then", "after that",
        "process all", "bulk", "sequence"
    ]
    
    # File extensions
    file_extensions = [".txt", ".py", ".json", ".pdf", ".doc", ".jpg", ".png", ".mp3", ".mp4"]
    
    # Check for workflow commands first
    is_workflow = any(keyword in cmd_lower for keyword in workflow_keywords)
    
    # Check if it's a file command
    is_file_cmd = (
        any(keyword in cmd_lower for keyword in file_keywords) or
        any(ext in cmd_lower for ext in file_extensions) or
        any(word in cmd_lower for word in ["directory", "folder", "desktop", "downloads", "documents"]) or
        is_workflow
    )
    
    if not is_file_cmd:
        return {
            "is_file_command": False,
            "action": None,
            "target": None,
            "pattern": None,
            "query": None,
            "src": None,
            "dst": None,
            "confidence": 0.0
        }
    
    # Extract action
    action = None
    if is_workflow:
        action = "workflow"
    elif any(word in cmd_lower for word in ["list", "show", "display"]):
        action = "list"
    elif any(word in cmd_lower for word in ["open", "launch"]):
        action = "open"
    elif any(word in cmd_lower for word in ["read", "view", "contents"]):
        action = "read"
    elif any(word in cmd_lower for word in ["delete", "remove", "trash"]):
        action = "delete"
    elif any(word in cmd_lower for word in ["move", "relocate"]):
        action = "move"
    elif any(word in cmd_lower for word in ["copy", "duplicate"]):
        action = "copy"
    elif any(word in cmd_lower for word in ["search", "find"]):
        action = "search"
    
    # Extract target folder
    target = None
    if "desktop" in cmd_lower:
        target = "desktop"
    elif "documents" in cmd_lower:
        target = "documents"
    elif "downloads" in cmd_lower:
        target = "downloads"
    elif "jarvis" in cmd_lower:
        target = "jarvis folder"
    
    return {
        "is_file_command": True,
        "action": action,
        "target": target,
        "pattern": None,
        "query": cmd_lower if action == "search" else None,
        "src": None,
        "dst": None,
        "confidence": 0.7,
        "requires_confirmation": action in ("delete", "write", "move")  # Phase 5A
    }

# Phase 4A: Content Summarization
import json
from openai import OpenAI

def summarize_text(text: str, max_sentences: int = 2) -> str:
    """
    Use GPT to compress `text` into up to max_sentences overview.
    """
    if not text or len(text.strip()) == 0:
        return "Empty file or no content available."
    
    # Load API key and create OpenAI client
    try:
        with open("config.json") as f:
            config = json.load(f)
        api_key = config.get("openai_api_key")
        org_id = config.get("openai_organization")
        
        if org_id:
            client = OpenAI(api_key=api_key, organization=org_id)
        else:
            client = OpenAI(api_key=api_key)
    except Exception as e:
        return f"Configuration error: {e}"
    
    # Truncate text if too long to avoid token limits
    if len(text) > 2000:
        text = text[:2000] + "..."
    
    prompt = (
        "Please summarize the following text in "
        f"at most {max_sentences} sentences. Focus on the main purpose, content type, and key information:\n\n"
        f"{text}"
    )
    
    try:
        resp = client.chat.completions.create(
            model="gpt-4-0613",
            messages=[
                {"role": "system", "content": "You are a concise summarizer who creates brief, informative summaries."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=max_sentences * 50
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating summary: {e}"

def get_file_preview(file_path: str, max_chars: int = 500) -> str:
    """
    Get a preview snippet from a file for summarization.
    Handles different file types appropriately.
    """
    try:
        # Get file extension
        _, ext = os.path.splitext(file_path.lower())
        
        # Handle different file types
        if ext in ['.txt', '.py', '.js', '.css', '.html', '.md', '.json', '.xml', '.csv']:
            # Text-based files - read directly
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(max_chars)
                return content
        elif ext in ['.pdf']:
            # For PDFs, return a placeholder - we'd need a PDF library for full extraction
            return f"PDF document: {os.path.basename(file_path)}"
        elif ext in ['.doc', '.docx']:
            # For Word docs, return a placeholder - we'd need a Word library for extraction
            return f"Word document: {os.path.basename(file_path)}"
        elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
            # For images, return metadata
            return f"Image file: {os.path.basename(file_path)}"
        else:
            # For other files, try to read as text but handle errors gracefully
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(max_chars)
                    return content if content.strip() else f"Binary or empty file: {os.path.basename(file_path)}"
            except:
                return f"Binary file: {os.path.basename(file_path)}"
    except Exception as e:
        return f"Could not read file: {e}"

def run_file_workflow(steps: list) -> str:
    """
    Execute a sequence of file-tool calls.
    Steps: list of {tool: str, args: dict}.
    Returns a summary of successes/errors.
    Enhanced to handle batch operations and file finding.
    """
    import json
    import os
    
    # Import TOOL_MAP to avoid circular import
    from agent_core import TOOL_MAP
    
    log = []
    found_files = []  # Store files found for later operations
    
    for i, step in enumerate(steps, start=1):
        tool = step.get("tool")
        args = step.get("args", {})
        fn = TOOL_MAP.get(tool)
        
        if not fn:
            log.append(f"{i}. ❌ Unknown tool '{tool}'")
            continue
            
        try:
            # Special handling for file listing tools to store results
            if tool in ["find_matching_files", "list_files_by_pattern"]:
                res = fn(**args)
                if isinstance(res, list):
                    # Handle different return formats
                    if tool == "find_matching_files":
                        # Extract file paths from dictionary results
                        found_files = [item.get('full_path', item.get('filename', str(item))) 
                                     if isinstance(item, dict) else str(item) 
                                     for item in res]
                    else:
                        # list_files_by_pattern returns file paths directly
                        found_files = res
                    
                    if found_files:
                        file_names = [os.path.basename(f) for f in found_files[:3]]
                        log.append(f"{i}. ✅ {tool} → Found {len(found_files)} files: {', '.join(file_names)}{'...' if len(found_files) > 3 else ''}")
                    else:
                        log.append(f"{i}. ⚠️ {tool} → No files found")
                else:
                    log.append(f"{i}. ❌ {tool} error: {res}")
                    found_files = []
            
            # Special handling for batch move operations
            elif tool == "move_file" and found_files and "src" not in args:
                # Move all found files to destination
                dst = args.get("dst") or args.get("destination")
                if not dst:
                    log.append(f"{i}. ❌ {tool} error: No destination specified")
                    continue
                
                moved_count = 0
                errors = []
                for file_path in found_files:
                    try:
                        # Ensure full path for move operation
                        if not os.path.isabs(file_path):
                            full_src = os.path.join(".", file_path)
                        else:
                            full_src = file_path
                        
                        # Create destination path
                        filename = os.path.basename(full_src)
                        full_dst = os.path.join(dst, filename)
                        
                        fn(full_src, full_dst)
                        moved_count += 1
                    except Exception as e:
                        errors.append(f"{os.path.basename(file_path)}: {e}")
                
                if moved_count > 0:
                    log.append(f"{i}. ✅ {tool} → Moved {moved_count} files to {dst}")
                    if errors and len(errors) <= 3:
                        log.append(f"    ⚠️ Errors: {'; '.join(errors)}")
                    elif errors:
                        log.append(f"    ⚠️ {len(errors)} files had errors")
                else:
                    log.append(f"{i}. ❌ {tool} error: No files moved")
                    if errors and len(errors) <= 3:
                        log.append(f"    Errors: {'; '.join(errors)}")
                
                found_files = []  # Clear after batch operation
            
            else:
                # Regular tool execution
                res = fn(**args)
                # Truncate long results for readability
                if isinstance(res, str) and len(res) > 100:
                    res_display = res[:100] + "..."
                else:
                    res_display = str(res)
                log.append(f"{i}. ✅ {tool} → {res_display}")
                
        except Exception as e:
            log.append(f"{i}. ❌ {tool} error: {e}")
    
    return "\n".join(log)


# Phase 5B: Docker-Based Sandboxed Web Automation

def open_page_sandbox(url: str) -> str:
    """Open a web page in the sandboxed browser."""
    try:
        response = requests.post(f"{SANDBOX_URL}/run", json={"tool": "open_page", "args": {"url": url}}, timeout=30)
        response.raise_for_status()
        result = response.json().get("result", "Page opened successfully")
        return result
    except Exception as e:
        return f"Error opening page: {str(e)}"

def click_sandbox(selector: str) -> str:
    """Click an element in the sandboxed browser using CSS selector."""
    try:
        response = requests.post(f"{SANDBOX_URL}/run", json={"tool": "click", "args": {"selector": selector}}, timeout=30)
        response.raise_for_status()
        result = response.json().get("result", "Element clicked successfully")
        return result
    except Exception as e:
        return f"Error clicking element: {str(e)}"

def extract_text_sandbox(selector: str) -> str:
    """Extract text from elements in the sandboxed browser."""
    try:
        response = requests.post(f"{SANDBOX_URL}/run", json={"tool": "extract_text", "args": {"selector": selector}}, timeout=30)
        response.raise_for_status()
        result = response.json().get("result", "No text found")
        return result
    except Exception as e:
        return f"Error extracting text: {str(e)}"

def fill_input_sandbox(selector: str, text: str) -> str:
    """Fill an input field in the sandboxed browser."""
    try:
        response = requests.post(f"{SANDBOX_URL}/run", json={"tool": "fill_input", "args": {"selector": selector, "text": text}}, timeout=30)
        response.raise_for_status()
        result = response.json().get("result", "Input filled successfully")
        return result
    except Exception as e:
        return f"Error filling input: {str(e)}"

def get_page_title_sandbox() -> str:
    """Get the current page title from the sandboxed browser."""
    try:
        response = requests.post(f"{SANDBOX_URL}/run", json={"tool": "get_page_title", "args": {}}, timeout=30)
        response.raise_for_status()
        result = response.json().get("result", "No title found")
        return result
    except Exception as e:
        return f"Error getting page title: {str(e)}"

def get_page_url_sandbox() -> str:
    """Get the current URL from the sandboxed browser."""
    try:
        response = requests.post(f"{SANDBOX_URL}/run", json={"tool": "get_page_url", "args": {}}, timeout=30)
        response.raise_for_status()
        result = response.json().get("result", "No URL found")
        return result
    except Exception as e:
        return f"Error getting page URL: {str(e)}"

def wait_for_element_sandbox(selector: str, timeout: int = 10) -> str:
    """Wait for an element to appear in the sandboxed browser."""
    try:
        response = requests.post(f"{SANDBOX_URL}/run", 
                               json={"tool": "wait_for_element", "args": {"selector": selector, "timeout": timeout}}, timeout=timeout+5)
        response.raise_for_status()
        result = response.json().get("result", "Element found")
        return result
    except Exception as e:
        return f"Error waiting for element: {str(e)}"

def get_element_attribute_sandbox(selector: str, attribute: str) -> str:
    """Get an attribute value from an element in the sandboxed browser."""
    try:
        response = requests.post(f"{SANDBOX_URL}/run", 
                               json={"tool": "get_element_attribute", "args": {"selector": selector, "attribute": attribute}}, timeout=30)
        response.raise_for_status()
        result = response.json().get("result", "No value found")
        return result
    except Exception as e:
        return f"Error getting attribute: {str(e)}"

def check_sandbox_health() -> str:
    """Check if the sandbox is running properly."""
    try:
        response = requests.get(f"{SANDBOX_URL}/health", timeout=10)
        response.raise_for_status()
        return "Sandbox is healthy and running"
    except Exception as e:
        return f"Sandbox health check failed: {str(e)}"

def reset_sandbox() -> str:
    """Reset the sandboxed browser session."""
    try:
        response = requests.post(f"{SANDBOX_URL}/reset", timeout=30)
        response.raise_for_status()
        result = response.json().get("result", "Sandbox reset successfully")
        return result
    except Exception as e:
        return f"Error resetting sandbox: {str(e)}"

def run_web_workflow(workflow: List[dict]) -> str:
    """
    Execute a sequence of web automation steps in the sandbox.
    
    Args:
        workflow: List of steps, each with {"tool": "function_name", "args": {...}}
    
    Returns:
        str: Result from the final step
    """
    result = ""
    for step in workflow:
        tool = step.get("tool")
        args = step.get("args", {})
        
        try:
            if tool == "open_page_sandbox":
                result = open_page_sandbox(**args)
            elif tool == "click_sandbox":
                result = click_sandbox(**args)
            elif tool == "extract_text_sandbox":
                result = extract_text_sandbox(**args)
            else:
                result = f"Unknown tool: {tool}"
                
            if "Error" in result:
                return f"Workflow failed at step {tool}: {result}"
                
        except Exception as e:
            return f"Workflow failed at step {tool}: {e}"
    
    return result

def open_website(
    query: Optional[str] = None,
    url: Optional[str] = None,
    top_k: int = 3,
    summary_only: bool = True
) -> Union[str, dict]:
    """
    1) If url given, use it. Else DDG-search(query) → top_k URLs.
    2) Try quick scrape: open_page_sandbox + extract_text_sandbox('body').
    3) If the result is too short (<500 chars) or not on-query-domain, FALLBACK:
       - Build a mini sandbox workflow to click through search results, then rescrape.
    4) Return summary (or full text) or a disambiguation dict if multiple candidates.
    """
    from search import search_web
    
    # 1) Gather candidate URLs
    candidates: List[str] = []
    
    # If URL is provided, use it directly (skip search entirely)
    if url and re.match(r"^https?://", url):
        candidates = [url]
        print(f"🌐 Using provided URL: {url}")
    elif query:
        # Auto-scope by domain if specific sites mentioned
        search_query = query
        if "nytimes" in query.lower() and "site:" not in query.lower():
            search_query = f"site:nytimes.com {query}"
        elif "wikipedia" in query.lower() and "site:" not in query.lower():
            search_query = f"site:wikipedia.org {query}"
            
        print(f"🔍 Searching for: '{search_query}'")
        try:
            results = search_web(search_query, max_results=top_k)
            
            # Parse URLs from search results
            for line in results.splitlines():
                # Look for URLs in the search results
                url_match = re.search(r'https?://[^\s\)]+', line)
                if url_match:
                    found_url = url_match.group().rstrip('.,;)')
                    if found_url not in candidates:
                        candidates.append(found_url)
                if len(candidates) >= top_k:
                    break
                    
        except Exception as e:
            return f"Search failed: {e}"
    else:
        return "No query or URL provided"

    if not candidates:
        return f"No search results found for '{query}'"

    # 2) Disambiguation if needed (only for search results, not direct URLs)
    if len(candidates) > 1 and not url:
        return {"needs_disambiguation": True, "options": candidates}

    chosen = candidates[0]
    print(f"🌐 Opening: {chosen}")

    # 3) Quick scrape attempt
    try:
        open_page_sandbox(chosen)
        full_text = extract_text_sandbox("body") or ""
        
        # If too short or clearly unrelated, fallback to search UI workflow
        if len(full_text) < 500 or query.lower() not in full_text.lower():
            print(f"⚠️ Quick scrape insufficient ({len(full_text)} chars), trying search UI fallback...")
            
            # Build a sandbox workflow to click the first result in the search UI
            workflow = [
                {"tool": "open_page_sandbox", "args": {"url": f"https://duckduckgo.com/?q={query.replace(' ', '+')}"}},
                {"tool": "click_sandbox", "args": {"selector": ".result__a"}},  # first link
                {"tool": "extract_text_sandbox", "args": {"selector": "body"}}
            ]
            
            try:
                fallback_text = run_web_workflow(workflow)
                if fallback_text and len(fallback_text) > len(full_text):
                    full_text = fallback_text
                    print(f"✅ Fallback workflow successful ({len(full_text)} chars)")
                else:
                    print(f"⚠️ Fallback workflow didn't improve results")
            except Exception as e:
                print(f"❌ Fallback workflow failed: {e}")
                
    except Exception as e:
        return f"Failed to scrape {chosen}: {e}"

    # 4) Return summary or raw
    if summary_only and full_text:
        try:
            return summarize_text(full_text, max_sentences=5)
        except Exception as e:
            return f"Text extracted but summarization failed: {e}\n\nRaw text (first 1000 chars):\n{full_text[:1000]}..."
    else:
        return full_text or "No content extracted"


def _extract_main_content() -> str:
    """Helper function to extract main content using multiple selector strategies"""
    content_selectors = [
        ".mw-content-text",  # MediaWiki/Fandom main content
        "#mw-content-text",  # Alternative MediaWiki selector
        ".content",          # Common content class
        "#content",          # Common content ID
        "main",             # HTML5 main element
        "article",          # HTML5 article element
        "body"              # Fallback to body
    ]
    
    for content_selector in content_selectors:
        try:
            extracted_text = extract_text_sandbox(content_selector)
            if extracted_text and "Error" not in extracted_text and "No text found" not in extracted_text and len(extracted_text.strip()) > 50:
                return extracted_text
        except Exception:
            continue
    
    return "No readable content found"

def _analyze_content_with_ai(content: str, url: str, original_query: str, question: Optional[str] = None) -> str:
    """Use OpenAI to analyze web content and provide intelligent summaries or answers"""
    try:
        # Load OpenAI configuration
        with open("config.json") as f:
            config = json.load(f)
        api_key = config.get("openai_api_key")
        
        if not api_key:
            # Fallback to truncated content if no AI available
            if len(content) > 3000:
                content = content[:3000] + "\n\n[Content truncated - showing first 3000 characters]"
            return f"Content from {url}:\n\n{content}"
        
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        # Prepare the prompt based on whether there's a specific question
        if question:
            system_prompt = (
                "You are an AI assistant that analyzes web content to answer specific questions. "
                "Read the provided web content carefully and answer the user's question accurately. "
                "If the information isn't in the content, say so clearly. "
                "Provide specific details like names, dates, episodes, etc. when available."
            )
            user_prompt = f"Question: {question}\n\nWeb content from {url}:\n{content[:8000]}"
        else:
            system_prompt = (
                "You are an AI assistant that summarizes web content intelligently. "
                "Create a comprehensive but concise summary that captures the key information. "
                "Focus on the main subject, important details, and relevant facts. "
                "Structure your response clearly with the most important information first."
            )
            user_prompt = f"Please summarize this web content from {url}:\n{content[:8000]}"
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=1000,
            temperature=0.1
        )
        
        ai_response = response.choices[0].message.content
        
        # Format the response nicely
        if question:
            return f"🔍 Answer from {url}:\n\n{ai_response}"
        else:
            return f"📄 Summary of {url}:\n\n{ai_response}"
            
    except Exception as e:
        # Fallback to raw content if AI analysis fails
        print(f"⚠️ AI analysis failed: {e}")
        if len(content) > 3000:
            content = content[:3000] + "\n\n[Content truncated - showing first 3000 characters]"
        return f"Content from {url}:\n\n{content}"

def interpret_intent(command: str) -> dict:
    """
    Classify any user command into one of:
      - chat               (straight LLM response)
      - web_search         (duckduckgo text search)
      - web_navigation     (sandboxed browser navigation/scraping)
      - file_op            (single file actions: list/read/delete/etc.)
      - file_workflow      (multi-step file workflows)
      - google_docs        (create/write/export Google Docs)
      - calendar           (schedule/cancel events)
    and extract slots needed for each.

    Returns a dict:
    {
      "category": str,               # one of the above
      "action":   str or null,       # e.g. "search", "open", "delete", "list_files", "create_doc", ...
      "query":    str or null,       # for web_search or web_navigation
      "url":      str or null,       # if direct URL given
      "selector": str or null,       # for web_navigation scraping
      "target":   str or null,       # folder alias or file description
      "pattern":  str or null,       # glob for file_ops
      "steps":    list or null,      # for workflows
      "requires_confirmation": bool  # if Jarvis should ask "Proceed?"
    }
    """
    try:
        # Load OpenAI configuration
        with open("config.json") as f:
            config = json.load(f)
        api_key = config.get("openai_api_key")
        org_id = config.get("openai_organization")
        
        from openai import OpenAI
        if org_id:
            client = OpenAI(api_key=api_key, organization=org_id)
        else:
            client = OpenAI(api_key=api_key)
    except Exception as e:
        print(f"Failed to load OpenAI config for intent analysis: {e}")
        # Fallback to chat if config fails
        return {
            "category": "chat",
            "action": None, "query": None, "url": None,
            "selector": None, "target": None, "pattern": None,
            "steps": None, "requires_confirmation": False
        }

    system_prompt = """
You are an intent parser. Given a user's natural language request, output JSON with:
- category: one of [chat, web_search, web_navigation, web_research, file_op, file_workflow, google_docs, calendar]
- action: the specific operation (e.g. "search", "open_page", "list_files", "delete_file", "create_google_doc", "schedule_event")
- query: string for web_search, web_navigation, or web_research
- url: if user gave a URL
- selector: CSS selector for scraping
- target: folder alias or file description for file ops
- pattern: glob pattern for file listing
- steps: array of {tool:..., args:...} for any multi-step workflow
- requires_confirmation: true if this action is destructive or needs your OK

CATEGORY GUIDELINES:
- chat: General conversation, questions you can answer with your knowledge, casual talk
- web_search: When user asks for quick web search results (search for, look up, google)
- web_navigation: When user wants to browse/scrape specific websites or URLs
- web_research: When user wants in-depth research with AI analysis (research, investigate, find information about)
- file_op: Single file operations (list, read, delete, move one file)
- file_workflow: Multi-step file operations (organize folders, batch operations)
- google_docs: Creating, editing, or managing Google Docs
- calendar: Scheduling, viewing, or managing calendar events

KNOWLEDGE GAP DETECTION:
If the user asks about specific people, events, or facts that are:
- Very recent (after your training cutoff)
- Highly specific (like character deaths in specific franchises)
- Obscure or niche topics
- Technical documentation for specific software
Set category to "web_search", "web_navigation", or "web_research" and requires_confirmation to true.

EXAMPLES:
- "What's the weather?" → {"category": "chat", "requires_confirmation": false}
- "Research Remy Erdman's death in VGHW" → {"category": "web_research", "query": "Remy Erdman VGHW death", "requires_confirmation": true}
- "Search for latest AI news" → {"category": "web_search", "query": "latest AI news", "requires_confirmation": false}
- "Go to the VGHW fandom page and extract the Origins section" → {"category": "web_navigation", "url": "VGHW fandom", "selector": "#Origins", "requires_confirmation": true}
- "Open google.com" → {"category": "web_navigation", "url": "https://google.com", "requires_confirmation": false}
- "List files in my documents" → {"category": "file_op", "action": "list_files", "target": "documents"}
- "Create a Google Doc about my project" → {"category": "google_docs", "action": "create_doc", "requires_confirmation": false}

Return ONLY valid JSON, no other text.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4-0613",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": command}
            ],
            temperature=0.1,
            max_tokens=500
        )
        
        text = response.choices[0].message.content.strip()
        intent = json.loads(text)
        
        # Ensure all required fields exist
        intent.setdefault("category", "chat")
        intent.setdefault("action", None)
        intent.setdefault("query", None)
        intent.setdefault("url", None)
        intent.setdefault("selector", None)
        intent.setdefault("target", None)
        intent.setdefault("pattern", None)
        intent.setdefault("steps", None)
        intent.setdefault("requires_confirmation", False)
        
        # Step 2C: Mark research-style queries for confirmation
        if intent["category"] in ("web_search", "web_navigation", "web_research"):
            # Ask for permission on any research-type verbs
            lower = command.lower()
            research_keywords = [
                "research", "investigate", "find out", "dig into", "look into",
                "explore", "examine", "study", "analyze", "discover"
            ]
            if any(keyword in lower for keyword in research_keywords):
                intent["requires_confirmation"] = True
        
        # Step 2: Improve intent parsing for fandom queries
        if intent["category"] in ("web_search", "web_navigation", "web_research"):
            query = intent.get("query", "")
            lower_query = query.lower()
            lower_command = command.lower()
            
            # Detect fandom-specific queries and auto-add site restrictions
            if ("fandom" in lower_query or "vghw" in lower_query or 
                "fandom" in lower_command or "vghw" in lower_command):
                # If not already site-restricted, add site filter
                if "site:" not in query:
                    if "vghw" in lower_query or "vghw" in lower_command:
                        intent["query"] = f"site:vghw.fandom.com {query}"
                    else:
                        # General fandom query - let the search decide
                        intent["query"] = f"{query} fandom wiki"
                    
                    print(f"🎯 Enhanced fandom query: {intent['query']}")
        
        return intent
        
    except Exception as e:
        print(f"Error in interpret_intent: {e}")
        # Fallback to chat if parsing fails
        return {
            "category": "chat",
            "action": None, "query": None, "url": None,
            "selector": None, "target": None, "pattern": None,
            "steps": None, "requires_confirmation": False
        }

