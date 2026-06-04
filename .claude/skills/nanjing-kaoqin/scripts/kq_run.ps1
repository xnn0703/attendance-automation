# Nanjing-Liu-Bu monthly attendance pipeline. Pure ASCII; Chinese via code points; keys by gonghao(ASCII).
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File kq_run.ps1 -Stage prep|worklist|build [-Dir <folder>]
param([Parameter(Mandatory=$true)][ValidateSet('prep','worklist','build')][string]$Stage,[string]$Dir)
$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[System.Text.Encoding]::UTF8
Add-Type -AssemblyName System.IO.Compression.FileSystem | Out-Null
if([string]::IsNullOrEmpty($Dir)){ $Dir=(Get-Location).Path }
$NS='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
$XMLNS='http://www.w3.org/XML/1998/namespace'
function Uni{ param($a) -join ($a | ForEach-Object {[char]$_}) }

# ---- Chinese tokens (code points) ----
$T_yuan = Uni 0x539F,0x8868                 # yuan-biao
$T_hua  = Uni 0x82B1,0x540D,0x518C          # hua-ming-ce
$T_tiao = Uni 0x8C03,0x73ED                 # diao-ban
$T_chu  = Uni 0x521D,0x8868                 # chu-biao
$T_kao  = Uni 0x8003,0x52E4                 # kao-qin
$P_yuan = Uni 0xFF08,0x539F,0x8868,0xFF09   # (yuan-biao)
$P_chu  = Uni 0xFF08,0x521D,0x8868,0xFF09   # (chu-biao)
$P_kao  = Uni 0xFF08,0x8003,0x52E4,0xFF09   # (kao-qin)
$DEPTOK = Uni 0x5357,0x4EAC,0x516D,0x90E8   # Nanjing-Liu-Bu (department)
$LIZHI  = Uni 0x79BB,0x804C                  # li-zhi
$SUF    = Uni 0xFF08,0x79BB,0x804C,0xFF09    # (li-zhi)
$WAIQIN = Uni 0x5916,0x52E4                   # wai-qin
$BAN    = Uni 0x73ED                          # ban (work)
$XIU    = Uni 0x4F11                          # xiu (rest)
$xinsong= Uni 0x65B0,0x5B8B,0x4F53            # font name
$lblOT  = Uni 0x52A0,0x73ED,0x65F6,0x957F     # "jia-ban-shi-chang"

# ---- low-level helpers ----
function ReadZip($p,$n){ $z=[System.IO.Compression.ZipFile]::OpenRead($p); try{ $e=$z.GetEntry($n); if(-not $e){return $null}; $sr=New-Object System.IO.StreamReader($e.Open(),[System.Text.Encoding]::UTF8); $t=$sr.ReadToEnd(); $sr.Close(); return $t } finally { $z.Dispose() } }
function ColLetters([string]$r){ return ($r -replace '[0-9]','') }
function ColIdx([string]$s){ $n=0; foreach($ch in $s.ToCharArray()){ $n=$n*26+([int][char]$ch-64) }; return $n }
function ColName([int]$ci){ $s=''; $nn=$ci; while($nn -gt 0){ $m=($nn-1)%26; $s=[char](65+$m)+$s; $nn=[int][math]::Floor(($nn-$m-1)/26) }; return $s }
function SharedStrings($xml){ if(-not $xml){return ,(New-Object System.Collections.ArrayList)}; [xml]$x=$xml; $m=New-Object System.Xml.XmlNamespaceManager($x.NameTable); $m.AddNamespace('a',$NS); $o=New-Object System.Collections.ArrayList; foreach($si in $x.SelectNodes('//a:si',$m)){ [void]$o.Add( (($si.SelectNodes('.//a:t',$m)|ForEach-Object{$_.InnerText}) -join '') ) }; return ,$o }
function FindFile($token,$notTokens){ $cands=Get-ChildItem -LiteralPath $Dir -Filter *.xlsx -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "*$token*" -and $_.Name -notlike '*~$*' }; foreach($nt in $notTokens){ $cands=$cands | Where-Object { $_.Name -notlike "*$nt*" } }; return ($cands | Select-Object -First 1) }

