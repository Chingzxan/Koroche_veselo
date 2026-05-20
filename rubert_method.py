import requests
import os
import time
from storage import finalize_result

API_URL = "https://api-inference.huggingface.co/models/blanchefort/rubert-base-cased-sentiment"

def analyze_with_rubert(text):
    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        print("❌ HF_TOKEN не задан в переменных окружения")
        return fallback_result(text, "No HF_TOKEN") 

    headers = {
        "Authorization": f"Bearer {hf_token}",
        "Content-Type": "application/json",
        "x-wait-for-model": "true"
    }
    payload = {
        "inputs": text,
        "parameters": {
            "truncation": True
        }
    }

    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"📡 Отправка запроса к RuBERT (попытка {attempt+1}/{max_retries})...")
            response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 503:
                wait_time = 5 * (attempt + 1)
                print(f"⏳ Модель загружается (503). Ждём {wait_time} сек...")
                time.sleep(wait_time)
                continue
            
            response.raise_for_status()
            data = response.json()
            
            if isinstance(data, dict) and "error" in data:
                raise Exception(f"API error: {data['error']}")
            
            predictions = []
            if isinstance(data, list) and len(data) > 0:
                predictions = data
            elif isinstance(data, dict) and "label" in data and "score" in data:
                predictions = [data]
            else:
                raise ValueError(f"Неожиданный формат ответа: {data}")
            
            best = max(predictions, key=lambda x: x['score'])
            label = best['label'].upper()
            score = best['score']
            
            if label == "POSITIVE":
                sentiment = "positive"
                emoji = "😊"
                color = "green"
            elif label == "NEGATIVE":
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
            
            print(f"✅ Результат: {sentiment} (score: {round(score, 2)})")
            return finalize_result(result, text)
        
        except requests.exceptions.Timeout:
            print(f"⏰ Таймаут при попытке {attempt+1}")
            if attempt == max_retries - 1:
                return fallback_result(text, "Timeout после нескольких попыток")
            time.sleep(2)
        
        except requests.exceptions.RequestException as e:
            print(f"🌐 Ошибка сети: {e}")
            if attempt == max_retries - 1:
                return fallback_result(text, f"Network error: {e}")
            time.sleep(2)
        
        except Exception as e:
            print(f"⚠️ Непредвиденная ошибка: {e}")
            return fallback_result(text, str(e))
    
    return fallback_result(text, "Max retries exceeded")

def fallback_result(text, error_msg):
    print(f"🔄 Использован fallback: {error_msg}")
    result = {
        "sentiment": "neutral",
        "emoji": "😐",
        "color": "gray",
        "score": 0.5,
        "keywords": ["api_error"]
    }
    return finalize_result(result, text)
