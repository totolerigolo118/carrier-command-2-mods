# Rapport de compilation du plugin cc2x_modes.dll — genere par `construire_modes.py`

Commit du SDK : `7ab05c79357e0cdb5bfaa2866bd3a81a101a09da`. Compilateur : Zig 0.15.2. Dossier de travail (hors depot, hors jeu) : `C:\Users\UTILISATEUR\Documents\cc2-modes-travail-v3_1`. **La DLL n'a pas ete chargee ni lancee, rien n'a ete copie dans le jeu.**

- taille 225280 octets, sha256 `4B2EBC04D772D7EFB2F21E70AA17CB7FE26CF7A044FDFE3B97F07FDCD1FE1D51`
- deuxieme compilation identique, hors horodatage PE et identifiant de build : oui
- PE32 i386 DLL : True ; TLS : present, callbacks identiques a ceux d une DLL vide (code du compilateur) ; imports retardes : absents ; exports : cc2x_plugin_load
- chaines suspectes : aucune
- verdict automatique : OK

| DLL importee | fonctions |
|---|---|
| api-ms-win-crt-convert-l1-1-0.dll | strtod, strtoul |
| api-ms-win-crt-runtime-l1-1-0.dll | _execute_onexit_table, _exit, _initialize_onexit_table, _initterm, _initterm_e, _register_onexit_function, abort |
| api-ms-win-crt-string-l1-1-0.dll | strcmp, strlen, strncmp |
| KERNEL32.dll | DeleteCriticalSection, EnterCriticalSection, GetLastError, GetPrivateProfileStringA, InitializeCriticalSection, LeaveCriticalSection, Sleep, TlsGetValue, VirtualProtect, VirtualQuery |
| api-ms-win-crt-stdio-l1-1-0.dll | __acrt_iob_func, __stdio_common_vfprintf, __stdio_common_vsprintf, fwrite |
| api-ms-win-crt-heap-l1-1-0.dll | calloc, free |