# ---- year/month from "...YYYY-MM-DD..." in A1 ; days in month ----
function YearMonthFromSheet($sheetXml,$ss){ [xml]$x=$sheetXml; $m=New-Object System.Xml.XmlNamespaceManager($x.NameTable); $m.AddNamespace('a',$NS); $a1=$x.SelectSingleNode("//a:c[@r='A1']",$m); $txt=''; if($a1){ $isn=$a1.SelectSingleNode('a:is',$m); if($isn){$txt=(($isn.SelectNodes('.//a:t',$m)|ForEach-Object{$_.InnerText}) -join '')} else { $v=$a1.SelectSingleNode('a:v',$m); if($v){ if($a1.GetAttribute('t') -eq 's' -and $ss){$txt=[string]$ss[[int]$v.InnerText]} else {$txt=$v.InnerText} } } }; if($txt -match '(\d{4})-(\d{1,2})-\d{1,2}'){ return @{y=[int]$matches[1]; m=[int]$matches[2]} }; throw 'cannot find YYYY-MM in A1' }

# ---- roster: name -> list of {gonghao,zhiwei,yong,rz,lz} ; prefer active ----
function LoadRoster($fRos){
  $ss=SharedStrings (ReadZip $fRos 'xl/sharedStrings.xml')
  [xml]$sh=(ReadZip $fRos 'xl/worksheets/sheet1.xml'); $m=New-Object System.Xml.XmlNamespaceManager($sh.NameTable); $m.AddNamespace('a',$NS)
  $r=@{}
  foreach($row in $sh.SelectNodes('//a:row',$m)){ $rn=[int]$row.GetAttribute('r'); if($rn -lt 4){continue}; $cc=@{}; foreach($c in $row.SelectNodes('a:c',$m)){ $col=ColLetters($c.GetAttribute('r')); $t=$c.GetAttribute('t'); $v=$c.SelectSingleNode('a:v',$m); $tx=''; if($v){ if($t -eq 's'){$tx=$ss[[int]$v.InnerText]} else {$tx=$v.InnerText} } elseif($t -eq 'inlineStr'){ $isn=$c.SelectSingleNode('a:is',$m); if($isn){$tx=(($isn.SelectNodes('.//a:t',$m)|ForEach-Object{$_.InnerText}) -join '')} }; $cc[$col]=$tx }; $nmv=[string]$cc['C']; if($nmv.Trim() -eq ''){continue}; $e=@{name=$nmv.Trim();zhiwei=[string]$cc['E'];yong=[string]$cc['F'];gonghao=([string]$cc['G']).Trim();rz=[string]$cc['H'];lz=[string]$cc['I']}; if(-not $r.ContainsKey($e.name)){$r[$e.name]=New-Object System.Collections.ArrayList}; [void]$r[$e.name].Add($e) }
  return $r
}
function RosOf($roster,$name){ if(-not $roster.ContainsKey($name)){return $null}; $l=$roster[$name]; $a=@($l|Where-Object{$_.yong -ne $LIZHI}); if($a.Count -ge 1){return $a[0]}; return $l[0] }
function InMonthDay($serial,$y,$mo){ if([string]::IsNullOrEmpty($serial)){return $null}; $dt=[DateTime]::FromOADate([double]$serial); if($dt.Year -eq $y -and $dt.Month -eq $mo){return $dt.Day}; return $null }

