import tempfile
import unittest
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET
from unittest.mock import patch
import split_emails as s


def fixture(path, templates):
    s.write_book(path, [["Zoë & Ann", "O'Neil", "a@example.com"] for _ in templates])
    with zipfile.ZipFile(path) as z:
        parts = {name: z.read(name) for name in z.namelist()}
    root = ET.fromstring(parts["xl/worksheets/sheet1.xml"])
    for i, (row, value) in enumerate(zip(root.findall("s:sheetData/s:row", s.NS), ["Template"] + templates), 1):
        c = ET.SubElement(row, "{%s}c" % s.NS["s"], r=f"D{i}", t="inlineStr")
        inline = ET.SubElement(c, "{%s}is" % s.NS["s"])
        ET.SubElement(inline, "{%s}t" % s.NS["s"]).text = value
    parts["xl/worksheets/sheet1.xml"] = ET.tostring(root)
    with zipfile.ZipFile(path, "w") as z:
        for name, data in parts.items():
            z.writestr(name, data)


def values(path):
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
    return [[n.text or "" for n in row.findall(".//s:t", s.NS)]
            for row in root.findall("s:sheetData/s:row", s.NS)]


class SplitTest(unittest.TestCase):
    def test_partitions_without_backup(self):
        for templates, counts in [
            ([s.STUDENT, "Staff", "", " " + s.STUDENT + " "], (2, 2)),
            ([s.STUDENT], (0, 1)), (["Staff"], (1, 0)), ([], (0, 0))
        ]:
            with self.subTest(templates=templates), tempfile.TemporaryDirectory() as tmp:
                p = Path(tmp) / "10.20.2026 Welcome Email.xlsx"
                fixture(p, templates)
                original = p.read_bytes()
                s.split(p)
                student = p.with_name(p.stem + " (STUDENTS ONLY).xlsx")
                a, b = values(p), values(student)
                self.assertEqual((len(a)-1, len(b)-1), counts)
                self.assertEqual(a[0], s.FIELDS)
                self.assertEqual(b[0], s.FIELDS)
                for row in a[1:] + b[1:]:
                    self.assertEqual(row, ["Zoë & Ann", "O'Neil", "a@example.com"])
                self.assertFalse((Path(tmp)/"Backups").exists())
                self.assertEqual(len(list(Path(tmp).iterdir())), 2)
                with self.assertRaises(ValueError):
                    s.split(p)

    def test_invalid_input_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "input.xlsx"
            s.write_book(p, [["A", "B", "c"]])
            original = p.read_bytes()
            with self.assertRaises(ValueError):
                s.split(p)
            self.assertEqual(original, p.read_bytes())
            self.assertEqual(len(list(Path(tmp).iterdir())), 1)

    def test_replace_failure_keeps_original(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "input.xlsx"
            fixture(p, [s.STUDENT])
            original = p.read_bytes()
            with patch.object(s.os, "replace", side_effect=OSError("locked")):
                with self.assertRaises(OSError):
                    s.split(p)
            self.assertEqual(original, p.read_bytes())
            self.assertFalse(p.with_name(p.stem + " (STUDENTS ONLY).xlsx").exists())


if __name__ == "__main__":
    unittest.main()
