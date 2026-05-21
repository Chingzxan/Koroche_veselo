from datetime import datetime

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification


MODEL_NAME = "blanchefort/rubert-base-cased-sentiment"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
model.eval()

LABELS = {
    0: "negative",
    1: "neutral",
    2: "positive",
}

EMOJI = {
    "positive": "😊",
    "negative": "😞",
    "neutral": "😐",
}

COLOR = {
    "positive": "#48bb78",
    "negative": "#f56565",
    "neutral": "#667eea",
}


def analyze_with_rubert(text):
    try:
        inputs = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=512,
        )

        with torch.no_grad():
            outputs = model(**inputs)
            probs = torch.nn.functional.softmax(outputs.logits, dim=1)[0]

        label_id = int(torch.argmax(probs))
        sentiment = LABELS.get(label_id, "neutral")
        score = float(probs[label_id])

        return {
            "text": text,
            "sentiment": sentiment,
            "emoji": EMOJI[sentiment],
            "color": COLOR[sentiment],
            "score": round(score, 3),
            "keywords": ["local_rubert"],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    except Exception as e:
        print("Local RuBERT error:", e)

        return {
            "text": text,
            "sentiment": "neutral",
            "emoji": "😐",
            "color": "#667eea",
            "score": 0.5,
            "keywords": ["local_rubert_error"],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
