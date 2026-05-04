import argparse
import json
import joblib
import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression


def rating_to_label(rating):
    if rating <= 2:
        return "negative"
    if rating == 3:
        return "neutral"
    return "positive"


def load_dataset(csv_path):
    df = pd.read_csv(csv_path)

    required_columns = {"text"}
    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"В CSV нет нужных колонок: {sorted(missing)}")

    df = df.copy()
    df = df.dropna(subset=["text"])
    df["text"] = df["text"].astype(str).str.strip()
    df = df[df["text"] != ""]

    if "label" in df.columns:
        df = df.dropna(subset=["label"])
        df["label"] = df["label"].astype(str).str.strip().str.lower()
    elif "rating" in df.columns:
        df = df.dropna(subset=["rating"])
        df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
        df = df.dropna(subset=["rating"])
        df["label"] = df["rating"].apply(rating_to_label)
    else:
        raise ValueError("В CSV должна быть колонка label или rating")

    return df[["text", "label"]]


def build_model(max_features=20000):
    return Pipeline([
        ("tfidf", TfidfVectorizer(
            max_features=max_features,
            ngram_range=(1, 2),
            min_df=2,
            lowercase=True
        )),
        ("clf", LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            random_state=42
        ))
    ])


def main():
    parser = argparse.ArgumentParser(
        description="Обучение модели тональности только на train-датасете."
    )
    parser.add_argument(
        "--csv",
        default="train_reviews.csv",
        help="Путь к train CSV-файлу"
    )
    parser.add_argument(
        "--model-out",
        default="trained_logreg_sentiment.joblib",
        help="Куда сохранить обученную модель"
    )
    parser.add_argument(
        "--report-out",
        default="training_report.json",
        help="Куда сохранить краткий отчёт"
    )
    args = parser.parse_args()

    print("Загружаю train-датасет...")
    df = load_dataset(args.csv)
    print(f"Записей после очистки: {len(df)}")

    print("Распределение классов:")
    print(df["label"].value_counts())

    X_train = df["text"]
    y_train = df["label"]

    print("\nОбучаю модель Logistic Regression + TF-IDF...")
    model = build_model()
    model.fit(X_train, y_train)

    joblib.dump(model, args.model_out)
    print(f"\nМодель сохранена в: {args.model_out}")

    result = {
        "dataset_size": int(len(df)),
        "train_size": int(len(X_train)),
        "labels_distribution": df["label"].value_counts().to_dict()
    }

    with open(args.report_out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Отчёт сохранён в: {args.report_out}")


if __name__ == "__main__":
    main()