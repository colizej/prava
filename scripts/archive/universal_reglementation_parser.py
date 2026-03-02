#!/usr/bin/env python3
"""
UNIVERSAL PARSER: codedelaroute.be (FR) + wegcode.be (NL) + RU translation
- Для каждой статьи ищет соответствие по номеру и заголовку на обоих сайтах
- Парсит контент FR и NL, объединяет в один JSON по шаблону _TEMPLATE.json
- Добавляет перевод RU (через API или Deepl/Google, если доступно)
- Сохраняет в data/reglementation_db/

Требования:
- requests, beautifulsoup4
- Для RU: требуется функция translate(text, src, tgt)

Usage:
    python3 scripts/universal_reglementation_parser.py --fr_url <FR_URL> --nl_url <NL_URL>

"""
import os
import re
import json
import argparse

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from copy import deepcopy
from datetime import datetime

TEMPLATE_PATH = 'data/reglementation/_TEMPLATE.json'
OUTPUT_DIR = 'data/reglementation_db/'
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9,nl-NL,nl;q=0.9",
}

# --- Dummy translation (replace with real API) ---
def translate(text, src, tgt):
    # TODO: Replace with real translation API (DeepL, Google, etc.)
    return f"[RU] {text}"

# --- Download and parse page ---
def fetch_soup(url):
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return BeautifulSoup(resp.content, 'lxml')

# --- Extract all articles from a regulation page ---
def extract_articles(soup, lang):
    main = soup.find('main', class_='site-main') or soup.find('main') or soup.body
    stc = main.find('div', class_='stickytoc-content')
    articles = []
    current = None
    for elem in stc.children:
        if isinstance(elem, Tag) and elem.name == 'h5' and ('Article' in elem.get_text() or 'Artikel' in elem.get_text()):
            if current:
                articles.append(current)
            current = {
                'header': elem,
                'content_blocks': []
            }
        elif current and isinstance(elem, Tag):
            current['content_blocks'].append(elem)
    if current:
        articles.append(current)

    # --- Подпункты и изображения ---
    def parse_sections(blocks):
        sections = []
        current = None
        subpoints = None
        in_subpoints = False
        for b in blocks:
            txt = b.get_text(separator=' ', strip=True)
            # Главная секция (например, 65.1., 65.2. и т.д.)
            m_main = re.match(r'^(\d+\.\d*\.?)(\s|$)', txt)
            # Подпункт вида 1°, 2°, ... (в начале строки или с <strong> внутри)
            m_sub = re.match(r'^(\d+)°', txt) or (b.find('strong') and re.match(r'^(\d+)°', b.find('strong').get_text(strip=True)))
            if m_main:
                if current:
                    sections.append(current)
                current = {'id': m_main.group(1).strip(), 'html': '', 'text': '', 'images': [], 'subpoints': []}
                subpoints = current['subpoints']
                in_subpoints = False
                current['html'] += str(b)
                current['text'] += txt + ' '
            elif m_sub and current and subpoints is not None:
                # Это подпункт внутри текущей секции
                in_subpoints = True
                sub_html = str(b)
                sub_text = txt
                sub_imgs = []
                for img in b.find_all('img'):
                    src = img.get('src')
                    alt = img.get('alt', '')
                    sign_code = None
                    next_text = img.next_sibling
                    if next_text and isinstance(next_text, str):
                        code_match = re.search(r'([A-Z][0-9]{1,3}[a-z]*)', next_text)
                        if code_match:
                            sign_code = code_match.group(1)
                    if not sign_code and alt:
                        code_match = re.search(r'([A-Z][0-9]{1,3}[a-z]*)', alt)
                        if code_match:
                            sign_code = code_match.group(1)
                    sub_imgs.append({
                        'source_url': src,
                        'alt': alt,
                        'sign_code': sign_code,
                        'caption': alt or '',
                    })
                subpoints.append({'id': m_sub.group(1) + '°', 'html': sub_html, 'text': sub_text, 'images': sub_imgs})
            else:
                # Если подпункты закончились, сбрасываем in_subpoints
                if in_subpoints and txt and not m_sub:
                    in_subpoints = False
                # Обычный блок (или вложенный подпункт, или текст)
                if current:
                    current['html'] += str(b)
                    current['text'] += txt + ' '
                    for img in b.find_all('img'):
                        src = img.get('src')
                        alt = img.get('alt', '')
                        sign_code = None
                        next_text = img.next_sibling
                        if next_text and isinstance(next_text, str):
                            code_match = re.search(r'([A-Z][0-9]{1,3}[a-z]*)', next_text)
                            if code_match:
                                sign_code = code_match.group(1)
                        if not sign_code and alt:
                            code_match = re.search(r'([A-Z][0-9]{1,3}[a-z]*)', alt)
                            if code_match:
                                sign_code = code_match.group(1)
                        current['images'].append({
                            'source_url': src,
                            'alt': alt,
                            'sign_code': sign_code,
                            'caption': alt or '',
                        })
        if current:
            sections.append(current)
        # Удаляем subpoints если пустой
        for sec in sections:
            if 'subpoints' in sec and not sec['subpoints']:
                del sec['subpoints']
        return sections

    # Build index by article number
    result = {}
    for idx, art in enumerate(articles):
        h = art['header']
        header_text = h.get_text(strip=True)
        m = re.match(r'(Article|Artikel)\s*(\d+[\w\.]*)\s*[\.:-]?\s*(.*)', header_text)
        article_number = m.group(2) if m else f"{idx+1}"
        title = m.group(3).strip() if m and m.group(3) else header_text
        slug = f"art{article_number.replace('.', '_').replace(' ', '_').lower()}"
        html_blocks = [str(b) for b in art['content_blocks']]
        content_html = '\n'.join(html_blocks)
        content_text = ' '.join(b.get_text(strip=True) for b in art['content_blocks'])
        # --- Новый массив sections с подпунктами и картинками ---
        sections = parse_sections(art['content_blocks'])
        # Собираем все картинки по подпунктам в общий images
        images = []
        for sec in sections:
            for img in sec['images']:
                img_copy = img.copy()
                img_copy['section_id'] = sec['id']
                images.append(img_copy)
        result[article_number] = {
            'article_number': article_number,
            'title': title,
            'slug': slug,
            f'content_html_{lang}': content_html,
            f'content_text_{lang}': content_text,
            f'title_{lang}': title,
            f'sections_{lang}': sections,
            f'images_{lang}': images,
        }
    return result

