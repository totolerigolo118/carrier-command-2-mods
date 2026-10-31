#!/usr/bin/env python3
"""PARTIE 1, etape B : fabrique les modules d'exe du NOUVEL exe de Steam (461E1262...) a partir des modules de l'ancien
build et des sites retrouves par localiser_sites.py.

LECTURE SEULE sur les deux exe. Ecrit seulement : les JSON des modules et un rapport. Rien n'est ecrit si UN controle echoue
(un site ambigu ou introuvable = arret, on ne devine pas).

Pour chaque champ de 4 octets :
  - imm   (immediat : energie, facteur de vitesse, centre du cercle) : meme valeur avant/apres qu'a l'ancien exe ;
  - abs   (adresse d'une constante lue par movss/addss/comiss/maxss) : `avant` = ce que le nouvel exe contient a cet endroit ;
          `apres` = adresse de la constante equivalente dans le nouvel exe = la PREMIERE copie en lecture seule de la meme
          valeur (meme regle que generer_module_exe.py), controlee comme etant le meme bloc de donnees que dans l'ancien
          exe (octets voisins identiques) ;
  - rel32 (saut du creneau) : `apres` = deplacement vers l'equivalent, dans le nouvel exe, du bloc « test de la piste »
          (retrouve lui aussi par son contexte) ;
  - en-tete : la valeur ajoutee dans le bourrage nul de l'en-tete (meme adresse, meme octets).

Usage : python -I -B fabriquer_modules_nouvel_exe.py <ancien_original> <nouveau> <dossier_modules_ancien> <sites_localises.json> <dossier_sortie> <rapport.md>
"""
import hashlib
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pe_lecture import Exe  # noqa: E402
from localiser_sites import Balayage, retrouver, lire_modules  # noqa: E402

SHA_ANCIEN = '1C9A01C3007CB2BEC2A04D716812CF9F24C87EFA11056395C89DDD7D2C341026'
SHA_NOUVEAU = '461E12623BACB7DE29CA27B4614425C87E8DF2C8327A5E958A957C850EFFE42A'
BLOC_PISTE_ANCIEN = 0x00701A2A        # `cmp dword ptr [edi], 1` : test de la piste (verifier_sites.py)
SORTIE_ANCIEN = 0x00701B04            # sortie commune des 3 sauts du creneau

STATUT = {
    'ascenseur_x2': "PRIORITAIRE (celui que le moddeur utilise) : utilise en jeu sur l'ancien exe ; sur le nouvel exe, controle sur les octets et au desassemblage seulement, jamais essaye en jeu.",
    'temps_x2': "PRIORITAIRE (celui que le moddeur utilise, MODE TEST) : utilise en jeu sur l'ancien exe ; sur le nouvel exe, controle sur les octets et au desassemblage seulement, jamais essaye en jeu.",
    'atterrissage_cercle': "SECONDAIRE : essaye en jeu sur l'ancien exe (essai 1 du 27/10 et essai 2 du 29/10) ; sur le nouvel exe, octets et desassemblage seulement.",
    'atterrissage_creneau': "SECONDAIRE : essaye en jeu sur l'ancien exe (essai 2 du 29/10, une seule partie, melange avec le cercle et pont_retour_x2) ; sur le nouvel exe, octets et desassemblage seulement.",
    'pont_retour_x2': "SECONDAIRE, PEU VU EN JEU : la fiche d'etude dit « jamais vu en jeu » ; il n'a tourne qu'une fois, melange aux autres (essai 2 du 29/10, copie « pont »). Sur le nouvel exe : octets et desassemblage seulement.",
    'helicos_approche_x2': "SECONDAIRE, JAMAIS VU EN JEU (valide sur le Mac seulement). Sur le nouvel exe : octets et desassemblage seulement.",
}


