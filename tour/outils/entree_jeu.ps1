# Envoie UNE entree (touche, mouvement de souris relatif, clic gauche) a la fenetre du jeu.
# Securite : rien n'est envoye si la fenetre du jeu n'est pas au premier plan (jamais a une autre application).
# Sortie : OK (code 0) / PAS_DE_FENETRE (3) / PAS_AU_PREMIER_PLAN (6) / TOUCHE_INCONNUE (8).
#   -Type touche -Touche shift|e|space|enter|escape|up|down|left|right|tab|une lettre a-z|un chiffre 0-9  [-Duree MS : touche MAINTENUE MS millisecondes, 20000 max]
#   -Type souris -Dx N -Dy N          (deplacement relatif en pixels, par petits pas)
#   -Type clic                        (clic gauche)
param(
    [string]$Processus = 'carrier_command',
    [ValidateSet('touche', 'souris', 'clic', 'curseur')][string]$Type = 'touche',
    [string]$Touche = 'shift',
    [int]$Dx = 0,
    [int]$Dy = 0,
    [int]$Duree = 0,
    [int]$X = 0,
    [int]$Y = 0
)
$ErrorActionPreference = 'Stop'
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class IN32 {
    [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr h);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int cmd);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern void keybd_event(byte vk, byte scan, uint flags, UIntPtr extra);
    [DllImport("user32.dll")] public static extern void mouse_event(uint flags, int dx, int dy, uint data, UIntPtr extra);
    [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
    [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
    [DllImport("user32.dll")] public static extern bool GetCursorPos(out POINT p);
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left, Top, Right, Bottom; }
    [StructLayout(LayoutKind.Sequential)] public struct POINT { public int X, Y; }
}
"@
$p = Get-Process -Name $Processus -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
if (-not $p) { Write-Output 'PAS_DE_FENETRE'; exit 3 }
$h = $p.MainWindowHandle
if ([IN32]::IsIconic($h)) { [void][IN32]::ShowWindow($h, 9) }
[void][IN32]::SetForegroundWindow($h)
Start-Sleep -Milliseconds 400
if ([IN32]::GetForegroundWindow() -ne $h) { Write-Output 'PAS_AU_PREMIER_PLAN'; exit 6 }

switch ($Type) {
    'touche' {
        $codes = @{ shift = 0xA0; e = 0x45; space = 0x20; enter = 0x0D; escape = 0x1B; up = 0x26; down = 0x28; left = 0x25; right = 0x27; tab = 0x09 }
        $nom = $Touche.ToLower()
        if ($codes.ContainsKey($nom)) { $vk = [byte]$codes[$nom] }
        elseif ($nom -match '^[a-z0-9]$') { $vk = [byte][int][char]$nom.ToUpper() }     # lettres et chiffres : code virtuel = code ASCII majuscule
        else { Write-Output 'TOUCHE_INCONNUE'; exit 8 }
        $attente = if ($Duree -gt 0) { [Math]::Min($Duree, 20000) } else { 90 }
        [IN32]::keybd_event($vk, 0, 0, [UIntPtr]::Zero)
        Start-Sleep -Milliseconds $attente
        [IN32]::keybd_event($vk, 0, 2, [UIntPtr]::Zero)
    }
    'souris' {
        # petits pas de 6 pixels maximum, comme une vraie main
        $nx = [Math]::Max([Math]::Abs($Dx), [Math]::Abs($Dy))
        $pas = [Math]::Max(1, [int][Math]::Ceiling($nx / 6.0))
        $ex = 0; $ey = 0
        for ($i = 1; $i -le $pas; $i++) {
            $cx = [int][Math]::Round($Dx * $i / $pas); $cy = [int][Math]::Round($Dy * $i / $pas)
            [IN32]::mouse_event(1, $cx - $ex, $cy - $ey, 0, [UIntPtr]::Zero)
            $ex = $cx; $ey = $cy
            Start-Sleep -Milliseconds 12
        }
    }
    'curseur' {
        # position ABSOLUE du curseur, en pixels a partir du coin haut-gauche de la fenetre du jeu (comme sur les captures)
        [void][IN32]::SetProcessDPIAware()
        $r = New-Object IN32+RECT
        [void][IN32]::GetWindowRect($h, [ref]$r)
        # SECURITE : la cible est ramenee DANS la fenetre du jeu (jamais sur la barre des taches ni une autre fenetre)
        $cx = [Math]::Min([Math]::Max($X, 20), ($r.Right - $r.Left) - 20)
        $cy = [Math]::Min([Math]::Max($Y, 45), ($r.Bottom - $r.Top) - 20)
        [void][IN32]::SetCursorPos($r.Left + $cx, $r.Top + $cy)
        Start-Sleep -Milliseconds 150
        [void][IN32]::SetCursorPos($r.Left + $cx, $r.Top + $cy)
    }
    'clic' {
        # SECURITE : on ne clique que si le curseur est DANS la fenetre du jeu (sinon rien n'est envoye)
        [void][IN32]::SetProcessDPIAware()
        $r = New-Object IN32+RECT
        [void][IN32]::GetWindowRect($h, [ref]$r)
        $pt = New-Object IN32+POINT
        [void][IN32]::GetCursorPos([ref]$pt)
        if ($pt.X -lt ($r.Left + 8) -or $pt.X -gt ($r.Right - 8) -or $pt.Y -lt ($r.Top + 40) -or $pt.Y -gt ($r.Bottom - 8)) {
            Write-Output 'CURSEUR_HORS_FENETRE'; exit 9
        }
        [IN32]::mouse_event(2, 0, 0, 0, [UIntPtr]::Zero)
        Start-Sleep -Milliseconds 70
        [IN32]::mouse_event(4, 0, 0, 0, [UIntPtr]::Zero)
    }
}
Write-Output 'OK'
