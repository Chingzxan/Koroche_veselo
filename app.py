from flask import Flask, request, jsonify, render_template
import secrets
import pandas as pd
import json
import os
from werkzeug.utils import secure_filename
from dictionary_method import analyze_with_dictionary
from knn_method import analyze_with_knn
from trained_method import analyze_with_trained_model
from rubert_method import analyze_with_rubert  # ← ДОБАВЛЕНО
from storage import load_reviews, save_reviews

app = Flask(__name__)

# секретный ключ 
app.config['SECRET_KEY'] = secrets.token_hex(32)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv', 'txt', 'json'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def parse_uploaded_file(filepath, filetype):
    texts = []
    
    if filetype == 'csv':
        df = pd.read_csv(filepath)
        text_column = None
        for col in ['text', 'review', 'comment', 'content', 'message', 'отзыв', 'текст']:
            if col in df.columns:
                text_column = col
                break
        if text_column:
            texts = df[text_column].dropna().astype(str).str.strip().tolist()
        else:
            texts = df.iloc[:, 0].dropna().astype(str).str.strip().tolist()
            
    elif filetype == 'json':
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            for item in data:
                if isinstance(item, str):
                    texts.append(item.strip())
                elif isinstance(item, dict):
                    for key in ['text', 'review', 'comment', 'content']:
                        if key in item:
                            texts.append(str(item[key]).strip())
                            break
                    else:
                        texts.append(str(list(item.values())[0]).strip())
        elif isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str) and len(value) > 10:
                    texts.append(value.strip())
                    
    elif filetype == 'txt':
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip()
                if line and len(line) > 2:
                    texts.append(line)
    
    texts = [t for t in texts if t and len(t) > 2]
    return texts

# CORS заголовки
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return response

# Обработка preflight запросов
@app.route('/analyze', methods=['OPTIONS'])
@app.route('/reviews', methods=['OPTIONS'])
@app.route('/upload', methods=['OPTIONS'])
def handle_options():
    return '', 200

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Нет данных'}), 400
            
        text = data.get('text', '').strip()
        method = data.get('method', 'dictionary')
        
        if not text:
            return jsonify({'error': 'Текст не может быть пустым'}), 400
        
        # Выбор модели
        if method == 'dictionary':
            result = analyze_with_dictionary(text)
            result['method_used'] = 'dictionary'
        elif method == 'knn':
            result = analyze_with_knn(text)
            result['method_used'] = 'knn'
        elif method == 'rubert':
            result = analyze_with_rubert(text) 
            result['method_used'] = 'rubert'
        elif method == 'logreg':
            result = analyze_with_trained_model(text)
            result['method_used'] = 'logreg'
        else:
            return jsonify({'error': f'Неизвестный метод: {method}'}), 400
        
        reviews = load_reviews()
        review_record = {
            'text': result['text'],
            'sentiment': result['sentiment'],
            'emoji': result['emoji'],
            'color': result['color'],
            'score': result['score'],
            'keywords': result.get('keywords', []),
            'method': method,
            'timestamp': result.get('timestamp', '')
        }
        reviews.insert(0, review_record)
        reviews = reviews[:50]
        save_reviews(reviews)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Ошибка при анализе: {str(e)}'}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        method = request.form.get('method', 'dictionary')
        
        if 'file' not in request.files:
            return jsonify({'error': 'Файл не выбран'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'Файл не выбран'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': f'Неподдерживаемый тип файла'}), 400
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        filetype = filename.rsplit('.', 1)[1].lower()
        texts = parse_uploaded_file(filepath, filetype)
        
        if not texts:
            return jsonify({'error': 'В файле не найдено текстов для анализа'}), 400
        
        if len(texts) > 100:
            return jsonify({'error': f'Слишком много отзывов. Максимум 100'}), 400
        
        results = []
        reviews = load_reviews()
        
        for text in texts:
            if method == 'dictionary':
                result = analyze_with_dictionary(text)
            elif method == 'knn':
                result = analyze_with_knn(text)
            elif method == 'rubert':
                result = analyze_with_rubert(text)
            elif method == 'logreg':
                result = analyze_with_trained_model(text)
            else:
                result = analyze_with_dictionary(text)
            
            results.append({
                'text': result['text'][:200],
                'sentiment': result['sentiment'],
                'emoji': result['emoji'],
                'score': result['score'],
                'keywords': result.get('keywords', [])[:3]
            })
            
            review_record = {
                'text': result['text'],
                'sentiment': result['sentiment'],
                'emoji': result['emoji'],
                'color': result['color'],
                'score': result['score'],
                'keywords': result.get('keywords', []),
                'method': method,
                'timestamp': result.get('timestamp', '')
            }
            reviews.insert(0, review_record)
        
        reviews = reviews[:50]
        save_reviews(reviews)
        
        stats = {
            'positive': len([r for r in results if r['sentiment'] == 'positive']),
            'negative': len([r for r in results if r['sentiment'] == 'negative']),
            'neutral': len([r for r in results if r['sentiment'] == 'neutral'])
        }
        
        os.remove(filepath)
        
        return jsonify({
            'success': True,
            'total': len(results),
            'stats': stats,
            'results': results[:20]
        })
        
    except Exception as e:
        return jsonify({'error': f'Ошибка при обработке файла: {str(e)}'}), 500

@app.route('/reviews', methods=['GET'])
def get_reviews():
    try:
        reviews = load_reviews()
        return jsonify(reviews[:15])
    except Exception as e:
        return jsonify({'error': f'Ошибка при загрузке отзывов: {str(e)}'}), 500

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
