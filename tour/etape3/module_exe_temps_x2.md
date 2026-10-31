# Module exe `temps_x2` : simulation 2x plus vite (MODE TEST)

Genere par `tour/outils/generer_module_temps_x2.py`. **Un seul changement de 4 octets.**

- Boucle du serveur `0x0077ee10` (relue au desassembleur) : `mov ebx,0x21` (pas par defaut 33 ms), `movss xmm1,[esi+0x140]` (facteur), `comiss > 0`, `movss xmm0,[33.0]`, `divss xmm0,xmm1`, plafond `0x7d0` (2000 ms).
- Constructeur du serveur `0x00835b50` : `mov dword ptr [edi+0x140], 0x3f800000` en `0x00835cc5` (la SEULE ecriture dans l'exe) : l'immediat `00 00 80 3f` (1.0) devient `00 00 00 40` (2.0), en `0x00835ccb` (decalage fichier `0x4350cb`).
- Effet attendu : pas de 33 / 2 = 16 ms (conversion entiere) soit environ x2,06 en temps reel ; plus vite encore pour un facteur plus grand (33 / 3 = 11 ms) ; la machine doit suivre.
- Precautions : mode test uniquement (le serveur dicte la vitesse, donc aussi aux joueurs d'une partie hebergee) ; toute la partie accelere ; meteo et ocean sur leurs propres fils.
- sha256 origine `1C9A01C3007CB2BEC2A04D716812CF9F24C87EFA11056395C89DDD7D2C341026`, sha256 avec ce seul module `CFE824405FA59EF2419D9E44D81AF09E9D0D7BA587901535AF6AB348C0E8055A`.
- Retour arriere : `patch_exe.py retirer --module temps_x2`.
