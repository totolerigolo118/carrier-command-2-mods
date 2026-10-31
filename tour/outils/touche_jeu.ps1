# Envoie UNE touche (Maj gauche, sans effet dans le jeu) a la fenetre du jeu, pour passer l'ecran-titre "PRESS ANY KEY".
# Securite : la touche n'est envoyee que si la fenetre du jeu est bien au premier plan ; sinon rien n'est envoye (jamais a une autre application).
# Sortie : OK (code 0) / PAS_DE_FENETRE (3) / PAS_AU_PREMIER_PLAN (6).
param([string]$Processus = 'carrier_command')
$ErrorActionPreference = 'Stop'
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class K32 {
    [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr h);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int cmd);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern void keybd_event(byte vk, byte scan, uint flags, UIntPtr extra);
}
"@
$p = Get-Process -Name $Processus -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
if (-not $p) { Write-Output 'PAS_DE_FENETRE'; exit 3 }
$h = $p.MainWindowHandle
if ([K32]::IsIconic($h)) { [void][K32]::ShowWindow($h, 9) }
[void][K32]::SetForegroundWindow($h)
Start-Sleep -Milliseconds 500
if ([K32]::GetForegroundWindow() -ne $h) { Write-Output 'PAS_AU_PREMIER_PLAN'; exit 6 }
[K32]::keybd_event(0xA0, 0x2A, 0, [UIntPtr]::Zero)      # Maj gauche enfoncee
Start-Sleep -Milliseconds 80
[K32]::keybd_event(0xA0, 0x2A, 2, [UIntPtr]::Zero)      # Maj gauche relachee
Write-Output 'OK'
