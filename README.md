# ⚡ OSCam Emu Patch Manager

**Build it. Check it. Ship it.**  
*Install. Manage. Patch. Publish.*

A desktop toolkit for managing the OSCam-Emu patch workflow — from creating and validating patches to applying changes locally and publishing updates to GitHub.

🌍 **Available in 6 Languages**

🇩🇪 German · 🇬🇧 English · 🇮🇹 Italian · 🇵🇱 Polish · 🇹🇷 Turkish · 🇬🇷 Greek

📦 [GitHub Repository](https://github.com/speedy005/oscam_patch_manager_new)

---

# 📖 About the Project

**OSCam Emu Patch Manager** is a Python-based desktop toolkit for managing OSCam-Emu patches and related Git workflows.

The application provides a graphical interface for supported patch, backup, configuration, and build tasks. The available functionality depends on the installed version, configuration, and external tools.

## ✨ Features

- 🧩 Create, validate, and apply patches
- 📦 Create backups and export them as ZIP archives
- ✏️ Edit patch headers and metadata
- 🖥️ PyQt6 graphical interface
- 🌐 Git and GitHub features where configured and available
- 📁 Select and persist the working directory
- ⚙️ Manage Python environments and dependencies
- 🛠️ Linux and WSL2 support for suitable build workflows
- 🔍 Check build tools and dependencies
- 🔒 Exclude supported files and directories from backups

## 🌍 Multilingual Interface – 6 Languages

The OSCam Emu Patch Manager now supports six interface languages.

| Flag | Language | Code |
|---|---|---|
| 🇩🇪 | German | DE |
| 🇬🇧 | English | EN |
| 🇮🇹 | Italian | IT |
| 🇵🇱 | Polish | PL |
| 🇹🇷 | Turkish | TR |
| 🇬🇷 | Greek | GR |

### 🚀 Language Features

- 🚩 Convenient language selection with country flags
- 🔄 Immediate interface language switching
- 💾 Automatic saving of the selected language
- 🔁 Language preference restored after restarting
- 🌐 Translated interface texts, buttons, messages and tooltips
- ⚡ No manual configuration required

**One application. Six languages. One seamless workflow.**

---

# 📋 Requirements

## Windows

- Windows 10 or Windows 11
- A supported Python version
- Internet access for installation downloads and any required GitHub operations
- Write permissions for the installation and working directories

## Linux and WSL2

- A supported Linux distribution, such as Ubuntu
- Python 3, `pip`, and `venv`
- PyQt6 and the Python dependencies actually required by the project
- System libraries for the graphical interface
- Git and any additional build tools required
- WSLg or another suitable graphical environment when running the GUI under WSL

OSCam-Emu builds may require additional libraries, headers, compilers, or a project-specific SDK.

**Download Python:** https://www.python.org/downloads/

> **Important:** Windows Python and Python inside WSL2 are separate installations. Python packages installed on Windows are not automatically available to Linux applications.

---

# 🚀 Installation

## 🪟 Windows 10 / Windows 11

### 1. Check Python

Open Command Prompt (`Win + R` → `cmd`) and run:

```bat
py -3 --version
```

If the command is not recognized, install Python from the official website and check your PATH configuration.

### 2. Download the installer

If the installer is available in the repository version you are using, it can be downloaded as follows:

```bat
curl -fL "https://raw.githubusercontent.com/speedy005/oscam_patch_manager_new/master/installer.py" -o "%TEMP%\oscam_installer.py"
```

Verify the source and then run it:

```bat
py -3 "%TEMP%\oscam_installer.py"
```

Use this download path only if the installer actually exists at that address and is intended for your version.

### 3. Complete setup

- Follow the installer's instructions.
- Choose the desired installation directory.
- Review overwrite prompts carefully.
- Back up existing configuration and local changes.
- Check the output for missing dependencies.

### 4. Launch the application

Navigate to the actual installation directory.

First, check which startup files are available:

```bat
dir *.bat
dir *.py
```

Run the startup script intended for your version. If `start_windows.bat` exists:

```bat
start_windows.bat
```

Not every version necessarily includes the same startup files.

---

## 🐧 Linux: Ubuntu, Debian, and Linux Mint

### 1. Install system packages

```bash
sudo apt update
sudo apt install -y \
    python3 \
    python3-venv \
    python3-pip \
    python3-dev \
    build-essential \
    git \
    curl \
    ca-certificates \
    dos2unix \
    libpulse0
```

For build workflows that use Meson and Ninja:

```bash
sudo apt install -y meson ninja-build gettext
```

These packages provide a basic Python environment, compiler tools, and selected system libraries. They do not replace a project-specific SDK installation.

### 2. Open the project directory

Navigate to the directory containing the project.

Example using a generic path:

```bash
cd "/path/to/project"
```

Check the contents:

```bash
pwd
ls -la
```

Replace the example path with your actual installation location.

### 3. Set up the Python environment

Create the virtual environment if it does not already exist:

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Upgrade `pip`:

```bash
python -m pip install --upgrade pip
```

Install dependencies using the files actually provided by the project.

If `requirements.txt` exists:

```bash
python -m pip install -r requirements.txt
```

If it does not exist, check the project installation instructions and Python imports. Do not guess undocumented dependencies.

### 4. Launch the application

Check that the entry point exists:

```bash
ls -l main.py
```

If the file exists and the dependencies are installed:

```bash
python main.py
```

Activate the virtual environment again in every new terminal session.

---

## 🐧 Windows with WSL2 and Ubuntu

WSL2 provides a Linux environment on Windows. Linux build tools and Python dependencies must be installed inside the WSL distribution actually being used.

### 1. Check WSL

Open PowerShell on Windows:

```powershell
wsl --status
wsl --list --verbose
```

If Ubuntu is not installed, installation can be started from an elevated PowerShell session:

```powershell
wsl --install -d Ubuntu
```

Complete the Windows setup process if necessary.

### 2. Open Ubuntu

Open Ubuntu from the Windows Start menu or launch it from PowerShell:

```powershell
wsl -d Ubuntu
```

Run all subsequent Linux commands inside the Ubuntu terminal.

### 3. Install WSL dependencies

```bash
sudo apt update
sudo apt install -y \
    python3 \
    python3-venv \
    python3-pip \
    python3-dev \
    build-essential \
    git \
    curl \
    ca-certificates \
    dos2unix \
    libpulse0
```

For additional build workflows:

```bash
sudo apt install -y meson ninja-build gettext
```

**Why `libpulse0`?**

This package provides the runtime library `libpulse.so.0`, which may be needed by GUI or audio components. Install additional libraries according to the actual error messages.

If `sudo` requests a password, use the password for your Ubuntu Linux user. No characters are displayed while typing. This is normal. The Ubuntu password is not automatically your Windows password.

### 4. Choose the project directory

Navigate to the directory where the project is actually stored.

For a Windows drive, WSL commonly provides access through `/mnt/<drive>/...`. Example:

```bash
cd "/mnt/<drive>/path/to/project"
```

Replace the example path with your actual location.

Alternatively, store the project in the WSL Linux filesystem.

Verify the directory:

```bash
pwd
ls -la
```

### 5. Set up Python

If the virtual environment does not exist:

```bash
python3 -m venv .venv
```

Activate it and upgrade `pip`:

```bash
source .venv/bin/activate
python -m pip install --upgrade pip
```

If the application contains `requirements.txt`:

```bash
python -m pip install -r requirements.txt
```

If no dependency file exists, check the documentation and actual project code.

### 6. Launch the graphical interface

WSLg can provide Linux GUI support under Windows 11 and supported Windows 10 configurations.

Check that the entry point exists:

```bash
ls -l main.py
```

Launch the application with the virtual environment activated:

```bash
python main.py
```

If `No module named PyQt6` appears, Python dependencies are missing from the active environment.

If `libpulse.so.0` is missing, install:

```bash
sudo apt install -y libpulse0
```

If no window appears, check the WSL version, graphical support, and complete error message.

### 7. Prepare OSCam-Emu builds

Build requirements depend on the script and SDK being used.

If a build script named `s3` exists, check it first:

```bash
file ./s3
head -n 1 ./s3
bash -n ./s3
```

If the file uses Windows line endings (`CRLF`), correct it with:

```bash
dos2unix ./s3
```

Other shell scripts can be checked individually. Convert only files that need correction.

If the syntax check succeeds, follow the script's own documentation. For example, it may provide a menu command:

```bash
chmod +x ./s3
./s3 menu
```

Use this command only if the script and menu mode exist in the version being used.

> **OpenPLi/OpenEmbedded SDK:** Standard Ubuntu packages do not replace a complete cross-compilation SDK. Depending on the target platform, a cross-compiler, SDK environment variables, libraries, headers, and other dependencies may be required.

---

# 🧰 Windows Batch Files and Linux Shell Scripts

Windows batch files (`.bat` and `.cmd`) and Linux shell scripts (`.sh`) are different script formats.

## On Windows

Check for batch files in the project directory:

```bat
dir *.bat
dir *.cmd
```

Run only a startup script that exists in the version being used and is intended for Windows.

## On Linux and WSL2

Search for shell scripts:

```bash
find . -maxdepth 3 -type f -name "*.sh" -not -path "./.git/*"
```

A shell script can be started with:

```bash
bash ./script.sh
```

To make it executable:

```bash
chmod +x ./script.sh
./script.sh
```

Replace `script.sh` with the actual filename.

A `.bat` file is not a native Linux startup script. Under WSL, use the intended Python entry point or an existing shell script. Windows programs can be launched separately when the WSL configuration supports it.

---

# 🔧 Fixing CRLF Line Endings

Windows commonly uses `CRLF` line endings, while Linux shell scripts normally use `LF`.

Typical errors include:

```text
/bin/bash^M: bad interpreter: No such file or directory
```

```text
$'\r': command not found
```

Check the affected script:

```bash
file ./script.sh
```

Convert it if necessary:

```bash
dos2unix ./script.sh
```

Check other files individually if they are sourced by shell scripts.

**Important:** Do not run `dos2unix` indiscriminately on ZIP files, images, binary files, or compiled files.

---

# 📦 Additional OSCam Build Dependencies

Depending on the build script, additional development libraries may be required. Examples of possible packages include:

```bash
sudo apt install -y \
    autoconf \
    automake \
    autoconf-archive \
    libtool-bin \
    pkg-config \
    jq \
    bzip2 \
    libssl-dev \
    libpcsclite-dev \
    libccid \
    libusb-1.0-0-dev
```

These packages are **not required for every build**. Install only the packages required by the specific build script or SDK.

If a package is missing, check its availability:

```bash
sudo apt update
apt-cache policy libusb-1.0-0-dev
```

---

# 🛠️ Troubleshooting

| Problem | Possible solution |
|---|---|
| `py` is not recognized on Windows | Install Python and check PATH. |
| `python3` is missing | Install Python using the Linux package manager. |
| `python` is not found in a new terminal | Activate the virtual environment with `source .venv/bin/activate`. |
| `venv` is missing | Run `sudo apt install -y python3-venv`. |
| `No module named PyQt6` | Install dependencies in the active virtual environment. |
| `libpulse.so.0` is missing | Run `sudo apt install -y libpulse0`. |
| `curl: command not found` | Run `sudo apt install -y curl`. |
| `git: command not found` | Run `sudo apt install -y git`. |
| `meson: command not found` | Run `sudo apt install -y meson`. |
| `ninja: command not found` | Run `sudo apt install -y ninja-build`. |
| `/bin/bash^M: bad interpreter` | Correct the affected shell script with `dos2unix`. |
| `Permission denied` | Check the path, file permissions, and startup command. |
| A `.bat` file does not start under Linux | Use the intended WSL or Linux startup method. |
| Build tools or headers are missing | Check the build script, SDK documentation, and error message. |
| GUI does not open | Check WSLg, GUI dependencies, the virtual environment, and the error message. |
| Installation fails | Check Python version, network access, write permissions, and the complete error message. |

---

# 🔄 Updating

Before every update:

- Back up configuration and local changes.
- Back up important patches and archives.
- Check whether files may be overwritten.
- Verify that the installer updates all required files.
- Recheck Python dependencies after updating.

Reinstalling does not guarantee that old files are removed or all existing files are updated.

---

# 🔒 Security

- Review source code before running it.
- Back up files before patching and updating.
- Review changes with `git diff` before committing.
- Never publish GitHub tokens or credentials.
- Run cleanup operations only in verified directories.
- Obtain installation scripts only from trusted sources.
- Check whether local changes must be preserved before overwriting.
- Handle symbolic links and external directories carefully when creating backups.

---

# 🤝 Contributing

Bug reports, reproducible test cases, and pull requests are welcome.

When reporting an issue, include:

- Steps to reproduce
- Operating system and WSL version, if applicable
- Python version
- SDK or build profile
- Relevant error messages and build logs
- Affected scripts and their line endings, where relevant

Remove credentials, tokens, and other confidential information before sharing.

---

# ⚠️ Disclaimer

This project is provided without warranties. Compatibility and functionality depend on the operating system, source code, SDK, firmware, and configuration.

Back up important files before modifying an existing installation. Successful compilation does not guarantee that the resulting binary will run on every target device.

---

# 📦 Project Links

- [GitHub Repository](https://github.com/speedy005/oscam_patch_manager_new)
- [Download Python](https://www.python.org/downloads/)

---

**Made for a smoother OSCam-Emu patch workflow.** ⚡

**Built with Python 3 · PyQt6 · Git · GitHub**

🌍 **German · English · Italian · Polish · Turkish · Greek**
