#!/usr/bin/env python3
import django, os, sys, re
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, '/Users/colizej/Documents/webApp/prava')
django.setup()
from apps.reglementation.models import CodeArticle

for art in CodeArticle.objects.all():
    c = art.content or ''
    if 'non repris' in c.lower():
        hits = re.findall(r'[^\n]{0,30}non repris[^\n]{0,60}', c, re.IGNORECASE)
        for h in hits[:3]:
            print(art.article_number + ': ' + repr(h.strip()[:100]))
