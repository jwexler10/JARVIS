# sandbox/server.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import uvicorn
import time

app = FastAPI()

# Initialize headless Chrome once
chrome_opts = Options()
chrome_opts.add_argument("--headless")
chrome_opts.add_argument("--no-sandbox")
chrome_opts.add_argument("--disable-dev-shm-usage")
chrome_opts.add_argument("--disable-gpu")
chrome_opts.add_argument("--window-size=1920,1080")
driver = None

def get_driver():
    global driver
    if driver is None:
        driver = webdriver.Chrome(options=chrome_opts)
    return driver

class Command(BaseModel):
    tool: str
    args: Dict[str, Any]

@app.post("/run")
def run(command: Command):
    try:
        tool = command.tool
        args = command.args
        driver = get_driver()
        
        # Only allow a fixed set of safe operations:
        if tool == "open_page":
            url = args["url"]
            driver.get(url)
            return {"result": f"Opened {url}", "title": driver.title}
        
        elif tool == "click":
            selector = args["selector"]
            wait = WebDriverWait(driver, 10)
            element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
            element.click()
            return {"result": f"Clicked {selector}"}
        
        elif tool == "extract_text":
            selector = args["selector"]
            wait = WebDriverWait(driver, 10)
            element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            return {"result": element.text}
        
        elif tool == "get_page_title":
            return {"result": driver.title}
        
        elif tool == "get_page_url":
            return {"result": driver.current_url}
        
        elif tool == "fill_input":
            selector = args["selector"]
            text = args["text"]
            wait = WebDriverWait(driver, 10)
            element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            element.clear()
            element.send_keys(text)
            return {"result": f"Filled input {selector} with text"}
        
        elif tool == "screenshot":
            # Take a screenshot and return base64 data
            screenshot_data = driver.get_screenshot_as_base64()
            return {"result": "Screenshot taken", "data": screenshot_data}
        
        elif tool == "wait_for_element":
            selector = args["selector"]
            timeout = args.get("timeout", 10)
            wait = WebDriverWait(driver, timeout)
            element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            return {"result": f"Element {selector} found"}
        
        elif tool == "get_element_attribute":
            selector = args["selector"]
            attribute = args["attribute"]
            wait = WebDriverWait(driver, 10)
            element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            value = element.get_attribute(attribute)
            return {"result": value}
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown tool: {tool}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "healthy", "driver_active": driver is not None}

@app.post("/reset")
def reset_driver():
    global driver
    if driver:
        driver.quit()
        driver = None
    return {"result": "Driver reset"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
