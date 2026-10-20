# Welcome Email Splitter

Double-click **Welcome Email Splitter.app**, then drop one `.xlsx` workbook into the window or click **Choose Excel File…**. Close the workbook in Excel before splitting.

For `mm.dd.yyyy Welcome Email.xlsx`, the results are saved in the input file's folder:

- `mm.dd.yyyy Welcome Email.xlsx`: all non-student employees, replacing the original.
- `mm.dd.yyyy Welcome Email (STUDENTS ONLY).xlsx`: only employees whose Template is `030 - Student (GT)`.

Other input names are preserved in the same way. Surrounding whitespace in Template is ignored; all other Template values, including blanks, are non-students. Row order and duplicates are retained.

Both outputs have exactly **First Name**, **Last Name**, and **Email**, in that order, on one worksheet. They contain values only; other source columns, worksheets, formatting, and objects are not retained. The original is replaced after successful processing. No backup is created.

The tool requires exactly one worksheet with all four required headers in its first 50 rows. It rejects ambiguous headers, formulas or errors in required fields, and existing student output files. A split file cannot be split again because it no longer has the Template column.

All processing stays on this Mac. Requires macOS and Python 3 (already present on this Mac); no third-party Python packages. `App.swift` is the native UI source; `split_emails.py` is the processing script and also supports `python3 split_emails.py "/path/to/file.xlsx"`.

## Editing the launch screen

Edit the text in `App.swift`: window title (line 26), heading (line 30), description (line 34), button (line 37), and initial status (line 41). Then double-click `Rebuild App.command` and reopen the app to see changes. Requires the installed Apple command-line tools.
