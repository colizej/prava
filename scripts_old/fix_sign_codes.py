import os, sys, django, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()
from apps.reglementation.models import ArticleImage

VALID_CODE = re.compile(r'^[A-MS]\d{1,3}[a-z]?$', re.IGNORECASE)

# 1. Clean bad codes
bad = 0
for ai in ArticleImage.objects.exclude(sign_code=''):
    code = ai.sign_code
    if code.endswith('.png'):
        code = code[:-4]
    if not VALID_CODE.match(code):
        print(f'  Clearing: {ai.image.name} had "{code}"')
        ai.sign_code = ''
        ai.alt_text = ''
        ai.save(update_fields=['sign_code', 'alt_text'])
        bad += 1
    elif code != ai.sign_code:
        ai.sign_code = code
        ai.alt_text = f'Panneau {code}'
        ai.save(update_fields=['sign_code', 'alt_text'])
        print(f'  Fixed: {ai.image.name} -> {code}')

# 2. Try to fill empty sign_codes from filename
filled = 0
for ai in ArticleImage.objects.filter(sign_code=''):
    fname = os.path.basename(ai.image.name)
    match = re.search(r'_([A-MS]\d{1,3}[a-z]?)_', fname, re.IGNORECASE)
    if match:
        code = match.group(1)
        ai.sign_code = code
        ai.alt_text = f'Panneau {code}'
        ai.save(update_fields=['sign_code', 'alt_text'])
        filled += 1
        print(f'  Filled: {ai.image.name} -> {code}')

print(f'Cleaned {bad}, Filled {filled}')
valid = ArticleImage.objects.exclude(sign_code='').count()
total = ArticleImage.objects.count()
print(f'Final: {valid} with codes out of {total} total')
