"""
Fix sign images where Wikimedia codes don't match our (older) Belgian sign codes.

Strategy:
1. F83 (Zone stationnement début) → copy p_begin image
2. F85 (Zone stationnement fin)   → copy p_einde image
3. F87 (Chemin cavaliers)         → Belgian_traffic_sign_D13.svg (current bridlepath)
4. F89, F91 (Chemin piétons/cavaliers) → no single Wikimedia match → clear image
5. F43 Zone 30 début              → Belgian_traffic_sign_F4a.svg (current zone 30 start)
6. F50 Début zone 30              → Belgian_traffic_sign_F4a.svg (same sign)
7. F59 Zone rencontre début       → keep BUT search correct filename
8. F61 Zone rencontre fin         → keep BUT search correct filename
9. F79 Sens obligatoire lourds    → Belgian_traffic_sign_F79.svg says "Reduction of lanes"
       → clear, no correct Wikimedia match found

For signs where Wikimedia Belgian_traffic_sign_X.svg IS the correct sign for our name:
- Most A-series, B-series, C-series signs have consistent enough codes that
  Belgian_traffic_sign_X.svg or Belgian_road_sign_X.svg shows the right sign.
  (The OLD numbering for standard signs like speed limit, stop, yield, etc. is the same.)
"""
import os, sys, shutil, ssl, time, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django; django.setup()

from apps.reglementation.models import TrafficSign

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

SIGNS_DIR = Path('media/signs')

def download(wiki_filename, dest):
    url = f'https://commons.wikimedia.org/wiki/Special:FilePath/{wiki_filename}?width=250'
    req = urllib.request.Request(url, headers={'User-Agent': 'sign-fix/1.0'})
    with urllib.request.urlopen(req, timeout=20, context=CTX) as r:
        data = r.read()
    if len(data) < 500:
        print(f"    Too small ({len(data)} bytes): {wiki_filename}")
        return False
    dest.write_bytes(data)
    return True

def copy_from_sign(src_code, dest_code):
    """Copy image from one sign to another."""
    src = TrafficSign.objects.filter(code=src_code).first()
    if not src or not src.image:
        print(f"    Source {src_code} has no image!")
        return False
    src_file = Path('media') / str(src.image)
    if not src_file.exists():
        print(f"    Source file not found: {src_file}")
        return False
    dest_file = SIGNS_DIR / f'{dest_code}.png'
    shutil.copy2(src_file, dest_file)
    dest_sign = TrafficSign.objects.filter(code=dest_code).first()
    if dest_sign:
        dest_sign.image = f'signs/{dest_code}.png'
        dest_sign.save(update_fields=['image'])
    print(f"  ✓ Copied {src_code} → {dest_code}")
    return True

def clear_image(code):
    """Remove wrong image from sign."""
    sign = TrafficSign.objects.filter(code=code).first()
    if not sign:
        return
    img_file = Path('media') / str(sign.image) if sign.image else None
    if img_file and img_file.exists():
        img_file.unlink()
    sign.image = ''
    sign.save(update_fields=['image'])
    print(f"  ✗ Cleared image for {code} ({sign.name})")

def try_download(wiki_file, our_code):
    dest = SIGNS_DIR / f'{our_code}.png'
    try:
        if download(wiki_file, dest):
            sign = TrafficSign.objects.filter(code=our_code).first()
            if sign:
                sign.image = f'signs/{our_code}.png'
                sign.save(update_fields=['image'])
            print(f"  ✓ Downloaded {wiki_file} → {our_code}")
            return True
        return False
    except Exception as e:
        print(f"  ! Error for {our_code}: {e}")
        if '429' in str(e):
            time.sleep(15)
        return False

print("=== Fixing known wrong sign images ===\n")

# 1. Parking zone signs (F83/F85) — copy from p_begin/p_einde (from codedelaroute.be, reliable)
print("1. Parking zone signs (F83 → p_begin, F85 → p_einde):")
copy_from_sign('p_begin', 'F83')
copy_from_sign('p_einde', 'F85')

