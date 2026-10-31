# Crédits et licence / Credits and licence

## SDK CC2X (logiciel tiers / third-party)

Les plugins de ce paquet sont écrits pour le **SDK CC2X** (« Carrier Command 2 extender »), auteur **Dioramawhois**,
sous licence **GNU GPL-3.0** : https://github.com/Dioramawhois/Carrier-Command-2-extender — version utilisée 0.5.0,
commit `7ab05c79357e0cdb5bfaa2866bd3a81a101a09da`. Merci à son auteur : sans ce SDK, aucun plugin Windows n'existerait.

The plugins in this package are written for the **CC2X SDK** ("Carrier Command 2 extender") by **Dioramawhois**,
licensed under the **GNU GPL-3.0** (link and commit above). Thanks to its author.

Le SDK n'est **pas** inclus : prenez-le à sa source. Notre modification pour le nouvel exe (2e profil) est un diff du
SDK, donc aussi sous GPL-3.0 : `tour/etude_port_nouvel_exe/sdk/profil_nouvel_exe.diff`. / The SDK is **not** included:
get it from its source. Our change for the new exe (second profile) is a diff of the SDK, also under GPL-3.0.

## Nos plugins / Our plugins — GPL-3.0-or-later

Ces sources incluent `cc2x.h` et sont compilées contre le SDK : elles sont distribuées sous **GPL-3.0-or-later**
(en-tête `SPDX-License-Identifier: GPL-3.0-or-later` dans chaque fichier C), texte complet dans `LICENSE`.
These sources include `cc2x.h` and are distributed under **GPL-3.0-or-later** (full text in `LICENSE`):

- `tour/atterrissage_manuel/frein/` — `cc2x_frein` (frein et reprise de l'avion / brake and hand-over)
- `tour/etude_bouton_hold/plugin/` — `cc2x_hold` v2.1 (copies synchronisées du bouton Hold / synchronised Hold button copies)
- `tour/etudes_modes_carburant/plugin/` — `cc2x_modes` (modes carburant / fuel modes)
- `extension_windows/` — `cc2_patchs` (squelette, jamais utilisé / skeleton, never used)

Aucune DLL compilée n'est fournie. Si vous distribuez une DLL compilée à partir de ces sources, la GPL vous demande de
fournir aussi ses sources (elles sont ici) et cette licence.
No compiled DLL is provided. If you distribute a DLL built from these sources, the GPL requires you to provide its
sources (they are here) and this licence.

## Le reste du paquet / The rest of the package

Outils Python, scripts Lua, études et mesures : même licence, **GPL-3.0-or-later** : vous pouvez tout réutiliser,
modifier et repartager. / Python tools, Lua scripts, studies and measurements: same licence, **GPL-3.0-or-later**:
reuse, change and share them freely.

## Le jeu / The game

*Carrier Command 2* est un jeu de **Geometa**. Ce paquet ne contient **aucun** exe, DLL, sauvegarde, picto, police ni
fichier du jeu. Les outils de patch ne contiennent que des adresses et quelques octets « avant / après » : il faut
posséder le jeu. Les mods fabriqués par les scripts (par exemple le mod Hold) recopient chez vous, à l'installation, un
fichier de votre jeu : ne redistribuez pas ces mods fabriqués. Respectez les conditions du développeur.

*Carrier Command 2* is a game by **Geometa**. This package contains **no** game exe, DLL, save, icon, font or game
file. The patch tools only hold addresses and a few "before / after" bytes: you need to own the game. Mods built by the
scripts copy one of your own game files at install time: do not redistribute those built mods.

## Outils utilisés / Tools used (non inclus / not included)

Python, Zig (compilateur / compiler), capstone, Pillow, ffmpeg.
