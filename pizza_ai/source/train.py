import json
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    DataCollatorForSeq2Seq,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
)

MODEL_NAME = "google/flan-t5-small"

TRAIN_FILE = "data/PIZZA_train.3480_shots.json"
DEV_FILE = "data/PIZZA_dev.json"

OUTPUT_DIR = "checkpoints/flan_t5_pizza"


def load_jsonl(path, src_key, target_key):
    rows = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)

            rows.append(
                {
                    "input": f"parse pizza order: {item[src_key]}",
                    "target": item[target_key],
                }
            )

    return rows


print("Loading datasets...")

train_rows = load_jsonl(
    TRAIN_FILE,
    "train.SRC",
    "train.EXR",
)

dev_rows = load_jsonl(
    DEV_FILE,
    "dev.SRC",
    "dev.EXR",
)

train_ds = Dataset.from_list(train_rows)
dev_ds = Dataset.from_list(dev_rows)

print("Train samples:", len(train_ds))
print("Dev samples:", len(dev_ds))

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)


def preprocess(batch):
    model_inputs = tokenizer(
        batch["input"],
        max_length=128,
        truncation=True,
    )

    labels = tokenizer(
        text_target=batch["target"],
        max_length=256,
        truncation=True,
    )

    model_inputs["labels"] = labels["input_ids"]

    return model_inputs


train_ds = train_ds.map(
    preprocess,
    batched=True,
    remove_columns=train_ds.column_names,
)

dev_ds = dev_ds.map(
    preprocess,
    batched=True,
    remove_columns=dev_ds.column_names,
)

model = AutoModelForSeq2SeqLM.from_pretrained(
    MODEL_NAME
)

data_collator = DataCollatorForSeq2Seq(
    tokenizer=tokenizer,
    model=model,
)

training_args = Seq2SeqTrainingArguments(
    output_dir=OUTPUT_DIR,

    learning_rate=3e-4,

    num_train_epochs=5,

    per_device_train_batch_size=4,
    per_device_eval_batch_size=4,

    gradient_accumulation_steps=8,

    fp16=True,

    save_strategy="epoch",
    eval_strategy="epoch",

    logging_steps=50,

    predict_with_generate=True,

    save_total_limit=3,
)

trainer = Seq2SeqTrainer(
    model=model,
    args=training_args,
    train_dataset=train_ds,
    eval_dataset=dev_ds,
    processing_class=tokenizer,
    data_collator=data_collator,
)

print("Starting training...")

trainer.train()

print("Saving model...")

trainer.save_model(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)

print("Done.")