# ---- calendar from diao-ban-biao: baseWork(day->true) + per-name override ----
function LoadCalendar($fTiao,$y,$mo){
  $ss=SharedStrings (ReadZip $fTiao 'xl/sharedStrings.xml')
  [xml]$sh=(ReadZip $fTiao 'xl/worksheets/sheet1.xml'); $m=New-Object System.Xml.XmlNamespaceManager($sh.NameTable); $m.AddNamespace('a',$NS)
  $baseWork=@{}; $swap=@{}
  $rePat='^\s*(\d{1,2})\s*(' + $BAN + '|' + $XIU + ')'
  foreach($row in $sh.SelectNodes('//a:row',$m)){
    foreach($c in $row.SelectNodes('a:c',$m)){
      $col=ColLetters($c.GetAttribute('r')); $ci=ColIdx($col)
      $t=$c.GetAttribute('t'); $v=$c.SelectSingleNode('a:v',$m); $tx=''
      if($v){ if($t -eq 's'){$tx=$ss[[int]$v.InnerText]} else {$tx=$v.InnerText} } elseif($t -eq 'inlineStr'){ $isn=$c.SelectSingleNode('a:is',$m); if($isn){$tx=(($isn.SelectNodes('.//a:t',$m)|ForEach-Object{$_.InnerText}) -join '')} }
      if($ci -ge 1 -and $ci -le 7 -and $tx -match $rePat){ $dd=[int]$matches[1]; if($matches[2] -eq $BAN){$baseWork[$dd]=$true} }
    }
  }
  # per-person: O + P columns' in-month dates -> FLIP base ban/xiu (which col=work/rest is not fixed; base decides)
  foreach($row in $sh.SelectNodes('//a:row',$m)){
    $rn=[int]$row.GetAttribute('r'); if($rn -lt 3){continue}
    $cc=@{}; foreach($c in $row.SelectNodes('a:c',$m)){ $col=ColLetters($c.GetAttribute('r')); $t=$c.GetAttribute('t'); $v=$c.SelectSingleNode('a:v',$m); $tx=''; if($v){ if($t -eq 's'){$tx=$ss[[int]$v.InnerText]} else {$tx=$v.InnerText} }; $cc[$col]=$tx }
    $nm=[string]$cc['M']; if($nm.Trim() -eq ''){continue}; $nm=$nm.Trim()
    foreach($d in ((DatesInMonth ([string]$cc['O']) $y $mo) + (DatesInMonth ([string]$cc['P']) $y $mo))){ if(-not $swap.ContainsKey($nm)){$swap[$nm]=@{}}; $swap[$nm][$d]=$true }
  }
  return @{base=$baseWork; swap=$swap}
}
function DatesInMonth($txt,$y,$mo){ $out=@(); if([string]::IsNullOrEmpty($txt)){return ,$out}; foreach($mm in [regex]::Matches($txt,'(\d{4})[/-](\d{1,2})[/-](\d{1,2})')){ if([int]$mm.Groups[1].Value -eq $y -and [int]$mm.Groups[2].Value -eq $mo){ $out += [int]$mm.Groups[3].Value } }; foreach($mm in [regex]::Matches($txt,'(?<![\d./-])(\d{5})(?:\.0+)?(?![\d./-])')){ try { $dt=[DateTime]::FromOADate([double]$mm.Groups[1].Value); if($dt.Year -eq $y -and $dt.Month -eq $mo){ $out += $dt.Day } } catch {} }; return ,$out }
function IsWork($cal,$name,$d){ $inb=$cal.base.ContainsKey($d); if($cal.swap.ContainsKey($name) -and $cal.swap[$name].ContainsKey($d)){return (-not $inb)}; return $inb }

# ---- punch parse / OT ----
function ParseDay([string]$txt){ $prev=$null;$off=0;$first=$null;$le=$null;$cnt=0;$wq=$false; foreach($ln in ($txt -split "`n")){ if($ln -match '(\d{1,2}):(\d{2})'){ $mm=[int]$matches[1]*60+[int]$matches[2]; if($prev -ne $null -and $mm -lt $prev){$off+=1440}; $eff=$mm+$off; if($cnt -eq 0){$first=$mm}; $le=$eff; $prev=$mm; $cnt++ }; if($ln -match $WAIQIN){$wq=$true} }; return @{cnt=$cnt;first=$first;le=$le;wq=$wq} }
function RU30([double]$m){ [int]([math]::Ceiling($m/30.0)*30) }
function RD30([double]$m){ [int]([math]::Floor($m/30.0)*30) }
function OTval($cnt,$first,$le,$wq,$isWork,$isExcl){ if($isExcl -or $cnt -lt 2){return 0.0}; if($isWork){ if($wq){return 0.0}; $end=RD30 $le; $o=$end-1110; if($o -lt 0){$o=0}; if($o -ge 120){$o-=30}; return $o/60.0 } else { $st=RU30 $first; if($st -lt 540){$st=540}; $er=$le; if($wq){$er=[math]::Min($er,1260)}; $end=RD30 $er; $raw=$end-$st; if($raw -lt 0){$raw=0}; $lunch=[math]::Max(0,[math]::Min($end,810)-[math]::Max($st,720)); $o=$raw-$lunch; if($o -gt 480){$o-=30}; if($o -lt 0){$o=0}; return $o/60.0 } }
function FmtOT([double]$h){ if($h -le 0){return $null}; $r=[math]::Round($h,1); if($r -eq [math]::Floor($r)){return ([int]$r).ToString()} else {return $r.ToString([System.Globalization.CultureInfo]::InvariantCulture)} }

