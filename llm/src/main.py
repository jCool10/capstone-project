from unsloth import FastLanguageModel
import torch
import os
import gc
import math
import time
import datetime
import wandb
import argparse
from datasets import load_dataset
from trl import SFTTrainer
from transformers import TrainingArguments, DataCollatorForSeq2Seq
from unsloth import is_bfloat16_supported
from unsloth.chat_templates import (
    get_chat_template,
    standardize_sharegpt,
    train_on_responses_only,
)

os.environ["HF_TOKEN"] = "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"


# Add argument parsing for flexibility
def parse_args():
    parser = argparse.ArgumentParser(
        description="Fine-tune a language model with Unsloth"
    )
    parser.add_argument(
        "--model_name",
        type=str,
        default="meta-llama/Llama-3.2-3B-Instruct",
        help="Model name",
    )
    parser.add_argument(
        "--dataset_name",
        type=str,
        default="jCool10/databricks_dolly15k",
        help="Dataset name",
    )
    parser.add_argument(
        "--max_seq_length", type=int, default=2048, help="Maximum sequence length"
    )
    parser.add_argument(
        "--load_in_4bit",
        action="store_true",
        default=True,
        help="Use 4-bit quantization",
    )
    parser.add_argument(
        "--learning_rate", type=float, default=1e-5, help="Learning rate"
    )
    parser.add_argument(
        "--batch_size", type=int, default=2, help="Batch size per device"
    )
    parser.add_argument(
        "--gradient_accumulation_steps",
        type=int,
        default=8,
        help="Gradient accumulation steps",
    )
    parser.add_argument(
        "--num_train_epochs", type=int, default=1, help="Number of training epochs"
    )
    parser.add_argument(
        "--warmup_steps", type=int, default=100, help="Number of warmup steps"
    )
    parser.add_argument(
        "--output_dir", type=str, default="outputs", help="Output directory"
    )
    parser.add_argument("--lora_r", type=int, default=8, help="Lora r parameter")
    parser.add_argument(
        "--lora_alpha", type=int, default=16, help="Lora alpha parameter"
    )
    parser.add_argument(
        "--lora_dropout", type=float, default=0.05, help="Lora dropout rate"
    )
    parser.add_argument(
        "--weight_decay", type=float, default=0.01, help="Weight decay rate"
    )
    parser.add_argument(
        "--full_finetuning",
        action="store_true",
        default=False,
        help="Do full finetuning instead of LoRA",
    )
    parser.add_argument(
        "--report_to",
        type=str,
        default="none",
        help="Where to report results (none, wandb, etc)",
    )
    parser.add_argument(
        "--gradient_checkpointing",
        action="store_true",
        default=True,
        help="Use gradient checkpointing",
    )
    parser.add_argument(
        "--merge_weights",
        action="store_true",
        default=True,
        help="Merge weights after training",
    )
    parser.add_argument(
        "--do_eval", action="store_true", default=True, help="Run evaluation"
    )
    return parser.parse_args()


def print_gpu_memory_usage(msg="Current"):
    if torch.cuda.is_available():
        gpu_stats = torch.cuda.get_device_properties(0)
        current_gpu_memory = round(
            torch.cuda.max_memory_reserved() / 1024 / 1024 / 1024, 3
        )
        max_memory = round(gpu_stats.total_memory / 1024 / 1024 / 1024, 3)
        print(f"GPU = {gpu_stats.name}. Max memory = {max_memory} GB.")
        print(f"{msg}: {current_gpu_memory} GB of memory reserved.")


