import re

def find_buttons(html_file):
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
    print("--- All Button-like Tags ---")
    # Find buttons
    buttons = re.findall(r'<(button|div|span)[^>]*aria-label="([^"]*)"[^>]*>', content)
    for tag, label in buttons:
        print(f"Tag: <{tag}>, Label: '{label}'")

    # Find text in brackets/tags
    texts = re.findall(r'>([^<]{1,50})<', content)
    print("\n--- Potential Text Labels ---")
    keyword_matches = []
    for text in texts:
        t = text.strip()
        if any(keyword in t for keyword in ["소스", "추가", "파일", "업로드", "Source", "Add", "Upload"]):
            keyword_matches.append(t)
    
    for m in sorted(list(set(keyword_matches))):
        print(f"Text found: '{m}'")

    print("\n--- All Inputs ---")
    inputs = re.findall(r'<input[^>]*type="([^"]*)"[^>]*>', content)
    for typ in inputs:
        print(f"Input Type: '{typ}'")

if __name__ == "__main__":
    find_buttons('notebooklm_debug.html')
