# GameBridge v1.1.0

## What is GameBridge?

GameBridge is a modular middleware platform designed to connect AI systems with external applications.

It separates communication with the user from interaction with connected applications and provides a common structure for adapters, plugins and AI providers.

This release is a **Windows standalone test build**.

The purpose of this release is to let people test the platform and its example components without setting up the Python development environment.

---

## Quick Start

### Windows standalone release

1. Download the GameBridge release ZIP.
2. Extract the **entire `GameBridge` folder**.
3. Do not move or remove files from the extracted folder.
4. Start:

```text
GameBridge.exe
```

No Python installation is required.

No `pip install` is required.

The `_internal` directory and the external runtime directories must remain next to `GameBridge.exe`.

---

## Included Components

The release contains example and test components so that GameBridge can be explored immediately.

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

### Adapters

Adapters provide the connection between GameBridge and external applications.

The release contains example/test adapter components.

### Plugins

Plugins extend GameBridge with application-specific functionality.

The release currently includes the **Notepad++ (Target X)** example plugin.

### Providers

Providers supply AI or other external service functionality to GameBridge.

Example/test providers may be included with the release.

### Configuration

The `config` directory contains runtime configuration and localization data.

Configuration files are intentionally external to the executable.

### Assets

The `assets` directory contains external presentation resources such as the GameBridge background.

### Logs

The `logs` directory is intentionally included in the release but is normally empty when the package is distributed.

GameBridge can use this directory for runtime logging.

---

## What You Can Test

The GUI provides several independent components and communication paths.

Depending on the available local setup, testers can explore:

- AI activation
- Internet AI control
- AI model selection
- Adapter selection
- Channel 1 communication
- Channel 2 application communication
- Audio / Push-To-Talk
- Persistent audio mode
- Keyboard lock
- Stay on Top
- Text colour controls
- Hotkey configuration
- Telemetry
- Application adapters
- Plugin discovery
- AI-to-application interaction

Not every feature requires an external service.

---

## AI Testing

AI functionality requires a compatible local AI environment.

For the current development/test configuration this means using **Ollama** with an available local model.

If AI infrastructure is not available, the rest of the GameBridge interface can still be explored.

---

## Notepad++ Test

The release includes a Notepad++ example integration.

To test it:

1. Install and start Notepad++.
2. Start GameBridge.
3. Allow the Notepad++ plugin to be discovered.
4. Select the appropriate adapter/component in GameBridge.
5. Test communication between GameBridge and Notepad++.

The example integration is included primarily to demonstrate how GameBridge can interact with an external application through its adapter/plugin architecture.

---

## Audio / Push-To-Talk

Audio functionality requires access to a working microphone and Windows audio input.

The audio controls can be tested independently from the AI functionality.

If audio capture is unavailable, GameBridge may report that no compatible audio capture backend is available.

---

## Windows Security

Windows security features may block unsigned or newly built executable files.

This can occur with development and test releases even when the application itself is functioning correctly.

If Windows or an organizational security policy blocks `GameBridge.exe`, the release may not be runnable on that system.

Do not disable security controls unless you understand the implications and are authorized to do so.

---

## Known Issues

This is a **test release**, not a final production release.

Known issues currently include:

### GUI resizing

The main window can be resized downward correctly.

Resizing upward does not currently propagate the increased size to the chat window correctly.

### Telemetry / Channel 2

Telemetry can appear in the Channel 1 chat under some configurations even when the Channel 2 monitor is not active.

Formatting and routing behaviour will be investigated further when a suitable working Channel 2 test target is available.

### External integrations

Some behaviour depends on the connected application and its adapter/plugin implementation.

Not all external application integrations are currently available for testing.

---

## Reporting Problems

When reporting a problem, please include:

- Windows version
- GameBridge version
- What you were testing
- What you expected to happen
- What actually happened
- Whether AI was enabled
- Whether Internet AI was enabled
- Which adapter/plugin was selected
- Relevant terminal output or logs, if available

Screenshots are also useful for GUI-related problems.

Please describe the smallest sequence of actions that reproduces the problem.

---

## Important

GameBridge is modular.

A problem in one component does not necessarily indicate a problem in the entire platform.

When testing, it is useful to identify which layer is involved:

```text
GUI
 ↓
Channel 1
 ↓
AI Bridge
 ↓
Channel 2
 ↓
Adapter
 ↓
Plugin
 ↓
External Application
```

This separation is one of the central design principles of GameBridge.

---

## Development

The standalone release does not require Python.

Developers working with the source code should use the project's development environment and follow the build instructions in:

```text
BUILD.md
```

The standalone Windows release is generated from the source project using PyInstaller.

---

## Version

**GameBridge v1.1.0**

Windows standalone test release.