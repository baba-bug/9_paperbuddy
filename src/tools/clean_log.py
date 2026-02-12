import os
import re
import argparse

def clean_log(input_path, output_path=None):
    """
    Remove the raw file reference sections (<details>...📎 本次分析的原始素材...</details>) from the log.
    """
    if not output_path:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_clean{ext}"

    if not os.path.exists(input_path):
        print(f"❌ Input file not found: {input_path}")
        return

    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Regex to match the <details> block containing "📎 本次分析的原始素材"
    # DOTALL flag allows . to match newlines
    pattern = re.compile(r'<details>\s*<summary>📎 本次分析的原始素材</summary>.*?</details>', re.DOTALL)
    
    cleaned_content = re.sub(pattern, "", content)
    
    # Remove excessive newlines that might be left behind (optional polish)
    cleaned_content = re.sub(r'\n{3,}', '\n\n', cleaned_content)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(cleaned_content)
    
    print(f"✅ Clean log saved to: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Remove raw file references from Research_Log.md")
    parser.add_argument("file", help="Path to the Research_Log.md file")
    args = parser.parse_args()
    
    clean_log(args.file)