# ---- config files ----
function ReadConfig(){ $cfg=@{ excl=@{}; strict=@{}; fontOnly=@{} }; $cfg.excl['Y17074']=$true; $cfg.excl['Y28001']=$true; $cfg.strict['Y28006']=545; $cfg.fontOnly['Y28001']=$true
  $f=Join-Path $Dir 'kq_config.txt'
  if(Test-Path $f){ $cfg=@{ excl=@{}; strict=@{}; fontOnly=@{} }; foreach($ln in (Get-Content -LiteralPath $f -Encoding UTF8)){ $ln=$ln.Trim(); if($ln -eq '' -or $ln.StartsWith('#')){continue}; $kv=$ln -split '=',2; if($kv.Count -lt 2){continue}; $k=$kv[0].Trim(); $val=$kv[1].Trim()
      if($k -eq 'OT_EXCLUDE'){ foreach($g in ($val -split ',')){ if($g.Trim()){$cfg.excl[$g.Trim()]=$true} } }
      elseif($k -eq 'LATE_FONT_ONLY'){ foreach($g in ($val -split ',')){ if($g.Trim()){$cfg.fontOnly[$g.Trim()]=$true} } }
      elseif($k -eq 'STRICT_LATE'){ foreach($pair in ($val -split ',')){ $p2=$pair -split ':'; if($p2.Count -eq 2){ $hm=$p2[1].Trim(); $mins=[int]$hm.Substring(0,2)*60+[int]$hm.Substring(2,2); $cfg.strict[$p2[0].Trim()]=$mins } } } } }
  return $cfg }
function ReadClassify(){ $c=@{}; $f=Join-Path $Dir 'kq_classify.txt'; if(Test-Path $f){ foreach($ln in (Get-Content -LiteralPath $f -Encoding UTF8)){ $ln=$ln.Trim(); if($ln -eq '' -or $ln.StartsWith('#')){continue}; $kv=$ln -split '='; if($kv.Count -eq 2){ $c[$kv[0].Trim()]=$kv[1].Trim().ToUpper() } } }; return $c }
function ReadKeep(){ $k=@{}; $f=Join-Path $Dir 'kq_keep.txt'; if(Test-Path $f){ foreach($ln in (Get-Content -LiteralPath $f -Encoding UTF8)){ foreach($g in ($ln -split '[,\s]+')){ if($g.Trim()){$k[$g.Trim()]=$true} } } }; return $k }

