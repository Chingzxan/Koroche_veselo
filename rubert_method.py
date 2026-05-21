import requests
import os
from storage import finalize_result

API_URL = "https://api-inference.huggingface.co/models/blanchefort/rubert-base-cased-sentiment"

def analyze_with_rubert(text):
    # Токен берётся из переменной окружения (настроим на Render)
    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        # На случай, если забыли добавить переменную – не падаем, а используем fallback
        return fallback_result(text, "No HF_TOKEN")

    headers = {"Authorization": f"Bearer {hf_token}"}
    payload = {"inputs": text}

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        # Ожидаемый ответ: [{'label': 'POSITIVE', 'score': 0.99}, ...]
        if isinstance(data, list) and len(data) > 0:
            best = max(data, key=lambda x: x['score'])
            label = best['label'].lower()
            score = best['score']
        else:
            raise ValueError("Unexpected API response")

        if label in ("positive", "pos"):
            sentiment = "positive"
            emoji = "😊"
            color = "green"
        elif label in ("negative", "neg"):
            sentiment = "negative"
            emoji = "😞"
            color = "red"
        else:
            sentiment = "neutral"
            emoji = "😐"
            color = "gray"

        result = {
            "sentiment": sentiment,
            "emoji": emoji,
            "color": color,
            "score": round(score, 2),
            "keywords": []
        }
        return finalize_result(result, text)

    except Exception as e:
        print(f"RuBERT API error: {e}")
        return fallback_result(text, str(e))

def fallback_result(text, error_msg):
    print(f"RuBERT fallback: {error_msg}")
    result = {
        "sentiment": "neutral",
        "emoji": "😐",
        "color": "gray",
        "score": 0.5,
        "keywords": ["api_error"]
    }
    return finalize_result(result, text)
