#!/usr/bin/env python3
"""Pannes injectees : verifie que le test hors jeu (tests/test_hold.c) DETECTE des erreurs volontaires dans le plugin.

    python -I -B injecter_pannes.py

Pour chaque panne : une copie de cc2x_hold.c avec UNE modification (remplacement exact, present une seule fois), compilee avec le
test (memes options que construire_hold.py : UBSan, -Werror), puis lancee. Panne detectee = le test echoue ou s'arrete.
Tout se passe dans C:\\Users\\UTILISATEUR\\Documents\\cc2-hold-travail\\plugin_v2\\pannes (hors depot, hors jeu) ; dans le depot,
seulement RAPPORT_pannes.md. Sous-processus : zig et les tests compiles. Aucun reseau, rien n'est lance dans le jeu.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
CLONE = Path(r'C:\Users\UTILISATEUR\Documents\cc2-sdk-tiers\Carrier-Command-2-extender')
TRAVAIL = Path(r'C:\Users\UTILISATEUR\Documents\cc2-hold-travail\plugin_v2\pannes')
RAPPORT = ICI / 'RAPPORT_pannes.md'
CFLAGS = ['-target', 'x86-windows-gnu', '-std=c11', '-O2', '-Wall', '-Wextra', '-Wno-unused-parameter',
          '-Werror=implicit-function-declaration', '-fno-strict-aliasing', '-fsanitize=undefined', '-Werror']

# (ce que la panne casse, texte d'origine, texte fautif)
PANNES = [
    ("synchro : l'original inutilisable (octet 2 = 0) n'arrete plus rien",
     "    if (st[0][2] == 0) {", "    if (0) {"),
    ("synchro : ecrit l'octet 2 au lieu de l'octet 0",
     "st[i][0] = (uint8_t)v;", "st[i][2] = (uint8_t)v;"),
    ("synchro : deux changements au meme instant recopies quand meme",
     "    if (nchanged != 1) {", "    if (nchanged == 0) {"),
    ("synchro : deux changements au meme instant non journalises",
     "        if (nchanged > 1) event(veh, EV_BOTH,", "        if (nchanged > 1 && other < 0) event(veh, EV_BOTH,"),
    ("message 20 avec le drapeau 1 (clic chez les joueurs) au lieu de 0",
     "g_enqueue(q[j], id, idx[i], (uint32_t)v, 0);", "g_enqueue(q[j], id, idx[i], (uint32_t)v, 1);"),
    ("mauvais numero du porte-avions (+0x84 au lieu de +0x80)",
     "#define OFF_ID 0x80 ", "#define OFF_ID 0x84 "),
    ("mauvaise file du joueur (+0x68 au lieu de +0x64)",
     "#define PEER_QUEUE 0x64 ", "#define PEER_QUEUE 0x68 "),
    ("liste des joueurs : pas de retour au debut de l'anneau",
     "        if (k >= p.cap) k -= p.cap;\n        player = p.base[k];", "        player = p.base[k];"),
    ("liste des joueurs : capacite non bornee",
     "p.count > p.cap || p.cap > MAX_PEERS ||", "p.count > p.cap ||"),
    ("file d'un joueur non verifiee (count > capacite)",
     "if (f[3] > f[1] || f[1] > (1u << 20) ||", "if (f[1] > (1u << 20) ||"),
    ("premiere mise a jour vue : recopie au lieu de seulement noter",
     "    if (fresh) { memcpy(m->last, cur, (size_t)nb); return; }", "    if (fresh) memset(m->last, 0, (size_t)nb);"),
    ("apres ecriture, l'etat note n'est pas mis a jour",
     "            cur[i] = (uint8_t)v;\n", ""),
    ("une copie inutilisable (octet 2 = 0) est ecrite quand meme",
     "            if (i == src || st[i][2] == 0 || cur[i] == v) continue;\n            st[i][0]",
     "            if (i == src || cur[i] == v) continue;\n            st[i][0]"),
    ("ecriture sans verifier que l'etat est modifiable",
     "        if (!writable(st[i], 1)) {", "        if (0 && !writable(st[i], 1)) {"),
    ("arret de la synchro non remis a zero a la partie suivante",
     "    g_sync_off = g_sync_fail = ", "    g_sync_fail = "),
    ("crochet de synchronisation jamais aiguille",
     "    if (w == HOOK_SYNC) {", "    if (w == 3) {"),
    ("chargement : bloc du groupe de 6 boutons non controle",
     "    if (!same_hex(bd->group, k_group)) return bd->group;\n", ""),
    ("chargement : cible de l'appel du groupe non controlee",
     "    if (!calls(bd->group + GROUP_CALL, bd->enqueue)) return bd->group + GROUP_CALL;\n", ""),
    ("chargement : type 20 du message non controle",
     "    if (!readable(type, sizeof(k_type20)) || memcmp(type, k_type20, sizeof(k_type20)) != 0) return",
     "    if (!readable(type, sizeof(k_type20))) return"),
    ("chargement : adresses relogees de 0x565ce0 non controlees",
     "        if (a != (uint32_t)A->va(bd->enq_abs[i]))", "        if (0 && a != (uint32_t)A->va(bd->enq_abs[i]))"),
    ("chargement : adresses de 0x565ce0 comparees au fichier, sans relocalisation (le defaut du 31/10 13 h 14)",
     "        if (a != (uint32_t)A->va(bd->enq_abs[i]))", "        if (a != bd->enq_abs[i])"),
    ("chargement : les jokers ?? ne sont plus acceptes",
     "        if (hex[2 * i] == '?' && hex[2 * i + 1] == '?') continue;\n", ""),
    ("chargement : la synchro est posee meme si le code differe",
     "        (!sync_bad && !a->patch_mid(", "        (!a->patch_mid("),
    ("xmm7 non restaure par l'enveloppe des crochets",
     '"movups 0x70(%esp), %xmm7\\n\\t"', '"nop\\n\\t"'),
    ("v1 : une copie passe outre l'original inutilisable",
     "    if (orig[2] == 0) { note(veh, -1); return -1; }", "    if (0) { note(veh, -1); return -1; }"),
    ("v1 : saut vers la mauvaise instruction",
     "    cpu->jump_to = g_next[w];", "    cpu->jump_to = g_next[w] + 2;"),
]


def zig(args, cwd):
    env = dict(os.environ)
    env['ZIG_GLOBAL_CACHE_DIR'] = str(TRAVAIL / 'cache')
    env['ZIG_LOCAL_CACHE_DIR'] = str(TRAVAIL / 'cache_local')
    return subprocess.run([sys.executable, '-m', 'ziglang', 'cc', *CFLAGS, *[str(a) for a in args]], cwd=cwd, env=env,
                          capture_output=True, text=True)


def essai(nom, source, dossier):
    """compile le test avec cette source du plugin et le lance : 'detectee', 'NON detectee' ou 'ne compile pas'"""
    (dossier / 'tests').mkdir(parents=True, exist_ok=True)
    (dossier / 'cc2x_hold.c').write_text(source, encoding='utf-8', newline='\n')
    (dossier / 'tests' / 'test_hold.c').write_bytes((ICI / 'tests' / 'test_hold.c').read_bytes())
    exe = dossier / 'test_hold.exe'
    r = zig(['-I', CLONE / 'include', dossier / 'tests' / 'test_hold.c', '-o', exe], dossier)
    if r.returncode:
        print((r.stdout + r.stderr).strip()[:600])
        return 'ne compile pas', ''
    try:
        t = subprocess.run([str(exe)], cwd=dossier, capture_output=True, text=True, timeout=120)
        code, sortie = t.returncode, t.stdout
    except subprocess.TimeoutExpired:
        return 'detectee', 'bloque (delai depasse)'
    if code == 0:
        return 'NON detectee', sortie.strip().splitlines()[-1] if sortie.strip() else ''
    fails = [l.strip() for l in sortie.splitlines() if 'FAIL' in l]
    return 'detectee', (f'{len(fails)} controle(s) en echec, ex. {fails[0][:110]}' if fails else f'arret du test (code {code & 0xffffffff:#x})')


def main():
    t = TRAVAIL.resolve()
    for interdit in (ICI.parents[2].resolve(), CLONE.resolve(), Path(os.environ.get('APPDATA', 'C:\\x'))):
        if t == interdit or interdit in t.parents:
            print('ARRET : le dossier de travail est dans', interdit)
            return 1
    if TRAVAIL.exists():
        shutil.rmtree(TRAVAIL)
    TRAVAIL.mkdir(parents=True)
    source = (ICI / 'cc2x_hold.c').read_text(encoding='utf-8')
    for _, avant, _ in PANNES:
        if source.count(avant) != 1:
            print('ARRET : texte a remplacer absent ou en double :', repr(avant[:70]))
            return 1
    print('reference (plugin intact) ...')
    ref, detail = essai('reference', source, TRAVAIL / '00_reference')
    if ref != 'NON detectee':
        print('ARRET : le test echoue deja sur le plugin intact :', ref, detail)
        return 1
    print('  le test passe :', detail)
    lignes, n_ok = [], 0
    for i, (quoi, avant, apres) in enumerate(PANNES, 1):
        verdict, detail = essai(quoi, source.replace(avant, apres), TRAVAIL / f'{i:02d}')
        n_ok += verdict == 'detectee'
        print(f'{i:2d}. {verdict:13s} {quoi} | {detail}')
        lignes.append(f'| {i} | {quoi} | **{verdict}** | {detail.replace("|", "/")} |')
    L = ['# Pannes injectees dans `cc2x_hold.c` v2 — genere par `injecter_pannes.py`', '',
         f'Chaque ligne : une copie du plugin avec UNE erreur volontaire, compilee avec `tests/test_hold.c` (UBSan, -Werror) et lancee, '
         f'dans `{TRAVAIL}` (hors depot, hors jeu). Plugin intact : le test passe ({detail_ref(ref)}).', '',
         f'**{n_ok} / {len(PANNES)} pannes detectees.**', '', '| n. | erreur volontaire | resultat | detail |', '|---|---|---|---|', *lignes]
    RAPPORT.write_text('\n'.join(L) + '\n', encoding='utf-8')
    print(f'\n{n_ok} / {len(PANNES)} pannes detectees ; rapport : {RAPPORT}')
    return 0 if n_ok == len(PANNES) else 1


def detail_ref(ref):
    return 'tous les controles passent' if ref == 'NON detectee' else ref


if __name__ == '__main__':
    sys.exit(main())
