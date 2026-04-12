from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from Constants import C_WHITE


def thin_border():
    s = Side(style="thin", color="CCCCCC")
    return Border(left=s, right=s, top=s, bottom=s)


def style_cell(cell, bold=False, color=C_WHITE, font_color="000000",
               size=10, h_align="center", num_fmt=None):
    cell.font = Font(name="Arial", bold=bold, color=font_color, size=size)
    cell.fill = PatternFill("solid", start_color=color)
    cell.alignment = Alignment(horizontal=h_align, vertical="center")
    cell.border = thin_border()
    if num_fmt:
        cell.number_format = num_fmt
