# Écran des caméras CCTV plus net — étude (25/10/2026)

Demande n° 1499 du site de Geometa (« 128x128 → 256x256 »). Écran `screen_veh_top_r` du porte-avions, script
`scripts/screen_cctv.lua`. Le moddeur le veut « aussi net que possible ». Phase 1 = lecture seule (rien modifié).

## 1. Pour le moddeur, en clair

- Aujourd'hui, l'écran CCTV est une **image de 128 × 128 points**. Le jeu y dessine d'abord la vue de la caméra,
  puis par-dessus le cadre, le titre, « 1/2 » et les boutons. Quand on s'approche de l'écran, chaque point devient
  un gros carré (le jeu agrandit l'image sans la lisser) : d'où l'aspect « pixelisé ».
- Le jeu utilise **la même taille pour une trentaine d'écrans** du pont (navigation, armes, puissance…). On ne
  change donc pas la taille commune : on ajoute un petit morceau de code qui donne une image plus grande
  **seulement à l'écran CCTV**.
- Le cadre, les textes et les boutons gardent **exactement la même taille et la même police** : seule la vue de la
  caméra devient plus fine.
- Ce que coûte la caméra : ce n'est **pas** le rendu complet du jeu. C'est un rendu 3D **simplifié** : seulement
  ce qui est à moins de 200 m (le porte-avions et ce qui est posé dessus ou tout près), avec les textures, mais
  **sans éclairage, sans ombres, sans mer, sans effets**. Agrandir l'image ne change pas le nombre d'objets
  dessinés (c'est ça qui pèse sur le processeur de son Mac, via Rosetta) ; ça augmente seulement le nombre de
  points à colorier, ce que la carte graphique fait très vite pour un rendu aussi simple.

| Choix | Points | × aujourd'hui | Mémoire vidéo en plus | Effet attendu |
|---|---|---|---|---|
| Aujourd'hui | 128 × 128 = 16 000 | 1 | — | gros carrés visibles |
| **512** | 512 × 512 = 262 000 | 16 | ≈ 2,5 Mo | 4 fois plus fin ; de près, petits carrés encore visibles si le jeu tourne en pleine résolution Retina |
| **1024** | 1024 × 1024 = 1 million | 64 | ≈ 10 Mo | 8 fois plus fin ; plus aucun carré visible, même écran plein cadre |

- Pour comparer : la vue principale du jeu fait plusieurs millions de points par image, **avec** tout l'éclairage.
  512 = coût négligeable. 1024 = petit coût sur la carte graphique, **pas chiffrable sans essai** : on le vérifie
  avec les courbes du lag (une partie avec, comparée à une sans). Sur sa tour Windows, aucune question.
- Au-delà de 1024, plus rien à gagner : l'écran n'occupe jamais plus d'environ 1 000 points de haut à l'écran.
- Petit changement visible en plus : l'effet « écran du pont » (`screen_crt.glsl`) règle ses franges colorées et
  son grain sur la taille de l'image, donc franges et grain deviennent eux aussi plus fins. Les lignes de
  balayage ne changent pas. Les autres écrans ne changent pas.
- Tour Windows : comme tous les modules « programme », à refaire plus tard sur le programme Windows.

## 2. Ce que fait le programme (Mac, build_mac du 05/01/2026)

### 2.1 Création de l'image (128 × 128)

`c_game_object_client::create_lite` (0x1000ad572), boucle sur les écrans de l'objet (nombre en 0xd0, éléments de
0x230) :

```
1000ad74f  movslq 0x60(%rax,%rcx),%rax        ; type de l'écran (XML type=, définition éléments de 0x78)
1000ad754  movl $0x80,%r9d                    ; hauteur par défaut (type > 5)
1000ad75a  movl $0x80,%r8d                    ; largeur par défaut
1000ad760  cmpq $5,%rax ; ja 1000ad77c
1000ad766  lea 0x1028b1470 → r9d = haut[type] ; u32 : 128,128,256,256,192,32
1000ad771  lea 0x1028b1488 → r8d = larg[type] ; u32 : 128,256,512,256,256,64
1000ad798  call mm_resource_handle_target::create(…, 2 (couleur), 8, larg, haut, filtre 0, nom)
```

La table n'est lue **nulle part ailleurs**. Type 0 = 128 × 128 = **35 écrans** dans les XML (dont screen_veh_top_r). Changer
la table toucherait tous ces écrans → il faut choisir l'écran CCTV dans le code.

Définition d'un écran (éléments de 0x78, d'après la lecture du XML 0x100246470…) : 0x00 `name`, 0x10
`display_name_loc`, 0x18 `script_file_name` (mm_string), 0x28 `body_index`, 0x2c `seat_index`, 0x30 `transform`,
0x60 `type`, 0x64 `refresh_interval`, 0x68 `help_tag`. Repère proposé : `script_file_name` =
`scripts/screen_cctv.lua` (format exact de mm_string à lire en phase 2).