def main():
    args = parse_args()

    # Set memory optimization environment variables
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = (
        "expandable_segments:True,max_split_size_mb:32"
    )

    if torch.cuda.is_available():
        torch.cuda.set_per_process_memory_fraction(0.8)  # Prevent OOM
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True

    # Configure dtype based on hardware
    dtype = None  # None for auto detection. Float16 for Tesla T4, V100, Bfloat16 for Ampere+
    full_finetuning = args.full_finetuning

    print("\n=== Loading model ===")
    print_gpu_memory_usage("Before model load")

    # Load the model with Unsloth
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=args.model_name,
        max_seq_length=args.max_seq_length,
        dtype=dtype,
        load_in_4bit=args.load_in_4bit,
        token=os.environ.get("HF_TOKEN", "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"),
        full_finetuning=full_finetuning,
        lora_r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
    )

    print_gpu_memory_usage("After model load")

    # Set up the tokenizer with the appropriate chat template
    tokenizer = get_chat_template(
        tokenizer,
        chat_template="llama-3.2",
    )

    # Load and prepare the dataset
    print("\n=== Loading dataset ===")
    dataset = load_dataset(args.dataset_name)

    # Enable gradient checkpointing if requested
    if args.gradient_checkpointing:
        model.gradient_checkpointing_enable()
        print("Gradient checkpointing enabled")

    def formatting_dataset(examples):
        formatted_data = [
            {"role": "system", "content": examples["system_prompt"]},
            {"role": "user", "content": examples["question_text"]},
            {"role": "assistant", "content": examples["orig_answer_texts"]},
        ]
        return {"formatted_texts": formatted_data}

    dataset_formatting = dataset["train"].map(formatting_dataset, batched=False)

    def formatting_prompts_func(examples):
        convos = examples["formatted_texts"]
        texts = [
            tokenizer.apply_chat_template(
                convo, tokenize=False, add_generation_prompt=False
            )
            for convo in convos
        ]
        return {
            "text": texts,
        }

    dataset_formatting = dataset_formatting.map(formatting_prompts_func, batched=True)

    # Calculate training steps and learning rate schedule
    num_update_steps_per_epoch = math.ceil(
        len(dataset_formatting) / (args.batch_size * args.gradient_accumulation_steps)
    )
    max_train_steps = args.num_train_epochs * num_update_steps_per_epoch

    # Configure the training arguments
    training_args = TrainingArguments(
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        warmup_steps=args.warmup_steps,
        num_train_epochs=args.num_train_epochs,
        learning_rate=args.learning_rate,
        fp16=not is_bfloat16_supported(),
        bf16=is_bfloat16_supported(),
        logging_steps=10,
        optim="adamw_8bit",
        weight_decay=args.weight_decay,
        lr_scheduler_type="cosine",
        seed=3407,
        output_dir=args.output_dir,
        report_to=args.report_to,
        save_strategy="epoch",
        save_total_limit=2,
        remove_unused_columns=False,
    )

    # Create the trainer
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset_formatting,
        dataset_text_field="text",
        max_seq_length=args.max_seq_length,
        data_collator=DataCollatorForSeq2Seq(tokenizer=tokenizer),
        dataset_num_proc=2,
        packing=False,  # Can make training 5x faster for short sequences.
        args=training_args,
    )

    # Configure to train only on the responses
    # trainer = train_on_responses_only(
    #     trainer,
    #     instruction_part="<|start_header_id|>user<|end_header_id|>\n\n",
    #     response_part="<|start_header_id|>assistant<|end_header_id|>\n\n",
    # )

    # Print current memory stats
    print_gpu_memory_usage("Before training")

    # Start training
    print("\n=== Starting training ===")
    start_time = time.time()
    trainer_stats = trainer.train()
    training_time = time.time() - start_time

    print(f"\n=== Training completed in {training_time/60:.2f} minutes ===")
    print_gpu_memory_usage("After training")

    # Save the model
    output_dir = f"{args.output_dir}/{args.model_name.split('/')[-1]}-finetuned-{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M')}"
    print(f"\n=== Saving model to {output_dir} ===")

    # If we're using LoRA, we can save just the adapter
    if not full_finetuning:
        model.save_pretrained_lora(output_dir)
        tokenizer.save_pretrained(output_dir)

        # Optionally merge weights if requested
        if args.merge_weights:
            print("\n=== Merging weights ===")
            merged_model = model.merge_and_unload()
            merged_model.save_pretrained(f"{output_dir}-merged")
            tokenizer.save_pretrained(f"{output_dir}-merged")
    else:
        # Save the full model
        model.save_pretrained(output_dir)
        tokenizer.save_pretrained(output_dir)

    # Evaluation if enabled
    if args.do_eval:
        print("\n=== Running evaluation ===")
        # Create a simple evaluation dataset
        eval_dataset = dataset["train"].select(range(min(10, len(dataset["train"]))))

        # Format for evaluation
        eval_formatted = eval_dataset.map(formatting_dataset, batched=False)
        eval_formatted = eval_formatted.map(formatting_prompts_func, batched=True)

        # Set up generation config
        from transformers import GenerationConfig

        generation_config = GenerationConfig(
            max_new_tokens=256,
            temperature=0.7,
            top_p=0.9,
            do_sample=True,
            repetition_penalty=1.2,
        )

        # Generate responses for a few examples
        model.eval()
        for i, example in enumerate(eval_formatted):
            input_text = tokenizer.decode(
                tokenizer.encode(example["text"]), skip_special_tokens=False
            )
            print(f"\nExample {i+1}:")
            print(f"Input: {input_text[:200]}...")

            inputs = tokenizer(input_text, return_tensors="pt").to(model.device)
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    generation_config=generation_config,
                )

            response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            print(f"Generated response: {response}")

            if i >= 2:  # Just show a few examples
                break

    print("\n=== Process complete ===")

    # Final memory cleanup
    del model, tokenizer, trainer
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()

    print_gpu_memory_usage("Final")


if __name__ == "__main__":
    main()

# python llm/src/main.py --model_name "meta-llama/Llama-3.2-3B-Instruct" --learning_rate 2e-5 --batch_size 4 --num_train_epochs 2 --merge_weights --do_eval
