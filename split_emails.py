#!/usr/bin/env python3
"""Local XLSX splitter; uses only the Python standard library."""
import os
from pathlib import Path
import posixpath
import shutil
import sys
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
FIELDS = ["First Name", "Last Name", "Email"]
REQUIRED = FIELDS + ["Template"]
STUDENT = "030 - Student (GT)"


def read_records(path):
    with zipfile.ZipFile(path) as z:
        strings = []
        if "xl/sharedStrings.xml" in z.namelist():
            strings = ["".join(t.text or "" for t in si.findall(".//s:t", NS))
                       for si in ET.fromstring(z.read("xl/sharedStrings.xml"))]
        rels = {r.attrib["Id"]: r.attrib["Target"]
                for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
        book = ET.fromstring(z.read("xl/workbook.xml"))
        matches = []
        for sheet in book.findall("s:sheets/s:sheet", NS):
            rid = sheet.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
            target = rels[rid]
            member = target.lstrip("/") if target.startswith("/") else posixpath.normpath("xl/" + target)
            rows = []
            for row in ET.fromstring(z.read(member)).findall("s:sheetData/s:row", NS):
                cells = {}
                for cell in row.findall("s:c", NS):
                    ref = cell.attrib.get("r", "")
                    col = "".join(c for c in ref if c.isalpha())
                    value = cell.find("s:v", NS)
                    text = value.text if value is not None and value.text else ""
                    if cell.attrib.get("t") == "s":
                        text = strings[int(text)]
                    elif cell.attrib.get("t") == "inlineStr":
                        text = "".join(t.text or "" for t in cell.findall(".//s:t", NS))
                    cells[col] = (text, cell.find("s:f", NS) is not None,
                                  cell.attrib.get("t") == "e")
                rows.append(cells)
            for index, row in enumerate(rows[:50]):
                headers = {}
                for col, (value, _, _) in row.items():
                    headers.setdefault(value.strip(), []).append(col)
                if all(name in headers for name in REQUIRED):
                    if any(len(headers[name]) != 1 for name in REQUIRED):
                        raise ValueError("Duplicate required column headers found.")
                    mapping = {name: headers[name][0] for name in REQUIRED}
                    records = []
                    for data in rows[index + 1:]:
                        if not any(v[0] for v in data.values()):
                            continue
                        record = {}
                        for name, col in mapping.items():
                            value, formula, error = data.get(col, ("", False, False))
                            if formula or error:
                                raise ValueError("Required columns contain formulas or Excel errors. Save a values-only copy first.")
                            record[name] = value
                        records.append(record)
                    matches.append(records)
                    break
        if len(matches) != 1:
            raise ValueError("Expected exactly one sheet with First Name, Last Name, Email, and Template headers within the first 50 rows.")
        return matches[0]


def write_book(path, rows):
    sheet = ['<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" state="frozen"/></sheetView></sheetViews><cols><col min="1" max="2" width="24" customWidth="1"/><col min="3" max="3" width="48" customWidth="1"/></cols><sheetData>']
    for r, values in enumerate([FIELDS] + rows, 1):
        sheet.append('<row r="%d">' % r)
        for col, value in zip("ABC", values):
            sheet.append('<c r="%s%d" t="inlineStr"><is><t xml:space="preserve">%s</t></is></c>' % (col, r, escape(str(value))))
        sheet.append("</row>")
    sheet.append('</sheetData><autoFilter ref="A1:C%d"/></worksheet>' % (len(rows) + 1))
    parts = {
        "[Content_Types].xml": '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>',
        "_rels/.rels": '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>',
        "xl/workbook.xml": '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Welcome Email" sheetId="1" r:id="rId1"/></sheets></workbook>',
        "xl/_rels/workbook.xml.rels": '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>',
        "xl/worksheets/sheet1.xml": "".join(sheet),
    }
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, content in parts.items():
            z.writestr(name, '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' + content)


def split(path):
    path = Path(path).resolve()
    if path.suffix.lower() != ".xlsx" or not path.is_file():
        raise ValueError("Choose an existing .xlsx workbook.")
    if "(STUDENTS ONLY)" in path.stem:
        raise ValueError("Choose the original workbook, not a STUDENTS ONLY file.")
    output = path.with_name(path.stem + " (STUDENTS ONLY).xlsx")
    if output.exists():
        raise ValueError("The STUDENTS ONLY file already exists. Move or rename it before splitting again.")
    original_bytes = path.read_bytes()
    records = read_records(path)
    students, others = [], []
    for row in records:
        (students if row["Template"].strip() == STUDENT else others).append([row[k] for k in FIELDS])
    with tempfile.TemporaryDirectory(prefix=".welcome-split-", dir=path.parent) as tmp:
        a, b = Path(tmp) / "others.xlsx", Path(tmp) / "students.xlsx"
        write_book(a, others)
        write_book(b, students)
        for candidate in (a, b):
            with zipfile.ZipFile(candidate) as z:
                if z.testzip():
                    raise ValueError("Output validation failed.")
        if path.read_bytes() != original_bytes:
            raise ValueError("The original file changed during processing. Please try again.")
        # Exclusive creation prevents overwriting an existing student list.
        try:
            with output.open("xb") as dest, b.open("rb") as source:
                shutil.copyfileobj(source, dest)
        except FileExistsError:
            raise ValueError("The student output already exists.")
        except Exception:
            output.unlink(missing_ok=True)
            raise
        try:
            os.replace(a, path)
        except Exception:
            output.unlink(missing_ok=True)
            raise
    return f"Done — {len(others)} non-students and {len(students)} students.\n\nNon-students: {path.name}\nStudents: {output.name}\n\nSaved in the original folder. Original replaced; no backup created."


if __name__ == "__main__":
    try:
        print(split(sys.argv[1]))
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
