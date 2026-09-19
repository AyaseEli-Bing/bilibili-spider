"""极简 xlsx 生成器：仅用标准库 zipfile 手写 OOXML，零第三方依赖。"""
from __future__ import annotations

import zipfile
from xml.sax.saxutils import escape

_NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_NS_PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
_NS_CONTENT = "http://schemas.openxmlformats.org/package/2006/content-types"

_CT_TYPES = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="{_NS_CONTENT}">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
</Types>"""

_RELS = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{_NS_PKG_REL}">
<Relationship Id="rId1" Type="{_NS_REL}/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""

_WORKBOOK = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="{_NS_MAIN}" xmlns:r="{_NS_REL}">
<sheets><sheet name="视频列表" sheetId="1" r:id="rId1"/></sheets>
</workbook>"""

_WORKBOOK_RELS = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{_NS_PKG_REL}">
<Relationship Id="rId1" Type="{_NS_REL}/worksheet" Target="worksheets/sheet1.xml"/>
<Relationship Id="rId2" Type="{_NS_REL}/styles" Target="styles.xml"/>
</Relationships>"""

_STYLES = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="{_NS_MAIN}">
<fonts count="2">
<font><sz val="11"/><name val="Calibri"/></font>
<font><b/><sz val="11"/><name val="Calibri"/></font>
</fonts>
<fills count="2">
<fill><patternFill patternType="none"/></fill>
<fill><patternFill patternType="gray125"/></fill>
</fills>
<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="2">
<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
<xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/>
</cellXfs>
<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>"""


def _col_name(idx: int) -> str:
    """0 基列索引 -> Excel 列字母（0->A, 25->Z, 26->AA）。"""
    s = ""
    idx += 1
    while idx:
        idx, rem = divmod(idx - 1, 26)
        s = chr(65 + rem) + s
    return s


def _cell(ref: str, value, bold: bool = False) -> str:
    attr = f' r="{ref}"'
    style = ' s="1"' if bold else ""
    if value is None:
        return f"<c{attr}{style}/>"
    if isinstance(value, bool):
        value = int(value)
    if isinstance(value, (int, float)):
        text = repr(value) if isinstance(value, float) else str(value)
        return f"<c{attr}{style}><v>{text}</v></c>"
    return (f'<c{attr}{style} t="inlineStr"><is>'
            f'<t xml:space="preserve">{escape(str(value))}</t></is></c>')


def _build_sheet(headers: list[str], rows: list[list]) -> str:
    lines = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
             f'<worksheet xmlns="{_NS_MAIN}">']
    # 列宽（表头字符数 * 1.2 + 2，限制 8~60）
    lines.append("<cols>")
    for i, h in enumerate(headers):
        width = max(8, min(60, len(str(h)) * 2 + 2))
        lines.append(f'<col min="{i + 1}" max="{i + 1}" width="{width}" customWidth="1"/>')
    lines.append("</cols><sheetData>")
    # 表头行
    lines.append('<row r="1">')
    for i, h in enumerate(headers):
        lines.append(_cell(f"{_col_name(i)}1", h, bold=True))
    lines.append("</row>")
    # 数据行
    for r, row in enumerate(rows, start=2):
        lines.append(f'<row r="{r}">')
        for c, val in enumerate(row):
            lines.append(_cell(f"{_col_name(c)}{r}", val))
        lines.append("</row>")
    lines.append("</sheetData></worksheet>")
    return "".join(lines)


def write_xlsx(path: str, headers: list[str], rows: list[list]) -> None:
    """把 headers + rows 写成一个标准 .xlsx 文件。"""
    sheet = _build_sheet(headers, rows)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _CT_TYPES)
        z.writestr("_rels/.rels", _RELS)
        z.writestr("xl/workbook.xml", _WORKBOOK)
        z.writestr("xl/_rels/workbook.xml.rels", _WORKBOOK_RELS)
        z.writestr("xl/styles.xml", _STYLES)
        z.writestr("xl/worksheets/sheet1.xml", sheet)
