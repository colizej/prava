"""
Middleware для обработки старых URL категорий с query параметрами.
Редирект с /blog/?category=slug на /blog/categorie/slug/
"""
from django.shortcuts import redirect
from django.urls import reverse
from blog.models import Category


class CategoryQueryRedirectMiddleware:
    """
    Middleware для редиректа старых URL категорий на новые.

    Старый формат: /blog/?category=creation-scenique
    Новый формат: /blog/categorie/creation-scenique/
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Проверяем, есть ли параметр category в GET запросе к /blog/
        if request.path == '/blog/' and 'category' in request.GET:
            category_slug = request.GET.get('category')

            # Проверяем, существует ли категория
            try:
                category = Category.objects.get(slug=category_slug)

                # Сохраняем остальные параметры (например, tags)
                query_params = request.GET.copy()
                del query_params['category']

                # Формируем новый URL
                new_url = reverse('blog:category_detail', kwargs={'slug': category.slug})

                # Добавляем остальные параметры, если есть
                if query_params:
                    new_url += '?' + query_params.urlencode()

                # Делаем 301 редирект (постоянный)
                return redirect(new_url, permanent=True)
            except Category.DoesNotExist:
                pass

        response = self.get_response(request)
        return response
