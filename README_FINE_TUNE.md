# MLX QLoRA Fine-Tuning Guide: Qwen2.5-Coder-1.5B-Instruct-4bit

This guide details the end-to-end workflow to fine-tune the **Qwen2.5-Coder-1.5B-Instruct-4bit** model using your custom compiled Angular v20+ dataset on Apple Silicon (M1/M2/M3/M4) via the Apple MLX framework.

---

## 1. Prerequisites & Environment Setup

Ensure all necessary MLX training libraries, dataset processing modules, and Hugging Face tools are installed in your Python environment:

```bash
# Upgrade pip to the latest version
pip install --upgrade pip

# Install MLX LM framework with training extensions and Hugging Face Hub
pip install "mlx-lm[train]" huggingface_hub
```

---

## 2. Dataset Preparation

Your dataset has already been parsed and split using the Qwen Chat ML system structure in `dataset_compiler.py`. 

To compile or refresh your dataset from the raw scraped codebase directory, run:
```bash
python dataset_compiler.py
```

This generates two key training files:
*   `data/train.jsonl` (Training tokensets)
*   `data/valid.jsonl` (Validation tokensets)

### Dataset Format (Qwen Chat ML)
Each line in your JSONL file contains the chat template that matches the instruction tuning format of Qwen2.5-Coder:
```json
{
  "text": "<|im_start|>system\nYou are an elite software architect specialized in Angular 20+ and modern TypeScript. You only generate pure, bug-free implementations optimized for [Role Description].<|im_end|>\n<|im_start|>user\nAnalyze and provide complete production-ready source contents for: [FileName]<|im_end|>\n<|im_start|>assistant\n```[Extension]\n[CodeContent]\n```<|im_end|>"
}
```

---

## 3. Launching QLoRA Fine-Tuning

Run the training process using the Apple MLX command-line interface. 

Because we are using a quantized model (`-4bit`), MLX automatically performs **QLoRA** (Quantized Low-Rank Adaptation). This utilizes very little unified memory (~1.5GB to 3GB RAM), making it run extremely fast on any Mac system.

```bash
python -m mlx_lm.lora \
  --model mlx-community/Qwen2.5-Coder-1.5B-Instruct-4bit \
  --train \
  --data data \
  --iters 1000 \
  --batch-size 4 \
  --learning-rate 1e-5 \
  --steps-per-eval 100 \
  --val-batches 25 \
  --adapter-path adapters
```

### Parameter Explanations:
| Parameter | Value | Description |
| :--- | :--- | :--- |
| `--model` | `mlx-community/Qwen2.5-Coder-1.5B-Instruct-4bit` | Hugging Face ID of the base 4-bit model. |
| `--train` | *Flag* | Instructs the framework to launch the training loop. |
| `--data` | `data` | Directory containing `train.jsonl` and `valid.jsonl`. |
| `--iters` | `1000` | The total number of steps/iterations to train (adjust up/down as needed). |
| `--batch-size` | `4` | Number of samples processed in parallel. |
| `--learning-rate`| `1e-5` | Small learning rate (standard for LoRA adapters). |
| `--steps-per-eval`| `100` | Run loss evaluations against validation data every 100 steps. |
| `--adapter-path` | `adapters` | Directory where your trained adapter weights (`adapters.safetensors`) will be saved. |

---

## 4. Evaluating the Model

Once training is complete, test how your fine-tuned model writes modern Angular code (e.g. using standalone architecture, Signals, and native control flows).

### Running Terminal-Based Generation
Load the base model combined with your trained adapters to test code output generation:

```bash
python -m mlx_lm.generate \
  --model mlx-community/Qwen2.5-Coder-1.5B-Instruct-4bit \
  --adapter-path adapters \
  --max-tokens 512 \
  --temp 0.1 \
  --prompt "<|im_start|>system\nYou are an elite software architect specialized in Angular 20+ and modern TypeScript.<|im_end|>\n<|im_start|>user\nGenerate a modern Angular component using Signals and OnPush change detection that fetches list items from an API.<|im_end|>\n<|im_start|>assistant\n"
```

---

## 5. Merging & Distributing (Optional)

If you want to bake the learned weights directly back into the base model so that it functions as a single independent model without requiring separate adapter files, you can merge them:

```bash
python -m mlx_lm.merge \
  --model mlx-community/Qwen2.5-Coder-1.5B-Instruct-4bit \
  --adapter-path adapters \
  --output-path merged_model
```

Your merged model will be saved inside the `merged_model/` directory, which can be run with any MLX, Llama.cpp, or Hugging Face application.
