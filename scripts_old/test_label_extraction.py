"""Test label extraction logic on Art. 65"""
import os, sys, re, django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.reglementation.models import CodeArticle
from bs4 import BeautifulSoup, NavigableString

SIGN_CODE_RE = re.compile(
    r"^[A-MS]\d{1,3}(?:(?:bis|ter|quater|quinquies|sexies|[a-z])(?:\.\d+)?)?$",
    re.IGNORECASE,
)


def collect_img_label_pairs(p_tag):
    pairs = []
    pending_label = ""
    for child in p_tag.children:
        if child.name == "img":
            label = ""
            if pending_label:
                label = pending_label
                pending_label = ""
            else:
                alt = (child.get("alt") or "").strip()
                if alt and SIGN_CODE_RE.match(alt):
                    label = alt
            pairs.append((child, label))
        elif isinstance(child, NavigableString):
            text = str(child).strip()
            if not text:
                continue
            words = text.split()
            if pairs and not pairs[-1][1]:
                first_word = words[0]
                if SIGN_CODE_RE.match(first_word):
                    img, _ = pairs[-1]
                    pairs[-1] = (img, first_word)
                    words = words[1:]
            if words:
                last_word = words[-1]
                if SIGN_CODE_RE.match(last_word):
                    pending_label = last_word
    return pairs


art = CodeArticle.objects.get(article_number="Art. 65")
soup = BeautifulSoup(art.content, "html.parser")

total_imgs = 0
total_labeled = 0

for i, p_tag in enumerate(soup.find_all("p")):
    imgs = p_tag.find_all("img")
    if not imgs:
        continue
    pairs = collect_img_label_pairs(p_tag)
    labels_found = sum(1 for _, label in pairs if label)
    total_imgs += len(pairs)
    total_labeled += labels_found
    print(f"<p> #{i}: {len(imgs)} imgs, {labels_found}/{len(pairs)} labeled")
    for img, label in pairs:
        src = img.get("src", "")[-20:]
        print(f"  ...{src} -> {label or '(none)'}")

print(f"\nTOTAL: {total_labeled}/{total_imgs} images labeled")
