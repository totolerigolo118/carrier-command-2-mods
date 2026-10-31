"""Lecture d'un journal cc2x.log : lignes CC2MAP (carte) et evenements « id 9 » du plugin frein.
Rien n'est ecrit ; aucune autre ligne du journal n'est gardee (elles peuvent contenir des chemins locaux)."""
import re

RX_LINE = re.compile(r'^(\d\d):(\d\d):(\d\d\.\d+) .*?CC2MAP\|([HVTM])\|(\d+)\|(.*)$')
RX_PART = re.compile(r'^(\d+)/(\d+)\|(.*)$')
RX_FREIN = re.compile(r'^(\d\d):(\d\d):(\d\d\.\d+) \[frein\] info: id (\d+): (BRAKE start|HOLD|STOPPED|RECALL start|IDLE ended|BRAKE released|left the zone)(.*)$')
GAP = {'V': 100, 'T': 600, 'M': 5}


def parse(path):
    """-> dict(V=[(heure_s, tick, {id: (def, team, x, z, yaw)})], T=[(heure_s, tick, {id: (team, x, z)})], events=[(heure_s, id, mot, reste_de_la_ligne)])"""
    groups = {'V': {}, 'T': {}, 'M': {}}
    events = []
    with open(path, encoding='latin-1') as f:
        for ln in f:
            m = RX_LINE.match(ln)
            if m:
                h, mi, s, kind, tick, rest = m.groups()
                if kind == 'H':
                    continue
                mm = RX_PART.match(rest)
                if not mm:
                    continue
                part, n, body = int(mm.group(1)), int(mm.group(2)), mm.group(3)
                wall = int(h) * 3600 + int(mi) * 60 + float(s)
                g = groups[kind].setdefault(int(tick), {'n': n, 'wall': wall, 'parts': {}})
                g['wall'] = min(g['wall'], wall)
                g['parts'][part] = body
                continue
            m = RX_FREIN.match(ln)
            if m:
                h, mi, s, uid, mot, rest = m.groups()
                events.append((int(h) * 3600 + int(mi) * 60 + float(s), int(uid), mot, rest))
    out = {'events': events}
    for kind in 'VTM':
        snaps, last = [], -10 ** 9
        for tick in sorted(groups[kind]):
            g = groups[kind][tick]
            if len(g['parts']) < g['n'] or tick - last < GAP[kind]:
                continue                          # instantane incomplet, ou doublon d'un autre ecran
            last = tick
            items = {}
            for p in range(1, g['n'] + 1):
                for it in g['parts'][p].split(';'):
                    if not it:
                        continue
                    a = [float(v) for v in it.split(',')]
                    if kind == 'V':
                        items[int(a[0])] = (int(a[1]), int(a[2]), a[3], a[4], a[5] if len(a) > 5 else 0.0)
                    elif kind == 'T':
                        items[int(a[0])] = (int(a[1]), a[2], a[3])
                    else:
                        items[int(a[0])] = (int(a[1]), int(a[2]), a[3], a[4])
            snaps.append((g['wall'], tick, items))
        out[kind] = snaps
    return out


def hms(s):
    s = int(round(s))
    return '%02d:%02d:%02d' % (s // 3600 % 24, s // 60 % 60, s % 60)
