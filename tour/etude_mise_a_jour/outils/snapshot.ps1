param([string]$Root,[string]$OutFile)
$sha=[System.Security.Cryptography.SHA256]::Create()
$files=Get-ChildItem -LiteralPath $Root -Recurse -File -Force | Sort-Object FullName
$lines=New-Object System.Collections.Generic.List[string]
$lines.Add("chemin`ttaille`tdate_modif`tsha256")
foreach($f in $files){
  try{
    $fs=[System.IO.File]::Open($f.FullName,'Open','Read','ReadWrite')
    try{ $h=([BitConverter]::ToString($sha.ComputeHash($fs))).Replace('-','') } finally { $fs.Dispose() }
  }catch{ $h='ERREUR: '+$_.Exception.Message }
  $rel=$f.FullName.Substring($Root.Length).TrimStart('\')
  $lines.Add(("{0}`t{1}`t{2}`t{3}" -f $rel,$f.Length,$f.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss'),$h))
}
[System.IO.File]::WriteAllLines($OutFile,$lines,(New-Object System.Text.UTF8Encoding($false)))
"$($files.Count) fichiers"