Filtrage de l'image (`create_surface_mipmap` 0x1000ae850) : RGBA8, MAG = **GL_NEAREST** (d'où les gros carrés),
MIN = GL_NEAREST_MIPMAP_LINEAR, mipmaps régénérés après chaque dessin (`generate_mipmap`, 0x10021cf2c). Vue de
loin = mipmaps, donc pas de scintillement avec une grande image.

### 2.2 Taille donnée au script Lua : indépendante

`c_vehicle_client_base::tick_screens` (0x10011e363…) passe `screen_w, screen_h` depuis **deux autres tables
float** (0x1028b1b54 largeurs, 0x1028b1b3c hauteurs, défaut 128.0 à 0x10286988c), mêmes valeurs. On ne les
touche pas : `screen_cctv.lua` et les library_custom continuent de voir 128 × 128 ; aucune autre supposition de
128 dans le script (bordures 5, barre 18, textes en points fixes, tous relatifs à 128). Le pointeur de la souris
passe par le type de l'écran, pas par l'image : inchangé.

### 2.3 Dessin de l'écran : ce qui suppose « points de l'image = unités du script »

`c_frontend_renderer::pass_screens` (0x10020ccae) → `render_screen` (0x10021cc14), cible = image de l'écran :

1. `render_command_screen_background` (0x10021d088) : fond type 9 (= caméra, `update_set_screen_background_type(9)`)
   en 0x10021d1c1…0x10021d911 : `mm_camera::build` avec le rapport largeur/hauteur de l'image, frustum, puis
   `mm_material_basic_texture` pour chaque objet. Marche à toute taille. (Le découpage optionnel des champs
   0x20…0x2c des réglages est en unités du script ; l'écran CCTV ne s'en sert pas.)
2. Caméra de l'interface (0x10021ce70…0x10021ce99) : orthographique (type 2), **largeur = image.w (0x20),
   hauteur = image.h (0x24)** → avec une image 1024, l'interface se dessinerait dans un coin, 8 fois trop petite.
   **À corriger** : 128 × 128 pour l'écran CCTV.
3. Interface : `callq *0x20(%rax)` à 0x10021cf10 (= `c_ui::element_container::render`). Les fenêtres découpent
   avec `c_ui::element_clip::render` (0x10015e658) = `glScissor(x, y, w, h)` (stub 0x10286807c, puis
   glEnable 0xC11) avec les unités du script **prises comme des points de l'image** → contenu de la fenêtre coupé.
   **À corriger** : multiplier x, y, w, h par l'échelle (4 ou 8) pendant le dessin de l'écran CCTV seulement
   (fonction partagée avec l'affichage de pilotage, la pause, l'overlay).
4. Traits `update_ui_line` = vraies lignes GL d'un point (`render_lines`) → seraient 4-8 fois plus fins ; l'écran
   CCTV n'en dessine pas (seuls `checkbox` et `divider` de library_ui.lua en font).

Effet du pont : `c_material_screen_crt::render` (0x10022633e) envoie `screen_resolution` = taille de l'image
(0x1002263b4) ; dans `screen_crt.glsl`, franges = 0,3 point de l'image, grain = taille / 256, balayage indépendant.

## 3. Plan de la phase 2 (greffes dans le code mort d'ImGui)

- **Greffe A** (create_lite, 0x1000ad754…0x1000ad77c) : si `script_file_name` = « scripts/screen_cctv.lua »,
  largeur = hauteur = N ; sinon code d'origine rejoué.
- **Greffe B** (render_screen, 0x10021ce70…) : si image N × N → caméra de l'interface 128 × 128 (128.0 existe :
  0x10286988c) et échelle = N / 128 dans une case libre ; sinon échelle 1.
- **Greffe C** (element_clip::render, 0x10015e662…0x10015e6a4) : x, y, w, h × échelle.
- **Greffe D** (fin de render_screen, après 0x10021cf10) : échelle remise à 1 (le pilotage, la pause et l'overlay
  utilisent aussi element_clip).
- Les entiers N sont écrits dans le code greffé : pas besoin des constantes float 512.0 / 1024.0 (n'importe
  quelle taille possible). Un module par taille (mêmes octets) : celui choisi dans `modules/`, l'autre en réserve.
- Vérifications : aucune cible de saut au milieu des instructions remplacées ; relecture objdump
  (`tests/test_patchs.py`) ; en jeu (par le moddeur) : interface CCTV à la même place et entière, les deux caméras,
  boutons < >, autres écrans inchangés ; courbes du lag avant / après.
- Retour arrière : menu de l'atelier, comme les autres.

## 4. Choix du moddeur

**512 × 512** (25/10). Module `cctv_net` écrit (`outil/generateurs/generer_cctv_net.py` + `cctv_net.s`),
testé sur copies (`tests/test_cctv_net.py` : relecture objdump + greffes exécutées sous Rosetta, 27 cas ;
`tests/test_patchs.py` : activation avec les autres modules). Activé dans le jeu le 25/10 à 09:04 (accord du moddeur) ; à vérifier en jeu.
