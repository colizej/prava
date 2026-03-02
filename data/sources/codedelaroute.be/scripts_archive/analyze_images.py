#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Анализ изображений в кодексе дорожного движения
"""

import json
import re
from collections import Counter
from bs4 import BeautifulSoup

def analyze_images():
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║   АНАЛИЗ ИЗОБРАЖЕНИЙ В КОДЕКСЕ                             ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    # Загружаем JSON
    with open('../output/code_de_la_route_complet.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"📄 Документ: {data['title'][:80]}...")
    print(f"📊 Всего статей: {len(data['articles'])}\n")

    # Анализ изображений
    all_images = []
    articles_with_images = []
    image_types = Counter()

    for article in data['articles']:
        if 'html' in article and article['html']:
            soup = BeautifulSoup(article['html'], 'html.parser')
            images = soup.find_all('img')

            if images:
                # Получаем текст правила (первые 300 символов)
                rule_text = article.get('full_text', '')[:300] + '...' if len(article.get('full_text', '')) > 300 else article.get('full_text', '')

                articles_with_images.append({
                    'number': article['number'],
                    'title': article['title'],
                    'rule_text': rule_text,
                    'full_text': article.get('full_text', ''),
                    'image_count': len(images),
                    'images': []
                })

                img_index_in_article = 0
                for img in images:
                    src = img.get('src', '')
                    alt = img.get('alt', '')

                    if src:
                        img_index_in_article += 1
                        all_images.append({
                            'src': src,
                            'alt': alt,
                            'full_url': f"https://www.codedelaroute.be{src}" if src.startswith('/') else src,
                            'article': article['number'],
                            'article_title': article['title'],
                            'rule_text': rule_text,
                            'image_index': img_index_in_article
                        })
                        articles_with_images[-1]['images'].append({
                            'src': src,
                            'alt': alt,
                            'index': img_index_in_article
                        })

                        # Определяем тип знака по alt
                        if alt:
                            # Извлекаем буквенно-цифровой код (например, C5, F17, B22)
                            code_match = re.search(r'([A-Z]\d+[a-z]*)', alt)
                            if code_match:
                                code = code_match.group(1)
                                image_types[code] = image_types.get(code, 0) + 1

    print("="*70)
    print("📊 СТАТИСТИКА")
    print("="*70 + "\n")

    print(f"✅ Всего изображений найдено: {len(all_images)}")
    print(f"✅ Статей с изображениями: {len(articles_with_images)}/{len(data['articles'])}")
    print(f"✅ Уникальных типов знаков: {len(image_types)}\n")

    if image_types:
        print("="*70)
        print("🚦 ТОП-20 ТИПОВ ДОРОЖНЫХ ЗНАКОВ")
        print("="*70 + "\n")

        for sign_type, count in image_types.most_common(20):
            print(f"   {sign_type:8s} : {count:3d} раз")

    print("\n" + "="*70)
    print("📝 ПРИМЕРЫ СТАТЕЙ С ИЗОБРАЖЕНИЯМИ")
    print("="*70 + "\n")

    for i, article in enumerate(articles_with_images[:10], 1):
        print(f"{i}. {article['title']}")
        print(f"   Изображений: {article['image_count']}")
        print(f"   Знаки: {', '.join([img['alt'] for img in article['images'] if img['alt']])}")
        print()

    if len(articles_with_images) > 10:
        print(f"... и ещё {len(articles_with_images) - 10} статей с изображениями\n")

    # Сохраняем список всех изображений
    images_output = {
        'total_images': len(all_images),
        'total_articles_with_images': len(articles_with_images),
        'unique_sign_types': len(image_types),
        'sign_types': dict(image_types),
        'images': all_images,
        'articles_with_images': articles_with_images
    }

    output_file = '../output/images_analysis.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(images_output, f, ensure_ascii=False, indent=2)

    print("="*70)
    print(f"💾 Анализ сохранён: {output_file}")
    print("="*70 + "\n")

    # Создаём список URL для скачивания
    urls_file = '../output/image_urls.txt'
    with open(urls_file, 'w', encoding='utf-8') as f:
        for img in all_images:
            f.write(img['full_url'] + '\n')

    print(f"📋 Список URL изображений: {urls_file}")
    print(f"   Можно использовать для скачивания: wget -i {urls_file}\n")


if __name__ == "__main__":
    analyze_images()
