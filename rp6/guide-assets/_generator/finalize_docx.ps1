param([string]$docx, [string]$pdf)
# Update TOC / list fields in Word, save, and export a PDF copy.
$ErrorActionPreference = 'Stop'
$w = New-Object -ComObject Word.Application
$w.Visible = $false; $w.DisplayAlerts = 0
$doc = $w.Documents.Open($docx)
try {
  $doc.Fields.Update() | Out-Null
  foreach ($t in $doc.TablesOfContents) { $t.Update() | Out-Null }
  $doc.Fields.Update() | Out-Null
  $doc.Save()
  $doc.ExportAsFixedFormat($pdf, 17)
  "pages: $($doc.ComputeStatistics(2))"
} finally { $doc.Close(0); $w.Quit() }
