#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест безопасности для PermisDeConduire-Online.be
Проверка защиты бесплатного и платного контента
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class SecurityTester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

    def test_url_access(self, url, content_type):
        """Тест доступа к URL"""
        print(f"\n📋 Тестирование: {content_type}")
        print(f"   URL: {url}")

        try:
            response = self.session.get(url, timeout=10, allow_redirects=True)

            print(f"   HTTP статус: {response.status_code}")

            # Проверка редиректа
            if response.url != url:
                print(f"   🔄 Редирект на: {response.url}")
                if 'login' in response.url.lower() or 'connexion' in response.url.lower():
                    return {
                        'type': content_type,
                        'protected': True,
                        'reason': 'Redirect to login',
                        'accessible': False
                    }

            # Парсинг контента
            soup = BeautifulSoup(response.text, 'html.parser')

            # Проверка на формы авторизации
            login_required = bool(soup.find('form', class_=lambda x: x and 'login' in str(x).lower()))

            # Проверка на сообщения о платном контенте
            premium_required = bool(soup.find_all(string=lambda x: x and any(
                word in str(x).lower() for word in ['premium', 'abonnement', 'payant', 's\'inscrire']
            )))

            # Проверка наличия вопросов/контента
            has_questions = bool(
                soup.find_all('input', {'type': 'radio'}) or
                soup.find_all('input', {'type': 'checkbox'})
            )

            has_theory = bool(soup.find_all(['h2', 'h3', 'p'], string=True))

            # Вердикт
            if login_required:
                status = "🔒 ЗАЩИЩЕНО: Требуется авторизация"
                protected = True
                accessible = False
            elif premium_required:
                status = "💰 ЗАЩИЩЕНО: Требуется подписка"
                protected = True
                accessible = False
            elif has_questions or has_theory:
                status = "⚠️ ДОСТУПНО: Контент доступен без авторизации"
                protected = False
                accessible = True
            else:
                status = "ℹ️ НЕОПРЕДЕЛЕННО: Контент не найден"
                protected = None
                accessible = False

            print(f"   {status}")

            return {
                'type': content_type,
                'protected': protected,
                'accessible': accessible,
                'has_questions': has_questions,
                'has_theory': has_theory,
                'login_required': login_required,
                'premium_required': premium_required
            }

        except Exception as e:
            print(f"   ❌ Ошибка: {str(e)}")
            return {
                'type': content_type,
                'protected': None,
                'accessible': False,
                'error': str(e)
            }


def main():
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║   ТЕСТ БЕЗОПАСНОСТИ КОНТЕНТА                               ║
    ║   PermisDeConduire-Online.be                               ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    tester = SecurityTester("https://www.permisdeconduire-online.be")

    # URLs для тестирования (из реального анализа сайта)
    test_cases = [
        {
            'url': 'https://www.permisdeconduire-online.be/theorie/theorie-permis-b',
            'type': 'Главная страница теории'
        },
        {
            'url': 'https://www.permisdeconduire-online.be/theorie/theorie',
            'type': 'Раздел "Théorie"'
        },
        {
            'url': 'https://www.permisdeconduire-online.be/theorie/examens',
            'type': 'Раздел "Examens" (экзамены)'
        },
        {
            'url': 'https://www.permisdeconduire-online.be/theorie/theorie/theorie-permis-b/intro',
            'type': 'Теория - Введение'
        },
        {
            'url': 'https://www.permisdeconduire-online.be/theorie/reactions',
            'type': 'Раздел "Réactions"'
        },
    ]

    results = []

    for test in test_cases:
        result = tester.test_url_access(test['url'], test['type'])
        if result:
            results.append(result)

    # Итоговый отчет
    print(f"\n{'='*70}")
    print("📊 ИТОГОВЫЙ ОТЧЕТ БЕЗОПАСНОСТИ")
    print('='*70 + "\n")

    protected_count = sum(1 for r in results if r.get('protected') is True)
    accessible_count = sum(1 for r in results if r.get('accessible') is True)
    unknown_count = sum(1 for r in results if r.get('protected') is None)

    print(f"✅ Защищенных разделов: {protected_count}/{len(results)}")
    print(f"⚠️  Доступных без авторизации: {accessible_count}/{len(results)}")
    print(f"❓ Неопределенных: {unknown_count}/{len(results)}\n")

    if accessible_count > 0:
        print("📝 ДОСТУПНЫЙ КОНТЕНТ БЕЗ АВТОРИЗАЦИИ:\n")
        for r in results:
            if r.get('accessible'):
                print(f"   ✓ {r['type']}")
                if r.get('has_theory'):
                    print(f"     → Теоретический контент найден")
                if r.get('has_questions'):
                    print(f"     → Вопросы найдены")
        print()

    if protected_count > 0:
        print("🔒 ЗАЩИЩЕННЫЙ КОНТЕНТ:\n")
        for r in results:
            if r.get('protected') is True:
                reason = []
                if r.get('login_required'):
                    reason.append("требуется логин")
                if r.get('premium_required'):
                    reason.append("требуется подписка")
                print(f"   ✓ {r['type']}")
                print(f"     → {', '.join(reason)}")
        print()

    # Вердикт
    print('='*70)
    print("🔐 ВЕРДИКТ:")
    print('='*70 + "\n")

    if accessible_count > 0 and protected_count > 0:
        print("⚖️  СМЕШАННАЯ ЗАЩИТА\n")
        print("➤ Часть контента доступна бесплатно")
        print("➤ Часть контента защищена авторизацией")
        print("➤ Можно скачать ТОЛЬКО бесплатный контент")
        print("➤ Платный контент требует подписки\n")
    elif accessible_count == len(results):
        print("⚠️  ВСЁ ДОСТУПНО БЕЗ АВТОРИЗАЦИИ\n")
        print("➤ Весь контент доступен публично")
        print("➤ Скачивание разрешено (публичный контент)")
        print("➤ Владельцу следует улучшить защиту\n")
    elif protected_count == len(results):
        print("✅ ВСЁ ЗАЩИЩЕНО ПРАВИЛЬНО\n")
        print("➤ Весь контент требует авторизации")
        print("➤ Система защиты работает корректно")
        print("➤ Скачивание возможно только с подпиской\n")
    else:
        print("❓ РЕЗУЛЬТАТЫ НЕОДНОЗНАЧНЫ\n")
        print("➤ Требуется дополнительный анализ")
        print("➤ Некоторые URL могут быть неверными\n")

    print('='*70 + "\n")


if __name__ == "__main__":
    main()
