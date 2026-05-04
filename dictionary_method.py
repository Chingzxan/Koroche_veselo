import json
import os
from storage import finalize_result

POSITIVE_WORDS_FILE = "positive_words.json"
NEGATIVE_WORDS_FILE = "negative_words.json"


def load_json_file(filename, default_value=None):
    if default_value is None:
        default_value = {}

    try:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        print(f"Файл {filename} не найден.")
        return default_value
    except json.JSONDecodeError:
        print(f"Ошибка JSON в файле {filename}.")
        return default_value
    except OSError:
        print(f"Не удалось открыть файл {filename}.")
        return default_value


def load_sentiment_dictionaries():
    positive_words = load_json_file(POSITIVE_WORDS_FILE, {})
    negative_words = load_json_file(NEGATIVE_WORDS_FILE, {})
    return {
        "positive": positive_words,
        "negative": negative_words
    }


DICTIONARIES = load_sentiment_dictionaries()


def analyze_sentiment_russian(text, dictionaries):
    positive_words = dictionaries["positive"]
    negative_words = dictionaries["negative"]

    negations = ["не", "ни", "нет", "без"]
    intensifiers = {
        "очень": 1.5, "реально": 1.3, "действительно": 1.3,
        "крайне": 1.6, "абсолютно": 1.4, "совершенно": 1.4
    }

    words = text.lower().split()

    total_score = 0
    word_count = 0
    found_keywords = []

    for i, word in enumerate(words):
        clean_word = word.strip(".,!?()\"'—–-:;")

        if clean_word in positive_words:
            score = positive_words[clean_word]
            found_keywords.append(clean_word)

            if i > 0 and words[i - 1] in negations:
                score = -score
                phrase = f"{words[i - 1]} {clean_word}"
                if phrase not in found_keywords:
                    found_keywords.append(phrase)

            if i > 0 and words[i - 1] in intensifiers:
                score *= intensifiers[words[i - 1]]

            total_score += score
            word_count += 1

        elif clean_word in negative_words:
            score = negative_words[clean_word]
            found_keywords.append(clean_word)

            if i > 0 and words[i - 1] in negations:
                score = -score
                phrase = f"{words[i - 1]} {clean_word}"
                if phrase not in found_keywords:
                    found_keywords.append(phrase)

            if i > 0 and words[i - 1] in intensifiers:
                score *= intensifiers[words[i - 1]]

            total_score += score
            word_count += 1

    sentiment_score = total_score / word_count if word_count > 0 else 0
    sentiment_score = max(-1, min(1, sentiment_score))

    if sentiment_score > 0.1:
        sentiment = "positive"
        emoji = "😊"
        color = "green"
    elif sentiment_score < -0.1:
        sentiment = "negative"
        emoji = "😞"
        color = "red"
    else:
        sentiment = "neutral"
        emoji = "😐"
        color = "gray"

    keywords = list(dict.fromkeys(found_keywords))[:5]

    return {
        "sentiment": sentiment,
        "emoji": emoji,
        "color": color,
        "score": round(sentiment_score, 2),
        "keywords": keywords
    }


def analyze_with_dictionary(text):
    result = analyze_sentiment_russian(text, DICTIONARIES)
    return finalize_result(result, text)