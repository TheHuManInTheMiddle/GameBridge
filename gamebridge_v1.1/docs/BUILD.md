# GameBridge v1.1.0 — Build Instructions

## Purpose

This document describes how to build the standalone Windows release of GameBridge from the source tree.

The release is built with PyInstaller and produces a self-contained Windows application that does **not** require Python or the project's Python libraries on the test machine.

## Requirements

Build machine:

- Windows
- Python 3.13.x
- `pip`
- A working GameBridge source tree
- The dependencies listed in `requirements.txt`
- PyInstaller

The normal Python dependencies are installed in the project's `.venv`.

## 1. Create the virtual environment

From the GameBridge project root:

```powershell
python -m venv .venv
```

If PowerShell prevents activation because of the system execution policy, activation is **not required**.

The virtual environment can be used directly:

```powershell
.\.venv\Scripts\python.exe
```

Verify it:

```powershell
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pip --version
```

## 2. Install dependencies

Install the project requirements:

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
```

Install PyInstaller:

```powershell
.\.venv\Scripts\python.exe -m pip install pyinstaller
```

## 3. Build the release

The project contains `GameBridge.spec`, which defines the PyInstaller build.

The recommended build command is:

```powershell
powershell -ExecutionPolicy Bypass -File .\build_release.ps1
```

The build script:

1. Removes the previous PyInstaller build output.
2. Builds the GameBridge executable.
3. Creates the standalone `dist\GameBridge` directory.
4. Copies the external runtime directories:
   - `adapters`
   - `assets`
   - `config`
   - `plugins`
   - `providers`
5. Creates the `logs` directory.

## 4. Release output

After a successful build, the release is located at:

```text
dist\GameBridge\
```

Expected structure:

```text
GameBridge/
├── GameBridge.exe
├── _internal/
├── adapters/
├── assets/
├── config/
├── logs/
├── plugins/
└── providers/
```

The directories outside `_internal` are intentionally kept as external runtime resources. This allows configuration, plugins, providers and other runtime components to remain accessible without rebuilding the executable.

## 5. Test the build

Run:

```powershell
.\dist\GameBridge\GameBridge.exe
```

Verify that:

- GameBridge starts successfully.
- The GUI loads correctly.
- The background image is present.
- Localization loads correctly.
- The example/test plugin is discovered.
- No missing runtime-directory warnings appear.
- The application can shut down cleanly.

For a proper release test, copy the complete `dist\GameBridge` directory to a separate location and run the executable from there.

The application should use the copied directory as its runtime root and must not depend on the original source tree.

## 6. Preparing the release package

Only the completed:

```text
dist\GameBridge\
```

directory belongs in the Windows release package.

Do **not** include the following development files/directories:

```text
.venv/
build/
main/
core/
interface/
functions/
GameBridge.spec
build_release.ps1
```

The final release package should contain the complete `GameBridge` directory, including its `_internal` directory and all external runtime directories.

The `logs` directory should normally be empty when the release ZIP is created.

## Important

`requirements.txt` is required for **building from source**.

It is **not required by users running the standalone Windows release**.

The standalone release is intended to allow users to test GameBridge without installing Python or the project's Python dependencies.