def main():

    parser = argparse.ArgumentParser(description="Universal FR+NL+RU reglementation parser")
    parser.add_argument('--fr_url', required=True, help='URL to codedelaroute.be (FR)')
    parser.add_argument('--nl_url', required=True, help='URL to wegcode.be (NL)')
    parser.add_argument('--only', type=str, default=None, help='Parse only this article number (e.g. 65)')
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as tf:
        BASE_TEMPLATE = json.load(tf)

    # --- Fetch and parse both pages ---
    soup_fr = fetch_soup(args.fr_url)
    soup_nl = fetch_soup(args.nl_url)
    arts_fr = extract_articles(soup_fr, 'fr')
    arts_nl = extract_articles(soup_nl, 'nl')

    # --- Merge by article number ---
    all_numbers = sorted(set(arts_fr.keys()) | set(arts_nl.keys()), key=lambda x: (int(re.match(r'\d+', x).group()), x))
    if args.only:
        # Поддержка поиска по номеру (например, 65, 65bis, 65ter)
        only_nums = [n for n in all_numbers if n.startswith(args.only)]
    else:
        only_nums = all_numbers
    for num in only_nums:
        data = deepcopy(BASE_TEMPLATE)
        fr = arts_fr.get(num, {})
        nl = arts_nl.get(num, {})
        data['article_number'] = f"Art. {num}"
        data['title'] = fr.get('title', nl.get('title', ''))
        data['title_nl'] = nl.get('title', '')
        data['title_ru'] = translate(data['title'], 'fr', 'ru')
        data['content_html'] = fr.get('content_html_fr', '')
        data['content_html_nl'] = nl.get('content_html_nl', '')
        data['content_html_ru'] = translate(data['content_html'], 'fr', 'ru')
        data['content_text'] = fr.get('content_text_fr', '')
        data['content_text_nl'] = nl.get('content_text_nl', '')
        data['content_text_ru'] = translate(data['content_text'], 'fr', 'ru')
        data['slug'] = fr.get('slug', nl.get('slug', f"art{num}"))
        data['parsed_at'] = datetime.now().isoformat()
        # --- Новые поля: подпункты и изображения ---
        data['sections'] = {
            'fr': fr.get('sections_fr', []),
            'nl': nl.get('sections_nl', [])
        }
        # Только изображения из текущей статьи (FR+NL)
        data['images'] = fr.get('images_fr', []) + nl.get('images_nl', [])
        # definitions и exam_questions будут формироваться только из текста текущей статьи (заглушка)
        data['definitions'] = []
        # TODO: реализовать парсинг определений только из текста текущей статьи
        fname = f"Art_{num.replace('.', '_')}_{data['slug']}.json"
        out_path = os.path.join(OUTPUT_DIR, fname)
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ Saved: {out_path}")

if __name__ == "__main__":
    main()
