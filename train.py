from unsloth import FastLanguageModel, is_bfloat16_supported
import torch
import os
from datasets import load_dataset
from unsloth.chat_templates import get_chat_template, train_on_responses_only
from trl import SFTTrainer
from transformers import TrainingArguments, DataCollatorForSeq2Seq, GenerationConfig


# Set environment variables and constants
os.environ["HF_TOKEN"] = "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"
HF_TOKEN = "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"
MODEL_NAME = "meta-llama/Llama-3.2-3B-Instruct"
OUTPUT_MODEL_NAME = "jCool10/chat_anything-3B"
DATASET_PATH = "/workspace/dataset/*.json"

# Model configuration
max_seq_length = 2048
dtype = None  # Auto detection
load_in_4bit = False
load_in_8bit = True
full_finetuning = False

# Load model and tokenizer
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=MODEL_NAME,
    max_seq_length=max_seq_length,
    dtype=dtype,
    load_in_4bit=load_in_4bit,
    load_in_8bit=load_in_8bit,
    token=HF_TOKEN,
    full_finetuning=full_finetuning,
)

# Configure LoRA fine-tuning
model = FastLanguageModel.get_peft_model(
    model,
    r=64,
    target_modules=["k_proj", "v_proj", "q_proj", "out_proj", "c_fc", "c_proj"],
    lora_alpha=16,
    lora_dropout=0,
    bias="none",
    use_gradient_checkpointing="unsloth",
    random_state=3407,
    use_rslora=False,
    init_lora_weights="loftq",
    loftq_config={"q_bit": 4},
)

# Set chat template
tokenizer = get_chat_template(
    tokenizer,
    chat_template="llama-3.2",
)

# Load and prepare dataset
dataset = load_dataset("json", data_files=DATASET_PATH)


def formatting_dataset(examples):
    formatted_data = [
        {"role": "system", "content": examples["system_prompt"]},
        {"role": "user", "content": examples["question_text"]},
        {"role": "assistant", "content": examples["orig_answer_texts"]},
    ]
    return {"formatted_texts": formatted_data}


def formatting_prompts_func(examples):
    convos = examples["formatted_texts"]
    texts = [
        tokenizer.apply_chat_template(
            convo, tokenize=False, add_generation_prompt=False
        )
        for convo in convos
    ]
    return {"text": texts}


model.train()

# Process dataset
dataset_formatting = dataset["train"].map(formatting_dataset, batched=False)
dataset_formatting = dataset_formatting.map(formatting_prompts_func, batched=True)

# Configure trainer
training_args = TrainingArguments(
    per_device_train_batch_size=2,
    gradient_accumulation_steps=128,
    warmup_steps=5,
    # num_train_epochs=1,
    max_steps=10,
    learning_rate=2e-5,
    fp16=not is_bfloat16_supported(),
    bf16=is_bfloat16_supported(),
    logging_steps=1,
    optim="paged_lion_8bit",
    weight_decay=0.01,
    lr_scheduler_type="cosine",
    seed=3407,
    output_dir="outputs",
    report_to="wandb",
    run_name="chat_anything-3B",
    save_strategy="steps",
    save_steps=10,
)

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset_formatting,
    dataset_text_field="text",
    max_seq_length=max_seq_length,
    data_collator=DataCollatorForSeq2Seq(tokenizer=tokenizer),
    dataset_num_proc=2,
    packing=False,
    args=training_args,
)

# Configure to train on responses only
trainer = train_on_responses_only(
    trainer,
    instruction_part="<|start_header_id|>user<|end_header_id|>\n\n",
    response_part="<|start_header_id|>assistant<|end_header_id|>\n\n",
)

# Display memory stats
gpu_stats = torch.cuda.get_device_properties(0)
start_gpu_memory = round(torch.cuda.max_memory_reserved() / 1024 / 1024 / 1024, 3)
max_memory = round(gpu_stats.total_memory / 1024 / 1024 / 1024, 3)
print(f"GPU = {gpu_stats.name}. Max memory = {max_memory} GB.")
print(f"{start_gpu_memory} GB of memory reserved.")

# Train the model
trainer_stats = trainer.train()

# Save and upload model
model.save_pretrained("chat_anything-3B")
tokenizer.save_pretrained("chat_anything-3B")

merged_model = model.merge_and_unload()
merged_model.save_pretrained("chat_anything-3B-merged")
tokenizer.save_pretrained("chat_anything-3B-merged")

model.push_to_hub(OUTPUT_MODEL_NAME, token=HF_TOKEN)
tokenizer.push_to_hub(OUTPUT_MODEL_NAME, token=HF_TOKEN)

merged_model.push_to_hub("jCool10/chat_anything-3B-merged", token=HF_TOKEN)
tokenizer.push_to_hub("jCool10/chat_anything-3B-merged", token=HF_TOKEN)

# evaluate the model
print("\n=== Running evaluation ===")
eval_dataset = dataset["train"].select(range(min(10, len(dataset["train"]))))
eval_formatted = eval_dataset.map(formatting_dataset, batched=False).map(
    formatting_prompts_func, batched=True
)

generation_config = GenerationConfig(
    max_new_tokens=512,
    temperature=0.7,
    top_p=0.9,
    repetition_penalty=1.1,
)

model.eval()
for i, example in enumerate(eval_formatted):
    input_text = tokenizer.decode(
        tokenizer.encode(example["text"]), skip_special_tokens=False
    )
    print(f"\nExample {i+1}: Input: {input_text[:200]}...")

    inputs = tokenizer(input_text, return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs = model.generate(**inputs, generation_config=generation_config)

    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print(f"Generated response: {response}")

    if i >= 2:  # Just show a few examples
        break

print("\n=== Process complete ===")

# Dependencies comment for reference
# pip install bitsandbytes accelerate xformers==0.0.29.post3 peft trl triton cut_cross_entropy unsloth_zoo sentencepiece protobuf datasets hf_transfer unsloth scipy wandb
