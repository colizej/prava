#!/usr/bin/env python3
"""Copy local question images to media/ and link to Question records."""
import os, sys, json, shutil, django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
django.setup()

from apps.examens.models import Question

MEDIA_DIR = os.path.join(BASE_DIR, 'media', 'questions')
LOCAL_DIR = os.path.join(BASE_DIR, 'data/sites/permisdeconduire-online.be/output/exam_images')
os.makedirs(MEDIA_DIR, exist_ok=True)

data = json.load(open(os.path.join(BASE_DIR, 'data/sites/permisdeconduire-online.be/output/exam_questions_complete.json')))

linked = 0
for q in data['questions']:
    qid = q['question_id']
    qnum = q['question_number']
    source_tag = f'permisdeconduire-online:{qid}'
    
    # Find local image: question_N.gif
    local_file = os.path.join(LOCAL_DIR, f'question_{qnum}.gif')
    if not os.path.exists(local_file):
        print(f"  SKIP Q{qnum}: no local image")
        continue
    
    # Find Question in DB
    try:
        question = Question.objects.get(source=source_tag)
    except Question.DoesNotExist:
        print(f"  SKIP Q{qnum}: not in DB")
        continue
    
    # Copy to media/questions/
    dest = os.path.join(MEDIA_DIR, f'q{qnum}_{qid}.gif')
    if not os.path.exists(dest):
        shutil.copy2(local_file, dest)
    
    question.image = f'questions/q{qnum}_{qid}.gif'
    question.save(update_fields=['image'])
    linked += 1

print(f"Linked {linked} images to questions.")
