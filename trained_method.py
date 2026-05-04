import joblib
from storage import finalize_result

MODEL_PATH = "trained_logreg_sentiment.joblib"
_MODEL = None


def _load_model():
    global _MODEL

    if _MODEL is not None:
        return _MODEL

    try:
        _MODEL = joblib.load(MODEL_PATH)
    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"Файл модели {MODEL_PATH} не найден. "
            "Сначала обучи модель через train_sentiment_model.py"
        ) from e

    return _MODEL


def analyze_with_trained_model(text):
    model = _load_model()

    probabilities = model.predict_proba([text])[0]
    classes = list(model.classes_)

    score_map = {
        cls: float(prob)
        for cls, prob in zip(classes, probabilities)
    }

    sentiment = max(score_map, key=score_map.get)

    if sentiment == "positive":
        emoji = "😊"
        color = "green"
    elif sentiment == "negative":
        emoji = "😞"
        color = "red"
    else:
        emoji = "😐"
        color = "gray"

    keywords = [
        f"{label}:{round(score, 3)}"
        for label, score in sorted(score_map.items(), key=lambda x: x[1], reverse=True)
    ]

    result = {
        "sentiment": sentiment,
        "emoji": emoji,
        "color": color,
        "score": round(score_map[sentiment], 2),
        "keywords": keywords[:5]
    }

    return finalize_result(result, text)
