param([string]$unitXls, [string]$reportXlsx, [string]$outDir)
# Render the statistics tables of the two workbooks as PNG (figures 4.1 and 4.2 of the test document).
$ErrorActionPreference = 'Stop'
$xl = New-Object -ComObject Excel.Application
$xl.Visible = $false; $xl.DisplayAlerts = $false

function Snap($ws, $addr, $png) {
  $rng = $ws.Range($addr)
  for ($try = 1; $try -le 5; $try++) {        # clipboard can be busy for a moment
    try { $rng.CopyPicture(1, 2) | Out-Null; break } catch { if ($try -eq 5) { throw }; Start-Sleep -Milliseconds 800 }
  }
  $w = $rng.Width; $h = $rng.Height
  $co = $ws.ChartObjects().Add(0, 0, $w, $h)
  $co.Activate() | Out-Null
  $co.Chart.ChartArea.Format.Line.Visible = 0
  $co.Chart.Paste() | Out-Null
  $co.Chart.Export($png, 'PNG') | Out-Null
  $co.Delete()
}

function LastRow($ws, $col, $text) {
  $f = $ws.Columns($col).Find($text)
  return $f.Row
}

$wb = $xl.Workbooks.Open($unitXls, 0, $true)
$ws = $wb.Worksheets.Item('Statistics')
$r = LastRow $ws 2 'Boundary case'
Snap $ws "A2:I$r" (Join-Path $outDir 'unit_test_statistics.png')
$wb.Close($false)

$wb = $xl.Workbooks.Open($reportXlsx, 0, $true)
$ws = $wb.Worksheets.Item('Test Statistics')
$r = LastRow $ws 3 'Test successful coverage'
Snap $ws "B1:H$r" (Join-Path $outDir 'test_statistics.png')
$wb.Close($false)
$xl.Quit()
'ok'
