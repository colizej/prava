#!/usr/bin/env python3
"""Patch Art. 85.2 content to add F1 and F3 sign images."""
import django
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, '/Users/colizej/Documents/webApp/prava')
django.setup()

from apps.reglementation.models import CodeArticle

F1_SRC = '/media/signs/e758aef1c502442f82e3f8f64ee6896d1929fb7e.gif'
F3_SRC = '/media/signs/a810e6756432cb60a8d3fe542093613019a9de3d.gif'

art85 = CodeArticle.objects.get(article_number='Art. 85')
content = art85.content

old_comm = '<p style="padding-left: 30px;"><em>Commencement d\'une agglomération.</em></p>'
new_comm = ('<p style="padding-left: 30px;">'
            '<img alt="F1" loading="lazy" src="' + F1_SRC + '" style="max-height:60px; margin-right:8px; vertical-align:middle;"/>'
            ' <em>Commencement d\'une agglomération.</em>'
            '</p>')

old_fin = '<p style="padding-left: 30px;"><em>Fin d\'agglomération.<br/></em></p>'
old_fin2 = '<p style="padding-left: 30px;"><em>Fin d\'agglomération.</em></p>'
new_fin = ('<p style="padding-left: 30px;">'
           '<img alt="F3" loading="lazy" src="' + F3_SRC + '" style="max-height:60px; margin-right:8px; vertical-align:middle;"/>'
           ' <em>Fin d\'agglomération.</em>'
           '</p>')

new_content = content
changed = False

if old_comm in new_content:
    new_content = new_content.replace(old_comm, new_comm, 1)
    print('Patched: Commencement + F1 image')
    changed = True
else:
    print('NOT FOUND:', repr(old_comm))

if old_fin in new_content:
    new_content = new_content.replace(old_fin, new_fin, 1)
    print('Patched: Fin (br) + F3 image')
    changed = True
elif old_fin2 in new_content:
    new_content = new_content.replace(old_fin2, new_fin, 1)
    print('Patched: Fin + F3 image')
    changed = True
else:
    print('NOT FOUND:', repr(old_fin))

if changed:
    art85.content = new_content
    art85.save()
    print('Art. 85 saved!')
    ar = CodeArticle.objects.get(article_number='Art. 85')
    i = ar.content.find('85.2.')
    print()
    print('Result:')
    print(ar.content[i:i+700])
else:
    print('No changes.')
    i = content.find('85.2.')
    print('Current 85.2:')
    print(repr(content[i:i+400]))
