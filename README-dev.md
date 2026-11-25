# AURA-Learn — Developer guide (VS Code / Cursor: a single F5 → Streamlit + Edge)

> This guide describes the demonstrator's **local development** setup.
> It modifies neither [`app.py`](app.py) nor [`requirements.txt`](requirements.txt).
> The application remains a proprietary academic prototype (see [`LICENSE`](LICENSE)).

---

## 1. What is configured

| Item | Value |
|---|---|
| Detected framework | **Streamlit** (`import streamlit as st`, `st.set_page_config(...)` inside `main()`) |
| Launch command | `python -m streamlit run app.py` |
| Port / local URL | **8501** → `http://localhost:8501` |
| Target browser | **Microsoft Edge**, regular tab — **no JavaScript debugger attached** |
| Browser opening mechanism | **`Streamlit: open Edge (detached)`** task (type `process`, `problemMatcher: []`) triggered as the `preLaunchTask` of the default configuration; it starts [`.vscode/open-edge.ps1`](.vscode/open-edge.ps1) as a detached background process, which waits for the port to respond and then opens Edge |

Relevant files:

- [`.vscode/launch.json`](.vscode/launch.json) — default configuration `Streamlit + Edge` and fallback configuration `Streamlit: server only`.
- [`.vscode/tasks.json`](.vscode/tasks.json) — task `Streamlit: open Edge (detached)` (used as `preLaunchTask`) and optional utility task `Streamlit: kill port 8501`.
- [`.vscode/open-edge.ps1`](.vscode/open-edge.ps1) — Edge opening script (port polling, `msedge.exe` detection, tab opening, log written to `.vscode/open-edge.log`).

---

## 2. Usage: a single F5

1. Open the **Run and Debug** panel (`Ctrl+Shift+D`).
2. In the drop-down list, select **`Streamlit + Edge`** (first configuration, selected by default).
3. Press **F5**.

Expected result:

- the `Streamlit: open Edge (detached)` task returns **immediately** (it only starts the script as a detached background process): there is therefore no delay before the debugger starts and no risk of "Timed out waiting for preLaunchTask";
- `debugpy` starts `streamlit run app.py` in the integrated terminal (Python debugging of the server);
- in parallel, [`.vscode/open-edge.ps1`](.vscode/open-edge.ps1) polls `http://localhost:8501` every 500 ms (60 s timeout); as soon as Streamlit responds, the script opens **Microsoft Edge** on `http://localhost:8501` in a regular tab;
- if the port does not respond after 60 s, the script **opens nothing**, writes an explicit message to `.vscode/open-edge.log` and exits with code 1 (the Python server keeps running on its own).

The script is idempotent: if an Edge instance has already been launched with this URL, it does not reopen a window; when restarted while Edge is already running, Edge simply reuses its existing instance.

### Available configurations

| Configuration | Default | Purpose |
|---|---|---|
| `Streamlit + Edge` | **Yes** | Starts Streamlit under `debugpy` **and** opens Edge through the detached `Streamlit: open Edge (detached)` task. |
| `Streamlit: server only` | No | Starts the server under `debugpy` only, without opening any browser (useful for remote access, another browser, or diagnostics). |

> There is **no longer** any browser-attach configuration: the former `Edge: app (direct)` configuration (type `msedge`) was removed because it reproduced the error described in §5.

---

## 3. Stopping / restarting the server

- The server runs **inside the debug session**: a click on **Stop** (`Shift+F5`) terminates the Streamlit process and frees port 8501. No background task survives the stop (the opening script itself exits on its own at the latest 60 s after it was started).
- If a port remains busy (orphan process, previous launch outside the IDE), run the **`Streamlit: kill port 8501`** task: `Ctrl+Shift+P` → **Tasks: Run Task** → `Streamlit: kill port 8501`. It terminates the process listening on 8501.
- Manual equivalent: `netstat -ano | findstr :8501` then `taskkill /PID <pid> /F`.

