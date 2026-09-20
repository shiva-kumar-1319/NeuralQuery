# NeuralQuery Production LoRA Adapter

This directory contains the configuration and trained PEFT LoRA adapter for **NeuralQuery**.

## Adapter Details

- **Base Model:** `Qwen/Qwen2.5-1.5B-Instruct`
- **Adapter Framework:** PEFT (Parameter-Efficient Fine-Tuning) LoRA
- **Task Type:** `CAUSAL_LM`
- **LoRA Rank ($r$):** 16
- **LoRA Alpha ($\alpha$):** 32
- **LoRA Dropout:** 0.05
- **Target Modules:** `q_proj`, `k_proj`, `v_proj`, `o_proj`

## Files in this Directory

| File | Description |
|---|---|
| `adapter_config.json` | LoRA hyperparameter and target module configuration |
| `tokenizer_config.json` | Tokenizer settings matching Qwen2.5 chat template |
| `adapter_model.safetensors` | Trained LoRA adapter tensor weights (~30MB) |
| `README.md` | This documentation |

## Placing Adapter Weights

Place your trained `adapter_model.safetensors` file inside this directory:
```bash
model/neuralquery-production-adapter/adapter_model.safetensors
```

### Git LFS / Artifact Release

Because Git repositories have strict file size and bandwidth limitations, model weight files are excluded in `.gitignore`. To track with Git LFS (Large File Storage):

```bash
# Initialize Git LFS
git lfs install

# Track safetensors
git lfs track "*.safetensors"
git add .gitattributes
git add model/neuralquery-production-adapter/adapter_model.safetensors
git commit -m "Add production LoRA adapter weights via Git LFS"
```

Alternatively, download the adapter weights from your release storage (Hugging Face Hub / Cloud Storage) to this directory during deployment.
