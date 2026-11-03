# Rapport de compilation (etape 3) — genere par `construire.py`

Commit du SDK : `7ab05c79357e0cdb5bfaa2866bd3a81a101a09da`. Compilateur : Zig 0.15.2. Dossier de travail (hors depot, hors jeu) : `C:\Users\UTILISATEUR\Documents\cc2-sdk-travail-v15`. Options = celles de `build.py` du SDK. **Rien n'a ete charge ni lance (les deux DLL), rien copie dans le jeu.**

**Dossier de travail separe** : le `dinput8.dll` ci-dessous (SDK a UN profil, recompile pour verifier les sources) n'est PAS celui du jeu (le jeu a le SDK a deux profils `E1DE25D5...`) et ne doit pas etre pose ; seul `cc2x_frein.dll` sert.

## dinput8.dll

- taille 267264 octets, sha256 `B4040F8D78BB460F6F291735D5AD7B90407C776B28C173EFC1B9106FBBC928A8`
- deuxieme compilation identique, hors horodatage PE et identifiant de build (20 octets) : oui
- PE32 i386 DLL : True ; TLS : present, callbacks identiques a ceux d une DLL vide (code du compilateur) ; imports retardes : absents; exports : DirectInput8Create, DllCanUnloadNow, DllGetClassObject, DllRegisterServer, DllUnregisterServer
- chaines suspectes : aucune
- verdict automatique : OK

| DLL importee | fonctions |
|---|---|
| api-ms-win-crt-math-l1-1-0.dll | atan2 |
| api-ms-win-crt-private-l1-1-0.dll | strrchr, strstr, wcsrchr |
| api-ms-win-crt-runtime-l1-1-0.dll | _execute_onexit_table, _exit, _initialize_onexit_table, _initterm, _initterm_e, _register_onexit_function, abort |
| api-ms-win-crt-stdio-l1-1-0.dll | __acrt_iob_func, __stdio_common_vfprintf, __stdio_common_vsprintf, __stdio_common_vswprintf, fclose, fopen, fwrite |
| api-ms-win-crt-string-l1-1-0.dll | _wcsicmp, strcmp, strlen, strncmp, wcscat, wcscpy, wcslen, wcsncpy |
| api-ms-win-crt-utility-l1-1-0.dll | qsort |
| KERNEL32.dll | CloseHandle, CreateDirectoryW, CreateFileW, DeleteCriticalSection, DeleteFileA, EnterCriticalSection, FindClose, FindFirstFileW, FindNextFileW, FlushInstructionCache, GetCurrentProcess, GetEnvironmentVariableW, GetFileAttributesW, GetFileSize, GetLastError, GetLocalTime, GetModuleFileNameA, GetModuleFileNameW, GetModuleHandleExW, GetModuleHandleW, GetPrivateProfileIntA, GetProcAddress, GetProcessHeap, GetSystemDirectoryW, HeapAlloc, HeapFree, InitOnceExecuteOnce, InitializeCriticalSection, LeaveCriticalSection, LoadLibraryExW, LoadLibraryW, MultiByteToWideChar, ReadFile, Sleep, TlsGetValue, VirtualAlloc, VirtualProtect, VirtualQuery, WideCharToMultiByte |
| api-ms-win-crt-heap-l1-1-0.dll | calloc, free |

## cc2x_frein.dll

- taille 253952 octets, sha256 `238B0456807AF87FE303F7033899C5CC7DC0F3659054DCDDF44C49FAD0FDE907`
- deuxieme compilation identique, hors horodatage PE et identifiant de build (20 octets) : oui
- PE32 i386 DLL : True ; TLS : present, callbacks identiques a ceux d une DLL vide (code du compilateur) ; imports retardes : absents; exports : cc2x_plugin_load
- chaines suspectes : aucune
- verdict automatique : OK

| DLL importee | fonctions |
|---|---|
| api-ms-win-crt-convert-l1-1-0.dll | atof |
| api-ms-win-crt-private-l1-1-0.dll | strchr |
| api-ms-win-crt-runtime-l1-1-0.dll | _execute_onexit_table, _exit, _initialize_onexit_table, _initterm, _initterm_e, _register_onexit_function, abort |
| api-ms-win-crt-string-l1-1-0.dll | strcmp, strlen, strncmp |
| KERNEL32.dll | DeleteCriticalSection, EnterCriticalSection, GetLastError, GetModuleHandleA, GetPrivateProfileStringA, InitializeCriticalSection, LeaveCriticalSection, Sleep, TlsGetValue, VirtualProtect, VirtualQuery |
| api-ms-win-crt-stdio-l1-1-0.dll | __acrt_iob_func, __stdio_common_vfprintf, __stdio_common_vsprintf, fwrite |
| api-ms-win-crt-heap-l1-1-0.dll | calloc, free |
