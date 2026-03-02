#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скачивание изображений дорожных знаков из кодекса
"""

import requests
import json
import os
import time
from pathlib import Path

def download_images():
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║   СКАЧИВАНИЕ ИЗОБРАЖЕНИЙ ДОРОЖНЫХ ЗНАКОВ                   ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    # Создаём папку для изображений
    images_dir = Path('../output/images')
    images_dir.mkdir(parents=True, exist_ok=True)

    # Загружаем анализ изображений
    with open('../output/images_analysis.json', 'r', encoding='utf-8') as f:
        analysis = json.load(f)

    print(f"📊 Всего изображений: {analysis['total_images']}")
    print(f"📁 Папка для сохранения: {images_dir}\n")

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })

    downloaded = 0
    skipped = 0
    errors = 0

    # Создаём маппинг для переименования файлов
    image_mapping = {}

    print("🚀 Начало загрузки...\n")

    for i, img_data in enumerate(analysis['images'], 1):
        url = img_data['full_url']
        original_filename = url.split('/')[-1]

        # Создаём понятное имя файла
        article_num = img_data['article'].replace('.', '').replace('/', '_')
        sign_code = img_data['alt'] if img_data['alt'] else f"img{img_data['image_index']}"
        sign_code = sign_code.replace(' ', '_').replace('/', '_')

        new_filename = f"art{article_num}_{sign_code}_{img_data['image_index']}.png"
        filepath = images_dir / new_filename

        # Сохраняем маппинг
        image_mapping[original_filename] = {
            'new_filename': new_filename,
            'article': img_data['article'],
            'article_title': img_data['article_title'],
            'sign_code': img_data['alt'],
            'rule_text': img_data['rule_text']
        }

        # Пропускаем уже загруженные
        if filepath.exists():
            skipped += 1
            continue

        try:
            print(f"[{i}/{analysis['total_images']}] {new_filename[:50]}...", end=' ')

            response = session.get(url, timeout=10)
            response.raise_for_status()

            with open(filepath, 'wb') as f:
                f.write(response.content)

            downloaded += 1
            print("✅")

            # Небольшая пауза между запросами
            time.sleep(0.3)

        except Exception as e:
            errors += 1
            print(f"❌ Ошибка: {e}")

    print("\n" + "="*70)
    print("📊 РЕЗУЛЬТАТЫ")
    print("="*70 + "\n")

    print(f"✅ Загружено новых: {downloaded}")
    print(f"⏭️  Уже существовало: {skipped}")
    print(f"❌ Ошибок: {errors}")
    print(f"📁 Всего файлов в папке: {len(list(images_dir.glob('*.png')))}\n")

    # Сохраняем маппинг изображений
    mapping_file = images_dir / 'image_mapping.json'
    with open(mapping_file, 'w', encoding='utf-8') as f:
        json.dump(image_mapping, f, ensure_ascii=False, indent=2)
    print(f"💾 Маппинг файлов сохранён: {mapping_file}\n")

    # Создаём индекс изображений
    if downloaded > 0 or skipped > 0:
        create_image_index(images_dir, analysis)


def create_image_index(images_dir, analysis):
    """Создаёт HTML индекс изображений с правилами"""

    index_file = images_dir / 'index.html'

    html = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Дорожные знаки - Code de la Route</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        h1 {
            color: #333;
            border-bottom: 4px solid #667eea;
            padding-bottom: 15px;
            font-size: 2.5em;
            margin-bottom: 20px;
        }
        .stats {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        .stat-item {
            text-align: center;
        }
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            display: block;
        }
        .stat-label {
            font-size: 0.9em;
            opacity: 0.9;
        }
        .article-section {
            background: #f8f9fa;
            padding: 25px;
            border-radius: 10px;
            margin: 30px 0;
            border-left: 5px solid #667eea;
        }
        .article-title {
            color: #667eea;
            font-size: 1.5em;
            font-weight: bold;
            margin-bottom: 15px;
        }
        .article-rule {
            background: white;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
            line-height: 1.6;
            color: #555;
            border: 1px solid #e0e0e0;
        }
        .signs-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .sign-card {
            background: white;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s, box-shadow 0.3s;
            border: 2px solid #e0e0e0;
        }
        .sign-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 15px rgba(0,0,0,0.2);
            border-color: #667eea;
        }
        .sign-card img {
            max-width: 100%;
            height: auto;
            max-height: 120px;
            margin: 10px 0;
        }
        .sign-code {
            font-weight: bold;
            color: #667eea;
            font-size: 1.2em;
            margin: 10px 0;
        }
        .sign-filename {
            font-size: 0.75em;
            color: #999;
            word-break: break-all;
        }
        .search-box {
            margin: 20px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
        }
        .search-box input {
            width: 100%;
            padding: 12px;
            font-size: 1em;
            border: 2px solid #667eea;
            border-radius: 8px;
            box-sizing: border-box;
        }
        .no-results {
            text-align: center;
            padding: 40px;
            color: #999;
            font-size: 1.2em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚦 Дорожные знаки - Code de la Route Belgique</h1>

        <div class="stats">
            <div class="stat-item">
                <span class="stat-number">""" + str(analysis['total_images']) + """</span>
                <span class="stat-label">Изображений</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">""" + str(analysis['unique_sign_types']) + """</span>
                <span class="stat-label">Типов знаков</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">""" + str(analysis['total_articles_with_images']) + """</span>
                <span class="stat-label">Статей</span>
            </div>
        </div>

        <div class="search-box">
            <input type="text" id="searchInput" placeholder="🔍 Поиск по коду знака, номеру статьи или тексту правила..." onkeyup="filterArticles()">
        </div>

        <div id="articlesContainer">
"""

    # Группируем изображения по статьям
    articles_dict = {}
    for img in analysis['images']:
        article_num = img['article']
        if article_num not in articles_dict:
            articles_dict[article_num] = {
                'title': img['article_title'],
                'rule_text': img['rule_text'],
                'images': []
            }

        # Формируем имя файла изображения
        article_num_clean = article_num.replace('.', '').replace('/', '_')
        sign_code = img['alt'] if img['alt'] else f"img{img['image_index']}"
        sign_code_clean = sign_code.replace(' ', '_').replace('/', '_')
        filename = f"art{article_num_clean}_{sign_code_clean}_{img['image_index']}.png"

        articles_dict[article_num]['images'].append({
            'filename': filename,
            'code': sign_code,
            'index': img['image_index']
        })

    # Генерируем HTML для каждой статьи
    def sort_key(article_num):
        """Создаёт ключ для сортировки номеров статей"""
        try:
            # Убираем точку в конце
            num = article_num.rstrip('.')

            # Обрабатываем специальные случаи
            replacements = {
                'bis': '.1',
                'ter': '.2',
                'quater': '.3',
                'quinquies': '.4',
                'sexies': '.5',
                'septies': '.6',
                'octies': '.7'
            }

            for old, new in replacements.items():
                if old in num:
                    num = num.replace(old, new)
                    break

            # Убираем слеши
            num = num.replace('/', '.')

            # Пытаемся конвертировать в float
            return float(num)
        except:
            # Если не получилось, возвращаем большое число
            return 9999

    for article_num in sorted(articles_dict.keys(), key=sort_key):
        article_data = articles_dict[article_num]

        html += f"""
        <div class="article-section" data-article="{article_num}" data-title="{article_data['title']}" data-rule="{article_data['rule_text']}">
            <div class="article-title">
                📋 {article_data['title']}
            </div>

            <div class="article-rule">
                <strong>Правило:</strong><br>
                {article_data['rule_text']}
            </div>

            <div class="signs-grid">
"""

        for img in article_data['images']:
            html += f"""
                <div class="sign-card" data-code="{img['code']}">
                    <img src="{img['filename']}" alt="{img['code']}" loading="lazy">
                    <div class="sign-code">{img['code'] if img['code'] else '—'}</div>
                    <div class="sign-filename">{img['filename']}</div>
                </div>
"""

        html += """
            </div>
        </div>
"""

    html += """
        </div>
    </div>

    <script>
        function filterArticles() {
            const searchTerm = document.getElementById('searchInput').value.toLowerCase();
            const articles = document.querySelectorAll('.article-section');
            let visibleCount = 0;

            articles.forEach(article => {
                const articleNum = article.dataset.article.toLowerCase();
                const title = article.dataset.title.toLowerCase();
                const rule = article.dataset.rule.toLowerCase();
                const signs = Array.from(article.querySelectorAll('.sign-card'))
                    .map(sign => sign.dataset.code.toLowerCase())
                    .join(' ');

                const matches = articleNum.includes(searchTerm) ||
                               title.includes(searchTerm) ||
                               rule.includes(searchTerm) ||
                               signs.includes(searchTerm);

                if (matches || searchTerm === '') {
                    article.style.display = 'block';
                    visibleCount++;
                } else {
                    article.style.display = 'none';
                }
            });

            // Показываем сообщение если ничего не найдено
            const container = document.getElementById('articlesContainer');
            let noResults = container.querySelector('.no-results');

            if (visibleCount === 0 && searchTerm !== '') {
                if (!noResults) {
                    noResults = document.createElement('div');
                    noResults.className = 'no-results';
                    noResults.textContent = '❌ Ничего не найдено';
                    container.appendChild(noResults);
                }
            } else if (noResults) {
                noResults.remove();
            }
        }
    </script>
</body>
</html>
"""

    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"📄 HTML индекс создан: {index_file}")
    print(f"   Откройте в браузере для просмотра всех знаков с правилами\n")
    print(f"   ✨ Функции:")
    print(f"      • Изображения привязаны к статьям")
    print(f"      • Показан текст правила для каждого знака")
    print(f"      • Поиск по коду знака, статье или тексту")
    print(f"      • Понятные имена файлов (art3_C5_1.png)\n")


if __name__ == "__main__":
    download_images()
