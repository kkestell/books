$ErrorActionPreference = 'Stop'

uv run python -m nuitka --standalone --plugin-enable=pyside6 --output-filename=Thoth.exe --windows-console-mode=disable --windows-icon-from-ico=assets/icon.ico --include-data-file=assets/icon.png=assets/icon.png thoth/main.py

if ($LASTEXITCODE -ne 0) {
    Write-Error "Nuitka build failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}

& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" install.iss