# ================= STAGE: prep =================
if($Stage -eq 'prep'){
  $fy=FindFile $T_yuan @($T_chu,$T_kao); if(-not $fy){ throw "no yuan-biao (*$T_yuan*) in $Dir" }
  $fr=FindFile $T_hua @(); if(-not $fr){ throw "no hua-ming-ce (*$T_hua*) in $Dir" }
  $roster=LoadRoster $fr.FullName; $keep=ReadKeep
  $doc=New-Object System.Xml.XmlDocument; $doc.PreserveWhitespace=$true; $doc.LoadXml((ReadZip $fy.FullName 'xl/worksheets/sheet1.xml'))
  $yss=SharedStrings (ReadZip $fy.FullName 'xl/sharedStrings.xml')
  $nm=New-Object System.Xml.XmlNamespaceManager($doc.NameTable); $nm.AddNamespace('a',$NS)
  function CT($c){ if(-not $c){return ''}; $t=$c.GetAttribute('t'); if($t -eq 'inlineStr'){ $isn=$c.SelectSingleNode('a:is',$nm); if($isn){return (($isn.SelectNodes('.//a:t',$nm)|ForEach-Object{$_.InnerText}) -join '')} }; $v=$c.SelectSingleNode('a:v',$nm); if(-not $v){return ''}; if($t -eq 's'){return [string]$yss[[int]$v.InnerText]}; return $v.InnerText }
  function Gcell($row,$col){ foreach($c in $row.SelectNodes('a:c',$nm)){ if((ColLetters($c.GetAttribute('r'))) -eq $col){return $c} }; return $null }
  function SetIn($c,$text){ $v=$c.SelectSingleNode('a:v',$nm); if($v){[void]$c.RemoveChild($v)}; $oi=$c.SelectSingleNode('a:is',$nm); if($oi){[void]$c.RemoveChild($oi)}; $c.SetAttribute('t','inlineStr'); $is=$doc.CreateElement('is',$NS); $t=$doc.CreateElement('t',$NS); $a=$doc.CreateAttribute('xml','space',$XMLNS); $a.Value='preserve'; [void]$t.Attributes.Append($a); $t.InnerText=$text; [void]$is.AppendChild($t); [void]$c.AppendChild($is) }
  $sheetData=$doc.SelectSingleNode('//a:sheetData',$nm); $allRows=@($sheetData.SelectNodes('a:row',$nm)); $rowByNum=@{}; foreach($rw in $allRows){ $rowByNum[[int]$rw.GetAttribute('r')]=$rw }
  $kept=New-Object System.Collections.ArrayList; $dropped=New-Object System.Collections.ArrayList; $askKeep=New-Object System.Collections.ArrayList
  foreach($rw in $allRows){ $r=[int]$rw.GetAttribute('r'); if($r -lt 5){continue}
    $nameRaw=CT (Gcell $rw 'A'); if($nameRaw.Trim() -eq ''){continue}; $dept=CT (Gcell $rw 'C'); $name=$nameRaw.Replace($SUF,'')
    $pd=0; foreach($c in $rw.SelectNodes('a:c',$nm)){ $ci=ColIdx(ColLetters($c.GetAttribute('r'))); if($ci -ge 7){ if((CT $c).Trim() -ne ''){$pd++} } }
    if($dept -ne $DEPTOK){ [void]$dropped.Add("$nameRaw  [dept=$dept]"); continue }
    $ros=RosOf $roster $name; if(-not $ros){ [void]$dropped.Add("$nameRaw  [no-roster-match]"); continue }
    if($ros.yong -eq $LIZHI -and $pd -lt 7){ if($keep.ContainsKey($ros.gonghao)){ [void]$askKeep.Add("$nameRaw $($ros.gonghao) pd=$pd -> KEPT") } else { [void]$dropped.Add("$nameRaw  [lizhi pd=$pd<7, not in kq_keep]"); [void]$askKeep.Add("$nameRaw $($ros.gonghao) pd=$pd -> DROPPED"); continue } }
    $cd=Gcell $rw 'D'; if(-not $cd){ $cd=$doc.CreateElement('c',$NS); $cd.SetAttribute('r',"D$r"); $cd.SetAttribute('s','10'); [void]$rw.AppendChild($cd) }; SetIn $cd $ros.gonghao
    $ce=Gcell $rw 'E'; if(-not $ce){ $ce=$doc.CreateElement('c',$NS); $ce.SetAttribute('r',"E$r"); $ce.SetAttribute('s','10'); [void]$rw.AppendChild($ce) }; SetIn $ce $ros.zhiwei
    [void]$kept.Add([pscustomobject]@{row=$rw;name=$name;gh=$ros.gonghao;ghn=[int]($ros.gonghao -replace '[^0-9]','');pd=$pd;yong=$ros.yong})
  }
  $sorted=@($kept | Sort-Object ghn)
  foreach($rw in $allRows){ [void]$sheetData.RemoveChild($rw) }
  foreach($n in 1..4){ if($rowByNum[$n]){ [void]$sheetData.AppendChild($rowByNum[$n]) } }
  $nr=5; foreach($p in $sorted){ $rw=$p.row; $rw.SetAttribute('r',"$nr"); foreach($c in @($rw.SelectNodes('a:c',$nm))){ $cl=ColLetters($c.GetAttribute('r')); $c.SetAttribute('r',"$cl$nr") }; [void]$sheetData.AppendChild($rw); $nr++ }
  $last=$nr-1; $dn=$doc.SelectSingleNode('//a:dimension',$nm); if($dn){$dn.SetAttribute('ref',"A1:AK$last")}
  $newSheet=$doc.OuterXml; if($newSheet -notmatch '^<\?xml'){ $newSheet='<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'+$newSheet }
  $initName= if($fy.Name -like "*$P_yuan*"){ $fy.Name.Replace($P_yuan,$P_chu) } else { [IO.Path]::GetFileNameWithoutExtension($fy.Name)+$P_chu+'.xlsx' }
  $fOut=Join-Path $Dir $initName
  Copy-Item -LiteralPath $fy.FullName -Destination $fOut -Force
  $za=[System.IO.Compression.ZipFile]::Open($fOut,'Update'); try{ $e=$za.GetEntry('xl/worksheets/sheet1.xml'); if($e){$e.Delete()}; $ne=$za.CreateEntry('xl/worksheets/sheet1.xml'); $sw=New-Object System.IO.StreamWriter($ne.Open(),(New-Object System.Text.UTF8Encoding($false))); $sw.Write($newSheet); $sw.Close() } finally { $za.Dispose() }
  Write-Host ("[prep] wrote: " + $fOut); Write-Host ("[prep] KEPT " + $sorted.Count + " ; DROPPED " + $dropped.Count)
  $i=0; foreach($p in $sorted){ $i++; Write-Host ("  {0,2} {1,-8} {2}  ({3}) pd={4}" -f $i,$p.gh,$p.name,$p.yong,$p.pd) }
  Write-Host "DROPPED:"; foreach($d in $dropped){ Write-Host ("  "+$d) }
  if($askKeep.Count -gt 0){ Write-Host "LIZHI-<7 CANDIDATES (edit kq_keep.txt with gonghao to KEEP, then re-run prep):"; foreach($a in $askKeep){ Write-Host ("  "+$a) } }
  return
}

