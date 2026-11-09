param([string]$Docx, [string]$Pdf)
# Export a .docx to PDF with Word and print the page count and the page where each heading starts.
$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    $doc = $word.Documents.Open($Docx, $false, $true)
    $pages = $doc.ComputeStatistics(2)
    "pages=$pages"
    foreach ($p in $doc.Paragraphs) {
        $style = $p.Style.NameLocal
        if ($style -like 'Heading*' -or $style -like 'Ti*u*') {
            $pg = $p.Range.Information(3)
            "p$pg  $($p.Range.Text.Trim())"
        }
    }
    $doc.ExportAsFixedFormat($Pdf, 17)
    $doc.Close($false)
} finally {
    $word.Quit()
}
