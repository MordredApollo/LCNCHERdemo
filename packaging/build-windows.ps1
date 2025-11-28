# Build script for Windows
# Requires: pyinstaller

if (!(Test-Path "dist")) { mkdir dist }

python -m pip install pyinstaller
pyinstaller --name LewdCornerLauncher `
  --onefile `
  --windowed `
  --noconfirm `
  src\lewdcorner\main.py

Write-Host "✅ LewdCorner Launcher build complete!"
