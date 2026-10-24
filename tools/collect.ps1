param(
 [Parameter(Mandatory=$true)][ValidatePattern('^COM[0-9]+$')][string]$Port,
 [ValidateSet(9600,115200)][int]$Baud=115200,
 [ValidateRange(1,3600)][int]$Seconds=120,
 [ValidateSet('UNLABELLED','LINE','BACKGROUND','TEXT','TRACK','MARKER')][string]$Label='UNLABELLED',
 [string]$OutputDirectory=(Join-Path $PSScriptRoot '..\captures')
)
# Receive-only. Never sends start commands, AT commands, or firmware.
$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Path $root -Force | Out-Null
$base=Join-Path $root ('run-'+[DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss-fff'))
$header='millis,tick,dt,rawA5,rawA4,rawA3,rawA2,rawA1,mask,state,reason,position,accepted_position,contrast,left_pwm,right_pwm,rejected,timing_faults'
$serial=[IO.Ports.SerialPort]::new($Port,$Baud,'None',8,'One')
$serial.DtrEnable=$false;$serial.RtsEnable=$false;$serial.ReadTimeout=200
$raw=$csv=$null;$count=0;$invalid=0;$bytes=0;$pending='';$problem=$null
$watch=[Diagnostics.Stopwatch]::new();$buffer=[byte[]]::new(8192)
try {
 $serial.Open()
 $raw=[IO.File]::Open($base+'.bin',[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
 $csv=[IO.StreamWriter]::new($base+'.csv',$false,[Text.UTF8Encoding]::new($false))
 $csv.WriteLine('host_ms,label,'+$header);$watch.Start()
 Write-Host "CONNECTED $Port; receive-only; label=$Label"
 Write-Host 'Keys: L=line G=background T=text R=track M=marker U=unlabelled Q=end capture.'
 Write-Host 'Capture mode keeps motors OFF. For track mode keep wheels raised for first start.'
 $done=$false
 while(-not $done -and $watch.Elapsed.TotalSeconds -lt $Seconds) {
  if(-not [Console]::IsInputRedirected) {
   while([Console]::KeyAvailable) {
    $key=[Console]::ReadKey($true).Key.ToString()
    $labels=@{L='LINE';G='BACKGROUND';T='TEXT';R='TRACK';M='MARKER';U='UNLABELLED'}
    if($key -eq 'Q'){$done=$true;break}
    if($labels.ContainsKey($key)){$Label=$labels[$key];Write-Host "LABEL=$Label"}
   }
  }
  $available=$serial.BytesToRead
  if($available -le 0){Start-Sleep -Milliseconds 5;continue}
  $n=$serial.Read($buffer,0,[Math]::Min($buffer.Length,$available))
  $raw.Write($buffer,0,$n);$bytes+=$n
  $pending += [Text.Encoding]::ASCII.GetString($buffer,0,$n)
  while($pending.Contains("`n")) {
   $end=$pending.IndexOf("`n");$line=$pending.Substring(0,$end).TrimEnd("`r")
   $pending=$pending.Substring($end+1)
   if($line -notmatch '^\d+(,(-?\d+)){17}$'){$invalid++;continue}
   $csv.WriteLine(([string]$watch.ElapsedMilliseconds)+','+$Label+','+$line);$count++
   if($count -eq 1 -or $count % 50 -eq 0){Write-Host $line;$csv.Flush();$raw.Flush()}
  }
  if($pending.Length -gt 16384){$invalid++;$pending=''}
 }
} catch {$problem=$_.Exception.Message;Write-Host "ERROR: $problem"}
finally {
 $watch.Stop();if($csv){$csv.Dispose()};if($raw){$raw.Dispose()}
 if($serial.IsOpen){$serial.Close()};$serial.Dispose()
}
$receipt=[ordered]@{recordedAt=[DateTime]::UtcNow.ToString('o');port=$Port;baud=$Baud;
 rows=$count;invalidLines=$invalid;partialTailCharacters=$pending.Length;bytesReceived=$bytes;
 elapsedSeconds=$watch.Elapsed.TotalSeconds;transmitPayloadBytes=0;error=$problem}
if(Test-Path -LiteralPath ($base+'.bin')){$receipt.rawSha256=(Get-FileHash -LiteralPath ($base+'.bin')).Hash}
$receipt | ConvertTo-Json | Set-Content -LiteralPath ($base+'.capture.json') -Encoding utf8
Write-Host "Saved $count records: $base.*"
if($problem -or $count -eq 0){exit 1}
