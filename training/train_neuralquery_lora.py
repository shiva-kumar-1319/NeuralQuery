"""
NeuralQuery LoRA Fine-Tuning Script.
Fine-tunes Qwen2.5-1.5B-Instruct on Grounded-RAG evidence synthesis using PEFT LoRA.
Designed to run on Google Colab (T4 GPU) or local CUDA environment.
"""

import os
import argparse
import torch
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments
)
from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training,
    TaskType
)
from trl import SFTTrainer


def parse_args():
    parser = argparse.ArgumentParser(description="Fine-tune Qwen2.5-1.5B with LoRA for NeuralQuery")
    parser.add_argument("--base_model", type=str, default="Qwen/Qwen2.5-1.5B-Instruct", help="Hugging Face base model")
    parser.add_argument("--dataset", type=str, default="training/dataset_sample.jsonl", help="Path to JSONL dataset")
    parser.add_argument("--output_dir", type=str, default="model/neuralquery-production-adapter", help="Output directory for adapter")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=2, help="Per-device batch size")
    parser.add_argument("--grad_accum", type=int, default=8, help="Gradient accumulation steps")
    parser.add_argument("--learning_rate", type=float, default=2e-4, help="Peak learning rate")
    parser.add_argument("--lora_r", type=int, default=16, help="LoRA rank")
    parser.add_argument("--lora_alpha", type=int, default=32, help="LoRA alpha")
    parser.add_argument("--lora_dropout", type=float, default=0.05, help="LoRA dropout")
    parser.add_argument("--max_seq_length", type=int, default=2048, help="Maximum sequence length")
    return parser.parse_args()


def format_prompts(example, tokenizer):
    """
    Format dataset record into Qwen chat template.
    """
    messages = [
        {"role": "system", "content": example.get("system", "You are NeuralQuery, an expert AI research intelligence engine.")},
        {"role": "user", "content": f"Research Question:\n{example['question']}\n\nRetrieved Evidence:\n{example['evidence']}\n\nProduce a rigorous, grounded research analysis:"},
        {"role": "assistant", "content": example["response"]}
    ]
    return {"text": tokenizer.apply_chat_template(messages, tokenize=False)}


def main():
    args = parse_args()
    print(f"\n{'='*60}")
    print("🚀 NeuralQuery LoRA Fine-Tuning Pipeline")
    print(f"   Base Model:  {args.base_model}")
    print(f"   Dataset:     {args.dataset}")
    print(f"   Output Dir:  {args.output_dir}")
    print(f"   LoRA Config: r={args.lora_r}, alpha={args.lora_alpha}, dropout={args.lora_dropout}")
    print(f"{'='*60}\n")

    # Check CUDA
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"📍 Device: {device} ({torch.cuda.get_device_name(0) if device == 'cuda' else 'CPU'})")

    # 4-bit Quantization Config (QLoRA)
    bnb_config = None
    if device == "cuda":
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True
        )

    # Load Tokenizer
    print("📚 Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Load Model
    print("📦 Loading base model...")
    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        quantization_config=bnb_config if device == "cuda" else None,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        device_map="auto" if device == "cuda" else None,
        trust_remote_code=True
    )

    if device == "cuda":
        model = prepare_model_for_kbit_training(model)

    # Configure PEFT LoRA
    print("🔧 Configuring LoRA adapter...")
    peft_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        bias="none"
    )
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    # Load Dataset
    print(f"📄 Loading dataset from {args.dataset}...")
    dataset = load_dataset("json", data_files=args.dataset, split="train")
    formatted_dataset = dataset.map(lambda ex: format_prompts(ex, tokenizer))

    # Training Arguments
    training_args = TrainingArguments(
        output_dir=os.path.join(args.output_dir, "checkpoints"),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.learning_rate,
        lr_scheduler_type="cosine",
        warmup_ratio=0.05,
        logging_steps=10,
        save_strategy="epoch",
        fp16=(device == "cuda"),
        optim="paged_adamw_8bit" if device == "cuda" else "adamw_torch",
        report_to="none"
    )

    # Initialize Trainer
    trainer = SFTTrainer(
        model=model,
        train_dataset=formatted_dataset,
        dataset_text_field="text",
        max_seq_length=args.max_seq_length,
        tokenizer=tokenizer,
        args=training_args
    )

    # Train
    print("\n⚡ Starting fine-tuning...")
    trainer.train()

    # Save Adapter Artifacts
    print(f"\n💾 Saving final LoRA adapter to {args.output_dir}...")
    os.makedirs(args.output_dir, exist_ok=True)
    model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)

    print("🎉 Fine-tuning complete! Adapter ready for NeuralQuery inference.\n")


if __name__ == "__main__":
    main()
