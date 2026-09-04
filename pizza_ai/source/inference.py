import torch
from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
)

MODEL_PATH = "checkpoints/flan_t5_pizza"

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_PATH
)

model = AutoModelForSeq2SeqLM.from_pretrained(
    MODEL_PATH
)

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

model.to(device)
model.eval()

print("Model loaded.")

while True:
    text = input("\nPizza Order > ").strip()

    if not text:
        continue

    if text.lower() in ["exit", "quit"]:
        break

    prompt = f"parse pizza order: {text}"

    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=128,
    )

    inputs = {
        k: v.to(device)
        for k, v in inputs.items()
    }

    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_length=256,

            num_beams=4,

            early_stopping=True,
        )

    prediction = tokenizer.decode(
        output_ids[0],
        skip_special_tokens=True,
    )

    print()
    print(prediction)