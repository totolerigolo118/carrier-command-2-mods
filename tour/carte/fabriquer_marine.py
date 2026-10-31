"""Fabrique la page de rejeu « carte marine » : le rejeu du Mac (modele_rejeu.html, jamais modifie) avec un autre rendu
(carte marine : hachures, cadre gradue, rose des vents ; couleurs du radar tactique ; pictos du jeu ; equipe 1 seule par defaut).
Le rendu est dans dessin_marine.js (a cote de ce fichier). Rien n'est envoye nulle part, et rien n'est ecrit hors de la sortie.

Usage : python -I fabriquer_marine.py <dossier carte_timelapse du Mac> <sortie.html> "Titre=chemin.log" ["Titre=chemin.log" ...]
  Le DERNIER journal donne se charge tout seul a l'ouverture ; les autres ont un bouton. Seules les lignes « CC2MAP| » sont lues.
  La sortie contient les pictos et la police du jeu : usage personnel, ne pas la partager ni la commiter (voir LISEZ-MOI_rendu_marine.md).
"""
import json
import os
import re
import sys

if len(sys.argv) < 4:
    raise SystemExit(__doc__)
MAC, OUT = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
PARTIES = []
for a in sys.argv[3:]:
    titre, sep, chemin = a.partition('=')
    if not sep or not titre or not os.path.isfile(chemin):
        raise SystemExit('REFUS : argument attendu « Titre=chemin.log » avec un fichier existant : %r' % a)
    PARTIES.append((titre, chemin))
if os.path.exists(OUT):
    raise SystemExit('REFUS : %s existe deja' % OUT)

ICI = os.path.dirname(os.path.abspath(__file__))
tpl = open(os.path.join(MAC, 'enregistreur', 'modele_rejeu.html'), encoding='utf-8').read()
rejeu = open(os.path.join(MAC, 'carte_rejeu.html'), encoding='utf-8').read()
fontcss = open(os.path.join(MAC, 'enregistreur', 'police_lanapixel.css'), encoding='utf-8').read()
dessin = open(os.path.join(ICI, 'dessin_marine.js'), encoding='utf-8').read()


def rep(s, old, new, n=1):
    assert s.count(old) == n, 'motif trouve %d fois (attendu %d) : %r' % (s.count(old), n, old[:70])
    return s.replace(old, new)


# --- ressources de la page du Mac : pictos du jeu et journal de demonstration
assets = re.search(r'const ASSETS = (\{.*?\});\nconst COL', rejeu, re.S).group(1)
json.loads(assets)
demolog = re.search(r'<script type="text/plain" id="demolog">(.*?)</script>', rejeu, re.S).group(1)

# --- style : couleurs du radar tactique, plus d'effets holographiques
s = tpl
s = rep(s, '<title>Table holographique CC2 : rejeu</title>', '<title>Carte marine CC2 : rejeu</title>')
s = rep(s, ':root{\n  --back:#00020a; --panel:rgba(0,26,52,.50); --line:rgba(0,123,201,.75);\n  --hi:#00ffff; --glow:#40ccff; --strong:#bff6ff; --body:#8fdcff; --weak:#4f9fd0;\n  --t1:#40ccff; --t2:#ffd21a; --t0:#ff3b30;',
        ':root{\n  --back:#05090b; --panel:rgba(10,26,30,.78); --line:rgba(61,242,255,.35);\n  --hi:#3df2ff; --glow:#3df2ff; --strong:#d8fbff; --body:#9fe8f0; --weak:#5fa3ad;\n  --t1:#3df2ff; --t2:#ff5a4d; --t0:#ffc24a;')
