"""
Management command: import traffic signs from local media files.

Sources (in priority order):
  1. media/reglementation/art*_<CODE>_*.png  — best quality, named by sign code
  2. media/signs/<hash>.png + images_analysis.json mapping — hash → sign code
"""
import json
import re
import shutil
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.reglementation.models import TrafficSign

# ── Belgian sign code → (name_fr, sign_type) ──────────────────────────────────
SIGN_REGISTRY = {
    # ── Danger / Avertissement (A) — triangulaires ────────────────────────────
    # Codes et noms selon la numérotation ACTUELLE du code belge (Wikimedia)
    'A1a':  ("Virage dangereux à gauche", 'danger'),
    'A1b':  ("Virage dangereux à droite", 'danger'),
    'A1c':  ("Double virage, premier à gauche", 'danger'),
    'A1d':  ("Double virage, premier à droite", 'danger'),
    'A3':   ("Descente dangereuse", 'danger'),
    'A5':   ("Montée dangereuse", 'danger'),
    'A7a':  ("Chaussée rétrécie (des deux côtés)", 'danger'),
    'A7b':  ("Chaussée rétrécie (à gauche)", 'danger'),
    'A7c':  ("Chaussée rétrécie (à droite)", 'danger'),
    'A9':   ("Pont mobile", 'danger'),
    'A11':  ("Débouché sur un quai ou une berge", 'danger'),
    'A13':  ("Chaussée déformée ou bosselée", 'danger'),
    'A14':  ("Dos d'âne isolé", 'danger'),
    'A15':  ("Chaussée glissante", 'danger'),
    'A17':  ("Gravillons", 'danger'),
    'A19':  ("Chute de pierres", 'danger'),
    'A21':  ("Passage pour piétons", 'danger'),
    'A23':  ("Enfants", 'danger'),
    'A25':  ("Cyclistes", 'danger'),
    'A27':  ("Passage d'animaux sauvages", 'danger'),
    'A29':  ("Passage d'animaux domestiques", 'danger'),
    'A31':  ("Travaux", 'danger'),
    'A33':  ("Feux de signalisation", 'danger'),
    'A35':  ("Avions à basse altitude", 'danger'),
    'A37':  ("Vent latéral", 'danger'),
    'A39':  ("Circulation en sens contraire", 'danger'),
    'A41':  ("Passage à niveau avec barrières", 'danger'),
    'A43':  ("Passage à niveau sans barrières", 'danger'),
    'A45':  ("Passage à niveau — voie unique", 'danger'),
    'A47':  ("Passage à niveau — voies multiples", 'danger'),
    'A49':  ("Passage à niveau de trams", 'danger'),
    'A50':  ("Début de bouchon", 'danger'),
    'A51':  ("Autres dangers", 'danger'),
    # ── Priorité (B) ─────────────────────────────────────────────────────────
    'B1':   ("Cédez le passage", 'priorite'),
    'B3':   ("Signal avancé de cédez le passage", 'priorite'),
    'B5':   ("Stop", 'priorite'),
    'B7':   ("Signal avancé de stop", 'priorite'),
    'B9':   ("Route prioritaire", 'priorite'),
    'B11':  ("Fin de route prioritaire", 'priorite'),
    'B13':  ("Signal avancé de fin de route prioritaire", 'priorite'),
    'B15a': ("Marque de priorité à la prochaine intersection (à droite)", 'priorite'),
    'B15b': ("Marque de priorité à la prochaine intersection (à gauche)", 'priorite'),
    'B17':  ("Priorité par rapport à la circulation venant en sens inverse", 'priorite'),
    'B19':  ("Cédez le passage à la prochaine intersection", 'priorite'),
    'B21':  ("Priorité sur la circulation venant en sens inverse", 'priorite'),
    'B23':  ("Impasse", 'priorite'),
    # ── Interdiction / Restriction (C) ────────────────────────────────────────
    'C1':   ("Accès interdit (sens unique)", 'interdiction'),
    'C3':   ("Accès interdit dans les deux sens", 'interdiction'),
    'C5':   ("Accès interdit aux véhicules à moteur à plus de deux roues", 'interdiction'),
    'C7':   ("Accès interdit aux motocycles", 'interdiction'),
    'C9':   ("Accès interdit aux cyclomoteurs", 'interdiction'),
    'C11':  ("Accès interdit aux cycles", 'interdiction'),
    'C13':  ("Accès interdit aux véhicules tractés par des animaux", 'interdiction'),
    'C15':  ("Accès interdit aux cavaliers", 'interdiction'),
    'C17':  ("Accès interdit aux voiturettes", 'interdiction'),
    'C19':  ("Accès interdit aux piétons", 'interdiction'),
    'C21':  ("Limitation de masse totale en charge", 'interdiction'),
    'C23':  ("Accès interdit aux camions (> 3,5 t)", 'interdiction'),
    'C25':  ("Limitation de longueur totale", 'interdiction'),
    'C27':  ("Limitation de largeur", 'interdiction'),
    'C29':  ("Limitation de hauteur", 'interdiction'),
    'C31':  ("Stationnement interdit les jours pairs", 'interdiction'),
    'C33':  ("Demi-tour interdit", 'interdiction'),
    'C35':  ("Interdiction de dépasser", 'interdiction'),
    'C37':  ("Fin d'interdiction de dépasser", 'interdiction'),
    'C39':  ("Interdiction de dépasser pour les véhicules lourds", 'interdiction'),
    'C41':  ("Fin d'interdiction de dépasser pour les lourds", 'interdiction'),
    'C43':  ("Vitesse maximale", 'interdiction'),
    'C45':  ("Fin de limitation de vitesse", 'interdiction'),
    'C47':  ("Poste de péage", 'interdiction'),
    # ── Obligation (D) ───────────────────────────────────────────────────────
    'D1':   ("Sens giratoire obligatoire", 'obligation'),
    'D3':   ("Sens obligatoire — tout droit", 'obligation'),
    'D5':   ("Sens giratoire (panneau de signalisation)", 'obligation'),
    'D7':   ("Piste cyclable obligatoire", 'obligation'),
    'D9':   ("Chemin séparé pour cyclistes et piétons", 'obligation'),
    'D10':  ("Chemin mixte pour piétons et cyclistes", 'obligation'),
    'D11':  ("Trottoir obligatoire", 'obligation'),
    'D13':  ("Chemin réservé aux cavaliers", 'obligation'),
    'D15':  ("Sentier pour cavaliers (obligatoire)", 'obligation'),
    'D17':  ("Feux de croisement obligatoires", 'obligation'),
    # ── Indication / Information (F) ─────────────────────────────────────────
    # Noms selon Wikipedia "Road signs in Belgium" (numérotation actuelle)
    'F1':   ("Début d'agglomération", 'indication'),
    'F1a':  ("Début d'agglomération", 'indication'),
    'F1b':  ("Début d'agglomération", 'indication'),
    'F3':   ("Fin d'agglomération", 'indication'),
    'F3a':  ("Fin d'agglomération", 'indication'),
    'F3b':  ("Fin d'agglomération", 'indication'),
    'F4a':  ("Début d'une zone 30", 'indication'),
    'F4b':  ("Fin d'une zone 30", 'indication'),
    'F5':   ("Autoroute", 'indication'),
    'F7':   ("Fin d'autoroute", 'indication'),
    'F9':   ("Route express", 'indication'),
    'F11':  ("Fin de route express", 'indication'),
    'F12a': ("Début d'une zone résidentielle", 'indication'),
    'F12b': ("Fin d'une zone résidentielle", 'indication'),
    'F13':  ("Files de circulation", 'indication'),
    'F15':  ("Indication du choix de direction", 'indication'),
    'F17':  ("Voie de bus", 'indication'),
    'F18':  ("Voie de bus et tram", 'indication'),
    'F19':  ("Rue à sens unique", 'indication'),
    'F23':  ("Numéro de route nationale", 'indication'),
    'F25':  ("Panneau de direction", 'indication'),
    'F27':  ("Panneau de direction", 'indication'),
    'F29':  ("Panneau de direction", 'indication'),
    'F33':  ("Panneau de direction", 'indication'),
    'F43':  ("Frontière de commune", 'indication'),
    'F45a': ("Impasse", 'indication'),
    'F45b': ("Impasse (sauf piétons et cyclistes)", 'indication'),
    'F47':  ("Fin de travaux", 'indication'),
    'F49':  ("Passage pour piétons", 'indication'),
    'F50':  ("Passage pour cyclistes et cyclomoteurs", 'indication'),
    'F51':  ("Passage souterrain ou aérien", 'indication'),
    'F59':  ("Parking", 'indication'),
    'F61':  ("Téléphone", 'indication'),
    'F63a': ("Panneau de direction — flèche droite", 'indication'),
    'F63b': ("Panneau de direction — flèche gauche", 'indication'),
    'F63c': ("Panneau de direction", 'indication'),
    'F63d': ("Panneau de direction", 'indication'),
    'F63e': ("Panneau de direction", 'indication'),
    'F63f': ("Panneau de direction", 'indication'),
    'F79':  ("Rétrécissement de voies", 'indication'),
    'F83':  ("Trouée dans le terre-plein central", 'indication'),
    'F85':  ("Circulation dans les deux sens", 'indication'),
    'F87':  ("Dos d'âne", 'indication'),
    'F89':  ("Limitation de vitesse par voie (préavis)", 'indication'),
    'F91':  ("Limitation de vitesse par voie", 'indication'),
    'F99a': ("Voie réservée — piétons, cyclistes et cavaliers", 'indication'),
    'F99b': ("Voie réservée séparée — piétons, cyclistes et cavaliers", 'indication'),
    'F101': ("Rue scolaire", 'indication'),
    'F101A':("Rue scolaire", 'indication'),
    'F101a':("Fin de voie réservée — piétons, cyclistes et cavaliers", 'indication'),
    'F101b':("Fin de voie réservée séparée — piétons, cyclistes et cavaliers", 'indication'),
    'F103': ("Début d'une zone piétonne", 'indication'),
    'F105': ("Fin d'une zone piétonne", 'indication'),
    'F117': ("Début d'une zone à faibles émissions (LEZ)", 'indication'),
    'F118': ("Fin d'une zone à faibles émissions (LEZ)", 'indication'),
    # ── Panneaux additionnels (M) — noms selon Wikipedia ───────────────────────
    'M1':   ("Réservé aux cyclistes", 'additionnel'),
    'M2':   ("Sauf cyclistes", 'additionnel'),
    'M3':   ("Sauf cyclistes et cyclomoteurs (classe A)", 'additionnel'),
    'M4':   ("Sauf cyclistes (variante)", 'additionnel'),
    'M5':   ("Sauf cyclistes et cyclomoteurs", 'additionnel'),
    'M6':   ("Obligatoire pour cyclomoteurs (classe B)", 'additionnel'),
    'M7':   ("Interdit aux cyclomoteurs (classe B)", 'additionnel'),
    'M8':   ("Réservé aux cyclistes et cyclomoteurs", 'additionnel'),
    'M9':   ("Cyclistes venant de gauche et de droite", 'additionnel'),
    'M18':  ("Sauf cyclistes", 'additionnel'),
    'M21':  ("Disque de stationnement obligatoire", 'additionnel'),
    'M22':  ("Durée limitée", 'additionnel'),
    'M23':  ("Durée limitée avec horodateur", 'additionnel'),
    'M24':  ("Sauf résidents", 'additionnel'),
    # ── Signaux spéciaux belges (E) — noms selon Wikipedia ───────────────────
    'E1':        ("Stationnement interdit", 'indication'),
    'E3':        ("Arrêt et stationnement interdits", 'indication'),
    'E9j_FR':    ("Zone de stationnement réglementé (FR)", 'indication'),
    'p_begin':   ("Début de zone de stationnement réglementé", 'indication'),
    'p_einde':   ("Fin de zone de stationnement réglementé", 'indication'),
    'rue_scolaire': ("Rue scolaire (signal)", 'indication'),
}

