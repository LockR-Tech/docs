"""Crow's-foot legend drawn under an ERD; parent end = ERone (FK NOT NULL) or ERzeroToOne (FK nullable)."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
NOTNULL = json.load(open(os.path.join(HERE, "fk_notnull.json")))
ITEMS = [("ERone", "exactly one (parent side, FK is NOT NULL)"),
         ("ERzeroToOne", "zero or one (parent side when the FK is nullable · child side of a 1 : 1)"),
         ("ERzeroToMany", "zero or many (child side of a 1 : N)")]


def parent_end(child, col):
    return "endArrow=ERone;" if NOTNULL[f"{child}.{col}"] else "endArrow=ERzeroToOne;"


def legend(d, x, y, font=14, line=70, gap=28):
    """draws the legend with its top-left at (x, y); returns its height"""
    dot = "text;html=1;strokeColor=none;fillColor=none;"
    for i, (arrow, text) in enumerate(ITEMS):
        yy = y + i * gap + gap / 2
        a = d.vertex("", x, yy - 1, 2, 2, dot)
        b = d.vertex("", x + line, yy - 1, 2, 2, dot)
        d.edge(a, b, "edgeStyle=none;html=1;strokeColor=#000000;startArrow=none;endFill=0;endSize=12;"
                     f"endArrow={arrow};exitX=0.5;exitY=0.5;exitDx=0;exitDy=0;entryX=0.5;entryY=0.5;entryDx=0;entryDy=0;")
        d.vertex(text, x + line + 14, yy - gap / 2, 900, gap,
                 f"text;html=1;align=left;verticalAlign=middle;fontSize={font};fontColor=#333333;")
    return len(ITEMS) * gap