s = rep(s, 'body{text-shadow:-.5px 0 rgba(255,40,40,.28),.5px 0 rgba(40,90,255,.32)}\n', '')
s = rep(s, 'button.on{border-color:var(--hi);color:var(--hi);box-shadow:0 0 6px rgba(0,255,255,.35)}', 'button.on{border-color:var(--hi);color:var(--hi)}')
s = rep(s, ';box-shadow:0 0 18px rgba(0,160,255,.28),inset 0 0 22px rgba(0,160,255,.12)}', '}')
s = rep(s, '.top .info b{color:var(--t2);font-weight:normal}', '.top .info b{color:var(--t0);font-weight:normal}')
s = rep(s, '#001a34', '#0a1c20')
s = s.replace('rgba(0,10,25,', 'rgba(5,12,14,')
s = rep(s, '<h1>TABLE HOLOGRAPHIQUE · REJEU</h1>', '<h1>CARTE MARINE · REJEU</h1>')
s = rep(s, '<button id="btnDemo">Démo</button>', '<button id="btnDemo">Démo</button><span id="parties" style="display:contents"></span>')
s = rep(s, '<script type="text/plain" id="demolog">/*DEMOLOG*/</script>', '<script type="text/plain" id="demolog">/*DEMOLOG*/</script>\n/*PARTIES*/')
s = rep(s, "Formes d'îles indicatives. Pictogrammes du jeu de base : usage perso, ne pas partager.",
        "Formes d'îles indicatives. Équipe 1 seule par défaut : le bouton « IA des îles » affiche aussi les autres. Pictogrammes du jeu de base : usage perso, ne pas partager.")

# --- constantes : couleurs, filtre d'equipe, police a empattement pour les noms sur la carte
s = rep(s, "const COL = {1:'#40ccff', 2:'#ffd21a', 0:'#ff3b30'};", "const COL = {1:'#3df2ff', 2:'#ff5a4d', 0:'#ffc24a'};")
s = rep(s, 'const RGB = {1:[64,204,255], 2:[255,210,26], 0:[255,59,48]};', 'const RGB = {1:[61,242,255], 2:[255,90,77], 0:[255,194,74]};')
s = rep(s, "const TNAME = {1:'ÉQUIPE 1', 2:'ÉQUIPE 2', 0:'IA DES ÎLES'};",
        "const TNAME = {1:'ÉQUIPE 1', 2:'ÉQUIPE 2', 0:'IA DES ÎLES'};\nlet ONLY = 1;                              // équipe affichée (1 = toi seul) ; null = toutes\nconst teamOk = t => ONLY === null || t === ONLY;")
s = rep(s, "const FONT=px=>px+'px LanaPixel, ui-monospace, Menlo, monospace';",
        "const FONT=px=>px+'px LanaPixel, ui-monospace, Menlo, monospace';\nconst SERIF=(px,st)=>(st||'italic')+' '+px+'px Georgia,\"Times New Roman\",serif';")

# --- analyse : une disparition en masse de l'IA = iles dechargees, pas des destructions
s = rep(s, "[1,2,0].forEach(tm=>{const L=lost.filter(u=>u.team===tm);if(!L.length)return;",
        "[1,2,0].forEach(tm=>{const L=lost.filter(u=>u.team===tm);if(!L.length)return;if(tm===0&&L.length>=8)return;   // îles déchargées par le jeu : pas des pertes\n     ")

# --- etat a l'instant T : on ne garde que les equipes affichees
s = rep(s, "A.units.forEach(u=>{const b=B.map.get(u.id);", "A.units.forEach(u=>{if(!teamOk(u.team))return;const b=B.map.get(u.id);")
s = rep(s, "Object.values(R.routes).forEach(r=>{const pts=", "Object.values(R.routes).forEach(r=>{if(!teamOk(r.team))return;const pts=")
s = rep(s, "R.tracks.forEach(tr=>{\n    if(t>=tr.start", "R.tracks.forEach(tr=>{if(!teamOk(tr.team))return;\n    if(t>=tr.start")
s = rep(s, "R.booms.forEach(b=>{if(t>=b.tick", "R.booms.forEach(b=>{if(!teamOk(b.team))return;if(t>=b.tick")