def copies_lecture_seule(exe, bits4):
    out = []
    for s in exe.secs:
        if s['exec'] or s['ecriture'] or s['rawsz'] <= 0:
            continue
        blob = exe.data[s['rawptr']:s['rawptr'] + min(s['vsize'], s['rawsz'])]
        j = blob.find(bits4)
        while j != -1:
            if j % 4 == 0:
                out.append(s['va'] + j)
            j = blob.find(bits4, j + 1)
    return sorted(out)


def main():
    if len(sys.argv) != 7:
        sys.exit(__doc__)
    p_old, p_new, d_mod, p_sites, d_out, p_md = sys.argv[1:7]
    A, N = Exe(p_old), Exe(p_new)
    if A.sha != SHA_ANCIEN or N.sha != SHA_NOUVEAU:
        sys.exit("REFUS : les exe donnes ne sont pas l'ancien original 1C9A01C3... et le nouvel exe 461E1262...")
    with open(p_sites, 'r', encoding='utf-8') as f:
        loc = json.load(f)
    if loc['problemes']:
        sys.exit('REFUS : localiser_sites.py a signale des problemes (%d) : rien n\'est fabrique.' % len(loc['problemes']))
    mods = lire_modules(d_mod)
    par_site = {(r['module'], r['va_ancien']): r for r in loc['resultats']}
    erreurs = []
    BA, BN = Balayage(A), Balayage(N)

    # --- equivalent du bloc « test de la piste » et de la sortie commune dans le nouvel exe
    equiv = {}
    for nom_b, va_b in (('piste', BLOC_PISTE_ANCIEN), ('sortie', SORTIE_ANCIEN)):
        i = BA.index_contenant(va_b, 1)
        if i is None or BA.addr[i] != va_b:
            erreurs.append('0x%08x n\'est pas un debut d\'instruction dans l\'ancien exe' % va_b)
            continue
        trouve, raison = retrouver(BA, BN, i)
        if trouve is None:
            erreurs.append('equivalent de %s 0x%08x : %s' % (nom_b, va_b, raison))
            continue
        Nn, i0, i1, pos = trouve
        va_deb = BN.va_texte + pos
        import bisect
        j = bisect.bisect_left(BN.addr, va_deb)
        va_new = BN.addr[j + (i - i0)]
        equiv[nom_b] = (va_new, Nn, BA.op[i], BN.op[j + (i - i0)], BA.mn[i], BN.mn[j + (i - i0)])
        if BA.mn[i] != BN.mn[j + (i - i0)]:
            erreurs.append('%s : instruction differente' % nom_b)
    if not erreurs:
        if equiv['piste'][4] != 'cmp' or equiv['piste'][2] != 'dword ptr [edi], 1' or equiv['piste'][3] != 'dword ptr [edi], 1':
            erreurs.append('le bloc piste n\'est pas `cmp dword ptr [edi], 1` dans les deux exe')

    rapport = []
    sortie = {}
    constantes = {}      # ancienne adresse de constante cible -> (nouvelle adresse, copies, verdict)
    tous_champs = []

    for nom, m in mods.items():
        nouveaux = []
        for c in m['changements']:
            r = par_site[(nom, c['va'])]
            if r['statut'] != 'sur':
                erreurs.append('%s 0x%08x : statut %s' % (nom, c['va'], r['statut']))
                continue
            typ = r['type']
            va_n, off_n = r['va_nouveau'], r['offset_nouveau']
            avant_n = N.data[off_n:off_n + 4]
            apres_n, cva_n, preuve = None, 0, ''
            if typ == 'cave_entete':
                apres_n, cva_n = bytes.fromhex(c['apres']), c['va']
                preuve = 'meme adresse, bourrage nul dans les deux exe'
            elif typ == 'imm':
                if avant_n.hex() != c['avant']:
                    erreurs.append('%s 0x%08x : immediat different' % (nom, c['va']))
                    continue
                apres_n = bytes.fromhex(c['apres'])
                preuve = 'immediat identique avant/apres qu\'a l\'ancien exe'
            elif typ == 'abs':
                p_old = struct.unpack('<I', bytes.fromhex(c['apres']))[0]
                if p_old in constantes:
                    q, copies, preuve = constantes[p_old]
                else:
                    bits = A.octets(p_old, 4) if p_old >= A.base + A.taille_en_tetes else bytes.fromhex(c['apres'])
                    if p_old < A.base + A.taille_en_tetes:
                        # valeur placee dans l'en-tete : meme adresse (le bourrage est identique) ; verifie plus haut
                        q, copies, preuve = p_old, [p_old], 'en-tete : meme adresse'
                    else:
                        copies = copies_lecture_seule(N, bits)
                        if not copies:
                            erreurs.append('%s 0x%08x : aucune copie de la valeur %s dans les sections en lecture seule du nouvel exe' % (nom, c['va'], bits.hex()))
                            continue
                        q = copies[0]
                        # meme bloc de donnees que dans l'ancien exe ? octets voisins identiques (16 avant, 20 apres)
                        voisin_a, voisin_n = A.octets(p_old - 16, 36), N.octets(q - 16, 36)
                        sa, sn = A.section(p_old), N.section(q)
                        if voisin_a != voisin_n or sa['nom'] != sn['nom']:
                            erreurs.append('%s 0x%08x : la constante cible 0x%08x -> 0x%08x n\'a pas les memes voisins (autre donnee ?)' % (nom, c['va'], p_old, q))
                            continue
                        preuve = 'premiere copie en lecture seule de %s (%s), voisins identiques a l\'ancien 0x%08x' % (
                            struct.unpack('<f', bits)[0], N.nom_section(q), p_old)
                    constantes[p_old] = (q, copies, preuve)
                apres_n, cva_n = struct.pack('<I', q), q
                # `avant` du nouvel exe : doit etre le nouvel avatar de la constante ancienne
                ta, tb = r['cible_ancien'], r['cible_nouveau']
                if struct.unpack('<I', avant_n)[0] != tb or A.f32(ta) != N.f32(tb):
                    erreurs.append('%s 0x%08x : `avant` incoherent' % (nom, c['va']))
                    continue
            elif typ == 'rel32':
                if 'piste' not in equiv or 'sortie' not in equiv:
                    continue
                rel_avant = struct.unpack('<i', avant_n)[0]
                cible_avant_n = va_n + 4 + rel_avant
                if cible_avant_n != equiv['sortie'][0]:
                    erreurs.append('%s 0x%08x : la cible d\'origine 0x%08x n\'est pas la sortie equivalente 0x%08x' % (nom, c['va'], cible_avant_n, equiv['sortie'][0]))
                    continue
                apres_n = struct.pack('<i', equiv['piste'][0] - (va_n + 4))
                preuve = 'saute au bloc « test de la piste » equivalent 0x%08x (contexte %d+%d) au lieu de la sortie 0x%08x' % (
                    equiv['piste'][0], equiv['piste'][1], equiv['piste'][1], equiv['sortie'][0])
            ch = dict(va=va_n, offset=off_n, avant=avant_n.hex(), apres=apres_n.hex(),
                      role='[NOUVEL EXE ; les adresses citees dans ce texte sont celles de l\'ANCIEN exe] ' + c['role'],
                      reglage=c['reglage'], constante_va=cva_n,
                      va_ancien=c['va'], offset_ancien=c['offset'], avant_ancien=c['avant'], apres_ancien=c['apres'],
                      type=typ, retrouve_par=r['contexte'], preuve=preuve)
            nouveaux.append(ch)
            tous_champs.append((nom, ch))
        sortie[nom] = (m, nouveaux)

    # --- chevauchements et coherence avec le fichier
    plages = sorted((ch['offset'], ch['offset'] + 4, nom) for nom, ch in tous_champs)
    for a, b in zip(plages, plages[1:]):
        if a[1] > b[0]:
            erreurs.append('chevauchement %x / %x' % (a[0], b[0]))
    for nom, ch in tous_champs:
        if N.data[ch['offset']:ch['offset'] + 4].hex() != ch['avant']:
            erreurs.append('%s 0x%08x : avant different du fichier' % (nom, ch['va']))
        if ch['type'] in ('abs',) and not N.est_reloc(ch['va']):
            erreurs.append('%s 0x%08x : pas de relocation sur l\'operande' % (nom, ch['va']))
        if ch['type'] in ('imm',) and N.est_reloc(ch['va']):
            erreurs.append('%s 0x%08x : relocation sur un immediat' % (nom, ch['va']))

    if erreurs:
        print("ERREURS (rien n'est ecrit) :")
        for e in erreurs:
            print(' -', e)
        return 1

    os.makedirs(d_out, exist_ok=True)
    md = ['# Modules d\'exe du NOUVEL exe de Steam (461E1262...) : octets site par site', '',
          'Genere par `tour/etude_port_nouvel_exe/outils/fabriquer_modules_nouvel_exe.py` a partir des 6 modules de l\'ancien build et des sites '
          'retrouves par `localiser_sites.py`. Etiquette : **MESURE** (octets et desassemblage), jamais vu en jeu.', '',
          '- nouvel exe : sha256 `%s`, %d octets, horodatage PE `0x%08x`' % (N.sha, len(N.data), N.horodatage)]
    resume = {}
    for nom, (m, nouveaux) in sortie.items():
        patche = bytearray(N.data)
        for ch in nouveaux:
            patche[ch['offset']:ch['offset'] + 4] = bytes.fromhex(ch['apres'])
        sha_p = hashlib.sha256(bytes(patche)).hexdigest().upper()
        module = dict(
            nom=nom,
            description=m['description'] + " [PORTE sur le build Steam du 28/10/2026 (461E1262...), horodatage 0x6ae228f3]",
            statut_portage=STATUT[nom],
            build=dict(fichier='carrier_command.exe', taille=len(N.data), horodatage_pe='0x%08x' % N.horodatage,
                       taille_image='0x%08x' % N.taille_image, base='0x%08x' % N.base),
            sha256_origine=N.sha, sha256_patche=sha_p, nb_changements=len(nouveaux), changements=nouveaux)
        if 'avertissement' in m:
            module['avertissement'] = m['avertissement']
        with open(os.path.join(d_out, nom + '.json'), 'w', encoding='utf-8') as f:
            json.dump(module, f, indent=1, ensure_ascii=False)
        resume[nom] = sha_p
        md += ['', '## `%s` (%d changements)' % (nom, len(nouveaux)), '', '*%s*' % STATUT[nom], '',
               '- sha256 avec ce module seul : `%s`' % sha_p, '',
               '| nouvelle adresse | decalage fichier | avant | apres | ancienne adresse | type | reglage | preuve |', '|---|---|---|---|---|---|---|---|']
        for ch in nouveaux:
            md.append('| `0x%08x` | `0x%x` | `%s` | `%s` | `0x%08x` | %s | `%s` | %s |' % (
                ch['va'], ch['offset'], ch['avant'], ch['apres'], ch['va_ancien'], ch['type'], ch['reglage'], ch['preuve'] or ch['retrouve_par']))
    md += ['', '## Constantes cibles (adresse ancienne -> nouvelle)', '', '| ancienne | nouvelle | valeur | choix |', '|---|---|---|---|']
    for p_old, (q, copies, preuve) in sorted(constantes.items()):
        md.append('| `0x%08x` | `0x%08x` | %s | %s (%d copie(s) en lecture seule) |' % (p_old, q, N.f32(q), preuve, len(copies)))
    with open(p_md, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md) + '\n')
    for nom, sha_p in resume.items():
        print('OK %-22s %2d changements  sha256 %s' % (nom, len(sortie[nom][1]), sha_p))
    print('constantes cibles :', len(constantes))
    return 0


if __name__ == '__main__':
    sys.exit(main())
