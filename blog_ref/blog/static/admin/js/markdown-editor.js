// CodeMirror Markdown Editor for Django Admin
(function() {
    'use strict';

    // Подключаем CodeMirror после загрузки страницы
    document.addEventListener('DOMContentLoaded', function() {
        // Находим все textarea с markdown контентом
        const markdownFields = document.querySelectorAll('textarea#id_content_markdown, textarea#id_description, textarea#id_seo_text');

        if (markdownFields.length === 0) return;

        // Загружаем CodeMirror CSS и JS
        const loadCSS = (href) => {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = href;
            document.head.appendChild(link);
        };

        const loadJS = (src) => {
            return new Promise((resolve, reject) => {
                const script = document.createElement('script');
                script.src = src;
                script.onload = resolve;
                script.onerror = reject;
                document.head.appendChild(script);
            });
        };

        // Загружаем CodeMirror
        loadCSS('https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/codemirror.min.css');
        loadCSS('https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/theme/github.min.css');

        // Добавляем кастомные стили для подсветки
        const style = document.createElement('style');
        style.textContent = `
            /* Ссылки Markdown - зелёные */
            .cm-s-github .cm-link { color: #22c55e !important; font-weight: 500; }
            .cm-s-github .cm-url { color: #16a34a !important; text-decoration: underline; }

            /* Заголовки - фиолетовые */
            .cm-s-github .cm-header { color: #7c3aed !important; font-weight: bold; }

            /* Цитаты - серый фон */
            .cm-s-github .cm-quote { color: #6b7280 !important; font-style: italic; background: #f3f4f6; padding: 2px 4px; }

            /* Жирный текст */
            .cm-s-github .cm-strong { color: #1f2937 !important; font-weight: bold; }

            /* Код - оранжевый */
            .cm-s-github .cm-comment { color: #f59e0b !important; background: #fef3c7; padding: 2px 4px; border-radius: 3px; }
        `;
        document.head.appendChild(style);

        Promise.all([
            loadJS('https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/codemirror.min.js'),
            loadJS('https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/mode/markdown/markdown.min.js')
        ]).then(() => {
            markdownFields.forEach(textarea => {
                const editor = CodeMirror.fromTextArea(textarea, {
                    mode: 'markdown',
                    theme: 'github',
                    lineNumbers: true,
                    lineWrapping: true,
                    viewportMargin: Infinity,
                    extraKeys: {
                        "Enter": "newlineAndIndentContinueMarkdownList",
                        "Tab": function(cm) {
                            cm.replaceSelection("  ", "end");
                        }
                    },
                    // Добавляем дополнительные стили для подсветки
                    styleActiveLine: true,
                    matchBrackets: true,
                    autoCloseBrackets: true
                });

                // Синхронизация при отправке формы
                const form = textarea.closest('form');
                if (form) {
                    form.addEventListener('submit', function() {
                        textarea.value = editor.getValue();
                    });
                }

                // Автосохранение в textarea при изменениях
                editor.on('change', function() {
                    textarea.value = editor.getValue();
                });

                // Установка высоты и ширины редактора в зависимости от поля
                let editorHeight = 600; // По умолчанию

                if (textarea.id === 'id_content_markdown') {
                    editorHeight = 800; // Большая высота для контента
                } else if (textarea.id === 'id_description') {
                    editorHeight = 150; // Маленькая высота для описания
                } else if (textarea.id === 'id_seo_text') {
                    editorHeight = 300;
                }

                // Устанавливаем ширину 100% и высоту
                editor.setSize('100%', editorHeight);
            });
        }).catch(err => {
            console.error('Ошибка загрузки CodeMirror:', err);
        });
    });
})();
