# Angular SLM (Small Language Model) 🚀

An end-to-end pipeline and codebase to build a specialized, open-source AI assistant for modern **Angular (v18, v19, v20+)** development.

This project covers the entire lifecycle of creating an AI coder: programmatically scraping high-quality standalone, signal-based Angular repositories, curating and compiling the dataset, performing QLoRA fine-tuning using Apple MLX, and converting the finished model to GGUF for local execution in **Ollama** and **VS Code**.

---

## ⚡ Highlights & Key Features

- **Modern Angular Codebases Only**: Specifically targets and filters for modern Angular architecture (Signals, Standalone components, control flow `@if`/`@for`, and RxJS-to-Signal interop).
- **Data Scraping & Curation**: Programmatic scrapers with GitHub API integration, rate-limit avoidance, and `package.json` validation to ensure only Angular 18+ repos are parsed.
- **Hardware-Accelerated QLoRA**: Configured specifically for Apple Silicon GPUs using Apple's MLX Framework.
- **IDE Ready**: Full workflow to convert adapter weights to GGUF and import them into Ollama for seamless integration into editors like Cursor and VS Code.

---

## 📁 Repository Structure

```text
├── phase_scraper.py               # Programmatic Github scraper & repo cloner
├── dataset_compiler.py            # TypeScript/HTML filtering and JSONL compiler
├── repositories.json              # List of validated target Angular codebases
├── requirements.txt               # Python package dependencies
├── Modelfile                      # Ollama configuration blueprint
├── huggingface_publishing_guide.md# Guide for merging, GGUF conversion, and publishing
└── README.md                      # This guide
```

---

## 🛠️ Getting Started & Setup

### 1. Prerequisites
Ensure you have Python 3.10+ and a machine with Apple Silicon (M1/M2/M3/M4) if training locally.

```bash
# Clone this repository
git clone https://github.com/dhananjayve/angular_slm.git
cd angular_slm

# Set up virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## 🛰️ The Data Pipeline

### Step 1: Scrape & Discover Repositories
The scraper searches GitHub for public repositories matching keywords like `angular signals` and validations for `@angular/core >= 18.0.0` in `package.json`.

```bash
python phase_scraper.py --github-token YOUR_GITHUB_TOKEN --max-repos 600
```
This stores repos inside a local `/data` directory and logs targets in `repositories.json`.

### Step 2: Compile the Dataset
The compiler crawls the cloned repositories, discards legacy code (e.g. references to `NgModule`), filters out files over 20KB to save memory, and formats TypeScript/HTML components into standard ChatML JSONL format.

```bash
python dataset_compiler.py --input-dir ./data --output-file dataset.jsonl
```

---

## 🏋️ Fine-Tuning with Apple MLX QLoRA

The model is fine-tuned on the base **`Qwen2.5-Coder-1.5B-Instruct-4bit`** model (or standard FP16) for 12,000 iterations using the MLX framework.

To start or resume fine-tuning, run:
```bash
python -m mlx_lm.lora \
  --model mlx-community/Qwen2.5-Coder-1.5B-Instruct-4bit \
  --train \
  --data ./data \
  --iters 12000 \
  --steps-per-eval 200 \
  --val-batches 25 \
  --learning-rate 1e-5 \
  --lora-layers 16 \
  --adapter-path adapters
```

---

## 🔄 Model Merging & GGUF Conversion

Once training is complete, your adapters need to be fused with the base model and compiled into a single `.gguf` file to run locally:

### 1. Fuse the Adapters
```bash
python -m mlx_lm fuse \
  --model Qwen/Qwen2.5-Coder-1.5B-Instruct \
  --adapter-path adapters \
  --save-path merged-angular-fp16
```

### 2. Convert and Quantize with `llama.cpp`
```bash
# Clone llama.cpp
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp
pip install -r requirements.txt

# Configure and compile llama-quantize
cmake -B build
cmake --build build --config Release -t llama-quantize

# Convert weights to GGUF
python convert_hf_to_gguf.py ../merged-angular-fp16 --outfile ../angular-qwen-1.5b.gguf

# Quantize GGUF to 4-bit (fast execution)
./build/bin/llama-quantize ../angular-qwen-1.5b.gguf ../angular-qwen-1.5b-q4_k_m.gguf Q4_K_M
```

*For complete Hugging Face and Ollama publishing details, see [huggingface_publishing_guide.md](huggingface_publishing_guide.md).*

---

## 🔌 Running the Model in VS Code & Cursor

### 1. Import to Ollama
Create a `Modelfile` inside your model folder:
```dockerfile
FROM ./angular-qwen-1.5b-q4_k_m.gguf

TEMPLATE """<|im_start|>system
{{ .System }}<|im_end|>
<|im_start|>user
{{ .Prompt }}<|im_end|>
<|im_start|>assistant
"""

SYSTEM "You are an elite software architect specialized in Angular 20+ and modern TypeScript. You only generate pure, bug-free standalone implementations."

PARAMETER temperature 0.1
PARAMETER stop "<|im_start|>"
PARAMETER stop "<|im_end|>"
```

Build the model:
```bash
ollama create angular-coder -f Modelfile
```

### 2. Configure Continue.dev Extension
Add the local model to your `~/.continue/config.json` settings:

```json
{
  "models": [
    {
      "title": "Angular Coder (Chat)",
      "provider": "ollama",
      "model": "angular-coder"
    }
  ],
  "tabAutocompleteModel": {
    "title": "Angular Coder (Autocomplete)",
    "provider": "ollama",
    "model": "angular-coder"
  }
}
```

---

## 📄 License
This repository is licensed under the MIT License. See [LICENSE](LICENSE) for details.