# ============ shared for worklist/build ============
$fc=FindFile $T_chu @($T_kao); if(-not $fc){ throw "no chu-biao (*$T_chu*) in $Dir - run -Stage prep first" }
$ft=FindFile $T_tiao @(); if(-not $ft){ throw "no diao-ban-biao (*$T_tiao*) in $Dir" }
$fr=FindFile $T_hua @(); if(-not $fr){ throw "no hua-ming-ce (*$T_hua*) in $Dir" }
$chuSheet=ReadZip $fc.FullName 'xl/worksheets/sheet1.xml'
$css=SharedStrings (ReadZip $fc.FullName 'xl/sharedStrings.xml')
$ym=YearMonthFromSheet $chuSheet $css; $Y=$ym.y; $MO=$ym.m; $DAYS=[DateTime]::DaysInMonth($Y,$MO)
$roster=LoadRoster $fr.FullName; $cal=LoadCalendar $ft.FullName $Y $MO
[xml]$cdoc=$chuSheet; $cm=New-Object System.Xml.XmlNamespaceManager($cdoc.NameTable); $cm.AddNamespace('a',$NS)
function CTc($c){ if(-not $c){return ''}; $t=$c.GetAttribute('t'); if($t -eq 'inlineStr'){ $isn=$c.SelectSingleNode('a:is',$cm); if($isn){return (($isn.SelectNodes('.//a:t',$cm)|ForEach-Object{$_.InnerText}) -join '')} }; $v=$c.SelectSingleNode('a:v',$cm); if(-not $v){return ''}; if($t -eq 's'){return [string]$css[[int]$v.InnerText]}; return $v.InnerText }
$ppl=New-Object System.Collections.ArrayList
foreach($row in $cdoc.SelectNodes('//a:row',$cm)){ $r=[int]$row.GetAttribute('r'); if($r -lt 5){continue}; $cells=@{}; foreach($c in $row.SelectNodes('a:c',$cm)){ $cells[(ColIdx(ColLetters($c.GetAttribute('r'))))]=$c }; $name=(CTc $cells[1]); if($name.Trim() -eq ''){continue}; $gh=(CTc $cells[4]); $dmap=@{}; foreach($d in 1..$DAYS){ $dmap[$d]=(CTc $cells[$d+6]) }; [void]$ppl.Add([pscustomobject]@{row=$row;cells=$cells;gh=$gh;ghn=[int]($gh -replace '[^0-9]','');name=$name;bare=$name.Replace($SUF,'');dmap=$dmap}) }
$ppl=@($ppl | Sort-Object ghn)
function PunchCnt($txt){ $n=0; foreach($ln in ($txt -split "`n")){ if($ln -match '\d{1,2}:\d{2}'){$n++} }; return $n }
function WinOf($bare){ $ros=RosOf $roster $bare; $s=1;$e=$DAYS;$j=$null; if($ros){ $md=InMonthDay $ros.rz $Y $MO; if($md){$s=$md;$j=$md}; $me=InMonthDay $ros.lz $Y $MO; if($me){$e=$me} }; return @{s=$s;e=$e;j=$j} }

# ================= STAGE: worklist =================
if($Stage -eq 'worklist'){
  Write-Host ("[worklist] " + $Y + "-" + $MO + " ; days=" + $DAYS + " ; people=" + $ppl.Count)
  $idx=0
  foreach($p in $ppl){ $w=WinOf $p.bare; $rows=New-Object System.Collections.ArrayList
    foreach($d in 1..$DAYS){ if($d -lt $w.s -or $d -gt $w.e){continue}; if(-not (IsWork $cal $p.bare $d)){continue}
      $cnt=PunchCnt $p.dmap[$d]; if($cnt -lt 2){ $idx++; $txt=$p.dmap[$d]; $wq= if($txt -match $WAIQIN){'WQ'}else{'  '}; $sug= if($cnt -eq 0){'R(absent)'}else{'G(missing)'}; $disp=($txt -replace "`r?`n",' | ').Trim(); if($disp -eq ''){$disp='(empty)'}; [void]$rows.Add(("    #{0,-3} d{1,2} cnt={2} {3} sug={4}  key={5}|{6}  [{7}]" -f $idx,$d,$cnt,$wq,$sug,$p.gh,$d,$disp)) } }
    if($rows.Count -gt 0){ Write-Host ("=== {0} {1} (win d{2}-d{3}) ===" -f $p.gh,$p.bare,$w.s,$w.e); $rows|ForEach-Object{Write-Host $_} } }
  Write-Host ("TOTAL <2-punch workday cases: " + $idx)
  Write-Host ("Classify each into kq_classify.txt as 'gonghao|day=B|G|R'  (B=gong-chu/blue, G=que-ka/green, R=wei-chu-qin/red).")
  return
}

