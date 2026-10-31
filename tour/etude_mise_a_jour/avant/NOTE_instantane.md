# Fiabilité de l'instantané « avant » (à lire avant de s'en servir)

**Heure** : 28/10/2026, lecture du dossier du jeu lancée vers 21:30:00 (voir `heure_instantane.txt` = fin de la copie, pas le début).

**Ce qui s'est passé** : Steam a appliqué la mise à jour **pendant** que je lisais les fichiers (journal Steam `content_log.txt` : début 21:30:03, copie des 791 fichiers à 21:30:04-05, fin 21:30:07). Le manifeste lu à 21:29:46 disait encore « mise à jour requise » (voir `appmanifest_AVANT_relu_21h29.txt`).

| Partie de l'instantané « avant » | Fiabilité | Pourquoi |
|---|---|---|
| Liste des 6 316 fichiers, **tailles** et **dates** | **Fiable** (état d'avant) | prises par l'énumération au tout début, avant la réécriture |
| **sha256 des 4 exécutables** (`carrier_command.exe` 0C5DFE52…, `carrier_command_vr.exe`, `dedicated_server.exe`, `build_content.exe`) | **Fiable** (état d'avant) | ils diffèrent de ceux d'après, donc lus avant la réécriture ; `carrier_command.exe` = bien l'exe patché connu |
| sha256 des 5 525 fichiers **non réécrits** par Steam (date inchangée) | **Fiable** | Steam ne les a pas touchés |
| sha256 des **787 fichiers `rom_0\audio\*.ogg`** | **Douteux** | Steam les a réécrits (taille identique) ; je les ai probablement lus *après* la réécriture. Si leur contenu avait changé, je ne le verrais pas. **INFÉRÉ** : ils n'ont pas changé (voir ETUDE.md §2) |
| `appmanifest_copie_prise_APRES_la_mise_a_jour_21h30.acf` | État **d'après** (copié trop tard) | gardé tel quel pour mémoire ; l'état d'avant est dans `appmanifest_AVANT_relu_21h29.txt` (recopié de ma lecture de 21:29:46) |
| `mods.xml` | Fiable | dossier AppData, non touché par Steam (date 27/10 17:44) |

Rien n'a été écrit ni modifié dans le dossier du jeu, dans AppData ni dans Steam.
