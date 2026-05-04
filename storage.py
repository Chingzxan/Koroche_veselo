import json
import os
from datetime import datetime

REVIEWS_FILE = "reviews.json"


def load_reviews():
    if os.path.exists(REVIEWS_FILE):
        try:
            with open(REVIEWS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            print(f"Не удалось прочитать {REVIEWS_FILE}. Будет создан новый список отзывов.")
    return []


def save_reviews(reviews):
    with open(REVIEWS_FILE, "w", encoding="utf-8") as f:
        json.dump(reviews, f, ensure_ascii=False, indent=2)


def finalize_result(result, text):
    result["text"] = text
    result["timestamp"] = datetime.now().isoformat(timespec="seconds")
    return result


def print_result(result):
    labels = {
        "positive": "Позитивный",
        "negative": "Негативный",
        "neutral": "Нейтральный"
    }

    print("\nРезультат анализа:")
    print(f"Метод: {result.get('method', 'unknown')}")
    print(f"Тональность: {labels.get(result['sentiment'], result['sentiment'])} {result['emoji']}")
    print(f"Оценка: {result['score']}")
    print(f"Цвет: {result['color']}")

    if result.get("keywords"):
        print("Ключевые слова:", ", ".join(result["keywords"]))
    else:
        print("Ключевые слова: не найдены")

    print(f"Текст: {result['text']}")
    print(f"Время: {result['timestamp']}")


def show_last_reviews():
    reviews = load_reviews()
    if not reviews:
        print("\nСохранённых отзывов пока нет.")
        return

    print("\nПоследние отзывы:")
    for i, review in enumerate(reviews[:10], start=1):
        print(f"\n{i}. {review['emoji']} {review['text']}")
        print(f"   Метод: {review.get('method', 'unknown')}")
        print(f"   Тональность: {review['sentiment']}")
        print(f"   Оценка: {review['score']}")
        if review.get("keywords"):
            print(f"   Ключевые слова: {', '.join(review['keywords'])}")
        print(f"   Время: {review['timestamp']}")