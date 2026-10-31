# Rapport de compilation du plugin cc2x_modes.dll — genere par `construire_modes.py`

Commit du SDK : `7ab05c79357e0cdb5bfaa2866bd3a81a101a09da`. Compilateur : Zig 0.15.2. Dossier de travail (hors depot, hors jeu) : `C:\Users\UTILISATEUR\Documents\cc2-modes-travail`. **La DLL n'a pas ete chargee ni lancee, rien n'a ete copie dans le jeu.**

- taille 222720 octets, sha256 `331581C64CB880AB0BC8CBC3258414F55C41723FB8DA7042CFDABE08CABC8729`
- deuxieme compilation identique, hors horodatage PE et identifiant de build : oui
- PE32 i386 DLL : True ; TLS : present, callbacks identiques a ceux d une DLL vide (code du compilateur) ; imports retardes : absents ; exports : cc2x_plugin_load
- chaines suspectes : aucune
- verdict automatique : OK

| DLL importee | fonctions |
|---|---|
| api-ms-win-crt-convert-l1-1-0.dll | atof, strtoul |
| api-ms-win-crt-private-l1-1-0.dll | strchr |
| api-ms-win-crt-runtime-l1-1-0.dll | _execute_onexit_table, _exit, _initialize_onexit_table, _initterm, _initterm_e, _register_onexit_function, abort |
| api-ms-win-crt-string-l1-1-0.dll | strlen, strncmp |
| KERNEL32.dll | DeleteCriticalSection, EnterCriticalSection, GetLastError, GetPrivateProfileStringA, InitializeCriticalSection, LeaveCriticalSection, Sleep, TlsGetValue, VirtualProtect, VirtualQuery |
| api-ms-win-crt-stdio-l1-1-0.dll | __acrt_iob_func, __stdio_common_vfprintf, __stdio_common_vsprintf, fwrite |
| api-ms-win-crt-heap-l1-1-0.dll | calloc, free |
