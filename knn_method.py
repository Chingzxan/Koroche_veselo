from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.neighbors import KNeighborsClassifier
from storage import finalize_result


positive_words = [
    "лучший", "хороший", "отличный", "прекрасный", "замечательный", "великолепный",
    "классный", "крутой", "супер", "приятный", "радостный", "счастливый",
    "успешный", "красивый", "любимый", "позитивный", "восхитительный",
    "блестящий", "чудесный", "потрясающий", "топ", "качественный",
    "невероятный", "превосходный", "роскошный", "шикарный", "бомбический",
    "офигенный", "клевый", "лайк", "великий", "изумительный", "восхитительный",
    "отлично", "хорошо", "прекрасно", "замечательно", "великолепно", "классно",
    "круто", "суперски", "здорово", "чудесно", "потрясающе", "восхитительно",
    "превосходно", "шикарно", "офигенно", "клево", "бомбически", "невероятно",
    "нравится", "обожаю", "люблю", "восхищаюсь", "радует", "впечатляет",
    "зачет", "огонь", "бомба", "топчик", "имба", "рекомендую"
]

negative_words = [
    "плохой", "ужасный", "отвратительный", "скучный", "глупый", "злой",
    "грустный", "неудачный", "омерзительный", "бесполезный", "унылый",
    "дешёвый", "мерзкий", "паршивый", "противный", "кошмарный", "негативный",
    "проблемный", "слабый", "убогий", "печальный", "разочаровывающий",
    "худший", "гавняный", "дерьмовый", "никудышный", "низкокачественный",
    "плохо", "ужасно", "отвратительно", "скучно", "глупо", "грустно",
    "неудачно", "омерзительно", "бесполезно", "уныло", "печально",
    "кошмарно", "разочаровывающе", "убийственно",
    "отстой", "гавно", "фигня", "беда", "провал", "разочарование",
    "кошмар", "ужас", "ерунда", "чушь"
]

neutral_words = [
    "бумага", "дерево", "кирпич", "бутылка", "стол", "стул", "книга", "окно",
    "дорога", "дом", "машина", "город", "вода", "ручка", "экран", "кнопка",
    "процесс", "компьютер", "мышь", "клавиатура", "монитор", "стена", "пол",
    "потолок", "лампа", "шкаф", "диван", "кровать", "телефон",
    "нормальный", "средний", "обычный", "стандартный", "типичный", "нейтральный",
    "неплохой", "норм", "сойдёт", "средне", "нормально", "приемлемо",
    "удовлетворительно", "так себе", "ничего", "сносно", "посредственно",
    "находится", "расположен", "имеется", "является", "состоит",
    "используется", "применяется", "работает", "функционирует"
]

positive_phrases = [
    "это отличный продукт", "мне очень нравится", "прекрасное качество",
    "замечательная вещь", "великолепно выглядит", "супер вещь",
    "действительно хороший", "очень радует", "лучшее решение",
    "я в восторге", "это просто бомба", "рекомендую к покупке"
]

negative_phrases = [
    "ужасное качество", "мне не нравится", "очень плохо",
    "разочарован покупкой", "кошмарная вещь", "полный отстой",
    "ужасно выглядит", "не рекомендую", "зря потратил деньги",
    "это просто ужас"
]

neutral_phrases = [
    "обычная вещь", "стандартное качество", "как обычно",
    "ничего особенного", "средний уровень", "обычный товар",
    "ничего выдающегося", "так себе", "нормально"
]

_all_keywords = set(positive_words + negative_words + neutral_words)
_all_phrases = positive_phrases + negative_phrases + neutral_phrases

def extract_keywords_knn(text):
    """Извлекает из текста значимые слова/фразы, которые есть в словарях."""
    text_lower = text.lower()
    found = []
    

    for phrase in _all_phrases:
        if phrase in text_lower:
            found.append(phrase)
    words = text_lower.split()
    for word in words:
        # Очищаем слово от пунктуации
        clean_word = word.strip(".,!?;:()\"'")
        if clean_word in _all_keywords and clean_word not in found:
            found.append(clean_word)
    
    
    unique = []
    for item in found:
        if item not in unique:
            unique.append(item)
    return unique[:5]


words_data = positive_words + negative_words + neutral_words
phrases_data = positive_phrases + negative_phrases + neutral_phrases

words_labels = [1] * len(positive_words) + [-1] * len(negative_words) + [0] * len(neutral_words)
phrases_labels = [1] * len(positive_phrases) + [-1] * len(negative_phrases) + [0] * len(neutral_phrases)

all_data = words_data + phrases_data
all_labels = words_labels + phrases_labels

vectorizer = TfidfVectorizer(
    analyzer="word",
    ngram_range=(1, 3),
    min_df=1,
    max_features=500,
    stop_words=None
)

X = vectorizer.fit_transform(all_data)

X_train, X_test, y_train, y_test = train_test_split(
    X, all_labels, test_size=0.25, random_state=42, stratify=all_labels
)

param_grid = {
    "n_neighbors": [3, 5, 7, 9, 11, 13],
    "metric": ["cosine", "euclidean", "manhattan"],
    "weights": ["uniform", "distance"]
}

knn_base = KNeighborsClassifier()
grid_search = GridSearchCV(
    knn_base, param_grid, cv=5, scoring="accuracy", n_jobs=-1, verbose=0
)
grid_search.fit(X_train, y_train)

best_knn = grid_search.best_estimator_

def analyze_with_knn(text):
    text_clean = text.strip().lower()
    text_vec = vectorizer.transform([text_clean])

    prediction = best_knn.predict(text_vec)[0]
    probabilities = best_knn.predict_proba(text_vec)[0]

    if prediction == 1:
        sentiment = "positive"
        emoji = "😊"
        color = "green"
    elif prediction == 0:
        sentiment = "neutral"
        emoji = "😐"
        color = "gray"
    else:
        sentiment = "negative"
        emoji = "😞"
        color = "red"

    score = float(max(probabilities))
    keywords = extract_keywords_knn(text_clean)
    
    result = {
        "sentiment": sentiment,
        "emoji": emoji,
        "color": color,
        "score": round(score, 2),
        "keywords": keywords
    }
    return finalize_result(result, text)
