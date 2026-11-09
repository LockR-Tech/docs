param([string]$template, [string]$json, [string]$out)
# Fill Report5_Test Report.xlsx (Cover, Test Cases, Test Statistics, one sheet per module) keeping the template formats.
$ErrorActionPreference = 'Stop'
function SetV($rng, $val) { try { [void]$rng.GetType().InvokeMember('Value2', [Reflection.BindingFlags]::SetProperty, $null, $rng, @(,$val)) } catch { throw "SetV failed at $($rng.Worksheet.Name)!$($rng.Address(0,0)) : $($_.Exception.InnerException.Message) :: $(($val | Out-String).Substring(0, [Math]::Min(200, ($val | Out-String).Length)))" } }
$d = Get-Content -Raw -Encoding UTF8 $json | ConvertFrom-Json
$p = $d.project
$xl = New-Object -ComObject Excel.Application
$xl.Visible = $false; $xl.DisplayAlerts = $false; $xl.ScreenUpdating = $false
$wb = $xl.Workbooks.Open($template)
$wb.SaveAs($out, 51)
try {
  $xl.Calculation = -4135   # manual while filling

  # ---------------------------------------------------------------- Cover
  $c = $wb.Worksheets.Item('Cover')
  SetV $c.Range('B4') ($p.name)
  SetV $c.Range('B5') ($p.code)
  SetV $c.Range('F4') ($p.creator)
  SetV $c.Range('F5') ([double]$p.issue); $c.Range('F5').NumberFormat = 'dd/mm/yyyy'
  $c.Range('B6').Formula = '=B5&"_"&"Test Report"&"_"&"v' + $p.version + '"'
  $c.Range('F6').NumberFormat = '@'; SetV $c.Range('F6') ([string]$p.version)
  SetV $c.Range('A11') ([double]$p.issue); $c.Range('A11').NumberFormat = 'dd/mm/yyyy'
  $c.Range('B11').NumberFormat = '@'; SetV $c.Range('B11') ([string]$p.version)
  SetV $c.Range('C11') ('Whole document')
  SetV $c.Range('D11') ('A')
  SetV $c.Range('E11') ("Initial test report: $($d.modules.Count) modules, integration / system / acceptance test cases with round 1 results.")
  SetV $c.Range('F11') ('Report3_Software Requirement Specification_LockR; Report3_Project Tracking_LockR')

  # ---------------------------------------------------------------- module sheets
  $tpl = $wb.Worksheets.Item('Feature 1')
  $tpl.PageSetup.LeftHeader = $p.code + '_Test Report'
  $last = $wb.Worksheets.Item($wb.Worksheets.Count)
  foreach ($m in $d.modules) {
    $tpl.Copy([Type]::Missing, $last)
    $ws = $wb.Worksheets.Item($last.Index + 1)
    $ws.Name = $m.sheet
    $last = $ws
    $n = $m.cases.Count
    SetV $ws.Range('B2') ($m.name)
    SetV $ws.Range('B3') ($m.req)
    SetV $ws.Range('A11') ($m.name)
    # rows 12..11+n take the plain format of template row 13
    $ws.Range('A14:O19').Clear()
    $ws.Rows(13).Copy($ws.Range("A12:A$(11 + $n)").EntireRow) | Out-Null
    $ws.Range("A12:O$(11 + $n)").ClearContents() | Out-Null
    for ($i = 0; $i -lt $n; $i++) {
      $t = $m.cases[$i]; $r = 12 + $i
      $vals = @([string]$t.id, [string]$t.desc, [string]$t.proc, [string]$t.exp, [string]$t.pre, [string]$t.res)
      for ($k = 0; $k -lt 6; $k++) { SetV $ws.Cells.Item($r, $k + 1) ($vals[$k]) }
      if ($t.date) { SetV $ws.Cells.Item($r, 7) ([double]$t.date) }
      if ($t.tester) { SetV $ws.Cells.Item($r, 8) ([string]$t.tester) }
      if ($t.note) { SetV $ws.Cells.Item($r, 15) ([string]$t.note) }
    }
    # template counts column F (round 1) for every round: round 2 = column I, round 3 = column L
    foreach ($pair in @(@(7, 'I'), @(8, 'L'))) {
      $row = $pair[0]; $col = $pair[1]
      foreach ($k in 2..5) { $ws.Cells.Item($row, $k).Formula = "=COUNTIF(`$$($col)12:`$$($col)998,$([char](64 + $k))5)" }
    }
    $rng = $ws.Range("A12:O$(11 + $n)")
    $rng.WrapText = $true
    $rng.VerticalAlignment = -4160
    $rng.Font.Italic = $false
    $rng.Font.ColorIndex = 1
    $ws.Range("G12:G$(11 + $n)").NumberFormat = 'dd/mm/yyyy'
    foreach ($col in 'H', 'K', 'N') { $ws.Columns($col).ColumnWidth = 17 }
    $rng.EntireRow.AutoFit() | Out-Null
    for ($r = 12; $r -le 11 + $n; $r++) { $ws.Rows($r).RowHeight = [Math]::Min(409, $ws.Rows($r).RowHeight + 8) }
    $ws.Rows(3).RowHeight = 30
  }
  $wb.Worksheets.Item('Feature 1').Delete()
  $wb.Worksheets.Item('Feature 2').Delete()

  # ---------------------------------------------------------------- Test Cases list
  $tc = $wb.Worksheets.Item('Test Cases')
  $tc.Range('D3').Formula = '=Cover!B4'
  $tc.Range('D4').Formula = '=Cover!B5'
  SetV $tc.Range('D5') ("1. Server: Azure virtual machine running the Spring Boot microservices with Docker Compose (api.locker-drone.tech)`n2. Database: PostgreSQL 16 (one database per service), pgvector for the assistant`n3. Web browser: Google Chrome (latest) for the admin web admin.locker-drone.tech`n4. Mobile: Android 11+ phone with the Lock.R app; mobile web on Chrome`n5. Locker: cabinet CAB-TU01 with Raspberry Pi controller and kiosk touch screen`n6. Messaging: RabbitMQ, MQTT broker; SePay (VietQR) in test mode")
  $nm = $d.modules.Count
  $tc.Range('B14:F21').Clear()
  $tc.Rows(10).Copy($tc.Range("A9:A$(8 + $nm)").EntireRow) | Out-Null
  for ($i = 0; $i -lt $nm; $i++) {
    $m = $d.modules[$i]; $r = 9 + $i
    SetV $tc.Cells.Item($r, 2) ([double]($i + 1))
    SetV $tc.Cells.Item($r, 3) ($m.name)
    SetV $tc.Cells.Item($r, 4) ($m.sheet)
    $tc.Hyperlinks.Add($tc.Cells.Item($r, 4), '', "'" + $m.sheet + "'!A1", '', $m.sheet) | Out-Null
    SetV $tc.Cells.Item($r, 5) ($m.req)
    SetV $tc.Cells.Item($r, 6) ($m.pre)
  }
  $lst = $tc.Range("B9:F$(8 + $nm)"); $lst.WrapText = $true; $lst.VerticalAlignment = -4160
  foreach ($col in 'C', 'E', 'F') { $f = $tc.Range("$($col)9:$col$(8 + $nm)").Font; $f.Underline = -4142; $f.ColorIndex = 1 }
  $lst.EntireRow.AutoFit() | Out-Null
  for ($r = 9; $r -le 8 + $nm; $r++) { $tc.Rows($r).RowHeight = [Math]::Min(409, $tc.Rows($r).RowHeight + 8) }
  $tc.Rows(5).RowHeight = 100

  # ---------------------------------------------------------------- Test Statistics
  $st = $wb.Worksheets.Item('Test Statistics')
  SetV $st.Range('C3') ($p.name)
  SetV $st.Range('C4') ($p.code)
  SetV $st.Range('G3') ($p.creator)
  SetV $st.Range('G4') ($p.reviewer)
  $st.Range('C5').Formula = '=C4&"_"&"Test Report"&"_"&"v' + $p.version + '"'
  SetV $st.Range('H5') ([double]$p.issue); $st.Range('H5').NumberFormat = 'dd/mm/yyyy'
  SetV $st.Range('C6') ("Release 1 includes $nm modules of the mobile app, kiosk, admin web, backend services and locker controller.")
  # make room: data rows 11..10+nm, sub total after them
  $st.Range("A13:A$(10 + $nm)").EntireRow.Insert() | Out-Null
  $st.Rows(11).Copy($st.Range("A12:A$(10 + $nm)").EntireRow) | Out-Null
  for ($i = 0; $i -lt $nm; $i++) {
    $m = $d.modules[$i]; $r = 11 + $i; $s = "'" + $m.sheet + "'!"
    SetV $st.Cells.Item($r, 2) ([double]($i + 1))
    $st.Cells.Item($r, 3).Formula = "=$($s)B2"
    $st.Cells.Item($r, 4).Formula = "=$($s)B6"
    $st.Cells.Item($r, 5).Formula = "=$($s)C6"
    $st.Cells.Item($r, 6).Formula = "=$($s)D6"
    $st.Cells.Item($r, 7).Formula = "=$($s)E6"
    $st.Cells.Item($r, 8).Formula = "=$($s)B4"
  }
  $sub = 12 + $nm   # one blank row then Sub total
  foreach ($col in 'D', 'E', 'F', 'G', 'H') { $st.Range("$col$sub").Formula = "=SUM($($col)11:$col$($sub - 1))" }
  $st.Range("E$($sub + 2)").Formula = "=ROUND((D$sub+E$sub)*100/(H$sub-G$sub),2)"
  $st.Range("E$($sub + 3)").Formula = "=ROUND(D$sub*100/(H$sub-G$sub),2)"
  $st.Range("E$($sub + 2):E$($sub + 3)").NumberFormat = 'General'
  $st.Columns('C').ColumnWidth = 34

  $xl.Calculation = -4105
  $wb.Worksheets.Item('Cover').Activate()
  $wb.Save()
  "Test Statistics: passed=$($st.Range("D$sub").Value2) failed=$($st.Range("E$sub").Value2) pending=$($st.Range("F$sub").Value2) total=$($st.Range("H$sub").Value2) coverage=$($st.Range("E$($sub+2)").Value2) success=$($st.Range("E$($sub+3)").Value2)"
} finally {
  $wb.Close($true); $xl.Quit()
  [System.Runtime.InteropServices.Marshal]::ReleaseComObject($xl) | Out-Null
}