# 2. F87 Chemin réservé aux cavaliers → current Belgian D13 = bridlepath
print("\n2. F87 Chemin cavaliers → Belgian_traffic_sign_D13.svg:")
time.sleep(2)
try_download('Belgian_traffic_sign_D13.svg', 'F87')

# 3. F89 "Chemin pour piétons et cavaliers" and F91 "Chemin piétons, cyclistes et cavaliers"
# These have no direct Wikimedia match → clear wrong images
print("\n3. F89, F91 — clearing wrong images (no reliable Wikimedia match):")
clear_image('F89')
clear_image('F91')
time.sleep(1)

# 4. Other known wrong signs in the F-series
# F43 "Zone 30 — début" shows Municipal boundary → use F4a image (Zone 30 start)
print("\n4. F43 Zone 30 début → copy from F4a:")
copy_from_sign('F4a', 'F43')

# F50 "Début d'une zone 30" (duplicate) → also use F4a
print("   F50 Début zone 30 → copy from F4a:")
copy_from_sign('F4a', 'F50')

# F51 "Fin d'une zone 30" → use F4b
print("   F51 Fin zone 30 → copy from F4b:")
copy_from_sign('F4b', 'F51')

# F59: Zone de rencontre — début → try Belgian_traffic_sign_F12a.svg (living street start)?
# Actually living street != rencontre. Zone de rencontre is a specific Belgian sign.
# Let's look for it: in Wikipedia indicatory signs section, there's no direct "zone de rencontre"
# F59 in Wikipedia = Parking lot. Our F59 = Zone rencontre début.
# Zone de rencontre = F12a/F12b in some systems? But we have F12a as "début rue sens unique"...
# Clear F59 and F61 for now (wrong Wikimedia "parking lot" and "telephone" images)
print("\n5. F59, F61 — clearing wrong images:")
clear_image('F59')
clear_image('F61')

# F79 "Sens obligatoire pour les véhicules lourds" → Wikipedia F79 = Reduction of lanes
# These are different signs. Clear F79.
print("   F79 — clearing wrong image:")
clear_image('F79')

# F19 "Voie réservée aux transports en commun" - check if correct
# Wikipedia F19 = One-way road → our F19 = Voie réservée TC. Might be wrong too.
# Let's check what F17 and F18 are in Wikipedia: F17=Bus lane, F18=Bus+tram lane
# Our F17 = Zone piétonne début (from reglementation/ path = reliable)
# F19 in Wikipedia = One-way road. Our F19 = Voie réservée TC → probably wrong
print("\n6. F19 — clearing (Wikipedia F19=One-way, our F19=Voie TC):")
f19 = TrafficSign.objects.filter(code='F19').first()
if f19 and f19.image and f19.image.startswith('signs/'):
    clear_image('F19')

# F25, F27, F29, F33, F47, F49 — medical/service signs
# Wikipedia: F25=Direction sign, F27=Direction sign, F29=Direction sign
# Our:       F25=Poste de secours, F27=Appel urgence, F29=Hôpital, F33=Station-service
# These are service icons. In Wikipedia: F55=First aid, F53=Healthcare, F63=Fuel
# So our F25=Poste secours should be F55 in current system
# CLEAR these since they're wrong service icons
print("\n7. Service signs (F25,F27,F29,F33,F47,F49) — clearing wrong direction signs:")
for code in ['F25', 'F27', 'F29', 'F33', 'F47', 'F49']:
    sign = TrafficSign.objects.filter(code=code).first()
    if sign and sign.image and sign.image.startswith('signs/'):
        # Check name to confirm mismatch
        print(f"   {code}: {sign.name}")
        # These maps direction signs to service names, so clear them
        if any(kw in sign.name.lower() for kw in ['secours', 'urgence', 'hôpital', 'station', 'parking', 'résidents']):
            clear_image(code)

print("\n=== Done ===")
print("\nSummary:")
for sign in TrafficSign.objects.filter(sign_type='indication').order_by('code'):
    img = str(sign.image) if sign.image else '(no image)'
    print(f"  {sign.code:10} {img[:50]:50} {sign.name[:40]}")
