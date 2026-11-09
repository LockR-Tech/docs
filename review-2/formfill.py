"""Shared helpers for filling the Review 2 forms (BM01–BM04) with python-docx.

A value is a str, or a list of str parts in which the marker TODO makes the next part a yellow placeholder
the team must still check or fill.
"""
import copy

from docx.enum.text import WD_COLOR_INDEX
from docx.oxml.ns import qn
from docx.shared import Cm, RGBColor

TODO = object()  # marker: the next text part is a placeholder (yellow)
BODY = RGBColor(0x1F, 0x29, 0x37)
GREY = RGBColor(0x66, 0x66, 0x66)


def write_runs(paragraph, value, template_run):
    """Write value (str or list with TODO markers) into paragraph, cloning template_run formatting."""
    parts = value if isinstance(value, list) else [value]
    for r in list(paragraph.runs):
        r._r.getparent().remove(r._r)
    yellow = False
    for part in parts:
        if part is TODO:
            yellow = True
            continue
        paragraph._p.append(copy.deepcopy(template_run))
        run = paragraph.runs[-1]
        run.text = part
        run.font.italic = False
        run.font.color.rgb = BODY
        if yellow:
            run.font.highlight_color = WD_COLOR_INDEX.YELLOW
        yellow = False


def run_template(cell):
    p = cell.paragraphs[0]
    r = p.runs[0] if p.runs else p.add_run('')
    return copy.deepcopy(r._r)


def set_cell(cell, value, tmpl):
    for extra in cell.paragraphs[1:]:
        extra._p.getparent().remove(extra._p)
    write_runs(cell.paragraphs[0], value, tmpl)


def fill_table(table, rows, first_col=0, start_row=1):
    """Write rows starting at start_row, adding rows (copies of the last) or removing extra rows."""
    tmpl = run_template(table.rows[start_row].cells[-1])
    needed = start_row + len(rows)
    while len(table.rows) < needed:
        table._tbl.append(copy.deepcopy(table.rows[-1]._tr))
    while len(table.rows) > needed:
        table._tbl.remove(table.rows[-1]._tr)
    for i, values in enumerate(rows):
        cells = table.rows[start_row + i].cells
        for j, v in enumerate(values):
            set_cell(cells[first_col + j], v, tmpl)


def fill_column(table, values, col=1, start_row=0):
    """Fill one column of a key/value table, row by row; None leaves a cell untouched."""
    tmpl = run_template(table.rows[start_row].cells[col])
    for row, v in zip(table.rows[start_row:], values):
        if v is not None:
            set_cell(row.cells[col], v, tmpl)


def set_widths(table, widths_cm):
    tblPr = table._tbl.tblPr
    tblW = tblPr.find(qn('w:tblW'))
    if tblW is None:
        tblW = tblPr.makeelement(qn('w:tblW'), {})
        tblPr.append(tblW)
    tblW.set(qn('w:type'), 'dxa')
    tblW.set(qn('w:w'), str(int(Cm(sum(widths_cm)).twips)))
    layout = tblPr.find(qn('w:tblLayout'))
    if layout is None:
        layout = tblPr.makeelement(qn('w:tblLayout'), {})
        tblPr.append(layout)
    layout.set(qn('w:type'), 'fixed')
    grid = table._tbl.tblGrid
    for gc, w in zip(grid.findall(qn('w:gridCol')), widths_cm):
        gc.set(qn('w:w'), str(int(Cm(w).twips)))
    for row in table.rows:
        for cell, w in zip(row.cells, widths_cm):
            cell.width = Cm(w)


def remove_grey_guidance(document, keep=()):
    """Delete the grey guidance paragraphs of the form, except those whose text starts with an item of keep."""
    for p in list(document.paragraphs):
        colors = {r.font.color.rgb for r in p.runs if r.font.color is not None and r.font.color.type is not None}
        if GREY in colors and not p.text.startswith(tuple(keep)):
            p._p.getparent().remove(p._p)


def keep_rows_together(document):
    """Rows never split across pages; the header row stays with the first data row; headings stay with what
    follows them."""
    for para in document.paragraphs:
        if para.style.name.startswith('Heading'):
            para.paragraph_format.keep_with_next = True
    for table in document.tables:
        for i, row in enumerate(table.rows):
            trPr = row._tr.get_or_add_trPr()
            if trPr.find(qn('w:cantSplit')) is None:
                trPr.append(trPr.makeelement(qn('w:cantSplit'), {}))
            if i == 0:
                for cell in row.cells:
                    for para in cell.paragraphs:
                        para.paragraph_format.keep_with_next = True
