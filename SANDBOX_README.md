# Phase 5B: Docker-Based Sandbox for Web/OS Automation

## Overview

Phase 5B introduces a secure Docker-based sandbox that allows Jarvis to safely perform web automation tasks without touching your host system directly. All web browsing, clicking, form filling, and content extraction happens inside an isolated headless Chrome browser running in a container.

## Features

- **Isolated Web Browsing**: Headless Chrome running in Docker container
- **Safe Web Automation**: No direct access to your host system
- **Full Browser Control**: Open pages, click elements, fill forms, extract text
- **CSS Selector Support**: Precise element targeting
- **Error Handling**: Robust error handling and timeout management
- **Health Monitoring**: Built-in health checks and driver reset capability

## Quick Setup

1. **Prerequisites**: Ensure Docker Desktop is installed and running
2. **Build & Run**: Execute `.\run_sandbox.ps1` (PowerShell) or `run_sandbox.bat` (Command Prompt)
3. **Test**: Run `python test_sandbox.py` to verify everything works
4. **Use**: Start talking to Jarvis about web automation tasks!

## Sandbox Tools Available

### Core Navigation
- `open_page_sandbox(url)` - Open any website
- `get_page_title_sandbox()` - Get current page title
- `get_page_url_sandbox()` - Get current URL

### Element Interaction
- `click_sandbox(selector)` - Click elements using CSS selectors
- `fill_input_sandbox(selector, text)` - Fill form inputs
- `extract_text_sandbox(selector)` - Extract text from elements
- `wait_for_element_sandbox(selector, timeout)` - Wait for dynamic content
- `get_element_attribute_sandbox(selector, attribute)` - Get element attributes

### Maintenance
- `check_sandbox_health()` - Verify sandbox is running
- `reset_sandbox()` - Reset browser if it becomes unresponsive

## Example Usage

```
You: "Open google.com in the sandbox"
Jarvis: Opens Google's homepage in the isolated browser

You: "Search for 'Python tutorials'"
Jarvis: Fills the search box and clicks search

You: "Click the first result"
Jarvis: Clicks the first search result link

You: "Extract the page title"
Jarvis: Returns the title of the opened page
```

## How It Works

1. **Docker Container**: Runs Ubuntu with headless Chrome and Xvfb (virtual display)
2. **FastAPI Server**: Exposes web automation endpoints on port 8000
3. **HTTP API**: Jarvis communicates with sandbox via HTTP requests
4. **Isolation**: Container has read-only access to your project folder only

## Security Benefits

- ✅ **Host Protection**: Malicious websites can't access your files
- ✅ **Process Isolation**: Browser crashes don't affect Jarvis
- ✅ **Network Isolation**: Configurable network restrictions
- ✅ **Resource Limits**: Container prevents resource exhaustion
- ✅ **Easy Reset**: Completely reset browser state anytime

## Architecture

```
[Jarvis Host] → HTTP → [Docker Container]
                           ├── FastAPI Server (port 8000)
                           ├── Headless Chrome
                           ├── Xvfb (virtual display)
                           └── Selenium WebDriver
```

## Container Management

- **Start**: `docker start jarvis-sb`
- **Stop**: `docker stop jarvis-sb`  
- **Logs**: `docker logs jarvis-sb`
- **Health**: `curl http://localhost:8000/health`
- **Remove**: `docker rm jarvis-sb` (after stopping)

## Troubleshooting

### Sandbox Not Responding
```powershell
# Check if container is running
docker ps -f name=jarvis-sb

# Check container logs
docker logs jarvis-sb

# Restart container
docker restart jarvis-sb
```

### Browser Issues
```
You: "Reset the sandbox"
Jarvis: Resets the browser driver and clears state
```

### Docker Issues
- Ensure Docker Desktop is running
- Check available disk space
- Verify port 8000 is not in use
- Try rebuilding: `docker build -t jarvis-sandbox sandbox/`

## Development

### Adding New Tools
1. Add endpoint to `sandbox/server.py`
2. Create wrapper function in `tools.py`
3. Add schema to `agent_core.py`
4. Update tool mapping

### Security Considerations
- Container runs with minimal privileges
- Only approved tools are exposed
- Read-only mount for project files
- Network policies can be added

## Next Steps

Future enhancements could include:
- Multiple browser instances
- Screenshot capabilities  
- File download handling
- Network traffic monitoring
- Browser performance metrics

The sandbox provides a solid foundation for safe web automation while keeping Jarvis's host system secure.
