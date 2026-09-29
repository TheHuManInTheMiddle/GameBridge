# GameBridge `.gbp` Plugin Packaging Guide

This guide describes the basic process used to package a GameBridge plugin as a `.gbp` file.

The `.gbp` format is a ZIP-based container containing the plugin entry point and its Python dependencies.

## 1. Plugin source structure

Start with a plugin directory containing the plugin entry point and its configuration files.

Example:

```text
notepad_plugin2/
├── main_adapter.py
├── plugin_config.json
└── plugin_prompt.txt
```

The runtime `temp/` directory is **not** part of the source package. GameBridge creates it automatically when the `.gbp` plugin is loaded.

---

## 2. Discover external dependencies

From inside the plugin directory, use `pipreqs` to inspect Python imports without manually opening the plugin source code:

```powershell
pipreqs . --print
```

Example result:

```text
WARNING: Import named "adapters" not found locally.
WARNING: Import named "core" not found locally.

adapters==1.3.0
core==1.0.1
pyautogui==0.9.54
```

`pipreqs` may incorrectly interpret GameBridge's own internal modules as external PyPI packages.

For example:

```text
adapters
core
```

are GameBridge internal modules and must **not** be installed as plugin dependencies.

Remove those entries from the generated dependency list.

The remaining entries are external Python dependencies.

For this example:

```text
pyautogui==0.9.54
```

Save the verified external dependencies as:

```text
requirements.txt
```

---

## 3. Install dependencies into the plugin

Create a dependency directory:

```powershell
mkdir dependencies
```

Then install the requirements directly into it:

```powershell
pip install -r requirements.txt --target dependencies
```

Using `--target dependencies` is important.

The dependencies are stored inside the plugin package instead of being installed into the main GameBridge Python environment.

`pip` also resolves and installs the required dependency tree automatically.

For example, installing PyAutoGUI may result in:

```text
dependencies/
├── pyautogui/
├── pyperclip/
├── pygetwindow/
├── pymsgbox/
├── pyrect/
├── pyscreeze/
├── pytweening/
├── mouseinfo/
└── ...
```

The exact dependency tree may vary between package versions.

---

## 4. Final source structure

Before packaging, the plugin directory should look approximately like this:

```text
notepad_plugin2/
├── main_adapter.py
├── plugin_config.json
├── plugin_prompt.txt
├── requirements.txt
└── dependencies/
    ├── pyautogui/
    ├── pyperclip/
    ├── pygetwindow/
    └── ...
```

`requirements.txt` is documentation/build input and does not need to be included in the `.gbp` runtime package unless desired.

---

## 5. Create the `.gbp` package

The `.gbp` file is a ZIP container with a different extension.

The package must contain:

```text
main_adapter.py
dependencies/
```

The package should therefore have this internal structure:

```text
main_adapter.py
dependencies/
├── pyautogui/
├── pyperclip/
├── pygetwindow/
└── ...
```

From the plugin directory, create the archive with:

```powershell
tar -a -c -f notepad_plugin2.gbp main_adapter.py dependencies
```

The resulting file is:

```text
notepad_plugin2.gbp
```

---

## 6. Verify the package

Before testing it in GameBridge, inspect the package contents:

```powershell
tar -tf notepad_plugin2.gbp
```

The listing should contain:

```text
main_adapter.py
dependencies/...
```

and should **not** contain the generated GameBridge runtime directory:

```text
temp/
```

---

## 7. GameBridge runtime

When GameBridge loads the `.gbp` plugin, the runtime extracts the package into its temporary runtime directory.

Conceptually:

```text
notepad_plugin2.gbp
        ↓
GameBridge GBP Runtime
        ↓
plugins/notepad_plugin2/temp/
        ↓
main_adapter.py
dependencies/
        ↓
Plugin loaded
```

The `temp/` directory is runtime-generated and can be removed when GameBridge exits or during startup cleanup. GameBridge recreates it from the `.gbp` package when required.

---

## Summary

The complete workflow is:

```text
Plugin source
     ↓
pipreqs . --print
     ↓
Remove GameBridge-internal modules
     ↓
requirements.txt
     ↓
pip install -r requirements.txt --target dependencies
     ↓
main_adapter.py + dependencies/
     ↓
Create ZIP-based .gbp
     ↓
Verify with tar -tf
     ↓
GameBridge loads .gbp
     ↓
Runtime extracts temp/
```

The important principle is:

> **Discover dependencies first, verify them, install them locally into the plugin, then package the plugin and its dependencies together.**

This keeps plugin-specific Python dependencies isolated from the GameBridge core.

> **PS:** If you prefer not to build your plugin package manually, you can just use [AIDE](https://github.com/TheHuManInTheMiddle/AIDE) with its built-in plugin autobuilder. 😉
