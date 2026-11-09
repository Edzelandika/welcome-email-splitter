# Windows portable version

Copy **Welcome Email Splitter.exe** to your Windows laptop and double-click it. No installation, Python, or Excel is needed to run the executable. Built for Windows x64.

Drop one original `.xlsx` file into the window, or click **Choose Excel File…**. Close the workbook in Excel first. The original is replaced by the non-student list and a `(STUDENTS ONLY).xlsx` file is created alongside it. No backup is created. Both files contain only First Name, Last Name, and Email.

The executable is unsigned. Follow your organization's software policy if Windows blocks it.

## Rebuilding

On Windows with Python 3 installed, double-click **Build Windows.cmd**. The result is `windows/dist/Welcome Email Splitter.exe`. The build needs internet access for dependencies; the finished app processes files locally without network access.

Alternatively, the GitHub Actions **Build Windows portable app** workflow builds and checks the app on Windows. Download its **Welcome-Email-Splitter-Windows** artifact and extract the executable.

Edit the Windows launch-screen text in `windows/app.py`. The shared workbook processing code is `split_emails.py` in the parent folder.
