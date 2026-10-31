# Capture d'ecran de LA FENETRE d'un processus (par defaut le jeu), pas de tout l'ecran, en PNG local. Rien n'est envoye nulle part.
# Methode : PrintWindow (contenu de la fenetre elle-meme, meme si une autre fenetre la recouvre -> on ne photographie jamais le travail
# de l'utilisateur). Repli CopyFromScreen SEULEMENT si la fenetre est au premier plan (donc rien ne la recouvre).
# Par defaut la fenetre n'est ni rouverte ni mise au premier plan (l'utilisateur travaille peut-etre dessus) ; -Rouvrir sert aux essais
# sans personne devant l'ecran : une fenetre reduite est rouverte (un jeu reduit ne dessine plus ses ecrans).
# Sortie : "OK LARGEURxHAUTEUR" (code 0) ou PAS_DE_FENETRE (3) / REDUITE (4) / FENETRE_TROP_PETITE (5) / NOIR_OU_OCCULTEE (7).
param(
    [Parameter(Mandatory = $true)][string]$Sortie,
    [string]$Processus = 'carrier_command',
    [switch]$Rouvrir,
    [switch]$Surlignage
)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class W32 {
    [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
    [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr h);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int cmd);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h, IntPtr hdc, uint flags);
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left, Top, Right, Bottom; }
}
"@
[void][W32]::SetProcessDPIAware()
$p = Get-Process -Name $Processus -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
if (-not $p) { Write-Output 'PAS_DE_FENETRE'; exit 3 }
$hwnd = $p.MainWindowHandle
if ($Rouvrir -and [W32]::IsIconic($hwnd)) {
    [void][W32]::ShowWindow($hwnd, 9)          # SW_RESTORE
    [void][W32]::SetForegroundWindow($hwnd)
    Start-Sleep -Milliseconds 1500
}
if ([W32]::IsIconic($hwnd)) { Write-Output 'REDUITE'; exit 4 }
$r = New-Object W32+RECT
[void][W32]::GetWindowRect($hwnd, [ref]$r)
$w = $r.Right - $r.Left
$h = $r.Bottom - $r.Top
if ($w -lt 200 -or $h -lt 200) { Write-Output "FENETRE_TROP_PETITE ${w}x${h}"; exit 5 }

function Test-Noir($bmp) {
    # echantillon de 600 points : image "noire" si presque aucun n'est allume
    $allumes = 0
    for ($i = 0; $i -lt 30; $i++) {
        for ($j = 0; $j -lt 20; $j++) {
            $c = $bmp.GetPixel([int](($bmp.Width - 1) * $i / 29), [int](($bmp.Height - 1) * $j / 19))
            if (($c.R + $c.G + $c.B) -gt 24) { $allumes++ }
        }
    }
    return ($allumes -lt 6)
}

$bmp = New-Object System.Drawing.Bitmap $w, $h
$g = [System.Drawing.Graphics]::FromImage($bmp)
$hdc = $g.GetHdc()
$ok = [W32]::PrintWindow($hwnd, $hdc, 2)       # PW_RENDERFULLCONTENT
$g.ReleaseHdc($hdc)
if (-not $ok -or (Test-Noir $bmp)) {
    if ([W32]::GetForegroundWindow() -eq $hwnd) {
        $g.CopyFromScreen($r.Left, $r.Top, 0, 0, $bmp.Size)       # fenetre au premier plan : rien ne la recouvre
    } else {
        $g.Dispose(); $bmp.Dispose()
        Write-Output 'NOIR_OU_OCCULTEE'; exit 7
    }
}
$g.Dispose()
$surligne = $null
if ($Surlignage) {
    # ligne "surlignee" d'une liste de menu = bandeau turquoise CLAIR ; on cherche ses lignes de pixels sur quelques colonnes
    $ys = New-Object System.Collections.Generic.List[int]
    $colonnes = 560, 640, 720, 800, 880, 960, 1040, 1100
    for ($y = [Math]::Min(100, $h - 1); $y -lt [Math]::Min(700, $h); $y += 2) {
        $n = 0
        foreach ($x in $colonnes) {
            if ($x -lt $w) {
                $c = $bmp.GetPixel($x, $y)
                if ($c.G -ge 135 -and $c.B -ge 135 -and $c.R -le 135 -and ($c.G - $c.R) -ge 45) { $n++ }
            }
        }
        if ($n -ge 5) { $ys.Add($y) }
    }
    # un vrai bandeau fait ~36 px de haut : on exige au moins 8 lignes balayees consecutives (16 px), ce qui ecarte un chiffre ou un mot turquoise
    $meilleur = $null; $groupe = New-Object System.Collections.Generic.List[int]
    foreach ($y in $ys) {
        if ($groupe.Count -gt 0 -and ($y - $groupe[$groupe.Count - 1]) -gt 2) {
            if ($groupe.Count -ge 8 -and ($null -eq $meilleur -or $groupe.Count -gt $meilleur.Count)) { $meilleur = $groupe }
            $groupe = New-Object System.Collections.Generic.List[int]
        }
        $groupe.Add($y)
    }
    if ($groupe.Count -ge 8 -and ($null -eq $meilleur -or $groupe.Count -gt $meilleur.Count)) { $meilleur = $groupe }
    if ($null -ne $meilleur) { $surligne = [int](($meilleur | Measure-Object -Average).Average) }
}
$bmp.Save($Sortie, [System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose()
Write-Output "OK ${w}x${h}"
if ($Surlignage) { if ($null -ne $surligne) { Write-Output "SURLIGNE $surligne" } else { Write-Output 'SURLIGNE aucun' } }