# Fallback: infer sign_type from first letter
_TYPE_BY_PREFIX = {
    'A': 'danger',
    'B': 'priorite',
    'C': 'interdiction',
    'D': 'obligation',
    'E': 'indication',
    'F': 'indication',
    'M': 'additionnel',
}


def _infer_type(code: str) -> str:
    return _TYPE_BY_PREFIX.get(code[0].upper(), 'indication')


def _extract_code_from_reglementation_filename(name: str) -> str | None:
    """
    art9_D7_1.png      → D7
    art42_D11.png_3.png → D11
    art65_M21_21.png   → M21
    art85_p_begin_1.png → p_begin
    art22un_rue_scolaire_2.png → rue_scolaire
    art22quinquies_F101A_2.png → F101A
    """
    # Strip .png suffixes and numeric order suffixes
    stem = re.sub(r'\.png$', '', name)
    stem = re.sub(r'\.png$', '', stem)  # double for D11.png_3.png
    stem = re.sub(r'_\d+$', '', stem)   # remove trailing _1 / _21

    # Remove art<article_prefix>_
    stem = re.sub(r'^art[a-z0-9]+_', '', stem, flags=re.IGNORECASE)
    stem = re.sub(r'\.png$', '', stem)  # strip leftover .png (e.g. 'D11.png' → 'D11')
    if not stem:
        return None
    return stem


