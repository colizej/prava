#!/usr/bin/env python3
"""Download question images and update Question records."""
import os, sys, json, django, urllib.request, ssl

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
django.setup()

from apps.examens.models import Question

MEDIA_DIR = os.path.join(BASE_DIR, 'media', 'questions')
os.makedirs(MEDIA_DIR, exist_ok=True)

data = json.load(open(os.path.join(BASE_DIR, 'data/sites/permisdeconduire-online.be/output/exam_questions_complete.json')))

downloaded = 0
linked = 0

for q in data['questions']:
    qid = q['question_id']
    image_url = q.get('image_url', '')
    if not image_url:
        continue

    source_tag = f'permisdeconduire-online:{qid}'

    # Find the Question in DB
    try:
        question = Question.objects.get(source=source_tag)
    except Question.DoesNotExist:
        print(f"  SKIP {qid}: not found in DB")
        continue

    # Download image
    ext = image_url.rsplit('.', 1)[-1] if '.' in image_url else 'gif'
    filename = f'{qid}.{ext}'
    filepath = os.path.join(MEDIA_DIR, filename)

    if not os.path.exists(filepath):
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            req = urllib.request.urlopen(image_url, context=ctx)
            with open(filepath, 'wb') as f:
                f.write(req.read())
            downloaded += 1
        except Exception as e:
            print(f"  ERROR {qid}: {e}")
            continue

    # Update the Question
    question.image = f'questions/{filename}'
    question.save(update_fields=['image'])
    linked += 1

print(f"Downloaded: {downloaded}, Linked: {linked}")
