# Publishing Your Fine-Tuned Angular Model to Hugging Face & Ollama

This guide walks you through the steps to open-source your model, host it on Hugging Face, and make it available for the community to run locally via `mlx_lm`, standard `transformers`, or Ollama.

---

## 🗺️ Distribution Strategies

You have three main options for sharing your fine-tuned model:

| Option | Distribution Format | File Size | Target Audience |
| :--- | :--- | :--- | :--- |
| **1. LoRA Adapters Only** | Upload `adapters/` folder directly to Hugging Face | ~80 MB | MLX users (Apple Silicon) |
| **2. Merged MLX Model** | Merge adapters with base model and upload | ~1.2 GB | MLX users looking for one-click setup |
| **3. Standard GGUF / Ollama** | Merge adapters, convert to GGUF, and publish | ~1.2 GB | All developers (Windows, Linux, Mac) via Ollama, LM Studio, etc. |

---

## 🛠️ Step-by-Step Instructions

### Option 1: Publish LoRA Adapters (Lightest & Easiest)
This uploads just your adapter weights. Users load the base model from Hugging Face and apply your adapter at runtime.

1. Install the Hugging Face CLI:
   ```bash
   pip install huggingface_hub
   ```
2. Log in to Hugging Face (generate a write-access token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)):
   ```bash
   huggingface-cli login
   ```
3. Create your model repository:
   ```bash
   huggingface-cli repo create angular-qwen-adapters --type model
   ```
4. Upload your `adapters` directory contents:
   ```bash
   huggingface-cli upload username/angular-qwen-adapters ./adapters .
   ```

**How others will use it:**
```python
from mlx_lm import load, generate

model, tokenizer = load(
    "mlx-community/Qwen2.5-Coder-1.5B-Instruct-4bit",
    adapter_path="username/angular-qwen-adapters"
)
```

---

### Option 2: Merge and Publish a Standalone MLX Model
This merges the adapter weights into the base model so users don't have to specify an adapter path.

1. **Merge the weights (Ensure your `pyenv` environment is active):**
   ```bash
   python -m mlx_lm fuse \
     --model mlx-community/Qwen2.5-Coder-1.5B-Instruct-4bit \
     --adapter-path adapters \
     --save-path merged-angular-mlx
   ```
2. **Create the repository on Hugging Face:**
   ```bash
   huggingface-cli repo create angular-qwen-1.5b-mlx --type model
   ```
3. **Upload the merged model:**
   ```bash
   huggingface-cli upload username/angular-qwen-1.5b-mlx ./merged-angular-mlx .
   ```

**How others will use it:**
```bash
mlx_lm.generate --model username/angular-qwen-1.5b-mlx --prompt "Write a modern Angular component using signals..."
```

---

### Option 3: Convert to GGUF and Publish to Ollama (Recommended for Maximum Reach)
To make your model runnable in Ollama or any IDE completion tool (like Continue.dev or VS Code), you can convert the merged model to GGUF format.

#### 1. Merge adapters with standard 16-bit base model (Ensure your `pyenv` environment is active)
Since quantized weights lose precision, merge your adapters with the standard 16-bit precision base model `Qwen/Qwen2.5-Coder-1.5B-Instruct`:
```bash
python -m mlx_lm fuse \
  --model Qwen/Qwen2.5-Coder-1.5B-Instruct \
  --adapter-path adapters \
  --save-path merged-angular-fp16
```

#### 2. Convert to GGUF using llama.cpp
1. Clone `llama.cpp`:
   ```bash
   git clone https://github.com/ggerganov/llama.cpp
   cd llama.cpp
   pip install -r requirements.txt
   ```
   > [!WARNING]
   > Installing `llama.cpp` requirements may downgrade your `transformers` package, which is incompatible with your current version of `mlx-lm`. Once you finish GGUF conversion, restore your MLX environment by running:
   > ```bash
   > pip install --upgrade mlx-lm
   > ```

2. **Compile the quantization binaries:**
   ```bash
   cmake -B build
   cmake --build build --config Release -t llama-quantize
   ```

3. Convert your FP16 merged model to GGUF:
   ```bash
   python convert_hf_to_gguf.py ../merged-angular-fp16 --outfile ../angular-qwen-1.5b.gguf
   ```

4. Quantize the GGUF to 4-bit (recommended for fast execution):
   ```bash
   ./build/bin/llama-quantize ../angular-qwen-1.5b.gguf ../angular-qwen-1.5b-q4_k_m.gguf Q4_K_M
   ```

#### 3. Publish to Ollama
1. Create a `Modelfile` in the directory where your GGUF is:
   ```dockerfile
   FROM ./angular-qwen-1.5b-q4_k_m.gguf
   
   # Set system prompt matching Qwen template
   SYSTEM "You are an elite software architect specialized in Angular 20+ and modern TypeScript. You only generate pure, bug-free implementations."
   
   # Set parameters
   PARAMETER temperature 0.1
   PARAMETER stop "<|im_start|>"
   PARAMETER stop "<|im_end|>"
   ```
2. Build the Ollama model locally:
   ```bash
   ollama create angular-coder -f Modelfile
   ```
3. Test it:
   ```bash
   ollama run angular-coder "Write a modern counter component with signals."
   ```
4. Push to Ollama library:
   * Create an account on [ollama.com](https://ollama.com).
   * Copy your local public key `~/.ollama/id_ed25519.pub` to your Ollama account settings.
   * Push your model:
     ```bash
     ollama tag angular-coder username/angular-coder
     ollama push username/angular-coder
     ```

---

## 📝 Writing a Great Model Card (README.md)

On Hugging Face, write a clean markdown README. Include:
1. **Prompt Template**: Explicitly state that it uses **ChatML** formatting:
   ```text
   <|im_start|>system
   You are an elite software architect specialized in Angular 20+...<|im_end|>
   <|im_start|>user
   {prompt}<|im_end|>
   <|im_start|>assistant
   ```
2. **Dataset Details**: Mention that it is fine-tuned on a high-quality, curated dataset of 600+ modern standalone/signal-based Angular repos.
3. **Intended Use Case**: Mention it's optimized for Signal-based state management, control flow syntax (`@if`/`@for`), standalone components, and modern Angular architecture patterns.
