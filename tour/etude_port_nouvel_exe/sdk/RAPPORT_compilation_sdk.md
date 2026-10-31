# Rapport de compilation du SDK avec le 2e profil (partie 2) — genere par `fabriquer_sdk_nouvel_exe.py`

Commit du SDK : `7ab05c79357e0cdb5bfaa2866bd3a81a101a09da` (CC2X 0.5.0). Compilateur : Zig 0.15.2, memes options que `build.py` du SDK et que `construire.py`. Dossier de travail (hors depot, hors jeu) : `C:\Users\UTILISATEUR\Documents\cc2-port-travail\sdk`. **Aucune DLL chargee, lancee ni posee.**

## 1. La chaine de compilation est-elle la meme ?

- sources INCHANGEES recompilees ici : `B1122032422299AFB342593DF2A0DC097AB127E22E3D4B559D68B39A5AFAFD37` (267264 octets)
- `dinput8.dll` du jeu (LECTURE seule) : `184B144D6E2BB868FFEB7D45ECD463F8919E64732E3B5681A16165363EBA0982` (somme attendue)
- identiques hors horodatage PE et identifiant de build : **OUI**

## 2. DLL avec les deux profils

- taille 268288 octets, sha256 `E1DE25D53A5588BDA62269D6D93335ACB9F32EA555AC9274FE7973C19D6225D7`
- deuxieme compilation identique hors horodatage PE et identifiant de build : **oui**
- PE32 i386 DLL : True ; TLS : present ; imports retardes : absents ; exports : DirectInput8Create, DllCanUnloadNow, DllGetClassObject, DllRegisterServer, DllUnregisterServer
- chaines suspectes : aucune
- verdict automatique : **OK**

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

- imports identiques a ceux de la DLL du jeu (184B144D...) : **OUI**
