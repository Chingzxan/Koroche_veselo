document.addEventListener('DOMContentLoaded', function() {
            // === ПЕРЕМЕННЫЕ ===
            let selectedFile = null;
            
            // === ВКЛАДКИ ===
            const tabs = document.querySelectorAll('.tab-btn');
            tabs.forEach(tab => {
                tab.addEventListener('click', () => {
                    const tabId = tab.dataset.tab;
                    document.querySelectorAll('.tab-btn').forEach(t => t.classList.remove('active'));
                    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                    tab.classList.add('active');
                    document.getElementById(`${tabId}-tab`).classList.add('active');
                });
            });

            // === РАБОТА С ФАЙЛАМИ ===
            const fileUploadArea = document.getElementById('file-upload-area');
            const fileInput = document.getElementById('file-input');

            if (fileUploadArea) {
                fileUploadArea.addEventListener('click', () => fileInput.click());
                
                fileUploadArea.addEventListener('dragover', (e) => {
                    e.preventDefault();
                    fileUploadArea.classList.add('dragover');
                });
                
                fileUploadArea.addEventListener('dragleave', () => {
                    fileUploadArea.classList.remove('dragover');
                });
                
                fileUploadArea.addEventListener('drop', (e) => {
                    e.preventDefault();
                    fileUploadArea.classList.remove('dragover');
                    const files = e.dataTransfer.files;
                    if (files.length > 0) {
                        selectedFile = files[0];
                        fileUploadArea.innerHTML = `<div>📄 Выбран: ${selectedFile.name}</div>
                            <div class="file-info">Нажмите "Анализировать файл" для начала</div>`;
                    }
                });
            }

            if (fileInput) {
                fileInput.addEventListener('change', (e) => {
                    if (e.target.files.length > 0) {
                        selectedFile = e.target.files[0];
                        fileUploadArea.innerHTML = `<div>📄 Выбран: ${selectedFile.name}</div>
                            <div class="file-info">Нажмите "Анализировать файл" для начала</div>`;
                    }
                });
            }

            // === ЗАГРУЗКА ФАЙЛА ===
            document.getElementById('upload-btn').addEventListener('click', async () => {
                if (!selectedFile) {
                    alert('Пожалуйста, выберите файл');
                    return;
                }

                const method = document.querySelector('input[name="batch-method"]:checked').value;
                const formData = new FormData();
                formData.append('file', selectedFile);
                formData.append('method', method);

                const uploadBtn = document.getElementById('upload-btn');
                const progressContainer = document.getElementById('progress-container');
                const progressFill = document.getElementById('progress-fill');
                const progressText = document.getElementById('progress-text');
                const batchResultContainer = document.getElementById('batch-result-container');

                uploadBtn.disabled = true;
                uploadBtn.textContent = '⏳ Обработка...';
                progressContainer.style.display = 'block';
                progressFill.style.width = '30%';
                progressText.textContent = 'Анализ файла...';

                try {
                    const response = await fetch('/upload', {
                        method: 'POST',
                        body: formData
                    });

                    progressFill.style.width = '100%';
                    progressText.textContent = 'Завершено!';

                    if (!response.ok) {
                        const errorData = await response.json();
                        throw new Error(errorData.error || 'Ошибка при загрузке');
                    }

                    const data = await response.json();
                    
                    if (data.error) {
                        alert(data.error);
                    } else {
                        displayBatchResults(data);
                        batchResultContainer.style.display = 'block';
                        await loadReviews();
                        selectedFile = null;
                        fileUploadArea.innerHTML = `<div>📁 Перетащите файл сюда или нажмите для выбора</div>
                            <div class="file-info">Поддерживаются: CSV, TXT, JSON (максимум 100 отзывов)</div>`;
                    }
                } catch (error) {
                    console.error('Ошибка:', error);
                    alert(error.message || 'Произошла ошибка');
                } finally {
                    uploadBtn.disabled = false;
                    uploadBtn.textContent = '📊 Анализировать файл';
                    setTimeout(() => {
                        progressContainer.style.display = 'none';
                    }, 1500);
                }
            });

            function displayBatchResults(data) {
                const statsContainer = document.getElementById('batch-stats');
                statsContainer.innerHTML = `
                    <div class="stat-card positive">
                        <div class="stat-number">${data.stats.positive}</div>
                        <div>😊 Позитивных</div>
                    </div>
                    <div class="stat-card negative">
                        <div class="stat-number">${data.stats.negative}</div>
                        <div>😞 Негативных</div>
                    </div>
                    <div class="stat-card neutral">
                        <div class="stat-number">${data.stats.neutral}</div>
                        <div>😐 Нейтральных</div>
                    </div>
                `;

                const resultsContainer = document.getElementById('batch-results');
                resultsContainer.innerHTML = `<h4>📝 Первые ${data.results.length} отзывов:</h4>` + 
                    data.results.map(r => `
                        <div class="batch-item" style="border-left-color: ${getColorForSentiment(r.sentiment)}">
                            <strong>${r.emoji} ${getSentimentText(r.sentiment)}</strong> (оценка: ${r.score})
                            <div style="margin-top: 5px; font-size: 12px; color: #666;">${escapeHtml(r.text)}</div>
                            ${r.keywords.length ? `<div style="margin-top: 5px; font-size: 11px;">🔑 ${r.keywords.join(', ')}</div>` : ''}
                        </div>
                    `).join('');
            }

            // === АНАЛИЗ ОДНОГО ОТЗЫВА ===
            const analyzeBtn = document.getElementById('analyze-btn');
            const reviewText = document.getElementById('review-text');
            const resultSection = document.getElementById('result-section');
            const resultContent = document.getElementById('result-content');
            const reviewsFeed = document.getElementById('reviews-feed');

            loadReviews();

            analyzeBtn.addEventListener('click', async function() {
                const text = reviewText.value.trim();
                
                if (!text) {
                    alert('Пожалуйста, введите текст отзыва');
                    return;
                }

                const selectedMethod = document.querySelector('input[name="method"]:checked').value;

                analyzeBtn.disabled = true;
                analyzeBtn.textContent = '⏳ Анализируем...';

                try {
                    const response = await fetch('/analyze', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ 
                            text: text,
                            method: selectedMethod
                        })
                    });

                    if (!response.ok) {
                        const errorData = await response.json();
                        throw new Error(errorData.error || 'Ошибка при анализе');
                    }

                    const result = await response.json();
                    displayResult(result);
                    await loadReviews();
                    reviewText.value = '';
                    
                } catch (error) {
                    console.error('Ошибка:', error);
                    alert(error.message || 'Произошла ошибка при анализе отзыва');
                } finally {
                    analyzeBtn.disabled = false;
                    analyzeBtn.textContent = '🚀 Анализировать';
                }
            });

            function displayResult(result) {
                resultSection.classList.remove('hidden');
                
                const methodNames = {
                    'dictionary': 'Словарный метод',
                    'knn': 'KNN (k-ближайших соседей)',
                    'rubert': 'RuBERT (трансформер)',
                    'logreg': 'Логистическая регрессия'
                };
                
                const sentimentText = {
                    'positive': 'Позитивная 😊',
                    'negative': 'Негативная 😞',
                    'neutral': 'Нейтральная 😐'
                };
                
                resultContent.innerHTML = `
                    <div class="review-text">
                        <strong>📝 Текст:</strong> ${escapeHtml(result.text)}
                    </div>
                    <div class="sentiment-display" style="border-left: 4px solid ${result.color}">
                        <span class="emoji">${result.emoji}</span>
                        <span class="sentiment-text">
                            ${sentimentText[result.sentiment]} (${result.score.toFixed(2)})
                        </span>
                    </div>
                    <div class="method-info">
                        <strong>🧠 Модель:</strong> ${methodNames[result.method_used] || result.method_used}
                    </div>
                    ${result.keywords && result.keywords.length > 0 ? `
                        <div class="keywords-section">
                            <strong>🔑 Ключевые слова:</strong>
                            <div class="keywords-tags">
                                ${result.keywords.slice(0, 5).map(keyword => 
                                    `<span class="keyword-tag">${escapeHtml(keyword)}</span>`
                                ).join('')}
                            </div>
                        </div>
                    ` : '<div class="keywords-section"><strong>🔑 Ключевые слова:</strong> не найдены</div>'}
                `;
            }

            async function loadReviews() {
                try {
                    const response = await fetch('/reviews');
                    if (!response.ok) {
                        throw new Error('Ошибка при загрузке отзывов');
                    }
                    
                    const reviews = await response.json();
                    displayReviews(reviews);
                } catch (error) {
                    console.error('Ошибка загрузки отзывов:', error);
                    reviewsFeed.innerHTML = '<div class="error">❌ Не удалось загрузить отзывы</div>';
                }
            }

            function displayReviews(reviews) {
                if (!reviews || reviews.length === 0) {
                    reviewsFeed.innerHTML = '<div class="loading">📭 Пока нет отзывов</div>';
                    return;
                }

                const methodNames = {
                    'dictionary': 'словарный',
                    'knn': 'KNN',
                    'rubert': 'RuBERT',
                    'logreg': 'лог.регрессия'
                };

                const sentimentText = {
                    'positive': 'Позитивный',
                    'negative': 'Негативный',
                    'neutral': 'Нейтральный'
                };

                reviewsFeed.innerHTML = reviews.map(review => `
                    <div class="review-card ${review.sentiment}">
                        <div class="review-header">
                            <span class="review-emoji">${review.emoji || '😐'}</span>
                            <span class="review-sentiment">${sentimentText[review.sentiment]}</span>
                            <span class="review-method">${methodNames[review.method] || review.method}</span>
                        </div>
                        <div class="review-text-preview">
                            ${escapeHtml(review.text.substring(0, 100))}${review.text.length > 100 ? '...' : ''}
                        </div>
                        <div class="review-score">⭐ Оценка: ${review.score}</div>
                    </div>
                `).join('');
            }

            function getColorForSentiment(sentiment) {
                const colors = {
                    'positive': '#48bb78',
                    'negative': '#f56565',
                    'neutral': '#667eea'
                };
                return colors[sentiment] || '#999';
            }

            function getSentimentText(sentiment) {
                const texts = {
                    'positive': 'Позитивный',
                    'negative': 'Негативный',
                    'neutral': 'Нейтральный'
                };
                return texts[sentiment] || sentiment;
            }

            function escapeHtml(text) {
                if (!text) return '';
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML;
            }

            reviewText.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' && e.ctrlKey) {
                    e.preventDefault();
                    analyzeBtn.click();
                }
            });
            // Летающие звёзды во все стороны
