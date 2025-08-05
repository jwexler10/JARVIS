from tools import open_page_sandbox, get_page_title_sandbox, get_page_url_sandbox, extract_text_sandbox

print("=== SANDBOX TEST ===")
print("1. Opening Google...")
print(open_page_sandbox("https://www.google.com"))
print("2. Getting title...")
print(get_page_title_sandbox())
print("3. Getting URL...")
print(get_page_url_sandbox())
print("4. Extracting search box...")
t = extract_text_sandbox("input[name=\"q\"]")
print((t[:50] + "...") if len(t) > 50 else t)
print("=== TEST COMPLETE ===")