---

## 4. Prerequisites

- **VS Code / Cursor extension**: `ms-python.python` (provides `debugpy`) for Python debugging. The **JavaScript Debugger** is no longer required by this flow, since no debugger is attached to the browser.
- **Microsoft Edge installed**: the script looks for `msedge.exe` in `%ProgramFiles%\Microsoft\Edge\Application`, `%ProgramFiles(x86)%\Microsoft\Edge\Application`, `%LOCALAPPDATA%\Microsoft\Edge\Application`, then in the `PATH`. Verified environment: Edge `158.0.4370.33`.
- **Python dependencies already installed** (`streamlit>=1.36.0`, `pandas>=2.1.0`, `requests>=2.31.0`) — this guide triggers no `pip install`. Verified environment: Python 3.12.10, Streamlit 1.67.0.
- **PowerShell 5.1** (shipped with Windows): the task calls `%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe`.
- If your interpreter is a virtual environment, select it with `Python: Select Interpreter`; the debugger then uses that interpreter.

---

## 5. Known limitations and troubleshooting

### 5.1 Error "Unable to attach to the browser" (former `debugWithEdge` configuration)

The former configuration opened Edge through `serverReadyAction` + `action: "debugWithEdge"`, i.e. by **attaching the JavaScript debugger** (js-debug) to the browser. On this machine, that attachment fails systematically with:

```text
Unable to launch browser: "Unable to attach to the browser"
```

**Identified cause**: protocol incompatibility between js-debug **1.93.0** bundled with the editor (Cursor, `resources/app/extensions/ms-vscode.js-debug`) and Edge **158** (Chromium 158). js-debug starts Edge with `--remote-debugging-pipe` and then calls `Target.attachToBrowserTarget`; on Chromium ≥ 137/138 the connection is closed immediately, hence the message. This is **not** a configuration problem: neither the profile, nor the enterprise policy, nor the extension is at fault (verified: profile unlocked and drivable through `--remote-debugging-port`, no `RemoteDebuggingAllowed` value, `ms-vscode.js-debug` and `debug-server-ready` extensions present). See VS Code issues #239705, #255774 and #261080.

**Adopted workaround (Case B)**: no browser debugger attachment at all. Edge is opened by a plain PowerShell script ([`.vscode/open-edge.ps1`](.vscode/open-edge.ps1)) triggered by a detached task. Display in Edge is therefore preserved, without browser JavaScript debugging (which was not needed here).

**Reproducing the diagnosis** (if needed): launch Edge manually with a profile outside the workspace and check that the endpoint responds, which proves that the OS allows debugging and that only the js-debug/Edge pair is faulty.

```bat
start "" "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --user-data-dir="%TEMP%\edge-diag" --remote-debugging-port=9222 about:blank
```

### 5.2 Other points

- **Script log**: `.vscode/open-edge.log` (timestamps, waiting, detected Edge path, exit code). It is a local artifact, to be ignored in version control. Launch it manually if needed:
  ```bat
  powershell -NoProfile -ExecutionPolicy Bypass -File .vscode\open-edge.ps1
  ```
- **Legacy debug profile**: `.vscode/.edge-profile` is **no longer used** by the F5 flow (it was only used by the former `msedge` configuration). It can be deleted without impact; if it is still locked by an old Edge instance, close that instance before deleting it.
- **Never launch a test Edge on the main user profile** when diagnosing: use a temporary `--user-data-dir`, otherwise an instance already open on the same profile prevents the debug port from being opened (hand-off to the existing instance).
- **Hot reload**: `--server.runOnSave` is not enabled; add `"--server.runOnSave", "true"` to the `args` of both configurations if you want it.
- **Streamlit 1.67.0** no longer prints `Local URL: ...` but simply `URL: http://localhost:8501` — no impact here, since availability is tested by HTTP request rather than by reading the server output.