# ================= STAGE: build =================
$cfg=ReadConfig; $cls=ReadClassify
# styles indices appended: 12 redbg,13 greenbg,14 bluebg,15 purplebg,16 redfont,17 rf+green,18 rf+blue,19 rf+redbg
function DayStyle($p,$d,$pi,$isWork){
  if(-not $isWork){ if($pi.cnt -ge 2 -and $pi.wq){return 14}; return 10 }
  if($pi.cnt -lt 2){ $k=$cls["$($p.gh)|$d"]; if(-not $k){ $k= if($pi.cnt -eq 0){'R'}else{'G'} }; if($k -eq 'R'){return 12}; if($k -eq 'G'){return 13}; return 14 }
  $thr= if($cfg.strict.ContainsKey($p.gh)){$cfg.strict[$p.gh]}else{570}
  $w=WinOf $p.bare
  if($cfg.fontOnly.ContainsKey($p.gh) -or ($w.j -ne $null -and $d -eq $w.j)){ $thr=100000 }
  if($pi.wq){ if($pi.first -ne $null -and $pi.first -gt 540 -and $pi.first -le $thr){return 18}; return 14 }
  $heavy=($pi.first -ne $null -and $pi.first -gt $thr); $mild=($pi.first -ne $null -and $pi.first -gt 540 -and -not $heavy); $early=($pi.le -ne $null -and $pi.le -lt 1110)
  if($heavy -or $early){ if($mild){return 19}; return 12 }
  if($mild){return 16}; return 10
}
function Breaks($p,$d,$pi,$isWork){ if(-not $isWork){return $false}; if($pi.cnt -lt 2){ $k=$cls["$($p.gh)|$d"]; if(-not $k){$k= if($pi.cnt -eq 0){'R'}else{'G'}}; return ($k -eq 'R' -or $k -eq 'G') }; if($pi.first -ne $null -and $pi.first -gt 540){return $true}; if((-not $pi.wq) -and $pi.le -ne $null -and $pi.le -lt 1110){return $true}; return $false }

