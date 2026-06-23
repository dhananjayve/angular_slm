import json
import os
import random

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_DIR = os.path.join(BASE_DIR, "my_angular_codebase")
OUTPUT_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_TRAIN = os.path.join(OUTPUT_DIR, "train.jsonl")
OUTPUT_VALID = os.path.join(OUTPUT_DIR, "valid.jsonl")

# Framework configuration tags
LEGACY_MARKERS = ["@NgModule", "BrowserModule", "RouterModule.forRoot"]
MODERN_MARKERS = ["standalone: true", "signal(", "computed(", "effect(", "provideZonelessChangeDetection", "httpResource"]

def is_strictly_modern(content, file_ext):
    """Enforces modern Angular styles for TypeScript files."""
    if file_ext != ".ts":
        return True # Docs and HTML templates pass through
        
    # Drop files explicitly containing legacy module architectures
    if any(marker in content for marker in LEGACY_MARKERS):
        return False
        
    return True

def create_prompt(file_name, file_ext, content):
    """Formats raw source files into Qwen Chat ML structure."""
    if file_ext == ".ts":
        role_desc = "Modern TypeScript logic and reactive state using Angular Signals"
    elif file_ext == ".html":
        role_desc = "Modern Angular template layout utilizing semantic control flows (@if, @for)"
    elif file_ext == ".md":
        role_desc = "Official engineering specifications and conceptual architectural definitions"
    else:
        role_desc = "Angular framework infrastructural configurations"

    # Strict structural schema for Qwen2.5-Coder instruction tuning
    prompt = {
        "text": f"<|im_start|>system\nYou are an elite software architect specialized in Angular 20+ and modern TypeScript. "
                f"You only generate pure, bug-free implementations optimized for {role_desc}.<|im_end|>\n"
                f"<|im_start|>user\nAnalyze and provide complete production-ready source contents for: {file_name}<|im_end|>\n"
                f"<|im_start|>assistant\n```{file_ext.replace('.', '')}\n{content}\n```<|im_end|>"
    }
    return prompt

def compile_dataset():
    if not os.path.exists(SOURCE_DIR):
        print(f"❌ Error: Source directory '{SOURCE_DIR}' not found. Please run your scraper first.")
        return

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    dataset = []
    skipped_legacy = 0
    total_processed = 0

    print("🔄 Commencing compilation and syntax mapping across 100 repositories...")

    MAX_FILE_SIZE_BYTES = 20 * 1024  # 20 KB limit to prevent OOM errors

    for root, _, files in os.walk(SOURCE_DIR):
        for file in files:
            file_ext = os.path.splitext(file)[1].lower()
            
            # Target only core development layers; drop tests, lockfiles, and configs
            if file_ext in [".ts", ".html", ".md", ".json"] and not file.endswith((".spec.ts", "-lock.json")):
                file_path = os.path.join(root, file)
                
                # Filter out files that are too large to protect training memory
                try:
                    if os.path.getsize(file_path) > MAX_FILE_SIZE_BYTES:
                        skipped_legacy += 1  # Counted as skipped/filtered
                        continue
                except Exception:
                    continue
                
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read().strip()
                        
                    if not content:
                        continue
                        
                    # Filter step
                    if not is_strictly_modern(content, file_ext):
                        skipped_legacy += 1
                        continue

                    # Structure the prompt
                    prompt_entry = create_prompt(file, file_ext, content)
                    dataset.append(prompt_entry)
                    total_processed += 1
                    
                except Exception as e:
                    print(f"⚠️ Error reading file {file}: {e}")

    print(f"\n📊 Extraction Summary:")
    print(f"   - Total valid files parsed: {total_processed}")
    print(f"   - Legacy files rejected: {skipped_legacy}")

    if not dataset:
        print("❌ Dataset generation failed: No valid files matched criteria.")
        return

    # Shuffle dataset to ensure a balanced mix of docs, templates, and TS files
    random.seed(42)
    random.shuffle(dataset)

    # 95/5 Data Distribution split for custom fine-tuning
    split_idx = int(len(dataset) * 0.95)
    train_data = dataset[:split_idx]
    valid_data = dataset[split_idx:]

    # Write training JSONL dataset
    with open(OUTPUT_TRAIN, "w", encoding="utf-8") as f:
        for entry in train_data:
            f.write(json.dumps(entry) + "\n")

    # Write validation JSONL dataset
    with open(OUTPUT_VALID, "w", encoding="utf-8") as f:
        for entry in valid_data:
            f.write(json.dumps(entry) + "\n")

    print(f"\n✅ Generation complete! Output targets:")
    print(f"   - Training: {OUTPUT_TRAIN} ({len(train_data)} tokensets)")
    print(f"   - Validation: {OUTPUT_VALID} ({len(valid_data)} tokensets)")

if __name__ == "__main__":
    compile_dataset()
