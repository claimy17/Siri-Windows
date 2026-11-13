# Siri Assistant for Windows (iOS 27 Style)   <img width="53" height="60" alt="icon" src="https://github.com/user-attachments/assets/be245136-1dae-47b0-8c40-66a35ad799f0" />

<img width="482" height="752" alt="Screenshot 2026-11-14 004741" src="https://github.com/user-attachments/assets/fa8019d1-5e68-40f5-ad02-2dc9259d1331" />
<img width="482" height="752" alt="Screenshot 2026-11-14 004751" src="https://github.com/user-attachments/assets/6d2dd292-a926-4268-a5bb-09d82b6f8f4f" />
<img width="482" height="752" alt="Screenshot 2026-11-14 004758" src="https://github.com/user-attachments/assets/0cba96b7-601a-4692-bad7-2ea013eb4d2b" />


A lightweight, offline Siri-inspired voice and text assistant for **Windows 10 and Windows 11**, built with **Python (PyQt6)** and paired with a native **Win32 C Setup & Uninstaller** (`Siri-Setup.exe`).

---

## Features

- **iOS 27 Inspired Glassmorphism UI**:
  - Translucent rounded window with live animated Siri soundwaves (`WaveAnimation`).
  - Instant switching between **Liquid Glass**, **Dark Theme**, and **Light Theme**, plus custom chat background images.
- **Teach Siri (Persistent Local Memory)**:
  - Slide-up **Teach** panel allowing you to teach Siri custom responses or system commands saved permanently in `~/.siri_memory`.
- **Built-in System Tools & Utilities**:
  - **App Launcher**: Open Notepad, Calculator, Google Chrome, Spotify, and File Explorer via text commands.
  - **System Monitor**: Check free/total RAM and operating system details.
  - **Smart Calculator**: Evaluate math expressions directly in chat (`calculate 25 * 4` or `120 / 3`).
  - **Flash Suggestions (`⚡`)**: Interactive quick tips for optimizing Windows performance and storage.
- **Native C Setup & Uninstaller (`Siri-Setup.exe`)**:
  - Pure Win32 C installer with zero external dependencies.
  - Automatically checks for Python 3 (installing it via `winget` if missing), installs `PyQt6`, sets up silent background execution (`pythonw.exe`), and creates **Desktop** and **Start Menu** shortcuts.
  - Includes a built-in **Uninstall** button for clean removal.

---

## Requirements

- **Operating System**: Windows 10 or Windows 11
- **Python 3**: Automatically installed by `Siri-Setup.exe` via Windows Package Manager (`winget`) if not already present on your PC.
- **Compiler** *(only if building `Siri-Setup.exe` from source)*: MinGW-w64 (`gcc` and `windres`).

---

## Installation (Recommended)

1. Go to the **[Releases](../../releases)** page and download the latest release archive (containing `Siri-Setup.exe`, `siri.py`, `icon.ico`, and `icon.png`).
2. Extract all files into the same folder.
3. Run **`Siri-Setup.exe`** and click **Install Siri**.
4. Once finished, click **Launch Siri Now** or open **Siri** from your Desktop or Start Menu.

*(To remove the application later, run `Siri-Setup.exe` again and click **Uninstall**).*

---

## Building the Setup from Source

1. Place `setup.c` and `icon.ico` in the same folder.
2. Compile the resource file and build `Siri-Setup.exe` using GCC:

```bat
echo 1 ICON "icon.ico" > app.rc
windres app.rc -O coff -o app.res
gcc setup.c app.res -o Siri-Setup.exe -mwindows -lole32 -luuid -lshell32 -ldwmapi -lmsimg32 -luxtheme
```

---

## Windows Security / Smart App Control Notice

Because open-source binaries compiled with GCC do not include a commercial code-signing certificate, Windows Defender SmartScreen or Windows 11 Smart App Control may display a warning on first launch:
- Click **More info > Run anyway** if SmartScreen appears, or
- Compile `Siri-Setup.exe` directly from `setup.c` on your machine.

---

## License

This project is open-source under the MIT License. Created by **claimy17**.