$doc=$cdoc; $nm=$cm
function NewEl($n){ return $doc.CreateElement($n,$NS) }
function SetSpace($el){ $a=$doc.CreateAttribute('xml','space',$XMLNS); $a.Value='preserve'; [void]$el.Attributes.Append($a) }
$sheetData=$doc.SelectSingleNode('//a:sheetData',$nm); $allRows=@($sheetData.SelectNodes('a:row',$nm)); $rowByNum=@{}; foreach($rw in $allRows){ $rowByNum[[int]$rw.GetAttribute('r')]=$rw }
foreach($rw in $allRows){ [void]$sheetData.RemoveChild($rw) }
foreach($n in 1..4){ if($rowByNum[$n]){ [void]$sheetData.AppendChild($rowByNum[$n]) } }
$summary=New-Object System.Collections.ArrayList; $k=0
foreach($p in $ppl){
  $w=WinOf $p.bare; $isExcl=$cfg.excl.ContainsKey($p.gh); $pNum=5+2*$k; $oNum=6+2*$k; $otByDay=@{}; $otTot=0.0; $quan=$true
  for($d=1;$d -le $DAYS;$d++){ if($d -lt $w.s -or $d -gt $w.e){continue}; $isW=IsWork $cal $p.bare $d; $pi=ParseDay $p.dmap[$d]
    $st=DayStyle $p $d $pi $isW; $cell=$p.cells[$d+6]; if($st -ne 10 -and $cell){ $cell.SetAttribute('s',"$st") }
    $ot=OTval $pi.cnt $pi.first $pi.le $pi.wq $isW $isExcl; if($ot -gt 0){ $otByDay[$d]=$ot; $otTot+=$ot }
    if(Breaks $p $d $pi $isW){ $quan=$false } }
  if($quan -and $p.cells[1]){ $p.cells[1].SetAttribute('s','15') }
  $prow=$p.row; $prow.SetAttribute('r',"$pNum"); foreach($c in @($prow.SelectNodes('a:c',$nm))){ $cl=ColLetters($c.GetAttribute('r')); $c.SetAttribute('r',"$cl$pNum") }; [void]$sheetData.AppendChild($prow)
  $orow=NewEl 'row'; $orow.SetAttribute('r',"$oNum"); $orow.SetAttribute('spans','1:37'); if($prow.HasAttribute('ht')){$orow.SetAttribute('ht',$prow.GetAttribute('ht'))}; if($prow.HasAttribute('customHeight')){$orow.SetAttribute('customHeight',$prow.GetAttribute('customHeight'))}
  foreach($ci in (@(1,2,3,4,5,6)+(7..37))){ $cell=NewEl 'c'; $cell.SetAttribute('r',((ColName $ci)+"$oNum")); $cell.SetAttribute('s','10'); if($ci -eq 1){ $cell.SetAttribute('t','inlineStr'); $is=NewEl 'is'; $t=NewEl 't'; SetSpace $t; $t.InnerText=$lblOT; [void]$is.AppendChild($t); [void]$cell.AppendChild($is) } elseif($ci -ge 7){ $d=$ci-6; if($otByDay.ContainsKey($d)){ $val=FmtOT $otByDay[$d]; if($val -ne $null){ $v=NewEl 'v'; $v.InnerText=$val; [void]$cell.AppendChild($v) } } }; [void]$orow.AppendChild($cell) }
  [void]$sheetData.AppendChild($orow)
  [void]$summary.Add([pscustomobject]@{gh=$p.gh;name=$p.bare;ot=$otTot;quan=$quan;excl=$isExcl}); $k++
}
$last=4+2*$ppl.Count; $dn=$doc.SelectSingleNode('//a:dimension',$nm); if($dn){$dn.SetAttribute('ref',"A1:AK$last")}
$newSheet=$doc.OuterXml; if($newSheet -notmatch '^<\?xml'){ $newSheet='<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'+$newSheet }
# styles
$styles=ReadZip $fc.FullName 'xl/styles.xml'
$redFont='<font><name val="'+$xinsong+'"/><sz val="12.0"/><color rgb="FFFF0000"/><u val="none"/></font>'
$fillsAdd='<fill><patternFill patternType="solid"><fgColor rgb="FFFF0000"/><bgColor indexed="64"/></patternFill></fill><fill><patternFill patternType="solid"><fgColor rgb="FF92D050"/><bgColor indexed="64"/></patternFill></fill><fill><patternFill patternType="solid"><fgColor rgb="FFDDEBF7"/><bgColor indexed="64"/></patternFill></fill><fill><patternFill patternType="solid"><fgColor rgb="FFD09ECE"/><bgColor indexed="64"/></patternFill></fill>'
function XF($f,$l){ '<xf numFmtId="0" fontId="'+$f+'" fillId="'+$l+'" borderId="4" xfId="0" applyBorder="true" applyFill="true" applyFont="true" applyAlignment="true"><alignment horizontal="center" vertical="center" wrapText="true"/></xf>' }
$xfsAdd=(XF 4 11)+(XF 4 12)+(XF 4 13)+(XF 4 14)+(XF 6 10)+(XF 6 12)+(XF 6 13)+(XF 6 11)
if($styles -notmatch '<fonts count="6">'){ throw 'unexpected styles.xml (fonts!=6); template assumptions broken' }
$styles=$styles -replace '<fonts count="6">','<fonts count="7">'; $styles=$styles -replace '</fonts>',($redFont+'</fonts>')
$styles=$styles -replace '<fills count="11">','<fills count="15">'; $styles=$styles -replace '</fills>',($fillsAdd+'</fills>')
$styles=$styles -replace '<cellXfs count="12">','<cellXfs count="20">'; $styles=$styles -replace '</cellXfs>',($xfsAdd+'</cellXfs>')
$kaoName= if($fc.Name -like "*$P_chu*"){ $fc.Name.Replace($P_chu,$P_kao) } else { [IO.Path]::GetFileNameWithoutExtension($fc.Name)+$P_kao+'.xlsx' }
$fOut=Join-Path $Dir $kaoName
Copy-Item -LiteralPath $fc.FullName -Destination $fOut -Force
$za=[System.IO.Compression.ZipFile]::Open($fOut,'Update'); try{ foreach($pair in @(@('xl/worksheets/sheet1.xml',$newSheet),@('xl/styles.xml',$styles))){ $e=$za.GetEntry($pair[0]); if($e){$e.Delete()}; $ne=$za.CreateEntry($pair[0]); $sw=New-Object System.IO.StreamWriter($ne.Open(),(New-Object System.Text.UTF8Encoding($false))); $sw.Write($pair[1]); $sw.Close() } } finally { $za.Dispose() }
Write-Host ("[build] wrote: " + $fOut + "  A1:AK" + $last + "  ("+$Y+"-"+$MO+")")
$qn=0; foreach($s in $summary){ if($s.quan){$qn++} }
Write-Host ("[build] people=" + $summary.Count + "  total OT=" + (($summary|Measure-Object ot -Sum).Sum) + "h  full-attendance=" + $qn)
foreach($s in $summary){ Write-Host ("  {0,-8} {1,-7} OT={2,5}  quan={3} excl={4}" -f $s.gh,$s.name,$s.ot,([int]$s.quan),([int]$s.excl)) }