function createFloatingStars() {
    const oldContainer = document.querySelector('.star-field');
    if (oldContainer) oldContainer.remove();

    const starContainer = document.createElement('div');
    starContainer.className = 'star-field';
    document.body.appendChild(starContainer);
    let active_emod=0;
    const Max_emod=20;
    function addStar() {
        if(active_emod>Max_emod)return;
        const star = document.createElement('div');
        star.className = 'floating-star';
        const icons = ['⭐', '🌟', '✨', '💫', '⭐', '🌟', '✧', '✦','🐱','😸','😻','😺'];
        star.textContent = icons[Math.floor(Math.random() * icons.length)];
        
        // Случайный размер
        const size = 14 + Math.random() * 22;
        star.style.fontSize = size + 'px';
        
        // Выбираем сторону появления: 0-верх, 1-низ, 2-лево, 3-право
        const edge = Math.floor(Math.random() * 4);
        let startX, startY;
        const padding = 30; // отступ от края
        
       if (edge === 0) { // верх
       startX = Math.random() * window.innerWidth;
        startY = -padding;
      } else if (edge === 1) { // низ
      startX = Math.random() * window.innerWidth;
      startY = window.innerHeight + padding;
      } else if (edge === 2) { // лево
     startX = -padding;
     startY = Math.random() * window.innerHeight;
     } else { // право
    startX = window.innerWidth + padding;
    startY = Math.random() * window.innerHeight;
    }
        
        star.style.left = startX + 'px';
        star.style.top = startY + 'px';
        
        // Случайное смещение: от -300 до +300 пикселей по X и Y
        const tx = (Math.random() - 0.5) * 600;
        const ty = (Math.random() - 0.5) * 600;
        star.style.setProperty('--tx', tx + 'px');
        star.style.setProperty('--ty', ty + 'px');
        
        // Длительность полёта: от 2.5 до 8 секунд
        const duration = 2.5 + Math.random() * 4.5;
        star.style.animationDuration = duration + 's';
        
        // Задержка перед стартом
        star.style.animationDelay = Math.random() * 4 + 's';
        active_emod++;
        starContainer.appendChild(star);
        
        star.addEventListener('animationend', () => {
            star.remove();
            active_emod--;
        });
    }

    // Запуск звёзд с интервалом 0.6 секунды
    setInterval(() => {
        addStar();
    }, 600);
    }   

// Запускаем после загрузки страницы
    window.addEventListener('load', createFloatingStars);
        });