class Command(BaseCommand):
    help = "Import TrafficSign records from local media files."

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--clear', action='store_true',
                            help='Delete all existing TrafficSign records first')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        clear = options['clear']
        base = Path('media')

        if clear and not dry_run:
            count = TrafficSign.objects.count()
            TrafficSign.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Cleared {count} existing signs.'))

        # ── Collect all candidates ─────────────────────────────────────────────
        candidates = []  # list of (code, rel_path, order)
        seen_codes = set()

        # Source 1: media/reglementation/ — files named with sign code
        rgl_dir = base / 'reglementation'
        if rgl_dir.exists():
            for i, f in enumerate(sorted(rgl_dir.iterdir())):
                if not re.match(r'^art', f.name):
                    continue
                code = _extract_code_from_reglementation_filename(f.name)
                if not code or re.match(r'^img\d*$', code):
                    continue
                if code in seen_codes:
                    continue
                seen_codes.add(code)
                candidates.append((code, f'reglementation/{f.name}', i + 1))

        # Source 2: media/signs/<hash>.png via hash_to_code.json
        # This mapping was built by analyse_sign_hashes.py from article img alt tags
        hash_map_file = base.parent / 'data/sources/codedelaroute.be/hash_to_code.json'
        if hash_map_file.exists():
            hash_to_code = json.loads(hash_map_file.read_text())
            signs_dir = base / 'signs'
            for hash_file, code in hash_to_code.items():
                code = re.sub(r'\.png$', '', code).replace(' ', '_').strip()
                if not code or code in seen_codes:
                    continue
                src_path = signs_dir / hash_file
                if not src_path.exists():
                    continue
                # Copy hash file to a code-named file for clarity
                dest_name = f'{code}.png'
                dest_path = signs_dir / dest_name
                if not dest_path.exists():
                    shutil.copy2(src_path, dest_path)
                seen_codes.add(code)
                candidates.append((code, f'signs/{dest_name}', len(candidates) + 1))

        self.stdout.write(f'Found {len(candidates)} sign candidates.\n')

        # ── Import ────────────────────────────────────────────────────────────
        created = updated = skipped = 0
        for code, rel_path, order in candidates:
            name_fr, sign_type = SIGN_REGISTRY.get(
                code, (f"Panneau {code.replace('_', ' ')}", _infer_type(code))
            )
            if dry_run:
                self.stdout.write(f'  [DRY] {code:15} {sign_type:15} → {rel_path}')
                continue

            obj, was_created = TrafficSign.objects.get_or_create(
                code=code,
                defaults={'name': name_fr, 'sign_type': sign_type,
                          'image': rel_path, 'order': order},
            )
            if was_created:
                self.stdout.write(f'  + {code:15} [{sign_type}]')
                created += 1
            elif not obj.image:
                obj.image = rel_path
                obj.save(update_fields=['image'])
                self.stdout.write(f'  ~ {code:15} (image added)')
                updated += 1
            else:
                skipped += 1

        # ── Create remaining registry entries without images ──────────────────
        no_image_count = 0
        for code, (name_fr, sign_type) in SIGN_REGISTRY.items():
            if code in seen_codes:
                continue  # already handled above
            if dry_run:
                self.stdout.write(f'  [DRY-NO-IMG] {code:15} {sign_type}')
                no_image_count += 1
                continue
            obj, was_created = TrafficSign.objects.get_or_create(
                code=code,
                defaults={'name': name_fr, 'sign_type': sign_type, 'order': 999},
            )
            if was_created:
                self.stdout.write(f'  + {code:15} [{sign_type}] (no image)')
                created += 1
                no_image_count += 1

        if no_image_count:
            self.stdout.write(f'  ({no_image_count} signs added without image)\n')

        # ── Summary ───────────────────────────────────────────────────────────
        if not dry_run:
            self.stdout.write(self.style.SUCCESS(
                f'\nDone — created: {created}, updated: {updated}, skipped: {skipped}'
                f' | Total: {TrafficSign.objects.count()}'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'\n[DRY RUN] {len(candidates)} signs would be imported.'))