# --- panneaux
s = rep(s, "[1,2,0].forEach(tm=>{const cnt={};", "[1,2,0].filter(teamOk).forEach(tm=>{const cnt={};")
s = rep(s, "R.events.filter(x=>x.tick<=T)", "R.events.filter(x=>teamOk(x.team)&&x.tick<=T)")
s = rep(s, "'<div style=\"color:#4f9fd0\">Aucun", "'<div style=\"color:var(--weak)\">Aucun")
s = rep(s, "const bar=$('bar');bar.querySelectorAll('u').forEach(u=>u.remove());R.events.forEach(ev=>{const u=document.createElement('u');u.style.left=((ev.tick-R.t0)/Math.max(1,R.t1-R.t0)*100)+'%';u.style.background=COL[ev.team];bar.appendChild(u);});",
        "buildMarks();")
s = rep(s, "+nU+' unités · '+", "+")
s = rep(s, "el.appendChild(b);});}\nfunction frame(t){",
        "el.appendChild(b);});\n  const ia=document.createElement('button');ia.textContent='IA DES ÎLES';ia.onclick=()=>{ONLY=ONLY===null?1:null;ia.classList.toggle('on',ONLY===null);buildMarks();};el.appendChild(ia);}\nfunction frame(t){")
s = rep(s, "if(location.hash==='#demo')$('btnDemo').click();", "if(location.hash==='#demo')$('btnDemo').click();parties();")

# --- dessin : on remplace tout l'ancien rendu holographique, en gardant les missiles du Mac (en plus petit)
i, j = s.index('function grid(c,e,g){'), s.index('function updateUI(w){')
ancien = s[i:j]
a, b = ancien.index('function missiles(c,e){'), ancien.index('function overlay(c,e){')
miss = ancien[a:b]
for vieux, neuf in (("icon(c,'missile',h[0],h[1],16,16,yaw,'#ffffff',7)", "icon(c,'missile',h[0],h[1],9,9,yaw,'#ffffff',0)"),
                    ("createRadialGradient(h[0],h[1],0,h[0],h[1],13)", "createRadialGradient(h[0],h[1],0,h[0],h[1],8)"),
                    ("c.arc(h[0],h[1],13,0,6.2832)", "c.arc(h[0],h[1],8,0,6.2832)"),
                    ("r:9,t:'Missile", "r:6,t:'Missile")):
    assert miss.count(vieux) == 1, vieux
    miss = miss.replace(vieux, neuf)
s = s[:i] + dessin.replace('/*MISSILES*/', miss) + s[j:]

# --- couleurs restantes (courbe de distance, infobulles)
for ancien_c, nouveau_c in (('#00ffff', '#3df2ff'), ('#bff6ff', '#d8fbff'), ('#4f9fd0', '#5fa3ad'), ('#8fdcff', '#9fe8f0')):
    s = s.replace(ancien_c, nouveau_c)

# --- assemblage
s = s.replace('/*FONT*/', fontcss).replace('/*ASSETS*/', assets).replace('/*DEMOLOG*/', demolog)
blocs = []
for k, (titre, chemin) in enumerate(PARTIES):
    t = open(chemin, encoding='latin-1').read()
    t = '\n'.join(l for l in t.splitlines() if 'CC2MAP|' in l)         # seulement les lignes de la carte
    assert '</script' not in t.lower()
    assert '"' not in titre
    blocs.append('<script type="text/plain" data-partie="%s"%s>%s</script>' % (titre, ' data-auto' if k == len(PARTIES) - 1 else '', t))
s = rep(s, '/*PARTIES*/', '\n'.join(blocs))
assert '/*' + 'FONT*/' not in s and '/*MISSILES*/' not in s
open(OUT, 'w', encoding='utf-8', newline='').write(s)
print('ecrit :', OUT, os.path.getsize(OUT), 'octets')
