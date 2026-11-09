param([string]$template, [string]$json, [string]$out)
# Fill Report5_Unit Test.xls (Cover, Functions, Statistics, one matrix sheet per function) keeping the template formats.
$ErrorActionPreference = 'Stop'
function SetV($rng, $val) { try { [void]$rng.GetType().InvokeMember('Value2', [Reflection.BindingFlags]::SetProperty, $null, $rng, @(,$val)) } catch { throw "SetV failed at $($rng.Worksheet.Name)!$($rng.Address(0,0)) : $($_.Exception.InnerException.Message)" } }
function GetV($rng) { return $rng.GetType().InvokeMember('Value2', [Reflection.BindingFlags]::GetProperty, $null, $rng, $null) }

$d = Get-Content -Raw -Encoding UTF8 $json | ConvertFrom-Json
$p = $d.project
$xl = New-Object -ComObject Excel.Application
$xl.Visible = $false; $xl.DisplayAlerts = $false; $xl.ScreenUpdating = $false
$wb = $xl.Workbooks.Open($template)
$wb.SaveAs($out, 56)
try {
  $xl.Calculation = -4135
  $funcs = @($d.funcs); $nf = $funcs.Count
  $tester = $p.creator

  # ---------------------------------------------------------------- Cover
  $c = $wb.Worksheets.Item('Cover')
  SetV $c.Range('B4') ([string]$p.name)
  SetV $c.Range('B5') ([string]$p.code)
  SetV $c.Range('F4') ([string]$p.creator)
  SetV $c.Range('F5') ([double]$p.issue); $c.Range('F5').NumberFormat = 'dd/mm/yyyy'
  $c.Range('B6').Formula = '=B5&"_"&"Unit Test"&"_"&"v' + $p.version + '"'
  $c.Range('F6').NumberFormat = '@'; SetV $c.Range('F6') ([string]$p.version)
  SetV $c.Range('A11') ([double]$p.issue); $c.Range('A11').NumberFormat = 'dd/mm/yyyy'
  $c.Range('B11').NumberFormat = '@'; SetV $c.Range('B11') ([string]$p.version)
  SetV $c.Range('C11') ('Whole document')
  SetV $c.Range('D11') ('A')
  SetV $c.Range('E11') ("Initial unit test document: $nf functions of the backend services, results of the JUnit 5 run on the main branch (commit 408d1fd).")
  SetV $c.Range('F11') ('Report4_Software Design Document_LockR')

  # ---------------------------------------------------------------- Functions list
  $fl = $wb.Worksheets.Item('Functions')
  SetV $fl.Range('E6') ('N/A')
  SetV $fl.Range('E7') ("1. Server / build: JDK 21, Maven 3.9, Spring Boot 3 test slice`n2. Framework: JUnit 5, Mockito, AssertJ, Spring MockMvc`n3. Database: H2 / mocked repositories; PostgreSQL tests use Testcontainers (Docker)`n4. Command: mvn -B test on the backend repository (main branch)")
  $fl.Rows(7).RowHeight = 62
  if ($nf -gt 3) { $fl.Range("A14:A$(10 + $nf)").EntireRow.Insert() | Out-Null }
  $fl.Rows(13).Copy($fl.Range("A11:A$(10 + $nf)").EntireRow) | Out-Null
  for ($i = 0; $i -lt $nf; $i++) {
    $f = $funcs[$i]; $r = 11 + $i
    SetV $fl.Cells.Item($r, 1) ([double]($i + 1))
    SetV $fl.Cells.Item($r, 2) ([string]$f.req)
    SetV $fl.Cells.Item($r, 3) ([string]$f.cls)
    SetV $fl.Cells.Item($r, 4) ([string]$f.method)
    SetV $fl.Cells.Item($r, 5) ([string]$f.code)
    SetV $fl.Cells.Item($r, 6) ([string]$f.sheet)
    SetV $fl.Cells.Item($r, 7) ([string]$f.desc)
    SetV $fl.Cells.Item($r, 8) ([string]$f.pre)
  }
  $lr = $fl.Range("A11:H$(10 + $nf)"); $lr.WrapText = $true; $lr.VerticalAlignment = -4160
  $lr.Font.Underline = -4142; $lr.Font.ColorIndex = 1
  $lr.EntireRow.AutoFit() | Out-Null

  # ---------------------------------------------------------------- function sheets
  $tpl = $wb.Worksheets.Item('Function 1')
  $tpl.PageSetup.LeftHeader = $p.code + '_Unit Test'
  $last = $wb.Worksheets.Item($wb.Worksheets.Count)
  for ($i = 0; $i -lt $nf; $i++) {
    $f = $funcs[$i]; $tests = @($f.tests); $nt = $tests.Count
    $tpl.Copy([Type]::Missing, $last)
    $ws = $wb.Worksheets.Item($last.Index + 1); $last = $ws
    $ws.Name = $f.sheet

    # distinct values per group, in first-use order
    $groups = [ordered]@{ pre = New-Object System.Collections.ArrayList; inp = New-Object System.Collections.ArrayList;
                          ret = New-Object System.Collections.ArrayList; exc = New-Object System.Collections.ArrayList;
                          log = New-Object System.Collections.ArrayList }
    foreach ($t in $tests) { foreach ($g in @('pre', 'inp', 'ret', 'exc', 'log')) { foreach ($v in @($t.$g)) { if ($v -and -not $groups[$g].Contains([string]$v)) { [void]$groups[$g].Add([string]$v) } } } }
    $needC = 1 + $groups.pre.Count + 1 + $groups.inp.Count          # Precondition label, values, Input label, values
    $needF = 1 + $groups.ret.Count + 1 + $groups.exc.Count + 1 + $groups.log.Count

    $ws.Range('F9:T9').ClearContents() | Out-Null
    $ws.Range('L3:T3').Merge(); $ws.Range('L3').WrapText = $false
    $ws.Range('C2').NumberFormat = 'General'; $ws.Range('L2').NumberFormat = 'General'
    $ws.Range('B10:T42').ClearContents() | Out-Null
    $ws.Range('B11:T38').UnMerge()
    # confirm block: rows 31..38 (8 rows)
    if ($needF -gt 8) { $ws.Range("A38:A$(38 + $needF - 9)").EntireRow.Insert() | Out-Null }
    elseif ($needF -lt 8) { $ws.Range("A$(31 + $needF):A38").EntireRow.Delete() | Out-Null }
    # condition block: rows 10..30 (21 rows)
    if ($needC -gt 21) { $ws.Range("A30:A$(30 + $needC - 22)").EntireRow.Insert() | Out-Null }
    elseif ($needC -lt 21) { $ws.Range("A$(10 + $needC):A30").EntireRow.Delete() | Out-Null }
    # columns: template has 15 test columns F..T
    if ($nt -gt 15) { for ($k = 0; $k -lt $nt - 15; $k++) { $ws.Columns(20).Insert() | Out-Null } }
    $lastCol = 5 + [Math]::Max($nt, 15)

    $cRow = 10; $fRow = 10 + $needC; $resRow = $fRow + $needF
    $map = New-Object 'System.Collections.Generic.Dictionary[string,int]'
    $r = $cRow
    SetV $ws.Cells.Item($r, 2) ('Precondition'); $r++
    foreach ($v in $groups.pre) { $map["pre|$v"] = $r; SetV $ws.Cells.Item($r, 4) ($v); $r++ }
    SetV $ws.Cells.Item($r, 2) ('Input'); $ws.Cells.Item($r, 2).Font.Bold = $true; $r++
    foreach ($v in $groups.inp) { $map["inp|$v"] = $r; SetV $ws.Cells.Item($r, 4) ($v); $r++ }
    $r = $fRow
    foreach ($g in @(@('ret', 'Return'), @('exc', 'Exception'), @('log', 'Log message'))) {
      SetV $ws.Cells.Item($r, 2) ($g[1]); $ws.Cells.Item($r, 2).Font.Bold = $true; $r++
      foreach ($v in $groups[$g[0]]) { $map["$($g[0])|$v"] = $r; SetV $ws.Cells.Item($r, 4) ($v); $r++ }
    }
    $ws.Range("D$($cRow):D$($resRow - 1)").Font.Bold = $false
    $ws.Range("D$($cRow):D$($resRow - 1)").HorizontalAlignment = -4152
    for ($k = 0; $k -lt $nt; $k++) {
      $t = $tests[$k]; $col = 6 + $k
      SetV $ws.Cells.Item(9, $col) ('UTCID{0:D2}' -f ($k + 1))
      foreach ($g in @('pre', 'inp', 'ret', 'exc', 'log')) { foreach ($v in @($t.$g)) { if ($v) { SetV $ws.Cells.Item($map["$g|$v"], $col) ('O') } } }
      SetV $ws.Cells.Item($resRow, $col) ([string]$t.type)
      if ($t.res) { SetV $ws.Cells.Item($resRow + 1, $col) ([string]$t.res); SetV $ws.Cells.Item($resRow + 2, $col) ([double]$d.run_date) }
    }
    $ws.Range($ws.Cells.Item($cRow + 1, 6), $ws.Cells.Item($resRow - 1, $lastCol)).HorizontalAlignment = -4108
    $ws.Range($ws.Cells.Item($resRow + 2, 6), $ws.Cells.Item($resRow + 2, $lastCol)).NumberFormat = 'dd/mm'
    # result labels (rows moved with the blocks)
    SetV $ws.Cells.Item($resRow, 2) ('Type(N : Normal, A : Abnormal, B : Boundary)')
    SetV $ws.Cells.Item($resRow + 1, 2) ('Passed/Failed')
    SetV $ws.Cells.Item($resRow + 2, 2) ('Executed Date')
    SetV $ws.Cells.Item($resRow + 3, 2) ('Defect ID')
    # header
    $ws.Range('C2').Formula = "=Functions!E$(11 + $i)"
    $ws.Range('L2').Formula = "=Functions!D$(11 + $i)"
    SetV $ws.Range('C3') ([string]$f.creator)
    SetV $ws.Range('L3') ([string]$tester)
    SetV $ws.Range('C4') ([double]$f.loc)
    SetV $ws.Range('C5') ("$($f.desc) Test class: $($f.testcls).")
    $ws.Range('C5').WrapText = $true; $ws.Rows(5).RowHeight = 28
    $ws.Range('A7').Formula = "=COUNTIF(F$($resRow + 1):HQ$($resRow + 1),""P"")"
    $ws.Range('C7').Formula = "=COUNTIF(F$($resRow + 1):HQ$($resRow + 1),""F"")"
    $ws.Range('L7').Formula = "=COUNTIF(E$($resRow):HQ$($resRow),""N"")"
    $ws.Range('M7').Formula = "=COUNTIF(E$($resRow):HQ$($resRow),""A"")"
    $ws.Range('N7').Formula = "=COUNTIF(E$($resRow):HQ$($resRow),""B"")"
    $ws.Range('O7').Formula = '=COUNTA(E9:HT9)'
  }
  foreach ($n in 'Function 1', 'Function 2', 'Function3', 'Example') { $wb.Worksheets.Item($n).Delete() }

  # hyperlinks from the Functions list
  for ($i = 0; $i -lt $nf; $i++) {
    $cell = $fl.Cells.Item(11 + $i, 6)
    $fl.Hyperlinks.Add($cell, '', "'" + $funcs[$i].sheet + "'!A1", '', [string]$funcs[$i].sheet) | Out-Null
  }

  # ---------------------------------------------------------------- Statistics
  $st = $wb.Worksheets.Item('Statistics')
  $st.Range('F4').Value2 | Out-Null
  SetV $st.Range('F4') ([string]$p.creator)
  SetV $st.Range('F5') ([string]$p.reviewer)
  $st.Range('B6').Formula = '=B5&"_"&"Unit Test"&"_"&"v' + $p.version + '"'
  SetV $st.Range('F6') ([double]$p.issue); $st.Range('F6').NumberFormat = 'dd/mm/yyyy'
  SetV $st.Range('B7') ("Release 1 includes $nf functions of 11 backend services (auth, user, store, order, payment, loyalty, notification, locker, iot, assistant). Untested = PostgreSQL tests skipped because Docker was not available on the test machine.")
  if ($nf -gt 3) { $st.Range("A15:A$(11 + $nf)").EntireRow.Insert() | Out-Null }
  $st.Rows(12).Copy($st.Range("A13:A$(11 + $nf)").EntireRow) | Out-Null
  for ($i = 0; $i -lt $nf; $i++) {
    $f = $funcs[$i]; $r = 12 + $i; $s = "'" + $f.sheet + "'!"
    SetV $st.Cells.Item($r, 1) ([double]($i + 1))
    SetV $st.Cells.Item($r, 2) ([string]$f.code)
    $st.Hyperlinks.Add($st.Cells.Item($r, 2), '', "'" + $f.sheet + "'!A1", '', [string]$f.code) | Out-Null
    $st.Cells.Item($r, 3).Formula = "=$($s)A7"
    $st.Cells.Item($r, 4).Formula = "=$($s)C7"
    $st.Cells.Item($r, 5).Formula = "=$($s)F7"
    $st.Cells.Item($r, 6).Formula = "=$($s)L7"
    $st.Cells.Item($r, 7).Formula = "=$($s)M7"
    $st.Cells.Item($r, 8).Formula = "=$($s)N7"
    $st.Cells.Item($r, 9).Formula = "=$($s)O7"
  }
  $sub = 14 + $nf
  foreach ($k in 3..9) { $L = [char](64 + $k); $st.Cells.Item($sub, $k).Formula = "=SUM($($L)12:$L$($sub - 1))" }
  $st.Range("D$($sub + 2)").Formula = "=ROUND((C$sub+D$sub)*100/I$sub,2)"
  $st.Range("D$($sub + 3)").Formula = "=ROUND(C$sub*100/I$sub,2)"
  $st.Range("D$($sub + 4)").Formula = "=ROUND(F$sub*100/I$sub,2)"
  $st.Range("D$($sub + 5)").Formula = "=ROUND(G$sub*100/I$sub,2)"
  $st.Range("D$($sub + 6)").Formula = "=ROUND(H$sub*100/I$sub,2)"
  $st.Range("D$($sub + 2):D$($sub + 6)").NumberFormat = 'General'

  $xl.Calculation = -4105
  $xl.CalculateFull()
  $vals = foreach ($k in 3..9) { GetV $st.Cells.Item($sub, $k) }
  "Statistics sub total (P,F,U,N,A,B,Total): $($vals -join ', ') | coverage $(GetV $st.Range("D$($sub+2)")) success $(GetV $st.Range("D$($sub+3)"))"
  $wb.Worksheets.Item('Cover').Activate()
  $wb.Save()
} finally {
  $wb.Close($true); $xl.Quit()
  [System.Runtime.InteropServices.Marshal]::ReleaseComObject($xl) | Out-Null
}
