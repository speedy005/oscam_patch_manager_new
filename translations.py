"""OSCam Patch Manager module fragment: Language selection and translated UI strings."""

# Explicit module imports (kept broad for compatibility with legacy callbacks).
import ctypes
import glob
import importlib.util
import io
import json
import locale
import os
import platform
import random
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import zipfile
from PyQt6.QtCore import QDateTime, QEasingCurve, QObject, QPoint, QPropertyAnimation, QRect, QSize, QThread, QTime, QTimer, QUrl, Qt, pyqtProperty, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QIcon, QPainter, QPen, QPolygon, QTextCursor
from PyQt6.QtWidgets import QApplication, QCheckBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QFrame, QGraphicsColorizeEffect, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLayout, QLineEdit, QMessageBox, QProgressBar, QPushButton, QSizePolicy, QSlider, QTextEdit, QVBoxLayout, QWidget, QWidgetItem
from datetime import datetime, timezone

def fill_missing_keys(texts):
    """Ergänzt fehlende deutsche Übersetzungen durch englische Texte."""
    en_keys = texts.get("en", {})
    de_keys = texts.setdefault("de", {})

    for key, value in en_keys.items():
        de_keys.setdefault(key, value)

LANG = "de"
TEXTS = {
    "en": {
        # Grid Buttons / Patch Aktionen
        "fix_permissions": "Berechtigungen reparieren",
        "restart_tool_admin": "Restart with administrator rights",
        "backup_button_text": "💾 Create Backup",
        "patch_create": "Create Patch",
        "patch_renew": "Renew Patch",
        "patch_check": "Check Patch",
        "settings_header": "Settings",
        "patch_folder_s3_ncam": "S3-NCam-patch Path",
        "patch_folder_s4": "S4 patch Path",
        "patch_copy_s3_ncam": "Patch to S3-NCam",
        "patch_copy_s4": "Patch to S4",
        "patch_folder_s3_ncam_tooltip": "Select S3-NCam-Bonecrew patch folder",
        "patch_folder_s4_tooltip": "Select S4 patch folder",
        # Repository selection / Revision picker
        "select_repository": "Select Repository",
        "current_source": "Current Source",
        "select_repository_prompt": "Please select a repository.",
        "no_repository_url": "No repository URL selected.",
        "working_tree_not_clean": "Working tree is not clean.",
        "select_revision": "Select Revision",
        "repository_load_failed": "Failed to load repository.",
        "revision_load_failed": "Failed to load revisions.",
        # "patch_save_label": "Save Patch",
        "patch_apply": "Apply Patch",
        "patch_path_label": "Save Patch",
        "patch_zip": "Zip Patch",
        "backup_old": "S3-Backup/Renew Patch",
        "clean_folder": "Clean Patch Folder",
        "change_old_dir": "Select S3 Patch Folder",
        "oscam_emu_revision": "OSCam-Emu Revision",
        # Commits
        "loading_commits": "Loading commits...",
        "commits_loaded": "Commits successfully loaded",
        # Githup Upload
        "github_config_load": "Loading GitHub configuration...",
        "github_emu_git_missing": "Error: GitHub configuration incomplete (URL, token, or user missing).",
        "patch_emu_git_missing": "Error: Local source directory not found: {path}",
        "git_repo_init": "Initializing new git repository in target folder...",
        "git_remote_add": "Linking local repository to GitHub...",
        "git_remote_update": "Updating remote connection...",
        "git_fetching": "Fetching current data from GitHub repository...",
        "plugin_uptodate": "✅ Plugin is up to date (Version: {current})",
        "tools_ok": "✅ All required system tools are already installed.",
        "checking_tools": "Starting system tool check...",
        "git_config_user": "Setting git user data ({user_name})...",
        "git_adding_files": "Indexing files for upload...",
        "git_committing": "Creating commit...",
        "github_upload_start": "Starting upload to GitHub (push)...",
        "github_emu_git_uploaded": "Upload completed successfully!",
        "github_emu_git_revision": "Uploaded revision {sha}. Message: {commit_msg}",
        "github_upload_failed": "Failed to upload to GitHub!",
        # ... tool first start check ...
        "log_start_header": "--- OSCam Emu Patch Generator v{} ---",
        "log_sys_info": "System: {} {}",
        "log_dep_check": "Prüfung: Git ({}), Patch ({}), Sound ({})",
        "log_status_ok": "Status: Alle Abhängigkeiten geladen. Bereit.",
        "ok": "OK",
        "language_done": "✅ Language switched!",
        "language_switch": "Switching language...",
        "missing": "FEHLT",
        "active": "Aktiv",
        "inactive": "Inaktiv",
        # --- Header & GroupBoxes ---
        "settings_header": "⚙️ Settings",
        "github_config_header": "📁 GitHub Configuration",
        # --- Labels ---
        "language_label": "Language:",
        "color_label": "Style / Color:",
        "commit_count_label": "Show Commits:",
        # --- Buttons & Tooltips ---
        "modifier_button_text": "👤 Patch Author",
        "modifier_tooltip_prefix": "Created by:",
        "check_tools_button": "🛠️ Check Tools",
        # --- System-Check Log ---
        "start_check": "Starting System Check...",
        "found": "OK",
        "missing": "MISSING!",
        "net_check": "Checking connection...",
        "net_online": "Online",
        "net_offline": "Offline",
        "upd_check": "🔍 Tool Update Check...",
        "sound_active": "Active",
        "sound_inactive": "Inactive",
        # --- Status Messages ---
        "status_up_to_date": "✅ OSCam is up to date",
        "status_update_avail": "🚀 Update available!",
        "welcome_msg": "Welcome to OSCam Emu Patch Generator!",
        # ... zip_patch ...
        "patch_file_missing": "Patch file does not exist: {path}",
        "zip_success": "✅ Patch successfully zipped: {zip_file}",
        "zip_failed": "❌ Error while zipping: {error}",
        # OSCam-Emu Git Patch
        "patch_creation_finished": "Patch creation finished.",
        "patch_emu_git_start": "🚀 Starting OSCam-Emu Git patch process...",
        "patch_emu_git_check_git": "🔎 Checking Git...",
        "patch_emu_git_prepare": "🧹 Preparing workspace...",
        "patch_emu_git_clone": "🌐 Cloning Streamboard...",
        "patch_emu_git_head": "📌 Determining current Streamboard revision...",
        "patch_emu_git_check_patch": "🔍 Checking patch...",
        "patch_emu_git_apply": "🔧 Applying OSCam-Emu patch...",
        "patch_emu_git_status": "📋 Checking changes...",
        "patch_emu_git_config": "👤 Configuring Git...",
        "patch_emu_git_commit": "💾 Committing patch...",
        "patch_emu_git_replace": "📦 Installing patched repository...",
        "patch_emu_git_validate": "🔎 Validating repository...",
        "patch_emu_git_success": "✅ OSCam-Emu Git patched successfully",
        "patch_emu_git_failed": "❌ OSCam-Emu Git patching failed",
        "patch_emu_git_done": "🎉 OScam-Emu Git successfully patched!",
        "patch_emu_git_start": "🚀 Starting OScam-Emu patch process...",
        "patch_emu_git_clone_failed": "❌ Error: Clone failed!",
        "patch_emu_git_start": "🔹 Creating OSCam-Emu Git Patch... (Path: {path})",
        "patch_emu_git_deleted": "✅ Old OSCam-Emu Git folder deleted: {path}",
        "delete_failed": "❌ Failed to delete folder: {path}",
        "patch_emu_git_clone_failed": "❌ Git clone failed",
        "patch_emu_git_apply_failed": "❌ Failed to apply patch",
        "patch_emu_git_applied": "✅ Patch successfully committed: {commit_msg}",
        "patch_emu_git_revision_failed": "⚠️ Failed to get Git revision: {error}",
        "patch_emu_git_revision": "🧾 Git revision: {sha}",
        "github_patch_uploaded": "✅ Patch successfully uploaded: {patch_version}",
        "github_upload_failed": "❌ GitHub upload failed.",
        "github_emu_git_uploaded": "✅ OSCam-Emu Git successfully uploaded!",
        "git_revision_failed": "⚠️ Git revision could not be determined: {error}",
        "github_emu_git_revision": "📊 Current Status: Revision {sha} ({commit_msg})",
        "github_upload_start": "🚀 GitHub upload started, please wait...",
        "github_emu_git_revision_failed": "⚠️ Could not retrieve revision: {error}",
        # online patch laden
        "online_patch_dl": "Get Online Patch",
        "patch_dl_title": "Patch Download",
        "patch_dl_select": "Select a patch (checking versions...):",
        "patch_dl_wait": "Checking patch versions on server...",
        "patch_dl_start": "Starting download from: ",
        "patch_dl_save": "Patch saved at: ",
        # Patch modifier
        "ok_button": "OK",
        "config_saved": "Settings updated",
        "auth_label": "Author",
        "repo_label": "Repository",
        "lang_label": "Language",
        "dir_label": "Patch Directory",
        "auto_update_label": "Auto-Update",
        "cancel_button": "Cancel",
        "mod_dialog_title": "Change Author",
        "mod_dialog_label": "Patch Author Name:",
        "mod_changed_success": "✅ Modifier changed to: {name}",
        "repo_dialog_title": "Repository Selection",
        "repo_dialog_label": "Select the desired Repo URL:",
        # Patch anwenden
        "executing_cmd": "Executing command:",
        "cmd_failed": "Command failed with exit code:",
        "executing_git_apply": "🚀 Applying patch: {patch}",
        "executing_git_check": "🔍 Checking patch compatibility: {patch}",
        # --- Patch Status ---
        # online check
        "net_check": "Checking internet connection...",
        "net_online": "Online",
        "net_offline": "Offline",
        "patch_file_missing": "❌ Patch file missing: {path}",
        "patch_emu_git_done": "🎉 OScam-Emu Git successfully patched!",
        "rev_label": "📝 Git Revision:",
        "patch_emu_git_apply_failed": "❌ Failed to apply patch!",
        # Tool Start
        "start": "Starting System-Check...",
        "found": "found",
        "missing": "MISSING!",
        "ready": "All required system tools are ready.",
        "upd_check": "🔍 Tooltest Update Check...",
        "up_to_date": "Plugin is up to date",
        "config": "🛠️ Active Configuration:",
        "author": "Patch Author",
        "repo": "Repository",
        "start_check": "Starting System-Check...",
        "found": "found",
        "missing": "MISSING!",
        "tools_ready": "All required system tools are ready.",
        "upd_check": "🔍 Tooltest Update Check...",
        "upd_ok": "Plugin is up to date",
        "active_conf": "🛠️ Active Configuration:",
        "patch_author": "Patch Author",
        "no_update_found": "No update available....",
        "upd_ok": "✅ Plugin is up to date",
        "upd_btn_current": "v{v} (Latest)",
        "upd_btn_new": "Update: v{v} available",
        "active_conf": "🛠️ Active Configuration:",
        "patch_author": "Patch Author",
        "repository": "Repository",
        "update_error": "Update check failed",
        "repository": "Repository",
        # change autor repo
        "config_saved": "Settings updated",
        "auth_label": "Author",
        "repo_label": "Repository",
        "start_check": "Starting system check...",
        "found": "found",
        "missing": "MISSING!",
        "upd_check": "🔍 Tooltest Update Check...",
        "info_title": "About OSCam Emu Toolkit",
        "mod_dialog_title": "Change Patch Author",
        "mod_dialog_label": "Author name:",
        # check box
        "stats_checkbox": "Stats",
        "stats_tooltip": "Allow/Disallow anonymous usage statistics (Hit-Counter).",
        # For the update check
        "new_version_available": "New version available",
        "update_title": "Update Available",
        "update_msg": "A new version was found. Do you want to update now?",
        # Exit / Confirmation
        "exit": "Exit",
        "yes": "Yes",
        "no": "No",
        "cancel": "Cancel",
        # "plugin_update": "Plugin Update",
        "btn_plugin_update": "Plugin Update",
        "state_plugin_uptodate": "Up to date",
        "check_tools_button": "🛠️ Check Tools",
        "new_version_label": "New",
        "old_version_label": "Installed",
        "upd_ok": "Plugin is up to date",
        "update_title": "Update Available",
        "update_msg": "A new version has been found. Do you want to update now?",
        "new_version_label": "New",
        "old_version_label": "Installed",
        "upd_ok": "Plugin is up to date",
        # "checking_tools": "Starting system check...",
        "state_plugin_update_available": "Update available: {current} → {latest}",
        "log_update_check_start": "Checking for updates …",
        "log_update_uptodate": "✅ Installed version: {version}",
        "log_update_declined": "Update skipped",
        "log_update_failed": "❌ Update check failed: {error}",
        "update_box_title": "Software Update",
        "update_box_msg": "A new version is available!\n\nNew: v{latest}\nCurrent: v{current}\n\nUpdate now?",
        "msg_update_available_title": "Update available",
        "msg_update_available_text": "A new version ({latest}) is available.\nCurrently installed: {current}.\nUpdate now?",
        "update_fail": "Update failed: {error}",
        "update_success": "✅ Update installed successfully! Please restart the tool.",
        "update_available_msg": "Current version: {current}\nNew version: {latest}",
        "restart_required_msg": "The update was installed successfully. The tool must be restarted.\nRestart now?",
        # "restart_tool_info": "ℹ️ Restarting application...",
        "restart_tool_cancelled": "ℹ️ Restart cancelled by user.",
        "update_started": "ℹ️ Update check started...",
        "update_backup_done": "✅ Old plugin files backed up.",
        "update_download_failed": "❌ Download failed: {error}",
        "update_extract_failed": "❌ Failed to extract new version: {error}",
        "update_done": "✅ Update to version {version} completed successfully.",
        "restart_tool": "Restart Tool",
        "update_check_done": "Done",
        "backup_created": "✅ Backup created: {file}",
        "exit_question": "Do you really want to close the tool?",
        "update_check_start": "Checking for updates ...",
        "github_version_available": "New version available: {version}",
        "github_version_fetch_failed": "Version check failed: {error}",
        # s3 install check

        "s3_install_button": "Install S3",
        "s3_tooltip": "Left-click: Install/Update\nRight-click: Select path manually",
        "restarting_check": "Restarting system check...",
        #s3 simplebuild
        "s3_choice_title": "Select S3 Simplebuild",
        "s3_choice_text": "Which S3 menu would you like to launch?",
        "s3_choice_info": (
            "Gorgone uses the 's3' folder.\n"
            "Speedy005 uses the 's3_speedy005' folder."
        ),
        "s3_choice_gorgone": "S3 Gorgone",
        "s3_choice_speedy005": "S3 Speedy005",
        "button_cancel": "Cancel",
        # s4 install check
        "s4_install_button": "Install S3",
        "s3_tooltip": "Left-click: Install/Update\nRight-click: Select path manually",
        "restarting_check": "Restarting system check...",
        # ... Log save ...
        "log_exported": "✅ Log exported to:",
        "log_save_error": "❌ Error saving log:",
        # Close Tool
        "info_title": "About this tool",
        "credits_label": "Credits / Authors",
        "close": "Close",
        # update on start
        "version_current": "Version {version} is up to date.",
        "update_check_failed": "Update check failed: {error}",
        "update_available_title": "Update Available",
        "update_no_update": "ℹ️ No update available",
        "installed_version": "Installed version is",
        "new_version_found": "New version available",
        # Option Buttons
        "git_status": "View Commits",
        "edit_patch_header": "Edit Patch Header",
        "github_emu_config_button": "Edit GitHub Config",
        "github_upload_patch": "Upload Patch File",
        "github_upload_emu": "Upload OSCam-Emu Git",
        "oscam_emu_git_patch": "OSCam EMU Git Patch",
        "oscam_emu_git_clear": "Clear OSCam EMU Git",
        "oscam_emu_patch_upload": "Upload OSCam EMU Patch",
        "version_current": "Version {version} is up to date.",
        "modifier_button_text": "👤 Patch Autor",
        "update_error": "Error checking for updates: {error}",
        "update_declined": "Update declined.",
        "update_current_version": "✅ Installed version: {version}",
        "restart_required_title": "Restart Required",
        "restart_required_msg": "The tool needs to be restarted, Restart now?",
        "yes": "Yes",
        "no": "No",
        "save": "Save",
        # patch ordner leeren
        "matrix_btn_exit": "🔙 EXIT MATRIX",
        # Statistik
        "STATS_TITLE": "TOOL STATISTICS",
        "STATS_GITHUB": "GitHub:",
        "STATS_LOCAL": "Local:",
        "STATS_TOTAL": "Total:",
        # ... deine anderen Einträge ...
        "foot_ok": "OK",
        "foot_ready": "Ready",
        "stats_title": "TOOL STATISTICS",
        "stats_github": "GitHub:",
        "stats_local": "Local:",
        "stats_total": "Total:",
        "temp_repo_deleted": "Temp repository deleted: {path}",
        "patch_file_deleted": "Patch file deleted: {path}",
        "temp_repo_already_deleted": "Temporary repository not found (already clean): {path}",
        # Labels
        "language_label": "Language:",
        "final_label": "🛠️ What are we building today?",
        "color_label": "Color",
        "commit_count_label": "Last Commits",
        "info_tooltip": "Info / Help",
        "restart_tool_question": "Do you want to restart the tool now?",
        # Info Text
        "info_text": (
            "This tool is a complete OSCam Emu Patch Manager.\n\n"
            "Features:\n"
            "- Create Patch: Generates a patch from the OSCam source code.\n"
            "- Renew Patch: Updates the existing patch.\n"
            "- Check Patch: Verifies if the patch can be applied correctly.\n"
            "- Apply Patch: Applies the patch to the local OSCam-Emu Git repository.\n"
            "- Zip Patch: Packs the patch into a ZIP file.\n"
            "- Backup Patch: Backs up the old patch and overwrites it with the new version.\n"
            "- Clean Patch Folder: Deletes temporary files in the patch folder (important files remain).\n"
            "- Patch OSCam-Emu Git: Applies the patch directly to the OSCam-Emu Git repository.\n"
            "- Clean OSCam-Emu Git: Deletes the local OSCam-Emu Git folder.\n"
            "- GitHub Upload: Uploads the patch or the OSCam-Emu Git folder to GitHub.\n"
            "- Manage GitHub Credentials: Configure username, token, repository URL, and branch.\n"
            "- Change Language and Color: Switch GUI language between English/German, change button/progressbar colors.\n"
            "- Progress Display: Shows action progress in the progress bar.\n"
            "- Show Commits: Displays the latest commits from the local repository.\n\n"
            "⚠️ Note: Only `oscam-emu.patch` is overwritten during patch upload; all other files remain untouched."
        ),
        # Patch creation
        "patch_create_start": "ℹ️ Patch creation started...",
        "patch_create_clone_start": "⚠️ Cloning git repository...",
        "patch_create_clone_failed": "❌ Failed to clone git repository",
        "patch_create_no_changes": "ℹ️ No changes found between STREAM_REPO and EMU_REPO",
        "patch_create_success": "✅ Patch successfully created: {patch_file}",
        "patch_version_from_header": "✅ Patch version from header: {patch_version}",
        "patch_create_failed": "❌ Patch creation failed: {error}",
        "plugin_update": "Update available: {current} → {latest}",
        "executing_git_apply": "🚀 Applying patch: {patch}",
        "executing_git_check": "🔍 Checking patch compatibility: {patch}",
        "check_commit_button": "🔄 Check for new commit",
        # Commits
        "loading_commits": "Lade Commits...",
        "commits_loaded": "Commits erfolgreich geladen",
        # Backup
        "backup_old_start": "ℹ️ Creating backup of old patch…",
        "backup_done": "✅ Backup successfully created: {path}",
        "update_downloading": "Downloading update...",
        "update_success_msg": "Update successful! The tool will now restart.",
        "no_old_patch": "ℹ️ No old patch found.",
        "new_patch_installed": "✅ New patch successfully installed: {path}",
        "patch_file_missing": "❌ Patch file missing: {path}",
        "patch_check_ok": "✅ Patch can be applied: no conflicts found",
        "github_dialog_title": "GitHub Emu Configuration",
        "patch_check_fail": "❌ Patch cannot be applied: conflicts or errors found",
        "patch_failed": "❌ Patch failed: {path}",
        # Oscam online check
        "oscam_uptodate": "OSCam Git is up to date.",
        "oscam_update_found": "Update available!",
        "oscam_check_start": "🔍 Checking OSCam Repository...",
        "oscam_server_error": "❌ Error: OSCam server not reachable.",
        # check for new commits
        "check_commit_button_short": "🔄 Check Commit",
        "check_commit_title": "OSCam Commit Check",
        "check_commit_current_hash": "Current Hash:",
        "check_commit_current": "Current Hash:",
        "check_commit_old": "Old Hash:",
        "check_commit_new": "New Hash:",
        "check_commit_no_hash": "Error: No commit hash found.",
        "check_commit_up_to_date": "No new commit found.",
        "check_commit_current": "Current status:",
        "check_commit_new_found": "New commit found!",
        "check_commit_new": "New:",
        "check_commit_old": "Old:",
        "check_commit_error": "Error during check:",
        "check_commit_button": "🔄 Check for new commit",
        "check_commit_tooltip": "Click here to check if a new commit is available in the Streamboard repository. If a new commit is found, the last commit hash will be displayed.",
        # patch erstellen
        "patch_creating": "🔨 Creating patch",
        "patch_created": "✅ Patch created",
        "patch_failed": "❌ Patch creation failed",

        "streamboard_preparing": "🔄 Preparing Streamboard",
        "stream_master_head": "Resolving exact {description} master HEAD (timeout per source: 35 s)...",
        "stream_source_retry": "Source unreachable, trying next source: {candidate} ({error})",
        "stream_source_check": "Checking Streamboard source: {url}",
        "stream_source_alternative": "Using alternative Streamboard source: {url}",
        "stream_source_failed": "Streamboard source failed: {url} ({error})",
        "streamboard_updated": "✅ Streamboard updated",
        "emu_updated": "✅ OSCam-Emu updated",
        "streamboard_imported": "✅ Streamboard revision imported",
        "patch_diff_created": "🔧 Patch diff created",
        "patch_checked": "✅ Patch successfully checked",
        "patch_header_created": "📝 Patch header inserted",
        # Clean Patch Folder
        "oscam_emu_git_missing": "⚠️ Folder not found: {path}",
        "clean_done": "✅ Cleanup completed successfully!",
        "oscam_emu_git_missing": "⚠️ Folder does not exist: {path}",
        "oscam_emu_git_patch_start": "🔹 Creating OSCam-Emu Git Patch...",
        "git_patch_success": "✅ Git Patch created successfully! Revision: {rev}",
        "git_patch_success": "✅ Patch created successfully! Git Revision: {rev}",
        "patch_version_from_header": "Patch version from header: {patch_version}",
        "patch_create_success": "Patch successfully created: {patch_file}",
        "cleaning_oscam_emu_git": "🔹 Emptying OSCam-Emu Git folder...",
        "oscam_emu_git_deleted": "✅ OSCam-Emu Git folder successfully deleted.",
        "oscam_emu_git_missing": "⚠️ OSCam-Emu Git folder not found: {path}",
        "delete_failed": "❌ Failed to delete: {path}",
        "oscam_emu_git_clearing": "🔹 Emptying OSCam-Emu Git folder...",
        "oscam_emu_git_cleared": "✅ Cleanup completed successfully!",
        "patch_check_ok": "✅ Patch check successful (Patch applies)! ",
        "patch_check_fail": "❌ Patch check failed (Patch does not apply)!",
        "patch_file_missing": "❌ Patch file not found!",
        "cleanup_start": "🔹 Cleaning up work directory...",
        "cleanup_success": "✅ Cleanup completed successfully! ✨",
        "delete_failed": "❌ Deletion failed: {path} - {error}",
        "patch_create_success": "✅ Patch created successfully: {patch_file}",
        "patch_create_failed": "❌ Error creating patch: {error}",
        "showing_commits": "ℹ️ Showing latest {count} commits",
        "copy_log_button": 'COPY LOG',
        "copy_log_tooltip": 'Copy all visible console output to the clipboard',
        "analyze_build_logs_button": 'ANALYZE BUILD LOG',
        "analyze_build_logs_tooltip": 'Check the newest build log for common errors and warnings',
        "diagnostics_button": 'SYSTEM DIAGNOSTICS',
        "diagnostics_tooltip": 'Check system, tool directories and existing build logs; does not start a build',
        "log_history_button": 'BUILD LOG HISTORY',
        "log_history_tooltip": 'Compare all build logs by status, time and error indicators',
        "clear_console_button": 'CLEAR CONSOLE',
        "clear_console_tooltip": 'Clear only the visible console output; log files remain unchanged',
        "cyber_center_button": 'OSCAM CONTROL CENTER',
        "cyber_center_tooltip": 'Central hub for all OSCam Control Center features',
        "patch_diff_button": 'COMPARE PATCHES',
        "patch_diff_tooltip": 'Compare two patch files or Git commits',
        "achievement_button": '🏆 ACHIEVEMENTS',
        "achievement_tooltip": 'View your OSCam achievements and progress',
        "ai_assistant_button": '🤖 AI ASSISTANT',
        "ai_assistant_tooltip": 'Open AI chat for patch analysis and troubleshooting',
        "music_player_button": '🎚 Open Player',
        "music_player_tooltip": 'Open the separate Cyber Music Player',
        'patch_copy_s3_ncam_tooltip': 'Copies oscam-emu.patch to the configured S3-NCam-Bonecrew patch folder.',
        'patch_copy_s4_tooltip': 'Copies oscam-emu.patch to the configured S4 patch folder.',
        'weather_button': '🌤 Show weather',
        'weather_tooltip': 'Show current weather and 5-day forecast',
        'log_button': '💾 Save Log',
        'log_tooltip': 'Saves the current log output to a file.',
        'music_button': '🎵 Music on',
        'music_tooltip': 'Toggle background music from the sounds folder.',
        'music_title_tooltip': 'Choose a music track',
        'oscam_source_button': 'OSCam Git URL',
        'oscam_source_tooltip': 'Choose source for Create Patch and OSCam-Emu-Git Patch',
        'console_panel_title': 'LIVE SYSTEM CONSOLE / STATUS & LOGS',
        "system_status": "SYSTEM STATUS:",
        "sound": "SOUND",
        "matrix_mode": "📟 MATRIX MODE",
        "theme_button": "🌓 THEME",
        "language_box_tooltip": "Choose the interface language",
        "commit_spin_tooltip": "Set the number of commits to display or analyze",
        'work_folder_button': 'Work Folder',
        'temp_repo_button': 'Temp Repo',
        'emu_git_button': 'Emu Git',
        'patch_online_button': '🌐 Load Patch',
    "commit_check_button": '🔄 Commit Check',
    "backup_button": '💾 Create Backup',
    "backup_tooltip": 'Creates backup/backup_gi.zip with the current project state',
    "settings_title": 'Settings',
    "patch_build_title": 'PATCH & BUILD',
        'loading_config': 'Loading configuration...',
        'config_ready': 'Configuration ready',
        'saved': 'Saved!',
        'github_config_saved': '✅ GitHub configuration saved.',
        'color_theme_tooltip': 'Choose the interface color theme',
        'live_system_monitor': 'LIVE | System Monitor',
        "music_on": '🎵 Music on',
        "music_off": '🎵 Music off',
        "music_toggle_tooltip": 'Toggle background music from the sounds folder.',
        'github_configuration_title': 'GitHub Configuration',
    },
    "de": {
        # Grid Buttons / Patch Aktionen
        
        "fix_perms": "Rechte fixen", 
        "fix_all_tool_permissions": "Rechte fixen", 
        "restart_tool_admin": "Mit Admin-Rechten neu starten",
        "backup_button_text": "💾 Backup erstellen",
        "patch_folder_s3_ncam": "S3-NCam Patch Pfad",
        "patch_folder_s4": "S4-Patch Pfad",
        "patch_copy_s3_ncam": "Patch zu S3-NCam",
        "patch_copy_s4": "Patch zu S4",
        "patch_folder_s3_ncam_tooltip": "S3-NCam-Bonecrew Patch-Ordner wählen",
        "patch_folder_s4_tooltip": "S4 Patch-Ordner wählen",
        "patch_create": "Emu Patch erstellen",
        "patch_renew": "Patch erneuern",
        "patch_check": "Patch prüfen",
        "patch_apply": "Patch anwenden",
        "patch_zip": "Patch zippen",
        "backup_old": "Patch zu S3 Ordner",
        "patch_creation_finished": "Patch-Erstellung beendet.",
        "clean_folder": "Patch Ordner leeren",
        "patch_path_label": "Patch speichern",
        "change_old_dir": "S3-Patch-Ordner",
        "oscam_emu_revision": "OSCam-Emu Revision",
        # Repository-Auswahl / Revision
        "select_repository": "Repository auswählen",
        "current_source": "Aktuelle Quelle",
        "select_repository_prompt": "Bitte ein Repository auswählen.",
        "no_repository_url": "Keine Repository-URL ausgewählt.",
        "working_tree_not_clean": "Das Arbeitsverzeichnis ist nicht sauber.",
        "select_revision": "Revision auswählen",
        "repository_load_failed": "Repository konnte nicht geladen werden.",
        "revision_load_failed": "Revisionen konnten nicht geladen werden.",
        # s3 auswahl
        "s3_choice_title": "S3 Simplebuild auswählen",
        "s3_choice_text": "Welches S3-Menü möchtest du starten?",
        "s3_choice_info": (
            "Gorgone verwendet den Ordner 's3'.\n"
            "Speedy005 verwendet den Ordner 's3_speedy005'."
        ),
        "s3_choice_gorgone": "S3 Gorgone",
        "s3_choice_speedy005": "S3 Speedy005",
        "button_cancel": "Abbrechen",
        # OSCam-Emu Git Patch
        "patch_emu_git_done": "🎉 OScam-Emu Git erfolgreich gepatcht!",
        "patch_emu_git_start": "🚀 Starte OScam-Emu Patch-Prozess...",
        "patch_emu_git_clone_failed": "❌ Fehler: Clone fehlgeschlagen!",
        "patch_emu_git_start": "🔹 OSCam-Emu Git Patch wird erstellt... (Pfad: {path})",
        "patch_emu_git_deleted": "✅ Alter OSCam-Emu Git Ordner gelöscht: {path}",
        "delete_failed": "❌ Löschen des Ordners fehlgeschlagen: {path}",
        "patch_emu_git_clone_failed": "❌ Git-Klon fehlgeschlagen",
        "patch_emu_git_apply_failed": "❌ Patch konnte nicht angewendet werden",
        "patch_emu_git_applied": "✅ Patch erfolgreich committet: {commit_msg}",
        "patch_emu_git_revision_failed": "⚠️ Git-Revision konnte nicht ermittelt werden: {error}",
        "patch_emu_git_done": "✅ Oscam Emu Git erfolgreich gepatcht",
        "edit_patch_header": "Edit Patch Header",
        "patch_emu_git_revision": "\U0001f4dd Git-Revision: {sha}",
        "patch_emu_git_start": "🚀 OSCam-Emu-Git Patch-Prozess wird gestartet...",
        "patch_emu_git_check_git": "🔎 Git wird geprüft...",
        "patch_emu_git_prepare": "🧹 Arbeitsumgebung wird vorbereitet...",
        "patch_emu_git_clone": "🌐 Streamboard wird geklont...",
        "patch_emu_git_head": "📌 Aktuellen Streamboard-Stand ermitteln...",
        "patch_emu_git_check_patch": "🔍 Patch wird geprüft...",
        "patch_emu_git_apply": "🔧 OSCam-Emu-Patch wird angewendet...",
        "patch_emu_git_status": "📋 Änderungen werden ermittelt...",
        "patch_emu_git_config": "👤 Git wird konfiguriert...",
        "patch_emu_git_commit": "💾 Patch wird committed...",
        "patch_emu_git_replace": "📦 Fertiges Repository wird übernommen...",
        "patch_emu_git_validate": "🔎 Repository wird geprüft...",
        "patch_emu_git_success": "✅ OSCam-Emu-Git erfolgreich gepatcht",
        "patch_emu_git_failed": "❌ OSCam-Emu-Git konnte nicht gepatcht werden",
        # Active autor repo
        "config_active_header": "🛠️ <b>Active Configuration:</b>",
        "current_author": "👤 Patch Author:",
        "current_repo": "🌐 Repository:",
        "settings_saved_info": "✅ Settings have been saved permanently.",
        # --- GitHub Dialog ---
        "github_dialog_title": "GitHub Configuration",
        "patch_repo_label": "Patch Repository:",
        "patch_branch_label": "Patch Branch:",
        "emu_repo_label": "EMU Repository:",
        "emu_branch_label": "EMU Branch:",
        "github_username_label": "GitHub User:",
        "github_token_label": "Token / PAT:",
        "github_user_name_label": "Git Name:",
        "github_user_email_label": "Git Email:",
        # Active autor repo
        "ok_button": "OK",
        "repo_dialog_title": "Repository Auswahl",
        "repo_dialog_label": "Wähle die gewünschte Repo-URL:",
        "cancel_button": "Abbrechen",
        "config_active_header": "🛠️ <b>Aktive Konfiguration:</b>",
        "current_author": "👤 Patch Autor:",
        "current_repo": "🌐 Repository:",
        "settings_saved_info": "✅ Einstellungen wurden dauerhaft gespeichert.",
        # change repo patch autor
        "config_saved": "Einstellungen aktualisiert",
        "auth_label": "Autor",
        "repo_label": "Repository",
        "start_check": "Starte System-Check...",
        "found": "gefunden",
        "missing": "FEHLT!",
        "upd_check": "🔍 Tooltest Update Check...",
        "info_title": "Über OSCam Emu Toolkit",
        "mod_dialog_title": "Patch Autor ändern",
        "mod_dialog_label": "Name des Autors:",
        # Matrix
        "matrix_system": "System",
        "matrix_engaged": "Wake up, Neo... Matrix Mode engaged. ■",
        "matrix_disabled": "Matrix Mode disabled.",
        "btn_matrix_on": "📟 MATRIX MODE",
        "btn_matrix_off": "🔙 EXIT MATRIX",
        "matrix_sys": "System",
        "matrix_on": "Wake up, Neo... Matrix Mode engaged. ■",
        "matrix_off": "Matrix Mode disabled.",
        "matrix_btn_enter": "📟 MATRIX MODE",
        "matrix_btn_exit": "🔙 EXIT MATRIX",
        # pacht erstellen
        "patch_creating": "🔨 Patch wird erstellt",
        "patch_created": "✅ Patch erstellt",
        "patch_failed": "❌ Patch-Erstellung fehlgeschlagen",
        "check_commit_button": "🔄 Check for new commit",
        "streamboard_preparing": "🔄 Streamboard wird vorbereitet",
        "stream_master_head": "Ermittle exakten {description} master-HEAD (Timeout je Quelle: 35 s)...",
        "stream_source_retry": "Quelle nicht erreichbar, nächste Quelle wird versucht: {candidate} ({error})",
        "stream_source_check": "Prüfe Streamboard-Quelle: {url}",
        "stream_source_alternative": "Alternative Streamboard-Quelle wird verwendet: {url}",
        "stream_source_failed": "Streamboard-Quelle fehlgeschlagen: {url} ({error})",
        "streamboard_updated": "✅ Streamboard aktualisiert",
        "emu_updated": "✅ OSCam-Emu aktualisiert",
        "streamboard_imported": "✅ Streamboard-Stand übernommen",
        "patch_diff_created": "🔧 Patch-Diff erstellt",
        "patch_checked": "✅ Patch erfolgreich geprüft",
        "patch_header_created": "📝 Patch-Header eingefügt",
        # Exit / Confirmation
        "exit": "Beenden",
        "yes": "Ja",
        "no": "Nein",
        "cancel": "Abbrechen",
        "github_upload_start": "🚀 GitHub Upload gestartet, bitte warten...",
        "github_config_load": "Lade GitHub-Konfiguration...",
        "github_emu_git_missing": "Fehler: GitHub-Konfigurationsdaten unvollständig (URL, Token oder User fehlen).",
        "patch_emu_git_missing": "Fehler: Lokaler Quellordner nicht gefunden: {path}",
        "git_repo_init": "Initialisiere neues Git-Repository im Zielordner...",
        "git_remote_add": "Verknüpfe lokales Repository mit GitHub...",
        "git_remote_update": "Aktualisiere Remote-Verbindung...",
        "git_fetching": "Hole aktuelle Daten vom GitHub-Repository...",
        "git_config_user": "Setze Git-Benutzerdaten ({user_name})...",
        "git_adding_files": "Indiziere Dateien für den Upload...",
        "git_committing": "Erstelle Commit...",
        "exit_question": "Möchten Sie das Tool wirklich schließen?",
        "update_current_version": "✅ Sie nutzen bereits die aktuelle Version: {version}",
        "update_started": "ℹ️ Update gestartet…",
        "backup_created": "✅ Backup erfolgreich erstellt: {file}",
        # "restart_tool_info": "ℹ️ Tool wird neu gestartet…",
        "restart_tool_cancelled": "ℹ️ Neustart vom Benutzer abgebrochen",
        "github_emu_git_uploaded": "✅ OSCam-Emu Git erfolgreich hochgeladen!",
        "github_emu_git_revision": "📊 Aktueller Stand: Revision {sha} ({commit_msg})",
        "github_emu_git_revision_failed": "⚠️ Revision konnte nicht ausgelesen werden: {error}",
        # oscam em git patch
        "patch_emu_git_start": "🚀 Starte OScam-Emu Patch-Prozess...\n📂 Pfad: {path}",
        "patch_emu_git_clone_failed": "❌ Fehler: Streamboard-Repository konnte nicht geklont werden!",
        "patch_file_missing": "⚠️ Fehler: Die Patch-Datei wurde nicht gefunden!",
        "patch_emu_git_apply_failed": "❌ Fehler: Der oscam-emu.patch konnte nicht angewendet werden!",
        "patch_emu_git_done": "🎉 OScam-Emu Git erfolgreich vorbereitet und lokal committed!",
        "patch_emu_git_done": "🎉 OScam-Emu Git erfolgreich gepatcht!",
        "rev_label": "📝 Git-Revision:",
        # Falls du weitere Keys aus der Log-Funktion brauchst:
        "git_rev_info": "📝 Git-Revision: {revision}",
        # online check
        "net_check": "Prüfe Internetverbindung...",
        "net_online": "Online",
        "net_offline": "Offline",
        # ... check tools first start ...
        "log_start_header": "--- OSCam Emu Patch Generator v{} ---",
        "log_sys_info": "System: {} {}",
        "log_dep_check": "Check: Git ({}), Patch ({}), Sound ({})",
        "log_status_ok": "Status: All dependencies loaded. Ready.",
        "ok": "OK",
        "missing": "MISSING",
        "active": "Active",
        "inactive": "Inactive",
        # --- Header & GroupBoxes ---
        "settings_header": "⚙️ Einstellungen",
        "github_config_header": "📁 GitHub Konfiguration",
        # Matrix mode
        "matrix_btn_exit": "🔙 MATRIX BEENDEN",
        # --- Labels ---
        "language_label": "Sprache:",
        "color_label": "Design / Farbe:",
        "commit_count_label": "Commits anzeigen:",
        # --- Buttons & Tooltips ---
        "modifier_button_text": "👤 Patch Autor",
        "modifier_tooltip_prefix": "Erstellt von:",
        "check_tools_button": "🛠️ Tools prüfen",
        # --- System-Check Log ---
        "start_check": "Starte System-Check...",
        "found": "OK",
        "missing": "FEHLT!",
        "net_check": "Prüfe Internetverbindung...",
        "net_online": "Online",
        "net_offline": "Offline",
        "upd_check": "🔍 Tool Update Check...",
        "final_label": "🛠️ Was bauen wir heute?",
        "language_done": "✅ Sprache umgestellt!",
        "language_switch": "Sprache wird angepasst...",
        "sound_active": "Aktiv",
        "sound_inactive": "Inaktiv",
        # --- Status Meldungen ---
        "status_up_to_date": "✅ OSCam ist aktuell",
        "status_update_avail": "🚀 Update verfügbar!",
        "welcome_msg": "Willkommen beim OSCam Emu Patch Generator!",
        # Patch anwenden
        "executing_cmd": "Führe Befehl aus:",
        "cmd_failed": "Befehl fehlgeschlagen mit Code:",
        "executing_git_apply": "🚀 Wende Patch an: {patch}",
        "executing_git_check": "🔍 Prüfe Patch-Kompatibilität: {patch}",
        # Oscam update check
        "oscam_uptodate": "OSCam Git ist aktuell.",
        "oscam_update_found": "Update verfügbar!",
        "oscam_check_start": "🔍 Prüfe OSCam Repository...",
        "oscam_server_error": "❌ Fehler: OSCam Server nicht erreichbar.",
        # --- Patch Status ---
        "patch_file_missing": "❌ Patch-Datei fehlt: {path}",
        "patch_emu_git_done": "✅ Patch erfolgreich angewendet!",
        "patch_emu_git_apply_failed": "❌ Patch konnte nicht angewendet werden!",
        # ... Log save ...
        "log_exported": "✅ Log exportiert nach:",
        "log_save_error": "❌ Fehler beim Speichern des Logs:",
        # ... zip_patch ...
        "patch_file_missing": "Patch-Datei existiert nicht: {path}",
        "zip_success": "✅ Patch erfolgreich gepackt: {zip_file}",
        "zip_failed": "❌ Fehler beim Zippen: {error}",
        "zip_file_already_deleted": "Kein ZIP-Archiv zum Löschen gefunden.",
        "zip_file_deleted": "ZIP-Archiv wurde gelöscht: {path}",
        # Close Tool
        "info_title": "Über dieses Tool",
        "credits_label": "Mitwirkende / Autoren",
        "close": "Schließen",
        # Online patch laden
        "online_patch_dl": "Online Patch laden",
        "patch_dl_title": "Patch Download",
        "patch_dl_select": "Wähle einen Patch (Versionen werden geprüft...):",
        "patch_dl_wait": "Prüfe Patch-Versionen am Server...",
        "patch_dl_start": "Starte Download von: ",
        "patch_dl_save": "Patch gespeichert unter: ",
        # Tool Start
        "start": "Starte System-Check...",
        "found": "gefunden",
        "missing": "FEHLT!",
        "ready": "Alle benötigten System-Tools sind bereit.",
        "upd_check": "🔍 Tooltest Update Check...",
        "up_to_date": "Plugin ist aktuell",
        "config": "🛠️ Aktive Konfiguration:",
        "author": "Patch Autor",
        "repo": "Repository",
        "start_check": "Starte System-Check...",
        "found": "gefunden",
        "missing": "FEHLT!",
        "tools_ready": "Alle benötigten System-Tools sind bereit.",
        "upd_check": "🔍 Tooltest Update Check...",
        "upd_ok": "Plugin ist aktuell",
        "active_conf": "🛠️ Aktive Konfiguration:",
        "patch_author": "Patch Autor",
        "repository": "Repository",
        # check box
        "stats_checkbox": "Stats",
        "stats_tooltip": "Anonyme Nutzungsstatistik (Hit-Counter) erlauben/verbieten.",
        # Für den Update-Check
        "new_version_available": "Neue Version verfügbar",
        "update_title": "Update verfügbar",
        "update_msg": "Eine neue Version wurde gefunden. Möchtest du jetzt aktualisieren?",
        "update_title": "Update verfügbar",
        "update_msg": "Eine neue Version wurde gefunden. Möchtest du jetzt aktualisieren?",
        "new_version_label": "Neu",
        "no_update_found": "Kein Update vorhanden....",
        "upd_ok": "✅ Plugin ist aktuell",
        "upd_btn_current": "v{v} (Aktuell)",
        "upd_btn_new": "Update: v{v} verfügbar",
        "active_conf": "🛠️ Aktive Konfiguration:",
        "patch_author": "Patch Autor",
        "repository": "Repository",
        "update_error": "Update-Check fehlgeschlagen",
        "old_version_label": "Installiert",
        "upd_ok": "Plugin ist aktuell",
        # Matrix
        "matrix_system": "System",
        "matrix_engaged": "Wake up, Neo... Matrix-Modus aktiviert. ■",
        "matrix_disabled": "Matrix-Mode deaktiviert.",
        "btn_matrix_on": "📟 MATRIX MODE",
        "btn_matrix_off": "🔙 EXIT MATRIX",
        "matrix_sys": "System",
        "matrix_on": "Wake up, Neo... Matrix-Modus aktiviert. ■",
        "matrix_off": "Matrix-Modus deaktiviert.",
        "matrix_btn_enter": "📟 MATRIX MODE",
        "matrix_btn_exit": "🔙 EXIT MATRIX",
        # Updates
        "restart_required_msg": "Das Update wurde erfolgreich installiert. Das Tool muss neu gestartet werden.\nJetzt neu starten?",
        "restart_required_title": "Neustart erforderlich",
        "update_success": "✅ Update erfolgreich! Bitte Plugin neu starten.",
        "update_fail": "Update fehlgeschlagen: {error}",
        "update_not_available": "Keine neue Version verfügbar.",
        "update_check_start": "Prüfe auf Updates ...",
        "github_version_available": "Neue Version {version} auf GitHub verfügbar",
        "github_version_fetch_failed": "⚠️ Fehler beim Abrufen der GitHub-Version: {error}",
        "plugin_update": "Update verfügbar: {current} → {latest}",
        "btn_plugin_update": "Plugin Update",
        "update_check_done": "Fertig",
        "state_plugin_uptodate": "Bereits aktuell",
        "state_plugin_update_available": "Update verfügbar: {current} → {latest}",
        "log_update_check_start": "Prüfe auf Updates …",
        "log_update_uptodate": "✅ Installierte Version: {version}",
        "log_update_declined": "Update übersprungen",
        "log_update_failed": "❌ Update-Prüfung fehlgeschlagen: {error}",
        "msg_update_available_title": "Update verfügbar",
        "new_version_label": "Neu",
        "old_version_label": "Installiert",
        "upd_ok": "Plugin ist aktuell",
        "update_done": "✅ Update auf Version {version} erfolgreich abgeschlossen.",
        "update_backup_done": "✅ Backup der alten Plugin-Dateien erstellt.",
        "msg_update_available_text": "Eine neue Version ({latest}) ist verfügbar.\nAktuell installiert: {current}.\nJetzt updaten?",
        # check for new commits
        "check_commit_button_short": "🔄 Commit Check",
        "check_commit_current_hash": "Aktueller Hash:",
        "check_commit_current": "Aktueller Hash:",
        "check_commit_new": "Neuer Hash:",
        "check_commit_title": "OSCam Commit-Check",
        "check_commit_no_hash": "Fehler: Kein Commit-Hash gefunden.",
        "check_commit_up_to_date": "Kein neuer Commit vorhanden.",
        "check_commit_current": "Aktueller Stand:",
        "check_commit_new_found": "Neuer Commit gefunden!",
        "check_commit_new": "Neu:",
        "check_commit_old": "Alt:",
        "check_commit_error": "Fehler beim Check:",
        "check_commit_button": "🔄 Prüfe auf neuen Commit",
        "check_commit_tooltip": "Klicke hier, um zu prüfen, ob ein neuer Commit im Streamboard-Repository vorhanden ist. Falls ein neuer Commit vorhanden ist, wird der Hash des letzten Commits angezeigt.",
        # Option Buttons
        "git_status": "Commits anzeigen",
        "restart_tool": "Tool Neustarten",
        "edit_patch_header": "Patch Header bearbeiten",
        "github_emu_config_button": "GitHub-Konfiguration",
        "github_upload_patch": "Patch hochladen",
        "github_upload_emu": "EMU Git hochladen",
        "oscam_emu_git_patch": "OSCam EMU Git Patch",
        "oscam_emu_git_clear": "OSCam EMU Git leeren",
        "update_available_title": "Update verfügbar",
        "modifier_button_text": "👤 Patch Autor",
        "update_current_version": "✅ Installierte Version: {version}",
        "update_check_failed": "Fehler bei Updateprüfung: {error}",
        "update_available_msg": "Aktuelle Version: {current}\nNeue Version: {latest}",
        "update_success": "✅ Update erfolgreich installiert! Bitte Tool neu starten.",
        "version_current": "Version {version} ist aktuell.",
        "update_error": "Fehler bei Updateprüfung: {error}",
        "update_box_title": "Software Update",
        "update_box_msg": "Eine neue Version ist verfügbar!\n\nNeu: v{latest}\nAktuell: v{current}\n\nJetzt aktualisieren?",
        "update_declined": "Update abgebrochen.",
        "update_no_update": "ℹ️ Kein Update vorhanden",
        "tools_ok": "✅ Alle benötigten System-Tools sind bereits installiert.",
        "tools_missing": "⚠️ Folgende Tools fehlen: {tools}. Installation wird vorbereitet...",
        "check_tools_button": "🛠️ Tools prüfen",
        "checking_tools": "Starte System-Check...",
        "restart_required_title": "Neustart erforderlich",
        "restart_tool_question": "Möchten Sie das Tool jetzt neu starten?",
        "patch_emu_git_success": "✅ OSCam Emu Git successfully patched",
        "restart_required_msg": "Das Tool muss neu gestartet werden. Jetzt neu starten?",
        "yes": "Ja",
        "no": "Nein",
        "Yes": "Ja",
        "No": "Nein",
        "installed_version": "Installierte Version ist",
        "new_version_found": "Neue Version verfügbar",
        "oscam_emu_patch_upload": "OSCam EMU Patch hochladen",
        # s4 install
        "s4_install_button": "S4 Installieren",
        "s4_tooltip": "Linksklick: Install/Update\nRechtsklick: Pfad manuell wählen",
        "restarting_check": "System-Check wird neu gestartet...",
        "s4_ok": "S4 OK",
        "s4_install": "S4 Installieren",
        # s3 install
        "s3_install_button": "S3 Installieren",
        "s3_tooltip": "Linksklick: Install/Update\nRechtsklick: Pfad manuell wählen",
        "restarting_check": "System-Check wird neu gestartet...",
        "s3_ok": "S3 OK",
        "s3_install": "S3 Installieren",
        # Labels
        "mod_dialog_title": "Modifier ändern",
        "mod_dialog_label": "Name des Patch-Erstellers:",
        "mod_changed_success": "✅ Modifier geändert zu: {name}",
        # "language_label": "Sprache:",
        "language_label": "Sprache:",
        "color_label": "Style:",
        "commit_count_label": "Anzahl Commits",
        "settings_header": "Einstellungen",
        "info_tooltip": "Info / Hilfe",
        # Info Text
        "info_text": (
            "Dieses Tool ist ein umfassender OSCam Emu Patch Manager.\n\n"
            "Funktionen:\n"
            "- Patch erstellen: Erstellt den Patch aus OSCam-Quellcode.\n"
            "- Patch erneuern: Aktualisiert den bestehenden Patch.\n"
            "- Patch prüfen: Überprüft, ob der Patch korrekt angewendet werden kann.\n"
            "- Patch anwenden: Wendet den Patch auf das lokale OSCam-Emu Git-Repository an.\n"
            "- Patch zippen: Packt den Patch in eine ZIP-Datei.\n"
            "- Patch sichern: Sichert die alte Patch-Datei und überschreibt sie mit der neuen Version.\n"
            "- Patch-Ordner leeren: Löscht temporäre Dateien im Patch-Ordner (wichtige Dateien bleiben erhalten).\n"
            "- OSCam-Emu Git patchen: Wendet den Patch direkt auf das OSCam-Emu Git-Repository an.\n"
            "- OSCam-Emu Git bereinigen: Löscht das lokale OSCam-Emu Git-Verzeichnis.\n"
            "- GitHub Upload: Upload des Patches oder des OSCam-Emu Git-Ordners auf GitHub.\n"
            "- GitHub Konfiguration verwalten: Benutzername, Token, Repository-URL und Branch anpassen.\n"
            "- Sprache und Farbe anpassen: GUI-Sprache zwischen Deutsch/Englisch wechseln, Farben für Buttons/Progressbar ändern.\n"
            "- Fortschrittsanzeige: Fortschritt von Aktionen in der Progressbar sichtbar.\n"
            "- Commit-Anzeige: Zeigt die letzten Commits aus dem lokalen Repository an.\n\n"
            "⚠️ Hinweis: Beim Patch-Upload wird nur `oscam-emu.patch` überschrieben; andere Dateien bleiben unverändert."
        ),
        # Patch creation
        "patch_create_start": "ℹ️ Patch-Erstellung gestartet...",
        "patch_create_clone_start": "⚠️ TEMP_REPO existiert nicht, Repository wird geklont...",
        "patch_create_clone_failed": "❌ Klonen fehlgeschlagen, Patch-Erstellung abgebrochen.",
        "patch_create_no_changes": "ℹ️ Keine Änderungen zwischen STREAM_REPO und EMU_REPO gefunden",
        "patch_create_success": "✅ Patch erfolgreich erstellt: {patch_file}",
        "patch_version_from_header": "✅ Patch-Version aus Header: {patch_version}",
        "patch_create_failed": "❌ Patch-Erstellung fehlgeschlagen: {error}",
        "git_patch_success": "✅ Git Patch erfolgreich erstellt! Revision: {rev}",
        # Statistik
        "STATS_TITLE": "TOOL STATISTIK",
        "STATS_GITHUB": "GitHub:",
        "STATS_LOCAL": "Lokal:",
        "STATS_TOTAL": "Gesamt:",
        "foot_ok": "OK",
        "foot_ready": "Bereit",
        "stats_title": "TOOL STATISTIK",
        "stats_github": "GitHub:",
        "stats_local": "Lokal:",
        "stats_total": "Gesamt:",
        # Patch ordner leeren
        "temp_patch_git_already_deleted": "Patch-Git-Ordner war bereits gelöscht oder nicht vorhanden.",
        "patch_file_deleted": "Patch-Datei wurde erfolgreich entfernt: {path}",
        "patch_file_already_deleted": "Keine Patch-Datei zum Löschen gefunden: {path}",
        "clean_done": "Bereinigung des Patch Temp Ordners erfolgreich abgeschlossen! ✨",
        "oscam_emu_git_missing": "⚠️ Ordner nicht gefunden: {path}",
        "temp_repo_deleted": "Temporäres Repository erfolgreich gelöscht: {path}",
        "oscam_emu_git_patch_start": "🔹 OSCam-Emu Git Patch wird erstellt...",
        "patch_file_deleted": "Patch-Datei gelöscht: {path}",
        "cleaning_oscam_emu_git": "🔹 OSCam-Emu Git Ordner wird geleert...",
        "oscam_emu_git_deleted": "✅ OSCam-Emu Git Ordner erfolgreich gelöscht.",
        "oscam_emu_git_missing": "⚠️ OSCam-Emu Git Ordner nicht gefunden: {path}",
        "delete_failed": "❌ Fehler beim Löschen: {path}",
        "patch_emu_git_success": "✅ OSCam Emu Git erfolgreich gepatcht",
        # "zip_file_deleted": "ZIP-Archiv entfernt: {path}",
        # Backup
        "backup_old_start": "ℹ️ Erstelle Backup des alten Patches…",
        "backup_done": "✅ Backup erfolgreich erstellt: {path}",
        "tools_missing": "⚠️ Folgende Tools fehlen: {tools}. Installation wird vorbereitet...",
        "checking_tools": "Starte System-Check...",
        "no_old_patch": "ℹ️ Keine alte Patch-Datei gefunden.",
        "new_patch_installed": "✅ Neuer Patch erfolgreich installiert: {path}",
        "patch_file_missing": "❌ Patch-Datei fehlt: {path}",
        "update_downloading": "Lade Update herunter...",
        "update_success_msg": "Update erfolgreich! Das Tool wird nun neu gestartet.",
        "github_dialog_title": "GitHub Emu Konfiguration",
        "patch_check_ok": "✅ Patch kann angewendet werden: keine Konflikte gefunden",
        "patch_check_fail": "❌ Patch kann nicht angewendet werden: Konflikte vorhanden oder Fehler",
        "patch_failed": "❌ Patch-Erstellung fehlgeschlagen",
        # Github config
        "github_dialog_title": "GitHub Konfiguration",
        "patch_repo_label": "Patch Repository:",
        "patch_branch_label": "Patch Branch:",
        "emu_repo_label": "EMU Repository:",
        "emu_branch_label": "EMU Branch:",
        "github_username_label": "GitHub Benutzer:",
        "github_token_label": "GitHub Token:",
        "github_user_name_label": "Git Name:",
        "github_user_email_label": "Git E-Mail:",
        "save": "Speichern",
        "github_config_saved": "✅ GitHub Konfiguration gespeichert.",
        "executing_git_apply": "🚀 Wende Patch an: {patch}",
        "executing_git_check": "🔍 Prüfe Patch-Kompatibilität: {patch}",
        # Clean Patch Folder
        "oscam_emu_git_missing": "⚠️ Ordner nicht gefunden: {path}",
        "delete_failed": "❌ Fehler: Konnte {path} nicht löschen. Fehler: {error}",
        "git_patch_success": "✅ Patch erfolgreich erstellt! Git Revision: {rev}",
        "oscam_emu_git_missing": "⚠️ Ordner existiert nicht: {path}",
        "delete_failed": "❌ Löschen fehlgeschlagen: {path} (Fehler: {error})",
        "github_patch_uploaded": "✅ Patch erfolgreich hochgeladen: {patch_version}",
        "github_upload_failed": "❌ Fehler beim Hochladen auf GitHub.",
        "patch_version_from_header": "Patch-Version aus Header: {patch_version}",
        "patch_create_success": "Patch erfolgreich erstellt: {patch_file}",
        "oscam_emu_git_clearing": "🔹 OSCam-Emu Git Ordner wird geleert...",
        "oscam_emu_git_cleared": "✅ Bereinigung erfolgreich abgeschlossen!",
        "patch_check_ok": "✅ Patch-Check erfolgreich (Patch passt)! ",
        "patch_check_fail": "❌ Patch-Check fehlgeschlagen (Patch passt nicht)!",
        "patch_file_missing": "❌ Patch-Datei nicht gefunden!",
        "cleanup_start": "🔹 Bereinigung des Arbeitsverzeichnisses...",
        "cleanup_success": "✅ Bereinigung erfolgreich abgeschlossen! ✨",
        "delete_failed": "❌ Löschen fehlgeschlagen: {path} - {error}",
        "patch_create_success": "✅ Patch erfolgreich erstellt: {patch_file}",
        "patch_create_failed": "❌ Fehler beim Erstellen des Patches: {error}",
        "showing_commits": "ℹ️ Zeige die letzten {count} Commits",
        "copy_log_button": 'LOG KOPIEREN',
        "copy_log_tooltip": 'Gesamte sichtbare Konsolenausgabe in die Zwischenablage kopieren',
        "analyze_build_logs_button": 'BUILD-LOG ANALYSIEREN',
        "analyze_build_logs_tooltip": 'Das neueste Build-Protokoll auf typische Fehler und Warnungen prüfen',
        "diagnostics_button": 'SYSTEM-DIAGNOSE',
        "diagnostics_tooltip": 'System, Tool-Verzeichnisse und vorhandene Build-Logs prüfen; startet keinen Build',
        "log_history_button": 'BUILD-LOG-VERLAUF',
        "log_history_tooltip": 'Alle Build-Logs nach Status, Zeit und Fehlerhinweisen vergleichen',
        "clear_console_button": 'KONSOLE LEEREN',
        "clear_console_tooltip": 'Nur die sichtbare Konsolenausgabe leeren; Logdateien bleiben unverändert',
        "cyber_center_button": 'OSCAM CONTROL CENTER',
        "cyber_center_tooltip": 'Zentrale für alle OSCam-Control-Center-Funktionen',
        "patch_diff_button": 'PATCH VERGLEICHEN',
        "patch_diff_tooltip": 'Zwei Patch-Dateien oder Git-Commits vergleichen',
        "achievement_button": '🏆 ERFOLGE',
        "achievement_tooltip": 'Deine OSCam-Erfolge und Fortschritte anzeigen',
        "ai_assistant_button": '🤖 KI-ASSISTENT',
        "ai_assistant_tooltip": 'KI-Chat für Patch-Analyse und Fehlersuche öffnen',
        "music_player_button": '🎚 Player öffnen',
        "music_player_tooltip": 'Separaten Cyber Music Player öffnen',
        'patch_copy_s3_ncam_tooltip': 'Kopiert oscam-emu.patch in den konfigurierten S3-NCam-Bonecrew-Patch-Ordner.',
        'patch_copy_s4_tooltip': 'Kopiert oscam-emu.patch in den konfigurierten S4-Patch-Ordner.',
        'weather_button': '🌤 Wetter anzeigen',
        'weather_tooltip': 'Aktuelles Wetter und 5-Tage-Vorhersage anzeigen',
        'log_button': '💾 Log speichern',
        'log_tooltip': 'Speichert den aktuellen Log-/Protokollinhalt in einer Datei.',
        'music_button': '🎵 Musik einschalten',
        'music_tooltip': 'Hintergrundmusik aus dem Ordner sounds ein- oder ausschalten.',
        'music_title_tooltip': 'Musiktitel auswählen',
        'oscam_source_button': 'OSCam Git URL',
        'oscam_source_tooltip': 'Quelle für Create Patch und OSCam-Emu-Git-Patch auswählen',
        'console_panel_title': 'LIVE-SYSTEMKONSOLE / STATUS & PROTOKOLLE',
        "system_status": "SYSTEMSTATUS:",
        "sound": "TON",
        "matrix_mode": "📟 MATRIX-MODUS",
        "theme_button": "🌓 DESIGN",
        "language_box_tooltip": "Sprache der Oberfläche auswählen",
        "commit_spin_tooltip": "Anzahl der Commits für Anzeige und Auswertung festlegen",
        'work_folder_button': 'Arbeitsordner',
        'temp_repo_button': 'Temp-Repo',
        'emu_git_button': 'Emu-Git',
        'patch_online_button': '🌐 Patch online',
    "commit_check_button": '🔄 Commit prüfen',
    "backup_button": '💾 Backup erstellen',
    "backup_tooltip": 'Erstellt backup/backup_gi.zip mit dem aktuellen Projektstand',
    "settings_title": 'Einstellungen',
    "patch_build_title": 'PATCH & BUILD',
        'loading_config': 'Konfiguration wird geladen...',
        'config_ready': 'Konfiguration bereit',
        'saved': 'Gespeichert!',
        'color_theme_tooltip': 'Farbschema der Oberfläche auswählen',
        'live_system_monitor': 'LIVE | Systemmonitor',
        "music_on": '🎵 Musik einschalten',
        "music_off": '🎵 Musik ausschalten',
        "music_toggle_tooltip": 'Hintergrundmusik aus dem Ordner sounds ein- oder ausschalten.',
        'github_configuration_title': 'GitHub-Konfiguration',
    },
}

# Traduzioni: italiano; le chiavi non ancora tradotte usano l'inglese come fallback.
TEXTS["it"] = dict(TEXTS["en"])

TEXTS["gr"] = dict(TEXTS["en"])
TEXTS["gr"].update({'fix_permissions': 'Διόρθωση δικαιωμάτων', 'restart_tool_admin': 'Επανεκκίνηση με δικαιώματα διαχειριστή', 'backup_button_text': '💾 Δημιουργία αντιγράφου ασφαλείας', 'patch_create': 'Δημιουργία patch', 'patch_renew': 'Ανανέωση patch', 'patch_check': 'Έλεγχος patch', 'settings_header': '⚙️ Ρυθμίσεις', 'patch_folder_s3_ncam': 'Διαδρομή patch S3-NCam', 'patch_folder_s4': 'Διαδρομή patch S4', 'patch_copy_s3_ncam': 'Αντιγραφή patch στο S3-NCam', 'patch_copy_s4': 'Αντιγραφή patch στο S4', 'patch_folder_s3_ncam_tooltip': 'Επιλογή φακέλου patch S3-NCam-Bonecrew', 'patch_folder_s4_tooltip': 'Επιλογή φακέλου patch S4', 'select_repository': 'Επιλογή αποθετηρίου', 'current_source': 'Τρέχουσα πηγή', 'select_repository_prompt': 'Παρακαλώ επιλέξτε ένα αποθετήριο.', 'no_repository_url': 'Δεν έχει επιλεγεί διεύθυνση URL αποθετηρίου.', 'working_tree_not_clean': 'Το δέντρο εργασίας δεν είναι καθαρό.', 'select_revision': 'Επιλογή αναθεώρησης', 'repository_load_failed': 'Η φόρτωση του αποθετηρίου απέτυχε.', 'revision_load_failed': 'Η φόρτωση των αναθεωρήσεων απέτυχε.', 'patch_apply': 'Εφαρμογή patch', 'patch_path_label': 'Αποθήκευση patch', 'patch_zip': 'Συμπίεση patch σε ZIP', 'backup_old': 'Αντίγραφο ασφαλείας / Ανανέωση S3 patch', 'clean_folder': 'Καθαρισμός φακέλου patch', 'change_old_dir': 'Επιλογή φακέλου S3 patch', 'oscam_emu_revision': 'Αναθεώρηση OSCam-Emu', 'loading_commits': 'Φόρτωση commits...', 'commits_loaded': 'Τα commits φορτώθηκαν με επιτυχία', 'github_config_load': 'Φόρτωση ρυθμίσεων GitHub...', 'github_emu_git_missing': 'Σφάλμα: Οι ρυθμίσεις GitHub είναι ελλιπείς (λείπει URL, token ή χρήστης).', 'patch_emu_git_missing': 'Σφάλμα: Δεν βρέθηκε ο τοπικός φάκελος πηγής: {path}', 'git_repo_init': 'Αρχικοποίηση νέου αποθετηρίου Git στον φάκελο προορισμού...', 'git_remote_add': 'Σύνδεση του τοπικού αποθετηρίου με το GitHub...', 'git_remote_update': 'Ενημέρωση απομακρυσμένης σύνδεσης...', 'git_fetching': 'Λήψη των τρεχόντων δεδομένων από το αποθετήριο GitHub...', 'plugin_uptodate': '✅ Το πρόσθετο είναι ενημερωμένο (Έκδοση: {current})', 'tools_ok': '✅ Όλα τα απαιτούμενα εργαλεία συστήματος είναι ήδη εγκατεστημένα.', 'checking_tools': 'Έναρξη ελέγχου εργαλείων συστήματος...', 'git_config_user': 'Ρύθμιση στοιχείων χρήστη Git ({user_name})...', 'git_adding_files': 'Προσθήκη αρχείων για μεταφόρτωση...', 'git_committing': 'Δημιουργία commit...', 'github_upload_start': '🚀 Η μεταφόρτωση στο GitHub ξεκίνησε, παρακαλώ περιμένετε...', 'github_emu_git_uploaded': '✅ Το OSCam-Emu Git μεταφορτώθηκε με επιτυχία!', 'github_emu_git_revision': '📊 Τρέχουσα κατάσταση: Αναθεώρηση {sha} ({commit_msg})', 'github_upload_failed': '❌ Η μεταφόρτωση στο GitHub απέτυχε.', 'log_start_header': '--- OSCam Emu Patch Generator v{} ---', 'log_sys_info': 'Σύστημα: {} {}', 'log_dep_check': 'Έλεγχος: Git ({}), Patch ({}), Ήχος ({})', 'log_status_ok': 'Κατάσταση: Όλες οι εξαρτήσεις φορτώθηκαν. Έτοιμο.', 'ok': 'OK', 'language_done': '✅ Η γλώσσα άλλαξε!', 'language_switch': 'Αλλαγή γλώσσας...', 'missing': 'ΛΕΙΠΕΙ!', 'active': 'Ενεργό', 'inactive': 'Ανενεργό', 'github_config_header': '📁 Ρυθμίσεις GitHub', 'language_label': 'Γλώσσα:', 'color_label': 'Χρώμα', 'commit_count_label': 'Τελευταία commits', 'modifier_button_text': '👤 Συντάκτης patch', 'modifier_tooltip_prefix': 'Δημιουργήθηκε από:', 'check_tools_button': '🛠️ Έλεγχος εργαλείων', 'start_check': 'Έναρξη ελέγχου συστήματος...', 'found': 'Βρέθηκε', 'net_check': 'Έλεγχος σύνδεσης στο διαδίκτυο...', 'net_online': 'Σε σύνδεση', 'net_offline': 'Εκτός σύνδεσης', 'upd_check': '🔍 Έλεγχος ενημέρωσης εργαλείου...', 'sound_active': 'Ενεργός', 'sound_inactive': 'Ανενεργός', 'status_up_to_date': '✅ Το OSCam είναι ενημερωμένο', 'status_update_avail': '🚀 Υπάρχει διαθέσιμη ενημέρωση!', 'welcome_msg': 'Καλώς ήρθατε στο OSCam Emu Patch Generator!'})

TEXTS["gr"].update({'patch_file_missing': '❌ Δεν βρέθηκε το αρχείο patch!', 'zip_success': '✅ Το patch συμπιέστηκε με επιτυχία: {zip_file}', 'zip_failed': '❌ Σφάλμα κατά τη συμπίεση: {error}', 'patch_creation_finished': 'Η δημιουργία του patch ολοκληρώθηκε.', 'patch_emu_git_start': '🔹 Δημιουργία patch OSCam-Emu Git... (Διαδρομή: {path})', 'patch_emu_git_check_git': '🔎 Έλεγχος Git...', 'patch_emu_git_prepare': '🧹 Προετοιμασία χώρου εργασίας...', 'patch_emu_git_clone': '🌐 Κλωνοποίηση Streamboard...', 'patch_emu_git_head': '📌 Εντοπισμός της τρέχουσας αναθεώρησης Streamboard...', 'patch_emu_git_check_patch': '🔍 Έλεγχος patch...', 'patch_emu_git_apply': '🔧 Εφαρμογή patch OSCam-Emu...', 'patch_emu_git_status': '📋 Έλεγχος αλλαγών...', 'patch_emu_git_config': '👤 Ρύθμιση Git...', 'patch_emu_git_commit': '💾 Δημιουργία commit...', 'patch_emu_git_replace': '📦 Εγκατάσταση τροποποιημένου αποθετηρίου...', 'patch_emu_git_validate': '🔎 Επικύρωση αποθετηρίου...', 'patch_emu_git_success': '✅ Το OSCam-Emu Git τροποποιήθηκε με επιτυχία', 'patch_emu_git_failed': '❌ Η τροποποίηση του OSCam-Emu Git απέτυχε', 'patch_emu_git_done': '🎉 Το OSCam-Emu Git τροποποιήθηκε με επιτυχία!', 'patch_emu_git_clone_failed': '❌ Η κλωνοποίηση Git απέτυχε', 'patch_emu_git_deleted': '✅ Ο παλιός φάκελος OSCam-Emu Git διαγράφηκε: {path}', 'delete_failed': '❌ Η διαγραφή απέτυχε: {path} - {error}', 'patch_emu_git_apply_failed': '❌ Η εφαρμογή του patch απέτυχε!', 'patch_emu_git_applied': '✅ Το patch έγινε commit με επιτυχία: {commit_msg}', 'patch_emu_git_revision_failed': '⚠️ Αποτυχία λήψης αναθεώρησης Git: {error}', 'patch_emu_git_done': '✅ Το OSCam-Emu Git τροποποιήθηκε με επιτυχία', 'patch_emu_git_revision': '🧾 Αναθεώρηση Git: {sha}', 'github_patch_uploaded': '✅ Το patch μεταφορτώθηκε με επιτυχία: {patch_version}', 'git_revision_failed': '⚠️ Δεν ήταν δυνατός ο προσδιορισμός της αναθεώρησης Git: {error}', 'github_emu_git_revision_failed': '⚠️ Δεν ήταν δυνατή η ανάκτηση της αναθεώρησης: {error}', 'online_patch_dl': 'Λήψη patch από το διαδίκτυο', 'patch_dl_title': 'Λήψη patch', 'patch_dl_select': 'Επιλέξτε patch (έλεγχος εκδόσεων...)', 'patch_dl_wait': 'Έλεγχος εκδόσεων patch στον διακομιστή...', 'patch_dl_start': 'Έναρξη λήψης από: ', 'patch_dl_save': 'Το patch αποθηκεύτηκε στη θέση: ', 'ok_button': 'OK', 'config_saved': 'Οι ρυθμίσεις ενημερώθηκαν', 'auth_label': 'Συντάκτης', 'repo_label': 'Αποθετήριο', 'lang_label': 'Γλώσσα', 'dir_label': 'Κατάλογος patch', 'auto_update_label': 'Αυτόματη ενημέρωση', 'cancel_button': 'Ακύρωση', 'mod_dialog_title': 'Αλλαγή συντάκτη patch', 'mod_dialog_label': 'Όνομα συντάκτη:', 'mod_changed_success': '✅ Ο συντάκτης άλλαξε σε: {name}', 'repo_dialog_title': 'Επιλογή αποθετηρίου', 'repo_dialog_label': 'Επιλέξτε την επιθυμητή διεύθυνση URL αποθετηρίου:', 'executing_cmd': 'Εκτέλεση εντολής:', 'cmd_failed': 'Η εντολή απέτυχε με κωδικό εξόδου:', 'executing_git_apply': '🚀 Εφαρμογή patch: {patch}', 'executing_git_check': '🔍 Έλεγχος συμβατότητας patch: {patch}', 'rev_label': '📝 Αναθεώρηση Git:', 'start': 'Έναρξη ελέγχου συστήματος...', 'ready': 'Όλα τα απαιτούμενα εργαλεία συστήματος είναι έτοιμα.', 'up_to_date': 'Το πρόσθετο είναι ενημερωμένο', 'config': '🛠️ Ενεργή διαμόρφωση:', 'author': 'Συντάκτης patch', 'repo': 'Αποθετήριο', 'tools_ready': 'Όλα τα απαιτούμενα εργαλεία συστήματος είναι έτοιμα.', 'upd_ok': 'Το πρόσθετο είναι ενημερωμένο', 'active_conf': '🛠️ Ενεργή διαμόρφωση:', 'patch_author': 'Συντάκτης patch', 'no_update_found': 'Δεν υπάρχει διαθέσιμη ενημέρωση....', 'upd_btn_current': 'v{v} (Τελευταία έκδοση)', 'upd_btn_new': 'Ενημέρωση: διαθέσιμη η έκδοση v{v}', 'foot_ok': 'OK', 'stats_github': 'GitHub:', 'info_tooltip': 'Πληροφορίες / Βοήθεια', 'final_label': '🛠️ Τι θα δημιουργήσουμε σήμερα;', 'restart_tool_question': 'Θέλετε να επανεκκινήσετε το εργαλείο τώρα;', 'clean_done': '✅ Ο καθαρισμός ολοκληρώθηκε με επιτυχία!', 'cleanup_success': '✅ Ο καθαρισμός ολοκληρώθηκε με επιτυχία! ✨'})

TEXTS["it"].update({'fix_permissions': 'Correggi permessi', 'restart_tool_admin': 'Riavvia con privilegi di amministratore', 'backup_button_text': '💾 Crea backup', 'patch_create': 'Crea patch', 'patch_renew': 'Rinnova patch', 'patch_check': 'Verifica patch', 'settings_header': '⚙️ Impostazioni', 'patch_folder_s3_ncam': 'Percorso patch S3-NCam', 'patch_folder_s4': 'Percorso patch S4', 'patch_copy_s3_ncam': 'Copia patch in S3-NCam', 'patch_copy_s4': 'Copia patch in S4', 'patch_folder_s3_ncam_tooltip': 'Seleziona la cartella patch S3-NCam-Bonecrew', 'patch_folder_s4_tooltip': 'Seleziona la cartella patch S4', 'select_repository': 'Seleziona repository', 'current_source': 'Sorgente corrente', 'select_repository_prompt': 'Seleziona un repository.', 'no_repository_url': 'Nessun URL del repository selezionato.', 'working_tree_not_clean': 'La directory di lavoro contiene modifiche.', 'select_revision': 'Seleziona revisione', 'repository_load_failed': 'Impossibile caricare il repository.', 'revision_load_failed': 'Impossibile caricare le revisioni.', 'patch_apply': 'Applica patch', 'patch_path_label': 'Salva patch', 'patch_zip': 'Comprimi patch in ZIP', 'backup_old': 'Backup S3 / Rinnova patch', 'clean_folder': 'Pulisci cartella patch', 'change_old_dir': 'Seleziona cartella patch S3', 'oscam_emu_revision': 'Revisione OSCam-Emu', 'loading_commits': 'Caricamento commit...', 'commits_loaded': 'Commit caricati correttamente', 'github_config_load': 'Caricamento configurazione GitHub...', 'github_emu_git_missing': 'Errore: configurazione GitHub incompleta (URL, token o utente mancante).', 'patch_emu_git_missing': 'Errore: directory sorgente locale non trovata: {path}', 'git_repo_init': 'Inizializzazione di un nuovo repository Git nella cartella di destinazione...', 'git_remote_add': 'Collegamento del repository locale a GitHub...', 'git_remote_update': 'Aggiornamento della connessione remota...', 'git_fetching': 'Recupero dei dati correnti dal repository GitHub...', 'plugin_uptodate': '✅ Il plugin è aggiornato (versione: {current})', 'tools_ok': '✅ Tutti gli strumenti di sistema richiesti sono già installati.', 'checking_tools': 'Avvio del controllo degli strumenti di sistema...', 'git_config_user': 'Impostazione dei dati utente Git ({user_name})...', 'git_adding_files': 'Indicizzazione dei file da caricare...', 'git_committing': 'Creazione del commit...', 'github_upload_start': '🚀 Caricamento su GitHub avviato, attendere...', 'github_emu_git_uploaded': '✅ OSCam-Emu Git caricato correttamente!', 'github_emu_git_revision': '📊 Stato corrente: revisione {sha} ({commit_msg})', 'github_upload_failed': '❌ Caricamento su GitHub non riuscito.', 'log_start_header': '--- Generatore patch OSCam Emu v{} ---', 'log_sys_info': 'Sistema: {} {}', 'log_dep_check': 'Controllo: Git ({}), Patch ({}), Audio ({})', 'log_status_ok': 'Stato: tutte le dipendenze sono caricate. Pronto.', 'ok': 'OK', 'language_done': '✅ Lingua cambiata!', 'language_switch': 'Cambio della lingua in corso...', 'missing': 'MANCANTE!', 'active': 'Attivo', 'inactive': 'Inattivo', 'github_config_header': '📁 Configurazione GitHub', 'language_label': 'Lingua:', 'color_label': 'Colore', 'commit_count_label': 'Ultimi commit', 'modifier_button_text': '👤 Autore della patch', 'modifier_tooltip_prefix': 'Creato da:', 'check_tools_button': '🛠️ Verifica strumenti', 'start_check': 'Avvio del controllo del sistema...', 'found': 'trovato', 'net_check': 'Verifica della connessione Internet...', 'net_online': 'Online', 'net_offline': 'Offline', 'upd_check': '🔍 Controllo aggiornamenti strumenti...', 'sound_active': 'Attivo', 'sound_inactive': 'Disattivato', 'status_up_to_date': '✅ OSCam è aggiornato', 'status_update_avail': '🚀 Aggiornamento disponibile!', 'welcome_msg': 'Benvenuto in OSCam Emu Patch Generator!', 'patch_file_missing': '❌ File patch non trovato!', 'zip_success': '✅ Patch compressa correttamente: {zip_file}', 'zip_failed': '❌ Errore durante la compressione: {error}', 'patch_creation_finished': 'Creazione della patch completata.', 'patch_emu_git_start': '🔹 Creazione della patch OSCam-Emu Git... (Percorso: {path})', 'patch_emu_git_check_git': '🔎 Controllo di Git...', 'patch_emu_git_prepare': "🧹 Preparazione dell'ambiente di lavoro...", 'patch_emu_git_clone': '🌐 Clonazione di Streamboard...', 'patch_emu_git_head': '📌 Rilevamento della revisione corrente di Streamboard...', 'patch_emu_git_check_patch': '🔍 Controllo della patch...', 'patch_emu_git_apply': '🔧 Applicazione della patch OSCam-Emu...', 'patch_emu_git_status': '📋 Controllo delle modifiche...', 'patch_emu_git_config': '👤 Configurazione di Git...', 'patch_emu_git_commit': '💾 Salvataggio del commit...', 'patch_emu_git_replace': '📦 Installazione del repository modificato...', 'patch_emu_git_validate': '🔎 Verifica del repository...', 'patch_emu_git_success': '✅ Patch OSCam-Emu Git applicata correttamente', 'patch_emu_git_failed': '❌ Applicazione della patch OSCam-Emu Git non riuscita', 'patch_emu_git_done': '🎉 OSCam-Emu Git aggiornato correttamente!', 'patch_emu_git_clone_failed': '❌ Clonazione Git non riuscita', 'patch_emu_git_deleted': '✅ Vecchia cartella OSCam-Emu Git eliminata: {path}', 'delete_failed': '❌ Eliminazione non riuscita: {path} - {error}', 'patch_emu_git_apply_failed': '❌ Applicazione della patch non riuscita!', 'patch_emu_git_applied': '✅ Patch salvata correttamente nel commit: {commit_msg}', 'patch_emu_git_revision_failed': '⚠️ Impossibile ottenere la revisione Git: {error}', 'patch_emu_git_done': '✅ OSCam-Emu Git aggiornato correttamente', 'patch_emu_git_revision': '🧾 Revisione Git: {sha}', 'github_patch_uploaded': '✅ Patch caricata correttamente: {patch_version}', 'git_revision_failed': '⚠️ Impossibile determinare la revisione Git: {error}', 'github_emu_git_revision_failed': '⚠️ Impossibile recuperare la revisione: {error}', 'online_patch_dl': 'Scarica patch online', 'patch_dl_title': 'Download patch', 'patch_dl_select': 'Seleziona una patch (controllo versioni in corso...):', 'patch_dl_wait': 'Controllo delle versioni della patch sul server...', 'patch_dl_start': 'Avvio del download da:', 'patch_dl_save': 'Patch salvata in:', 'ok_button': 'OK', 'config_saved': 'Impostazioni aggiornate', 'auth_label': 'Autore', 'repo_label': 'Repository', 'lang_label': 'Lingua', 'dir_label': 'Directory patch', 'auto_update_label': 'Aggiornamento automatico', 'cancel_button': 'Annulla', 'mod_dialog_title': 'Modifica autore della patch', 'mod_dialog_label': 'Nome autore:', 'mod_changed_success': '✅ Autore modificato in: {name}', 'repo_dialog_title': 'Selezione repository', 'repo_dialog_label': "Seleziona l'URL del repository desiderato:", 'executing_cmd': 'Esecuzione comando:', 'cmd_failed': 'Comando non riuscito con codice di uscita:', 'executing_git_apply': '🚀 Applicazione della patch: {patch}', 'executing_git_check': '🔍 Verifica compatibilità della patch: {patch}', 'rev_label': '📝 Revisione Git:', 'start': 'Avvio del controllo del sistema...', 'ready': 'Tutti gli strumenti di sistema richiesti sono pronti.', 'up_to_date': 'Plugin aggiornato', 'config': '🛠️ Configurazione attiva:', 'author': 'Autore della patch', 'repo': 'Repository', 'tools_ready': 'Tutti gli strumenti di sistema richiesti sono pronti.', 'upd_ok': 'Plugin aggiornato', 'active_conf': '🛠️ Configurazione attiva:', 'patch_author': 'Autore della patch', 'no_update_found': 'Nessun aggiornamento disponibile...', 'upd_btn_current': 'v{v} (Ultima versione)', 'upd_btn_new': 'Aggiornamento: v{v} disponibile'})
TEXTS["pl"] = dict(TEXTS["en"])
TEXTS["pl"].update({'fix_permissions': 'Napraw uprawnienia', 'restart_tool_admin': 'Uruchom ponownie jako administrator', 'backup_button_text': '💾 Utwórz kopię zapasową', 'patch_create': 'Utwórz patch', 'patch_renew': 'Odśwież patch', 'patch_check': 'Sprawdź patch', 'settings_header': '⚙️ Ustawienia', 'patch_folder_s3_ncam': 'Ścieżka patcha S3-NCam', 'patch_folder_s4': 'Ścieżka patcha S4', 'patch_copy_s3_ncam': 'Kopiuj patch do S3-NCam', 'patch_copy_s4': 'Kopiuj patch do S4', 'patch_folder_s3_ncam_tooltip': 'Wybierz folder patchy S3-NCam-Bonecrew', 'patch_folder_s4_tooltip': 'Wybierz folder patchy S4', 'select_repository': 'Wybierz repozytorium', 'current_source': 'Aktualne źródło', 'select_repository_prompt': 'Wybierz repozytorium.', 'no_repository_url': 'Nie wybrano adresu URL repozytorium.', 'working_tree_not_clean': 'Katalog roboczy zawiera zmiany.', 'select_revision': 'Wybierz rewizję', 'repository_load_failed': 'Nie udało się wczytać repozytorium.', 'revision_load_failed': 'Nie udało się wczytać rewizji.', 'patch_apply': 'Zastosuj patch', 'patch_path_label': 'Zapisz patch', 'patch_zip': 'Spakuj patch do ZIP', 'backup_old': 'Kopia zapasowa S3 / Odśwież patch', 'clean_folder': 'Wyczyść folder patchy', 'change_old_dir': 'Wybierz folder patchy S3', 'oscam_emu_revision': 'Rewizja OSCam-Emu', 'loading_commits': 'Wczytywanie commitów...', 'commits_loaded': 'Commity zostały wczytane pomyślnie', 'github_config_load': 'Wczytywanie konfiguracji GitHub...', 'github_emu_git_missing': 'Błąd: niekompletna konfiguracja GitHub (brak URL, tokenu lub użytkownika).', 'patch_emu_git_missing': 'Nie znaleziono lokalnego katalogu źródłowego: {path}', 'git_repo_init': 'Inicjalizacja nowego repozytorium Git w katalogu docelowym...', 'git_remote_add': 'Łączenie lokalnego repozytorium z GitHub...', 'git_remote_update': 'Aktualizowanie połączenia zdalnego...', 'git_fetching': 'Pobieranie aktualnych danych z repozytorium GitHub...', 'plugin_uptodate': '✅ Wtyczka jest aktualna (wersja: {current})', 'tools_ok': '✅ Wszystkie wymagane narzędzia systemowe są już zainstalowane.', 'checking_tools': 'Rozpoczynanie sprawdzania narzędzi systemowych...', 'git_config_user': 'Ustawianie danych użytkownika Git ({user_name})...', 'git_adding_files': 'Dodawanie plików do przesłania...', 'git_committing': 'Tworzenie commita...', 'github_upload_start': '🚀 Rozpoczęto przesyłanie do GitHub, proszę czekać...', 'github_emu_git_uploaded': '✅ OSCam-Emu Git został pomyślnie przesłany!', 'github_emu_git_revision': '📊 Aktualny stan: rewizja {sha} ({commit_msg})', 'github_upload_failed': '❌ Przesyłanie do GitHub nie powiodło się.', 'log_start_header': '--- Generator patchy OSCam Emu v{} ---', 'log_sys_info': 'System: {} {}', 'log_dep_check': 'Sprawdzanie: Git ({}), Patch ({}), Audio ({})', 'log_status_ok': 'Stan: wszystkie zależności są dostępne. Gotowe.', 'ok': 'OK', 'language_done': '✅ Zmieniono język!', 'language_switch': 'Zmiana języka...', 'missing': 'BRAK!', 'active': 'Aktywny', 'inactive': 'Nieaktywny', 'github_config_header': '📁 Konfiguracja GitHub', 'language_label': 'Język:', 'color_label': 'Kolor', 'commit_count_label': 'Ostatnie commity', 'modifier_button_text': '👤 Autor patcha', 'modifier_tooltip_prefix': 'Utworzone przez:', 'check_tools_button': '🛠 ️ Sprawdź narzędzia', 'start_check': 'Rozpoczynanie sprawdzania systemu...', 'found': 'znaleziono', 'net_check': 'Sprawdzanie połączenia z Internetem...', 'net_online': 'Online', 'net_offline': 'Offline', 'upd_check': '🔍 Sprawdzanie aktualizacji narzędzi...', 'sound_active': 'Aktywny', 'sound_inactive': 'Wyłączony', 'status_up_to_date': '✅ OSCam jest aktualny', 'status_update_avail': '🚀 Dostępna aktualizacja!', 'welcome_msg': 'Witamy w OSCam Emu Patch Generator!', 'patch_file_missing': '❌ Nie znaleziono pliku patcha!', 'zip_success': '✅ Patch został pomyślnie spakowany: {zip_file}', 'zip_failed': '❌ Błąd podczas pakowania: {error}', 'patch_creation_finished': 'Tworzenie patcha zakończone.'})


TEXTS["pl"].update({'patch_emu_git_start': '🔹 Tworzenie patcha OSCam-Emu Git... (Ścieżka: {path})', 'patch_emu_git_check_git': '🔎 Sprawdzanie Git...', 'patch_emu_git_prepare': '🧹 Przygotowywanie środowiska roboczego...', 'patch_emu_git_clone': '🌐 Klonowanie Streamboard...', 'patch_emu_git_head': '📌 Ustalanie aktualnej rewizji Streamboard...', 'patch_emu_git_check_patch': '🔍 Sprawdzanie patcha...', 'patch_emu_git_apply': '🔧 Stosowanie patcha OSCam-Emu...', 'patch_emu_git_status': '📋 Sprawdzanie zmian...', 'patch_emu_git_config': '👤 Konfiguracja Git...', 'patch_emu_git_commit': '💾 Zapisywanie commita...', 'patch_emu_git_replace': '📦 Instalowanie zmodyfikowanego repozytorium...', 'patch_emu_git_validate': '🔎 Weryfikacja repozytorium...', 'patch_emu_git_success': '✅ Patch OSCam-Emu Git został pomyślnie zastosowany', 'patch_emu_git_failed': '❌ Nie udało się zastosować patcha OSCam-Emu Git', 'patch_emu_git_done': '🎉 OSCam-Emu Git został pomyślnie zaktualizowany!', 'patch_emu_git_clone_failed': '❌ Klonowanie Git nie powiodło się', 'patch_emu_git_deleted': '✅ Usunięto starą lokalną kopię OSCam-Emu Git: {path}', 'delete_failed': '❌ Nie udało się usunąć: {path} - {error}', 'patch_emu_git_apply_failed': '❌ Nie udało się zastosować patcha!', 'patch_emu_git_applied': '✅ Patch zapisany w commicie: {commit_msg}', 'patch_emu_git_revision_failed': '⚠️ Nie można pobrać rewizji Git: {error}', 'patch_emu_git_done': '✅ OSCam-Emu Git został pomyślnie zaktualizowany', 'patch_emu_git_revision': '🧾 Rewizja Git: {sha}', 'github_patch_uploaded': '✅ Patch został pomyślnie przesłany: {patch_version}', 'git_revision_failed': '⚠️ Nie można ustalić rewizji Git: {error}', 'github_emu_git_revision_failed': '⚠️ Nie można pobrać rewizji: {error}', 'online_patch_dl': 'Pobierz patch online', 'patch_dl_title': 'Pobieranie patcha', 'patch_dl_select': 'Wybierz patch (sprawdzanie wersji...)', 'patch_dl_wait': 'Sprawdzanie wersji patcha na serwerze...', 'patch_dl_start': 'Rozpoczynanie pobierania z:', 'patch_dl_save': 'Patch zapisany w:', 'ok_button': 'OK', 'config_saved': 'Ustawienia zostały zaktualizowane', 'auth_label': 'Autor', 'repo_label': 'Repozytorium', 'lang_label': 'Język', 'dir_label': 'Katalog patcha', 'auto_update_label': 'Automatyczna aktualizacja', 'cancel_button': 'Anuluj', 'mod_dialog_title': 'Zmień autora patcha', 'mod_dialog_label': 'Nazwa autora:', 'mod_changed_success': '✅ Autor został zmieniony na: {name}', 'repo_dialog_title': 'Wybór repozytorium', 'repo_dialog_label': 'Wybierz adres URL repozytorium:', 'executing_cmd': 'Wykonywanie polecenia:', 'cmd_failed': 'Polecenie zakończone błędem o kodzie:', 'executing_git_apply': '🚀 Stosowanie patcha: {patch}', 'executing_git_check': '🔍 Sprawdzanie zgodności patcha: {patch}', 'rev_label': '📝 Rewizja Git:', 'start': 'Rozpoczynanie sprawdzania systemu...', 'ready': 'Wszystkie wymagane narzędzia systemowe są gotowe.', 'up_to_date': 'Wtyczka jest aktualna', 'config': '🛠️ Aktywna konfiguracja:', 'author': 'Autor patcha', 'repo': 'Repozytorium', 'tools_ready': 'Wszystkie wymagane narzędzia systemowe są gotowe.', 'upd_ok': 'Wtyczka jest aktualna', 'active_conf': '🛠️ Aktywna konfiguracja:', 'patch_author': 'Autor patcha', 'no_update_found': 'Nie znaleziono dostępnych aktualizacji...', 'upd_btn_current': 'v{v} (Najnowsza wersja)', 'upd_btn_new': 'Aktualizacja: dostępna wersja v{v}'})

TEXTS["pl"].update({'repository': 'Repozytorium', 'update_error': 'Błąd podczas sprawdzania aktualizacji: {error}', 'info_title': 'Informacje o programie', 'stats_checkbox': 'Statystyki', 'stats_tooltip': 'Zezwól na anonimowe statystyki użytkowania lub je wyłącz.', 'new_version_available': 'Dostępna nowa wersja', 'update_title': 'Dostępna aktualizacja', 'update_msg': 'Dostępna jest nowa wersja. Czy chcesz teraz zaktualizować program?', 'exit': 'Wyjście', 'yes': 'Tak', 'no': 'Nie', 'cancel': 'Anuluj', 'btn_plugin_update': 'Aktualizacja wtyczki', 'state_plugin_uptodate': 'Aktualne', 'new_version_label': 'Nowa', 'old_version_label': 'Zainstalowana', 'state_plugin_update_available': 'Dostępna aktualizacja: {current} → {latest}', 'log_update_check_start': 'Sprawdzanie aktualizacji…', 'log_update_uptodate': '✅ Zainstalowana wersja: {version}', 'log_update_declined': 'Aktualizacja pominięta', 'log_update_failed': '❌ Nie udało się sprawdzić aktualizacji: {error}', 'update_box_title': 'Aktualizacja oprogramowania', 'update_box_msg': 'Dostępna jest nowa wersja!\n\nNowa: v{latest}\nObecna: v{current}\n\nCzy zaktualizować teraz?', 'msg_update_available_title': 'Dostępna aktualizacja', 'msg_update_available_text': 'Dostępna jest nowa wersja ({latest}).\nObecnie zainstalowana: {current}.\nCzy zaktualizować teraz?', 'update_fail': 'Aktualizacja nie powiodła się: {error}', 'update_success': '✅ Aktualizacja została pomyślnie zainstalowana! Uruchom ponownie program.', 'update_available_msg': 'Obecna wersja: {current}\nNowa wersja: {latest}', 'restart_required_msg': 'Program wymaga ponownego uruchomienia. Uruchomić ponownie teraz?', 'restart_tool_cancelled': 'ℹ️ Użytkownik anulował ponowne uruchomienie.', 'update_started': 'ℹ️ Rozpoczęto sprawdzanie aktualizacji...', 'update_backup_done': '✅ Utworzono kopię zapasową starych plików wtyczki.', 'update_download_failed': '❌ Pobieranie nie powiodło się: {error}', 'update_extract_failed': '❌ Nie udało się rozpakować nowej wersji: {error}', 'update_done': '✅ Aktualizacja do wersji {version} została zakończona pomyślnie.', 'restart_tool': 'Uruchom ponownie program', 'update_check_done': 'Gotowe', 'backup_created': '✅ Utworzono kopię zapasową: {file}', 'exit_question': 'Czy na pewno chcesz zamknąć program?', 'update_check_start': 'Sprawdzanie aktualizacji...', 'github_version_available': 'Dostępna nowa wersja: {version}', 'github_version_fetch_failed': 'Nie udało się sprawdzić wersji: {error}', 's3_install_button': 'Zainstaluj S3', 's3_tooltip': 'Lewy przycisk myszy: instaluj/aktualizuj\nPrawy przycisk myszy: wybierz ścieżkę ręcznie', 'restarting_check': 'Ponowne uruchamianie sprawdzania systemu...', 's3_choice_title': 'Wybierz S3 Simplebuild', 's3_choice_text': 'Które menu S3 chcesz uruchomić?', 's3_choice_info': "Gorgone używa folderu 's3'.\nSpeedy005 używa folderu 's3_speedy005'.", 's3_choice_gorgone': 'S3 Gorgone', 's3_choice_speedy005': 'S3 Speedy005', 'button_cancel': 'Anuluj', 's4_install_button': 'Zainstaluj S4', 'log_exported': '✅ Dziennik zapisano w:', 'log_save_error': '❌ Błąd podczas zapisywania dziennika:', 'credits_label': 'Podziękowania / Autorzy', 'close': 'Zamknij', 'version_current': 'Wersja {version} jest aktualna.', 'update_check_failed': 'Nie udało się sprawdzić aktualizacji: {error}', 'update_available_title': 'Dostępna aktualizacja', 'update_no_update': 'ℹ️ Brak dostępnych aktualizacji', 'installed_version': 'Zainstalowana wersja to', 'new_version_found': 'Znaleziono nową wersję', 'git_status': 'Wyświetl commity', 'edit_patch_header': 'Edytuj nagłówek patcha', 'github_emu_config_button': 'Edytuj konfigurację GitHub', 'github_upload_patch': 'Prześlij plik patcha', 'github_upload_emu': 'Prześlij OSCam-Emu Git', 'oscam_emu_git_patch': 'Patch OSCam-Emu Git', 'oscam_emu_git_clear': 'Wyczyść OSCam-Emu Git', 'oscam_emu_patch_upload': 'Prześlij patch OSCam-Emu', 'update_declined': 'Aktualizacja została odrzucona.', 'update_current_version': '✅ Zainstalowana wersja: {version}', 'restart_required_title': 'Wymagane ponowne uruchomienie', 'save': 'Zapisz', 'matrix_btn_exit': '🔙 WYJDŹ Z MATRIX'})

TEXTS["pl"].update({'STATS_TITLE': 'STATYSTYKI PROGRAMU', 'STATS_GITHUB': 'GitHub:', 'STATS_LOCAL': 'Lokalnie:', 'STATS_TOTAL': 'Łącznie:', 'foot_ok': 'OK', 'foot_ready': 'Gotowe', 'stats_title': 'STATYSTYKI PROGRAMU', 'stats_github': 'GitHub:', 'stats_local': 'Lokalnie:', 'stats_total': 'Łącznie:', 'temp_repo_deleted': 'Tymczasowe repozytorium usunięte: {path}', 'patch_file_deleted': 'Plik patcha usunięty: {path}', 'temp_repo_already_deleted': 'Nie znaleziono tymczasowego repozytorium (już wyczyszczone): {path}', 'final_label': '🛠️ Co dzisiaj tworzymy?', 'info_tooltip': 'Informacje / Pomoc', 'restart_tool_question': 'Czy chcesz teraz ponownie uruchomić program?', 'info_text': 'To narzędzie jest kompletnym menedżerem patchy OSCam Emu.\n\nFunkcje:\n- Utwórz patch: generuje patch z kodu źródłowego OSCam.\n- Odśwież patch: aktualizuje istniejący patch.\n- Sprawdź patch: weryfikuje, czy patch można poprawnie zastosować.\n- Zastosuj patch: stosuje patch do lokalnego repozytorium Git OSCam-Emu.\n- Spakuj patch: tworzy archiwum ZIP z patchem.\n- Kopia zapasowa patcha: zapisuje stary patch i zastępuje go nową wersją.\n- Wyczyść folder patchy: usuwa pliki tymczasowe z folderu patchy (ważne pliki pozostają).\n- Patch OSCam-Emu Git: stosuje patch bezpośrednio do repozytorium Git OSCam-Emu.\n- Wyczyść OSCam-Emu Git: usuwa lokalny folder Git OSCam-Emu.\n- Przesyłanie do GitHub: wysyła patch lub folder OSCam-Emu Git do GitHub.\n- Zarządzanie danymi GitHub: konfiguracja nazwy użytkownika, tokenu, adresu repozytorium i gałęzi.\n- Zmiana języka i kolorów: zmienia język interfejsu oraz kolory przycisków i paska postępu.\n- Pasek postępu: pokazuje postęp wykonywanych operacji.\n- Pokaż commity: wyświetla najnowsze commity lokalnego repozytorium.\n\n⚠️ Uwaga: podczas przesyłania patcha nadpisywany jest tylko plik `oscam-emu.patch`; wszystkie pozostałe pliki pozostają bez zmian.', 'patch_create_start': 'ℹ️ Rozpoczęto tworzenie patcha...', 'patch_create_clone_start': '⚠️ Klonowanie repozytorium Git...', 'patch_create_clone_failed': '❌ Nie udało się sklonować repozytorium Git', 'patch_create_no_changes': 'ℹ️ Nie znaleziono zmian między STREAM_REPO a EMU_REPO', 'patch_create_success': '✅ Patch został pomyślnie utworzony: {patch_file}', 'patch_version_from_header': 'Wersja patcha z nagłówka: {patch_version}', 'patch_create_failed': '❌ Błąd podczas tworzenia patcha: {error}', 'plugin_update': 'Dostępna aktualizacja: {current} → {latest}', 'check_commit_button': '🔄 Sprawdź nowe commity', 'backup_old_start': 'ℹ️ Tworzenie kopii zapasowej starego patcha…', 'backup_done': '✅ Kopia zapasowa została utworzona: {path}', 'update_downloading': 'Pobieranie aktualizacji...', 'update_success_msg': 'Aktualizacja zakończona pomyślnie! Program zostanie teraz uruchomiony ponownie.', 'no_old_patch': 'ℹ️ Nie znaleziono starego patcha.', 'new_patch_installed': '✅ Nowy patch został pomyślnie zainstalowany: {path}', 'patch_check_ok': '✅ Sprawdzanie patcha zakończone pomyślnie (patch można zastosować)!', 'github_dialog_title': 'Konfiguracja GitHub Emu', 'patch_check_fail': '❌ Sprawdzanie patcha nie powiodło się (nie można zastosować patcha)!', 'patch_failed': '❌ Tworzenie patcha nie powiodło się', 'oscam_uptodate': 'Git OSCam jest aktualny.', 'oscam_update_found': 'Dostępna aktualizacja!', 'oscam_check_start': '🔍 Sprawdzanie repozytorium OSCam...', 'oscam_server_error': '❌ Błąd: serwer OSCam jest niedostępny.', 'check_commit_button_short': '🔄 Sprawdź commit', 'check_commit_title': 'Sprawdzanie commitów OSCam', 'check_commit_current_hash': 'Aktualny hash:', 'check_commit_current': 'Aktualny stan:', 'check_commit_old': 'Poprzedni:', 'check_commit_new': 'Nowy:', 'check_commit_no_hash': 'Błąd: nie znaleziono hasha commita.', 'check_commit_up_to_date': 'Nie znaleziono nowych commitów.', 'check_commit_new_found': 'Znaleziono nowy commit!', 'check_commit_error': 'Błąd podczas sprawdzania:', 'check_commit_tooltip': 'Kliknij tutaj, aby sprawdzić, czy w repozytorium Streamboard jest dostępny nowy commit. Jeśli zostanie znaleziony, wyświetlony zostanie hash ostatniego commita.', 'patch_creating': '🔨 Tworzenie patcha', 'patch_created': '✅ Patch utworzony', 'streamboard_preparing': '🔄 Przygotowywanie Streamboard', 'stream_master_head': 'Ustalanie dokładnego master HEAD dla {description} (limit czasu na źródło: 35 s)...', 'stream_source_retry': 'Źródło niedostępne, próba użycia następnego źródła: {candidate} ({error})', 'stream_source_check': 'Sprawdzanie źródła Streamboard: {url}', 'stream_source_alternative': 'Używanie alternatywnego źródła Streamboard: {url}', 'stream_source_failed': 'Źródło Streamboard nie powiodło się: {url} ({error})', 'streamboard_updated': '✅ Streamboard zaktualizowany', 'emu_updated': '✅ OSCam-Emu zaktualizowany', 'streamboard_imported': '✅ Zaimportowano rewizję Streamboard', 'patch_diff_created': '🔧 Utworzono różnicę patcha', 'patch_checked': '✅ Patch został pomyślnie sprawdzony', 'patch_header_created': '📝 Dodano nagłówek patcha', 'oscam_emu_git_missing': '⚠️ Nie znaleziono folderu OSCam-Emu Git: {path}', 'clean_done': '✅ Czyszczenie zakończone pomyślnie!', 'oscam_emu_git_patch_start': '🔹 Tworzenie patcha OSCam-Emu Git...', 'git_patch_success': '✅ Patch został pomyślnie utworzony! Rewizja Git: {rev}', 'cleaning_oscam_emu_git': '🔹 Czyszczenie folderu OSCam-Emu Git...', 'oscam_emu_git_deleted': '✅ Folder OSCam-Emu Git został pomyślnie usunięty.', 'oscam_emu_git_clearing': '🔹 Czyszczenie folderu OSCam-Emu Git...', 'oscam_emu_git_cleared': '✅ Czyszczenie zakończone pomyślnie!', 'cleanup_start': '🔹 Czyszczenie katalogu roboczego...', 'cleanup_success': '✅ Czyszczenie zakończone pomyślnie! ✨', 'showing_commits': 'ℹ️ Wyświetlanie ostatnich {count} commitów'})

TEXTS["pl"]["patch_emu_git_start"] = "🔹 Tworzenie patcha OSCam-Emu Git... (Ścieżka: {path})"

TEXTS["tr"] = dict(TEXTS["en"])
TEXTS["tr"].update({'fix_permissions': 'İzinleri düzelt', 'restart_tool_admin': 'Yönetici olarak yeniden başlat', 'backup_button_text': '💾 Yedek oluştur', 'patch_create': 'Patch oluştur', 'patch_renew': "Patch'i yenile", 'patch_check': "Patch'i kontrol et", 'settings_header': '⚙️ Ayarlar', 'patch_folder_s3_ncam': 'S3-NCam patch yolu', 'patch_folder_s4': 'S4 patch yolu', 'patch_copy_s3_ncam': "Patch'i S3-NCam'e kopyala", 'patch_copy_s4': "Patch'i S4'e kopyala", 'patch_folder_s3_ncam_tooltip': 'S3-NCam-Bonecrew patch klasörünü seç', 'patch_folder_s4_tooltip': 'S4 patch klasörünü seç', 'select_repository': 'Depo seç', 'current_source': 'Geçerli kaynak', 'select_repository_prompt': 'Lütfen bir depo seçin.', 'no_repository_url': "Herhangi bir depo URL'si seçilmedi.", 'working_tree_not_clean': 'Çalışma dizininde değişiklikler var.', 'select_revision': 'Revizyon seç', 'repository_load_failed': 'Depo yüklenemedi.', 'revision_load_failed': 'Revizyonlar yüklenemedi.', 'patch_apply': "Patch'i uygula", 'patch_path_label': "Patch'i kaydet", 'patch_zip': "Patch'i ZIP olarak paketle", 'backup_old': "S3 yedeği / Patch'i yenile", 'clean_folder': 'Patch klasörünü temizle', 'change_old_dir': 'S3 patch klasörünü seç', 'oscam_emu_revision': 'OSCam-Emu revizyonu', 'loading_commits': "Commit'ler yükleniyor...", 'commits_loaded': "Commit'ler başarıyla yüklendi", 'github_config_load': 'GitHub yapılandırması yükleniyor...', 'github_emu_git_missing': 'Hata: GitHub yapılandırması eksik (URL, token veya kullanıcı adı yok).', 'patch_emu_git_missing': 'Hata: Yerel kaynak dizini bulunamadı: {path}', 'git_repo_init': 'Hedef klasörde yeni Git deposu başlatılıyor...', 'git_remote_add': "Yerel depo GitHub'a bağlanıyor...", 'git_remote_update': 'Uzak depo bağlantısı güncelleniyor...', 'git_fetching': 'GitHub deposundan güncel veriler alınıyor...', 'plugin_uptodate': '✅ Eklenti güncel (sürüm: {current})', 'tools_ok': '✅ Gerekli tüm sistem araçları zaten yüklü.', 'checking_tools': 'Sistem araçları kontrol ediliyor...', 'git_config_user': 'Git kullanıcı bilgileri ayarlanıyor ({user_name})...', 'git_adding_files': 'Yüklenecek dosyalar hazırlanıyor...', 'git_committing': 'Commit oluşturuluyor...', 'github_upload_start': "🚀 GitHub'a yükleme başladı, lütfen bekleyin...", 'github_emu_git_uploaded': '✅ OSCam-Emu Git başarıyla yüklendi!', 'github_emu_git_revision': '📊 Geçerli durum: revizyon {sha} ({commit_msg})', 'github_upload_failed': "❌ GitHub'a yükleme başarısız oldu.", 'log_start_header': '--- OSCam Emu Patch Generator v{} ---', 'log_sys_info': 'Sistem: {} {}', 'log_dep_check': 'Kontrol: Git ({}), Patch ({}), Ses ({})', 'log_status_ok': 'Durum: tüm bağımlılıklar hazır. Başlatılabilir.', 'ok': 'Tamam', 'language_done': '✅ Dil değiştirildi!', 'language_switch': 'Dil değiştiriliyor...', 'missing': 'EKSİK!', 'active': 'Etkin', 'inactive': 'Devre dışı', 'github_config_header': '📁 GitHub yapılandırması', 'language_label': 'Dil:', 'color_label': 'Renk', 'commit_count_label': "Son commit'ler", 'modifier_button_text': '👤 Patch yazarı', 'modifier_tooltip_prefix': 'Oluşturan:', 'check_tools_button': '🛠️ Araçları kontrol et', 'start_check': 'Sistem kontrolü başlatılıyor...', 'found': 'bulundu', 'net_check': 'İnternet bağlantısı kontrol ediliyor...', 'net_online': 'Çevrimiçi', 'net_offline': 'Çevrimdışı', 'upd_check': '🔍 Araç güncellemeleri kontrol ediliyor...', 'sound_active': 'Etkin', 'sound_inactive': 'Devre dışı', 'status_up_to_date': '✅ OSCam güncel', 'status_update_avail': '🚀 Güncelleme mevcut!', 'welcome_msg': "OSCam Emu Patch Generator'a hoş geldiniz!", 'patch_file_missing': '❌ Patch dosyası bulunamadı!', 'zip_success': '✅ Patch başarıyla ZIP olarak paketlendi: {zip_file}', 'zip_failed': '❌ ZIP oluşturma hatası: {error}', 'patch_creation_finished': 'Patch oluşturma tamamlandı.'})

TEXTS["tr"].update({'patch_emu_git_start': '🚀 OSCam-Emu Git patch işlemi başlatılıyor... (Yol: {path})', 'patch_emu_git_check_git': '🔎 Git kontrol ediliyor...', 'patch_emu_git_prepare': '🧹 Çalışma alanı hazırlanıyor...', 'patch_emu_git_clone': '🌐 Streamboard klonlanıyor...', 'patch_emu_git_head': "📌 Streamboard'un geçerli revizyonu belirleniyor...", 'patch_emu_git_check_patch': '🔍 Patch kontrol ediliyor...', 'patch_emu_git_apply': "🔧 OSCam-Emu patch'i uygulanıyor...", 'patch_emu_git_status': '📋 Değişiklikler kontrol ediliyor...', 'patch_emu_git_config': '👤 Git yapılandırılıyor...', 'patch_emu_git_commit': '💾 Commit kaydediliyor...', 'patch_emu_git_replace': '📦 Değiştirilmiş depo yükleniyor...', 'patch_emu_git_validate': '🔎 Depo doğrulanıyor...', 'patch_emu_git_success': "✅ OSCam-Emu Git patch'i başarıyla uygulandı", 'patch_emu_git_failed': "❌ OSCam-Emu Git patch'i uygulanamadı", 'patch_emu_git_done': '🎉 OSCam-Emu Git başarıyla güncellendi!', 'patch_emu_git_clone_failed': '❌ Git klonlama başarısız oldu', 'patch_emu_git_deleted': '✅ Eski OSCam-Emu Git klasörü silindi: {path}', 'delete_failed': '❌ Klasör silinemedi: {path} - {error}', 'patch_emu_git_apply_failed': '❌ Patch uygulanamadı!', 'patch_emu_git_applied': "✅ Patch commit'e kaydedildi: {commit_msg}", 'patch_emu_git_revision_failed': '⚠️ Git revizyonu alınamadı: {error}', 'patch_emu_git_revision': '🧾 Git revizyonu: {sha}', 'github_patch_uploaded': '✅ Patch başarıyla yüklendi: {patch_version}', 'git_revision_failed': '⚠️ Git revizyonu belirlenemedi: {error}', 'github_emu_git_revision_failed': '⚠️ Revizyon alınamadı: {error}', 'online_patch_dl': 'Çevrimiçi patch indir', 'patch_dl_title': 'Patch indirme', 'patch_dl_select': 'Bir patch seçin (sürümler kontrol ediliyor...):', 'patch_dl_wait': 'Sunucudaki patch sürümleri kontrol ediliyor...', 'patch_dl_start': 'İndirme başlatılıyor:', 'patch_dl_save': 'Patch şuraya kaydedildi:', 'ok_button': 'Tamam', 'config_saved': 'Ayarlar güncellendi', 'auth_label': 'Yazar', 'repo_label': 'Depo', 'lang_label': 'Dil', 'dir_label': 'Patch dizini', 'auto_update_label': 'Otomatik güncelleme', 'cancel_button': 'İptal', 'mod_dialog_title': 'Patch yazarını değiştir', 'mod_dialog_label': 'Yazar adı:', 'mod_changed_success': '✅ Yazar şu şekilde değiştirildi: {name}', 'repo_dialog_title': 'Depo seçimi', 'repo_dialog_label': "İstenen depo URL'sini seçin:", 'executing_cmd': 'Komut yürütülüyor:', 'cmd_failed': 'Komut şu çıkış koduyla başarısız oldu:', 'executing_git_apply': '🚀 Patch uygulanıyor: {patch}', 'executing_git_check': '🔍 Patch uyumluluğu kontrol ediliyor: {patch}', 'rev_label': '📝 Git revizyonu:', 'start': 'Sistem kontrolü başlatılıyor...', 'ready': 'Gerekli tüm sistem araçları hazır.', 'up_to_date': 'Eklenti güncel', 'config': '🛠️ Etkin yapılandırma:', 'author': 'Patch yazarı', 'repo': 'Depo', 'tools_ready': 'Gerekli tüm sistem araçları hazır.', 'upd_ok': 'Eklenti güncel', 'active_conf': '🛠️ Etkin yapılandırma:', 'patch_author': 'Patch yazarı', 'no_update_found': 'Kullanılabilir güncelleme bulunamadı...', 'upd_btn_current': 'v{v} (En son sürüm)', 'upd_btn_new': 'Güncelleme: v{v} mevcut'})

TEXTS["tr"].update({'repository': 'Depo', 'update_error': 'Güncelleme kontrol hatası: {error}', 'info_title': 'Program hakkında', 'stats_checkbox': 'İstatistikler', 'stats_tooltip': 'Anonim kullanım istatistiklerine izin ver veya devre dışı bırak.', 'new_version_available': 'Yeni sürüm mevcut', 'update_title': 'Güncelleme mevcut', 'update_msg': 'Yeni bir sürüm mevcut. Programı şimdi güncellemek ister misiniz?', 'exit': 'Çıkış', 'yes': 'Evet', 'no': 'Hayır', 'cancel': 'İptal', 'btn_plugin_update': 'Eklentiyi güncelle', 'state_plugin_uptodate': 'Güncel', 'new_version_label': 'Yeni', 'old_version_label': 'Yüklü', 'state_plugin_update_available': 'Güncelleme mevcut: {current} → {latest}', 'log_update_check_start': 'Güncellemeler kontrol ediliyor…', 'log_update_uptodate': '✅ Yüklü sürüm: {version}', 'log_update_declined': 'Güncelleme atlandı', 'log_update_failed': '❌ Güncelleme kontrol edilemedi: {error}', 'update_box_title': 'Yazılım güncellemesi', 'update_box_msg': 'Yeni bir sürüm mevcut!\n\nYeni: v{latest}\nMevcut: v{current}\n\nŞimdi güncellensin mi?', 'msg_update_available_title': 'Güncelleme mevcut', 'msg_update_available_text': 'Yeni bir sürüm mevcut ({latest}).\nYüklü sürüm: {current}.\nŞimdi güncellensin mi?', 'update_fail': 'Güncelleme başarısız: {error}', 'update_success': '✅ Güncelleme başarıyla yüklendi! Lütfen programı yeniden başlatın.', 'update_available_msg': 'Mevcut sürüm: {current}\nYeni sürüm: {latest}', 'restart_required_msg': 'Programın yeniden başlatılması gerekiyor. Şimdi yeniden başlatılsın mı?', 'restart_tool_cancelled': 'ℹ️ Kullanıcı yeniden başlatmayı iptal etti.', 'update_started': 'ℹ️ Güncelleme kontrolü başlatıldı...', 'update_backup_done': '✅ Eski eklenti dosyalarının yedeği oluşturuldu.', 'update_download_failed': '❌ İndirme başarısız: {error}', 'update_extract_failed': '❌ Yeni sürüm çıkarılamadı: {error}', 'update_done': '✅ {version} sürümüne güncelleme başarıyla tamamlandı.', 'restart_tool': 'Programı yeniden başlat', 'update_check_done': 'Tamamlandı', 'backup_created': '✅ Yedek oluşturuldu: {file}', 'exit_question': 'Programı kapatmak istediğinizden emin misiniz?', 'update_check_start': 'Güncelleme kontrolü başlatılıyor...', 'github_version_available': 'Yeni sürüm mevcut: {version}', 'github_version_fetch_failed': 'Sürüm kontrol edilemedi: {error}', 's3_install_button': "S3'ü yükle", 's3_tooltip': 'Sol tıklama: yükle/güncelle\nSağ tıklama: yolu elle seç', 'restarting_check': 'Sistem kontrolü yeniden başlatılıyor...', 's3_choice_title': 'S3 Simplebuild seçin', 's3_choice_text': 'Hangi S3 menüsünü başlatmak istiyorsunuz?', 's3_choice_info': "Gorgone 's3' klasörünü kullanır.\nSpeedy005 's3_speedy005' klasörünü kullanır.", 's3_choice_gorgone': 'S3 Gorgone', 's3_choice_speedy005': 'S3 Speedy005', 'button_cancel': 'İptal', 's4_install_button': "S4'ü yükle", 'log_exported': '✅ Günlük şuraya kaydedildi:', 'log_save_error': '❌ Günlük kaydedilirken hata oluştu:', 'credits_label': 'Teşekkürler / Katkıda bulunanlar', 'close': 'Kapat', 'version_current': '{version} sürümü güncel.', 'update_check_failed': 'Güncelleme kontrol edilemedi: {error}', 'update_available_title': 'Güncelleme mevcut', 'update_no_update': 'ℹ️ Kullanılabilir güncelleme yok', 'installed_version': 'Yüklü sürüm:', 'new_version_found': 'Yeni sürüm bulundu', 'git_status': "Commit'leri göster", 'edit_patch_header': 'Patch başlığını düzenle', 'github_emu_config_button': 'GitHub yapılandırmasını düzenle', 'github_upload_patch': 'Patch dosyasını yükle', 'github_upload_emu': "OSCam-Emu Git'i yükle", 'oscam_emu_git_patch': "OSCam-Emu Git patch'i", 'oscam_emu_git_clear': "OSCam-Emu Git'i temizle", 'oscam_emu_patch_upload': "OSCam-Emu patch'ini yükle", 'update_declined': 'Güncelleme reddedildi.', 'update_current_version': '✅ Yüklü sürüm: {version}', 'restart_required_title': 'Yeniden başlatma gerekli', 'save': 'Kaydet', 'matrix_btn_exit': "🔙 MATRIX'TEN ÇIK"})

TEXTS["tr"].update({'repository': 'Depo', 'update_error': 'Güncelleme kontrol hatası: {error}', 'info_title': 'Program hakkında', 'stats_checkbox': 'İstatistikler', 'stats_tooltip': 'Anonim kullanım istatistiklerine izin ver veya devre dışı bırak.', 'new_version_available': 'Yeni sürüm mevcut', 'update_title': 'Güncelleme mevcut', 'update_msg': 'Yeni bir sürüm mevcut. Programı şimdi güncellemek ister misiniz?', 'exit': 'Çıkış', 'yes': 'Evet', 'no': 'Hayır', 'cancel': 'İptal', 'btn_plugin_update': 'Eklentiyi güncelle', 'state_plugin_uptodate': 'Güncel', 'new_version_label': 'Yeni', 'old_version_label': 'Yüklü', 'state_plugin_update_available': 'Güncelleme mevcut: {current} → {latest}', 'log_update_check_start': 'Güncellemeler kontrol ediliyor…', 'log_update_uptodate': '✅ Yüklü sürüm: {version}', 'log_update_declined': 'Güncelleme atlandı', 'log_update_failed': '❌ Güncelleme kontrol edilemedi: {error}', 'update_box_title': 'Yazılım güncellemesi', 'update_box_msg': 'Yeni bir sürüm mevcut!\n\nYeni: v{latest}\nMevcut: v{current}\n\nŞimdi güncellensin mi?', 'msg_update_available_title': 'Güncelleme mevcut', 'msg_update_available_text': 'Yeni bir sürüm mevcut ({latest}).\nYüklü sürüm: {current}.\nŞimdi güncellensin mi?', 'update_fail': 'Güncelleme başarısız: {error}', 'update_success': '✅ Güncelleme başarıyla yüklendi! Lütfen programı yeniden başlatın.', 'update_available_msg': 'Mevcut sürüm: {current}\nYeni sürüm: {latest}', 'restart_required_msg': 'Programın yeniden başlatılması gerekiyor. Şimdi yeniden başlatılsın mı?', 'restart_tool_cancelled': 'ℹ️ Kullanıcı yeniden başlatmayı iptal etti.', 'update_started': 'ℹ️ Güncelleme kontrolü başlatıldı...', 'update_backup_done': '✅ Eski eklenti dosyalarının yedeği oluşturuldu.', 'update_download_failed': '❌ İndirme başarısız: {error}', 'update_extract_failed': '❌ Yeni sürüm çıkarılamadı: {error}', 'update_done': '✅ {version} sürümüne güncelleme başarıyla tamamlandı.', 'restart_tool': 'Programı yeniden başlat', 'update_check_done': 'Tamamlandı', 'backup_created': '✅ Yedek oluşturuldu: {file}', 'exit_question': 'Programı kapatmak istediğinizden emin misiniz?', 'update_check_start': 'Güncelleme kontrolü başlatılıyor...', 'github_version_available': 'Yeni sürüm mevcut: {version}', 'github_version_fetch_failed': 'Sürüm kontrol edilemedi: {error}', 's3_install_button': "S3'ü yükle", 's3_tooltip': 'Sol tıklama: yükle/güncelle\nSağ tıklama: yolu elle seç', 'restarting_check': 'Sistem kontrolü yeniden başlatılıyor...', 's3_choice_title': 'S3 Simplebuild seçin', 's3_choice_text': 'Hangi S3 menüsünü başlatmak istiyorsunuz?', 's3_choice_info': "Gorgone 's3' klasörünü kullanır.\nSpeedy005 's3_speedy005' klasörünü kullanır.", 's3_choice_gorgone': 'S3 Gorgone', 's3_choice_speedy005': 'S3 Speedy005', 'button_cancel': 'İptal', 's4_install_button': "S4'ü yükle", 'log_exported': '✅ Günlük şuraya kaydedildi:', 'log_save_error': '❌ Günlük kaydedilirken hata oluştu:', 'credits_label': 'Teşekkürler / Katkıda bulunanlar', 'close': 'Kapat', 'version_current': '{version} sürümü güncel.', 'update_check_failed': 'Güncelleme kontrol edilemedi: {error}', 'update_available_title': 'Güncelleme mevcut', 'update_no_update': 'ℹ️ Kullanılabilir güncelleme yok', 'installed_version': 'Yüklü sürüm:', 'new_version_found': 'Yeni sürüm bulundu', 'git_status': "Commit'leri göster", 'edit_patch_header': 'Patch başlığını düzenle', 'github_emu_config_button': 'GitHub yapılandırmasını düzenle', 'github_upload_patch': 'Patch dosyasını yükle', 'github_upload_emu': "OSCam-Emu Git'i yükle", 'oscam_emu_git_patch': "OSCam-Emu Git patch'i", 'oscam_emu_git_clear': "OSCam-Emu Git'i temizle", 'oscam_emu_patch_upload': "OSCam-Emu patch'ini yükle", 'update_declined': 'Güncelleme reddedildi.', 'update_current_version': '✅ Yüklü sürüm: {version}', 'restart_required_title': 'Yeniden başlatma gerekli', 'save': 'Kaydet', 'matrix_btn_exit': "🔙 MATRIX'TEN ÇIK"})

TEXTS["tr"].update({'log_start_header': '--- OSCam Emu Patch Oluşturucu v{} ---', 'patch_emu_git_done': "✅ OSCam Emu Git patch'i başarıyla uygulandı", 's3_choice_gorgone': 'S3 Gorgone', 's3_choice_speedy005': 'S3 Speedy005', 'STATS_TITLE': 'ARAÇ İSTATİSTİKLERİ', 'STATS_GITHUB': 'GitHub:', 'STATS_LOCAL': 'Yerel:', 'STATS_TOTAL': 'Toplam:', 'foot_ok': 'Tamam', 'foot_ready': 'Hazır', 'stats_title': 'ARAÇ İSTATİSTİKLERİ', 'stats_github': 'GitHub:', 'stats_local': 'Yerel:', 'stats_total': 'Toplam:', 'temp_repo_deleted': 'Geçici depo silindi: {path}', 'patch_file_deleted': 'Patch dosyası silindi: {path}', 'temp_repo_already_deleted': 'Geçici depo bulunamadı (zaten temiz): {path}', 'final_label': '🛠️ Bugün ne oluşturuyoruz?', 'info_tooltip': 'Bilgi / Yardım', 'restart_tool_question': 'Aracı şimdi yeniden başlatmak istiyor musunuz?', 'info_text': "Bu araç, kapsamlı bir OSCam Emu Patch Manager uygulamasıdır.\n\nÖzellikler:\n- Patch oluştur: OSCam kaynak kodundan bir patch oluşturur.\n- Patch yenile: Mevcut patch'i günceller.\n- Patch kontrolü: Patch'in doğru şekilde uygulanıp uygulanamayacağını denetler.\n- Patch uygula: Patch'i yerel OSCam-Emu Git deposuna uygular.\n- Patch'i ZIP'le: Patch'i bir ZIP dosyasına paketler.\n- Patch yedeği: Eski patch'in yedeğini alır ve üzerine yeni sürümü yazar.\n- Patch klasörünü temizle: Patch klasöründeki geçici dosyaları siler (önemli dosyalar korunur).\n- OSCam-Emu Git patch'i: Patch'i doğrudan OSCam-Emu Git deposuna uygular.\n- OSCam-Emu Git'i temizle: Yerel OSCam-Emu Git klasörünü siler.\n- GitHub'a yükle: Patch'i veya OSCam-Emu Git klasörünü GitHub'a yükler.\n- GitHub kimlik bilgilerini yönet: Kullanıcı adını, token'ı, depo URL'sini ve dalı yapılandırır.\n- Dil ve renk değiştir: GUI dilini değiştirir ve düğme/ilerleme çubuğu renklerini ayarlar.\n- İlerleme göstergesi: İşlem ilerlemesini ilerleme çubuğunda gösterir.\n- Commit'leri göster: Yerel depodaki en son commit'leri görüntüler.\n\n⚠️ Not: Patch yükleme sırasında yalnızca `oscam-emu.patch` dosyasının üzerine yazılır; diğer tüm dosyalar değiştirilmeden kalır.", 'patch_create_start': 'ℹ️ Patch oluşturma başlatıldı...', 'patch_create_clone_start': '⚠️ Git deposu klonlanıyor...', 'patch_create_clone_failed': '❌ Git deposu klonlanamadı', 'patch_create_no_changes': 'ℹ️ STREAM_REPO ile EMU_REPO arasında değişiklik bulunamadı', 'patch_create_success': '✅ Patch başarıyla oluşturuldu: {patch_file}', 'patch_version_from_header': 'Başlıktaki patch sürümü: {patch_version}', 'patch_create_failed': '❌ Patch oluşturulurken hata oluştu: {error}', 'plugin_update': 'Güncelleme mevcut: {current} → {latest}', 'check_commit_button': '🔄 Yeni commit kontrol et', 'backup_old_start': "ℹ️ Eski patch'in yedeği oluşturuluyor…", 'backup_done': '✅ Yedek başarıyla oluşturuldu: {path}', 'update_downloading': 'Güncelleme indiriliyor...', 'update_success_msg': 'Güncelleme başarılı! Araç şimdi yeniden başlatılacak.', 'no_old_patch': 'ℹ️ Eski patch bulunamadı.', 'new_patch_installed': '✅ Yeni patch başarıyla yüklendi: {path}', 'patch_check_ok': '✅ Patch kontrolü başarılı (Patch uygulanabiliyor)! ', 'github_dialog_title': 'GitHub Emu Yapılandırması', 'patch_check_fail': '❌ Patch kontrolü başarısız (Patch uygulanamıyor)!', 'patch_failed': '❌ Patch oluşturulamadı', 'oscam_uptodate': 'OSCam Git güncel.', 'oscam_update_found': 'Güncelleme mevcut!', 'oscam_check_start': '🔍 OSCam deposu kontrol ediliyor...', 'oscam_server_error': '❌ Hata: OSCam sunucusuna ulaşılamıyor.', 'check_commit_button_short': '🔄 Commit kontrol et', 'check_commit_title': 'OSCam Commit Kontrolü', 'check_commit_current_hash': 'Mevcut Hash:', 'check_commit_current': 'Mevcut durum:', 'check_commit_old': 'Eski:', 'check_commit_new': 'Yeni:', 'check_commit_no_hash': 'Hata: Commit hash bulunamadı.', 'check_commit_up_to_date': 'Yeni commit bulunamadı.', 'check_commit_new_found': 'Yeni commit bulundu!', 'check_commit_error': 'Kontrol sırasında hata:', 'check_commit_tooltip': "Streamboard deposunda yeni bir commit olup olmadığını kontrol etmek için buraya tıklayın. Yeni bir commit bulunursa son commit hash'i gösterilir.", 'patch_creating': '🔨 Patch oluşturuluyor', 'patch_created': '✅ Patch oluşturuldu', 'streamboard_preparing': '🔄 Streamboard hazırlanıyor', 'stream_master_head': 'Tam {description} master HEAD sürümü belirleniyor (kaynak başına zaman aşımı: 35 sn)...', 'stream_source_retry': 'Kaynağa ulaşılamıyor, sonraki kaynak deneniyor: {candidate} ({error})', 'stream_source_check': 'Streamboard kaynağı kontrol ediliyor: {url}', 'stream_source_alternative': 'Alternatif Streamboard kaynağı kullanılıyor: {url}', 'stream_source_failed': 'Streamboard kaynağı başarısız oldu: {url} ({error})', 'streamboard_updated': '✅ Streamboard güncellendi', 'emu_updated': '✅ OSCam-Emu güncellendi', 'streamboard_imported': '✅ Streamboard revizyonu içe aktarıldı', 'patch_diff_created': '🔧 Patch farkı oluşturuldu', 'patch_checked': '✅ Patch başarıyla kontrol edildi', 'patch_header_created': '📝 Patch başlığı eklendi', 'oscam_emu_git_missing': '⚠️ OSCam-Emu Git klasörü bulunamadı: {path}', 'clean_done': '✅ Temizlik başarıyla tamamlandı!', 'oscam_emu_git_patch_start': "🔹 OSCam-Emu Git patch'i oluşturuluyor...", 'git_patch_success': '✅ Patch başarıyla oluşturuldu! Git revizyonu: {rev}', 'cleaning_oscam_emu_git': '🔹 OSCam-Emu Git klasörü boşaltılıyor...', 'oscam_emu_git_deleted': '✅ OSCam-Emu Git klasörü başarıyla silindi.', 'oscam_emu_git_clearing': '🔹 OSCam-Emu Git klasörü boşaltılıyor...', 'oscam_emu_git_cleared': '✅ Temizlik başarıyla tamamlandı!', 'cleanup_start': '🔹 Çalışma dizini temizleniyor...', 'cleanup_success': '✅ Temizlik başarıyla tamamlandı! ✨', 'showing_commits': 'ℹ️ En son {count} commit gösteriliyor'})

TEXTS["gr"].update({'repository': 'Αποθετήριο', 'update_error': 'Σφάλμα ελέγχου ενημερώσεων: {error}', 'info_title': 'Πληροφορίες προγράμματος', 'stats_checkbox': 'Στατιστικά', 'stats_tooltip': 'Ενεργοποίηση ή απενεργοποίηση ανώνυμων στατιστικών χρήσης.', 'new_version_available': 'Υπάρχει νέα έκδοση', 'update_title': 'Διαθέσιμη ενημέρωση', 'update_msg': 'Υπάρχει νέα έκδοση. Θέλετε να ενημερώσετε τώρα;', 'exit': 'Έξοδος', 'yes': 'Ναι', 'no': 'Όχι', 'cancel': 'Ακύρωση', 'btn_plugin_update': 'Ενημέρωση πρόσθετου', 'state_plugin_uptodate': 'Ενημερωμένο', 'new_version_label': 'Νέα', 'old_version_label': 'Εγκατεστημένη', 'state_plugin_update_available': 'Διαθέσιμη ενημέρωση: {current} → {latest}', 'log_update_check_start': 'Έλεγχος για ενημερώσεις…', 'log_update_uptodate': '✅ Εγκατεστημένη έκδοση: {version}', 'log_update_declined': 'Η ενημέρωση παραλείφθηκε', 'log_update_failed': '❌ Αποτυχία ελέγχου ενημερώσεων: {error}', 'update_box_title': 'Ενημέρωση λογισμικού', 'update_box_msg': 'Υπάρχει νέα έκδοση!\n\nΝέα: v{latest}\nΤρέχουσα: v{current}\n\nΘέλετε να ενημερώσετε τώρα;', 'msg_update_available_title': 'Διαθέσιμη ενημέρωση', 'msg_update_available_text': 'Υπάρχει νέα έκδοση ({latest}).\nΕγκατεστημένη έκδοση: {current}.\nΘέλετε να ενημερώσετε τώρα;', 'update_fail': 'Αποτυχία ενημέρωσης: {error}', 'update_success': '✅ Η ενημέρωση εγκαταστάθηκε με επιτυχία! Κάντε επανεκκίνηση του προγράμματος.', 'update_available_msg': 'Τρέχουσα έκδοση: {current}\nΝέα έκδοση: {latest}', 'restart_required_msg': 'Απαιτείται επανεκκίνηση του προγράμματος. Να γίνει τώρα;', 'restart_tool_cancelled': 'ℹ️ Ο χρήστης ακύρωσε την επανεκκίνηση.', 'update_started': 'ℹ️ Ο έλεγχος ενημερώσεων ξεκίνησε...', 'update_backup_done': '✅ Δημιουργήθηκε αντίγραφο ασφαλείας των παλιών αρχείων.', 'update_download_failed': '❌ Αποτυχία λήψης: {error}', 'update_extract_failed': '❌ Αποτυχία αποσυμπίεσης της νέας έκδοσης: {error}', 'update_done': '✅ Η ενημέρωση στην έκδοση {version} ολοκληρώθηκε με επιτυχία.', 'restart_tool': 'Επανεκκίνηση προγράμματος', 'update_check_done': 'Ολοκληρώθηκε', 'backup_created': '✅ Δημιουργήθηκε αντίγραφο ασφαλείας: {file}', 'exit_question': 'Είστε βέβαιοι ότι θέλετε να κλείσετε το πρόγραμμα;', 'update_check_start': 'Έναρξη ελέγχου ενημερώσεων...', 'github_version_available': 'Διαθέσιμη νέα έκδοση: {version}', 'github_version_fetch_failed': 'Αποτυχία ελέγχου έκδοσης: {error}', 's3_install_button': 'Εγκατάσταση S3', 's3_tooltip': 'Αριστερό κλικ: εγκατάσταση/ενημέρωση\nΔεξί κλικ: χειροκίνητη επιλογή διαδρομής', 'restarting_check': 'Επανεκκίνηση ελέγχου συστήματος...', 's3_choice_title': 'Επιλογή S3 Simplebuild', 's3_choice_text': 'Ποιο μενού S3 θέλετε να ξεκινήσετε;', 's3_choice_info': "Το Gorgone χρησιμοποιεί τον φάκελο 's3'.\nΤο Speedy005 χρησιμοποιεί τον φάκελο 's3_speedy005'.", 's3_choice_gorgone': 'S3 Gorgone', 's3_choice_speedy005': 'S3 Speedy005', 'button_cancel': 'Ακύρωση', 's4_install_button': 'Εγκατάσταση S4', 'log_exported': '✅ Το αρχείο καταγραφής αποθηκεύτηκε στο:', 'log_save_error': '❌ Σφάλμα κατά την αποθήκευση του αρχείου καταγραφής:', 'credits_label': 'Ευχαριστίες / Συντελεστές', 'close': 'Κλείσιμο', 'version_current': 'Η έκδοση {version} είναι ενημερωμένη.', 'update_check_failed': 'Αποτυχία ελέγχου ενημερώσεων: {error}', 'update_available_title': 'Διαθέσιμη ενημέρωση', 'update_no_update': 'ℹ️ Δεν υπάρχουν διαθέσιμες ενημερώσεις', 'installed_version': 'Εγκατεστημένη έκδοση:', 'new_version_found': 'Βρέθηκε νέα έκδοση', 'git_status': 'Προβολή commits', 'edit_patch_header': 'Επεξεργασία κεφαλίδας patch', 'github_emu_config_button': 'Επεξεργασία ρυθμίσεων GitHub', 'github_upload_patch': 'Μεταφόρτωση αρχείου patch', 'github_upload_emu': 'Μεταφόρτωση OSCam-Emu Git', 'oscam_emu_git_patch': 'Patch OSCam-Emu Git', 'oscam_emu_git_clear': 'Καθαρισμός OSCam-Emu Git', 'oscam_emu_patch_upload': 'Μεταφόρτωση patch OSCam-Emu', 'update_declined': 'Η ενημέρωση απορρίφθηκε.', 'update_current_version': '✅ Εγκατεστημένη έκδοση: {version}', 'restart_required_title': 'Απαιτείται επανεκκίνηση', 'save': 'Αποθήκευση', 'matrix_btn_exit': '🔙 ΕΞΟΔΟΣ ΑΠΟ ΤΟ MATRIX'})


TEXTS["gr"].update({'STATS_TITLE': 'ΣΤΑΤΙΣΤΙΚΑ ΕΡΓΑΛΕΙΟΥ', 'STATS_GITHUB': 'GitHub:', 'STATS_LOCAL': 'Τοπικά:', 'STATS_TOTAL': 'Σύνολο:', 'foot_ok': 'OK', 'foot_ready': 'Έτοιμο', 'stats_title': 'ΣΤΑΤΙΣΤΙΚΑ ΕΡΓΑΛΕΙΟΥ', 'stats_github': 'GitHub:', 'stats_local': 'Τοπικά:', 'stats_total': 'Σύνολο:', 'temp_repo_deleted': 'Το προσωρινό αποθετήριο διαγράφηκε: {path}', 'patch_file_deleted': 'Το αρχείο patch διαγράφηκε: {path}', 'temp_repo_already_deleted': 'Δεν βρέθηκε προσωρινό αποθετήριο (έχει ήδη καθαριστεί): {path}', 'final_label': '🛠️ Τι θα δημιουργήσουμε σήμερα;', 'info_tooltip': 'Πληροφορίες / Βοήθεια', 'restart_tool_question': 'Θέλετε να επανεκκινήσετε το εργαλείο τώρα;', 'patch_create_start': 'ℹ️ Η δημιουργία patch ξεκίνησε...', 'patch_create_clone_start': '⚠️ Κλωνοποίηση αποθετηρίου Git...', 'patch_create_clone_failed': '❌ Αποτυχία κλωνοποίησης αποθετηρίου Git', 'patch_create_no_changes': 'ℹ️ Δεν βρέθηκαν αλλαγές μεταξύ STREAM_REPO και EMU_REPO', 'patch_create_success': '✅ Το patch δημιουργήθηκε με επιτυχία: {patch_file}', 'patch_version_from_header': 'Έκδοση patch από την κεφαλίδα: {patch_version}', 'patch_create_failed': '❌ Σφάλμα κατά τη δημιουργία patch: {error}', 'plugin_update': 'Διαθέσιμη ενημέρωση: {current} → {latest}', 'check_commit_button': '🔄 Έλεγχος για νέα commit', 'backup_old_start': 'ℹ️ Δημιουργία αντιγράφου ασφαλείας του παλιού patch…', 'backup_done': '✅ Το αντίγραφο ασφαλείας δημιουργήθηκε: {path}', 'update_downloading': 'Λήψη ενημέρωσης...', 'update_success_msg': 'Η ενημέρωση ολοκληρώθηκε! Το εργαλείο θα επανεκκινηθεί τώρα.', 'no_old_patch': 'ℹ️ Δεν βρέθηκε παλιό patch.', 'new_patch_installed': '✅ Το νέο patch εγκαταστάθηκε με επιτυχία: {path}', 'patch_check_ok': '✅ Ο έλεγχος patch ολοκληρώθηκε με επιτυχία (το patch εφαρμόζεται)! ', 'github_dialog_title': 'Ρυθμίσεις GitHub Emu', 'patch_check_fail': '❌ Ο έλεγχος patch απέτυχε (το patch δεν εφαρμόζεται)!', 'patch_failed': '❌ Η δημιουργία patch απέτυχε', 'oscam_uptodate': 'Το OSCam Git είναι ενημερωμένο.', 'oscam_update_found': 'Βρέθηκε διαθέσιμη ενημέρωση!', 'oscam_check_start': '🔍 Έλεγχος αποθετηρίου OSCam...', 'oscam_server_error': '❌ Σφάλμα: Ο διακομιστής OSCam δεν είναι προσβάσιμος.', 'check_commit_button_short': '🔄 Έλεγχος commit', 'check_commit_title': 'Έλεγχος commit OSCam', 'check_commit_current_hash': 'Τρέχον Hash:', 'check_commit_current': 'Τρέχουσα κατάσταση:', 'check_commit_old': 'Παλαιό:', 'check_commit_new': 'Νέο:', 'check_commit_no_hash': 'Σφάλμα: Δεν βρέθηκε hash commit.', 'check_commit_up_to_date': 'Δεν βρέθηκε νέο commit.', 'check_commit_new_found': 'Βρέθηκε νέο commit!', 'check_commit_error': 'Σφάλμα κατά τον έλεγχο:', 'patch_creating': '🔨 Δημιουργία patch', 'patch_created': '✅ Το patch δημιουργήθηκε', 'streamboard_preparing': '🔄 Προετοιμασία Streamboard', 'stream_master_head': 'Εντοπισμός του ακριβούς master HEAD του {description} (χρονικό όριο ανά πηγή: 35 s)...', 'stream_source_retry': 'Η πηγή δεν είναι προσβάσιμη, δοκιμή της επόμενης: {candidate} ({error})', 'stream_source_check': 'Έλεγχος πηγής Streamboard: {url}', 'stream_source_alternative': 'Χρήση εναλλακτικής πηγής Streamboard: {url}', 'stream_source_failed': 'Αποτυχία πηγής Streamboard: {url} ({error})', 'streamboard_updated': '✅ Το Streamboard ενημερώθηκε', 'emu_updated': '✅ Το OSCam-Emu ενημερώθηκε', 'streamboard_imported': '✅ Η αναθεώρηση Streamboard εισήχθη', 'patch_diff_created': '🔧 Δημιουργήθηκε το diff του patch', 'patch_checked': '✅ Το patch ελέγχθηκε με επιτυχία', 'patch_header_created': '📝 Προστέθηκε η κεφαλίδα του patch', 'oscam_emu_git_missing': '⚠️ Δεν βρέθηκε ο φάκελος OSCam-Emu Git: {path}', 'clean_done': '✅ Ο καθαρισμός ολοκληρώθηκε με επιτυχία!', 'oscam_emu_git_patch_start': '🔹 Δημιουργία patch OSCam-Emu Git...', 'git_patch_success': '✅ Το patch δημιουργήθηκε με επιτυχία! Αναθεώρηση Git: {rev}', 'cleaning_oscam_emu_git': '🔹 Εκκαθάριση φακέλου OSCam-Emu Git...', 'oscam_emu_git_deleted': '✅ Ο φάκελος OSCam-Emu Git διαγράφηκε με επιτυχία.', 'oscam_emu_git_clearing': '🔹 Εκκαθάριση φακέλου OSCam-Emu Git...', 'oscam_emu_git_cleared': '✅ Ο καθαρισμός ολοκληρώθηκε με επιτυχία!', 'cleanup_start': '🔹 Καθαρισμός καταλόγου εργασίας...', 'cleanup_success': '✅ Ο καθαρισμός ολοκληρώθηκε με επιτυχία! ✨', 'showing_commits': 'ℹ️ Εμφάνιση των τελευταίων {count} commit'})

TEXTS["gr"].update({'STATS_TITLE': 'ΣΤΑΤΙΣΤΙΚΑ ΕΡΓΑΛΕΙΟΥ', 'STATS_GITHUB': 'GitHub:', 'STATS_LOCAL': 'Τοπικά:', 'STATS_TOTAL': 'Σύνολο:', 'foot_ok': 'OK', 'foot_ready': 'Έτοιμο', 'stats_title': 'ΣΤΑΤΙΣΤΙΚΑ ΕΡΓΑΛΕΙΟΥ', 'stats_github': 'GitHub:', 'stats_local': 'Τοπικά:', 'stats_total': 'Σύνολο:', 'temp_repo_deleted': 'Το προσωρινό αποθετήριο διαγράφηκε: {path}', 'patch_file_deleted': 'Το αρχείο patch διαγράφηκε: {path}', 'temp_repo_already_deleted': 'Δεν βρέθηκε προσωρινό αποθετήριο (έχει ήδη καθαριστεί): {path}', 'final_label': '🛠️ Τι θα δημιουργήσουμε σήμερα;', 'info_tooltip': 'Πληροφορίες / Βοήθεια', 'restart_tool_question': 'Θέλετε να επανεκκινήσετε το εργαλείο τώρα;', 'patch_create_start': 'ℹ️ Η δημιουργία patch ξεκίνησε...', 'patch_create_clone_start': '⚠️ Κλωνοποίηση αποθετηρίου Git...', 'patch_create_clone_failed': '❌ Αποτυχία κλωνοποίησης αποθετηρίου Git', 'patch_create_no_changes': 'ℹ️ Δεν βρέθηκαν αλλαγές μεταξύ STREAM_REPO και EMU_REPO', 'patch_create_success': '✅ Το patch δημιουργήθηκε με επιτυχία: {patch_file}', 'patch_version_from_header': 'Έκδοση patch από την κεφαλίδα: {patch_version}', 'patch_create_failed': '❌ Σφάλμα κατά τη δημιουργία patch: {error}', 'plugin_update': 'Διαθέσιμη ενημέρωση: {current} → {latest}', 'check_commit_button': '🔄 Έλεγχος για νέα commit', 'backup_old_start': 'ℹ️ Δημιουργία αντιγράφου ασφαλείας του παλιού patch…', 'backup_done': '✅ Το αντίγραφο ασφαλείας δημιουργήθηκε: {path}', 'update_downloading': 'Λήψη ενημέρωσης...', 'update_success_msg': 'Η ενημέρωση ολοκληρώθηκε! Το εργαλείο θα επανεκκινηθεί τώρα.', 'no_old_patch': 'ℹ️ Δεν βρέθηκε παλιό patch.', 'new_patch_installed': '✅ Το νέο patch εγκαταστάθηκε με επιτυχία: {path}', 'patch_check_ok': '✅ Ο έλεγχος patch ολοκληρώθηκε με επιτυχία (το patch εφαρμόζεται)! ', 'github_dialog_title': 'Ρυθμίσεις GitHub Emu', 'patch_check_fail': '❌ Ο έλεγχος patch απέτυχε (το patch δεν εφαρμόζεται)!', 'patch_failed': '❌ Η δημιουργία patch απέτυχε', 'oscam_uptodate': 'Το OSCam Git είναι ενημερωμένο.', 'oscam_update_found': 'Βρέθηκε διαθέσιμη ενημέρωση!', 'oscam_check_start': '🔍 Έλεγχος αποθετηρίου OSCam...', 'oscam_server_error': '❌ Σφάλμα: Ο διακομιστής OSCam δεν είναι προσβάσιμος.', 'check_commit_button_short': '🔄 Έλεγχος commit', 'check_commit_title': 'Έλεγχος commit OSCam', 'check_commit_current_hash': 'Τρέχον Hash:', 'check_commit_current': 'Τρέχουσα κατάσταση:', 'check_commit_old': 'Παλαιό:', 'check_commit_new': 'Νέο:', 'check_commit_no_hash': 'Σφάλμα: Δεν βρέθηκε hash commit.', 'check_commit_up_to_date': 'Δεν βρέθηκε νέο commit.', 'check_commit_new_found': 'Βρέθηκε νέο commit!', 'check_commit_error': 'Σφάλμα κατά τον έλεγχο:', 'patch_creating': '🔨 Δημιουργία patch', 'patch_created': '✅ Το patch δημιουργήθηκε', 'streamboard_preparing': '🔄 Προετοιμασία Streamboard', 'stream_master_head': 'Εντοπισμός του ακριβούς master HEAD του {description} (χρονικό όριο ανά πηγή: 35 s)...', 'stream_source_retry': 'Η πηγή δεν είναι προσβάσιμη, δοκιμή της επόμενης: {candidate} ({error})', 'stream_source_check': 'Έλεγχος πηγής Streamboard: {url}', 'stream_source_alternative': 'Χρήση εναλλακτικής πηγής Streamboard: {url}', 'stream_source_failed': 'Αποτυχία πηγής Streamboard: {url} ({error})', 'streamboard_updated': '✅ Το Streamboard ενημερώθηκε', 'emu_updated': '✅ Το OSCam-Emu ενημερώθηκε', 'streamboard_imported': '✅ Η αναθεώρηση Streamboard εισήχθη', 'patch_diff_created': '🔧 Δημιουργήθηκε το diff του patch', 'patch_checked': '✅ Το patch ελέγχθηκε με επιτυχία', 'patch_header_created': '📝 Προστέθηκε η κεφαλίδα του patch', 'oscam_emu_git_missing': '⚠️ Δεν βρέθηκε ο φάκελος OSCam-Emu Git: {path}', 'clean_done': '✅ Ο καθαρισμός ολοκληρώθηκε με επιτυχία!', 'oscam_emu_git_patch_start': '🔹 Δημιουργία patch OSCam-Emu Git...', 'git_patch_success': '✅ Το patch δημιουργήθηκε με επιτυχία! Αναθεώρηση Git: {rev}', 'cleaning_oscam_emu_git': '🔹 Εκκαθάριση φακέλου OSCam-Emu Git...', 'oscam_emu_git_deleted': '✅ Ο φάκελος OSCam-Emu Git διαγράφηκε με επιτυχία.', 'oscam_emu_git_clearing': '🔹 Εκκαθάριση φακέλου OSCam-Emu Git...', 'oscam_emu_git_cleared': '✅ Ο καθαρισμός ολοκληρώθηκε με επιτυχία!', 'cleanup_start': '🔹 Καθαρισμός καταλόγου εργασίας...', 'cleanup_success': '✅ Ο καθαρισμός ολοκληρώθηκε με επιτυχία! ✨', 'showing_commits': 'ℹ️ Εμφάνιση των τελευταίων {count} commit'})

TEXTS["it"].update({'repository': 'Repository', 'update_error': 'Errore durante il controllo degli aggiornamenti: {error}', 'info_title': 'Informazioni sul programma', 'stats_checkbox': 'Statistiche', 'stats_tooltip': 'Consenti/Disattiva le statistiche anonime di utilizzo.', 'new_version_available': 'Nuova versione disponibile', 'update_title': 'Aggiornamento disponibile', 'update_msg': 'È disponibile una nuova versione. Vuoi aggiornare ora?', 'exit': 'Esci', 'yes': 'Sì', 'no': 'No', 'cancel': 'Annulla', 'btn_plugin_update': 'Aggiornamento plugin', 'state_plugin_uptodate': 'Aggiornato', 'new_version_label': 'Nuova', 'old_version_label': 'Installata', 'state_plugin_update_available': 'Aggiornamento disponibile: {current} → {latest}', 'log_update_check_start': 'Controllo degli aggiornamenti in corso…', 'log_update_uptodate': '✅ Versione installata: {version}', 'log_update_declined': 'Aggiornamento ignorato', 'log_update_failed': '❌ Controllo aggiornamenti non riuscito: {error}', 'update_box_title': 'Aggiornamento software', 'update_box_msg': 'È disponibile una nuova versione!\n\nNuova: v{latest}\nAttuale: v{current}\n\nVuoi aggiornare ora?', 'msg_update_available_title': 'Aggiornamento disponibile', 'msg_update_available_text': 'È disponibile una nuova versione ({latest}).\nVersione attualmente installata: {current}.\nVuoi aggiornare ora?', 'update_fail': 'Aggiornamento non riuscito: {error}', 'update_success': '✅ Aggiornamento installato correttamente! Riavvia il programma.', 'update_available_msg': 'Versione attuale: {current}\nNuova versione: {latest}', 'restart_required_msg': 'È necessario riavviare il programma. Riavviare ora?', 'restart_tool_cancelled': "ℹ️ Riavvio annullato dall'utente.", 'update_started': 'ℹ️ Controllo aggiornamenti avviato...', 'update_backup_done': '✅ Vecchi file del plugin salvati.', 'update_download_failed': '❌ Download non riuscito: {error}', 'update_extract_failed': '❌ Estrazione della nuova versione non riuscita: {error}', 'update_done': '✅ Aggiornamento alla versione {version} completato correttamente.', 'restart_tool': 'Riavvia programma', 'update_check_done': 'Completato', 'backup_created': '✅ Backup creato: {file}', 'exit_question': 'Vuoi davvero chiudere il programma?', 'update_check_start': 'Controllo degli aggiornamenti in corso...', 'github_version_available': 'Nuova versione disponibile: {version}', 'github_version_fetch_failed': 'Controllo della versione non riuscito: {error}', 's3_install_button': 'Installa S3', 's3_tooltip': 'Clic sinistro: installa/aggiorna\nClic destro: seleziona manualmente il percorso', 'restarting_check': 'Riavvio del controllo di sistema...', 's3_choice_title': 'Seleziona S3 Simplebuild', 's3_choice_text': 'Quale menu S3 vuoi avviare?', 's3_choice_info': "Gorgone utilizza la cartella 's3'.\nSpeedy005 utilizza la cartella 's3_speedy005'.", 's3_choice_gorgone': 'S3 Gorgone', 's3_choice_speedy005': 'S3 Speedy005', 'button_cancel': 'Annulla', 's4_install_button': 'Installa S4', 'log_exported': '✅ Log esportato in:', 'log_save_error': '❌ Errore durante il salvataggio del log:', 'credits_label': 'Crediti / Autori', 'close': 'Chiudi', 'version_current': 'La versione {version} è aggiornata.', 'update_check_failed': 'Controllo aggiornamenti non riuscito: {error}', 'update_available_title': 'Aggiornamento disponibile', 'update_no_update': 'ℹ️ Nessun aggiornamento disponibile', 'installed_version': 'La versione installata è', 'new_version_found': 'Nuova versione disponibile', 'git_status': 'Visualizza commit', 'edit_patch_header': 'Modifica intestazione patch', 'github_emu_config_button': 'Modifica configurazione GitHub', 'github_upload_patch': 'Carica file patch', 'github_upload_emu': 'Carica OSCam-Emu Git', 'oscam_emu_git_patch': 'Patch OSCam-Emu Git', 'oscam_emu_git_clear': 'Pulisci OSCam-Emu Git', 'oscam_emu_patch_upload': 'Carica patch OSCam-Emu', 'update_declined': 'Aggiornamento rifiutato.', 'update_current_version': '✅ Versione installata: {version}', 'restart_required_title': 'Riavvio necessario', 'save': 'Salva', 'matrix_btn_exit': '🔙 ESCI DA MATRIX'})

TEXTS["it"].update({'STATS_TITLE': 'STATISTICHE DEL PROGRAMMA', 'STATS_GITHUB': 'GitHub:', 'STATS_LOCAL': 'Locale:', 'STATS_TOTAL': 'Totale:', 'foot_ok': 'OK', 'foot_ready': 'Pronto', 'stats_title': 'STATISTICHE DEL PROGRAMMA', 'stats_github': 'GitHub:', 'stats_local': 'Locale:', 'stats_total': 'Totale:', 'temp_repo_deleted': 'Repository temporaneo eliminato: {path}', 'patch_file_deleted': 'File patch eliminato: {path}', 'temp_repo_already_deleted': 'Repository temporaneo non trovato (già pulito): {path}', 'final_label': '🛠️ Cosa creiamo oggi?', 'info_tooltip': 'Informazioni / Aiuto', 'restart_tool_question': 'Vuoi riavviare il programma adesso?', 'info_text': "Questo strumento è un gestore completo di patch OSCam Emu.\n\nFunzioni:\n- Crea patch: genera una patch dal codice sorgente OSCam.\n- Rinnova patch: aggiorna la patch esistente.\n- Verifica patch: controlla se la patch può essere applicata correttamente.\n- Applica patch: applica la patch al repository Git locale OSCam-Emu.\n- Comprimi patch: crea un archivio ZIP della patch.\n- Backup patch: salva la vecchia patch e la sostituisce con la nuova versione.\n- Pulisci cartella patch: elimina i file temporanei dalla cartella (i file importanti rimangono).\n- Patch OSCam-Emu Git: applica la patch direttamente al repository Git OSCam-Emu.\n- Pulisci OSCam-Emu Git: elimina la cartella Git locale OSCam-Emu.\n- Caricamento GitHub: carica la patch o la cartella OSCam-Emu Git su GitHub.\n- Gestione credenziali GitHub: configura nome utente, token, URL del repository e branch.\n- Lingua e colore: cambia la lingua dell'interfaccia e i colori di pulsanti e barra di avanzamento.\n- Visualizzazione avanzamento: mostra il progresso delle operazioni.\n- Mostra commit: visualizza gli ultimi commit del repository locale.\n\n⚠️ Nota: durante il caricamento della patch viene sovrascritto solo il file `oscam-emu.patch`; tutti gli altri file rimangono invariati.", 'patch_create_start': 'ℹ️ Creazione della patch avviata...', 'patch_create_clone_start': '⚠️ Clonazione del repository Git...', 'patch_create_clone_failed': '❌ Clonazione del repository Git non riuscita', 'patch_create_no_changes': 'ℹ️ Nessuna modifica trovata tra STREAM_REPO ed EMU_REPO', 'patch_create_success': '✅ Patch creata correttamente: {patch_file}', 'patch_version_from_header': "Versione della patch dall'intestazione: {patch_version}", 'patch_create_failed': '❌ Errore durante la creazione della patch: {error}', 'plugin_update': 'Aggiornamento disponibile: {current} → {latest}', 'check_commit_button': '🔄 Verifica nuovi commit', 'backup_old_start': 'ℹ️ Creazione del backup della vecchia patch…', 'backup_done': '✅ Backup creato correttamente: {path}', 'update_downloading': "Download dell'aggiornamento in corso...", 'update_success_msg': 'Aggiornamento completato! Il programma verrà riavviato.', 'no_old_patch': 'ℹ️ Nessuna vecchia patch trovata.', 'new_patch_installed': '✅ Nuova patch installata correttamente: {path}', 'patch_check_ok': '✅ Verifica della patch riuscita (la patch può essere applicata)!', 'github_dialog_title': 'Configurazione GitHub Emu', 'patch_check_fail': '❌ Verifica della patch non riuscita (la patch non può essere applicata)!', 'patch_failed': '❌ Creazione della patch non riuscita', 'oscam_uptodate': 'Git OSCam è aggiornato.', 'oscam_update_found': 'Aggiornamento disponibile!', 'oscam_check_start': '🔍 Controllo del repository OSCam...', 'oscam_server_error': '❌ Errore: server OSCam non raggiungibile.', 'check_commit_button_short': '🔄 Verifica commit', 'check_commit_title': 'Controllo commit OSCam', 'check_commit_current_hash': 'Hash attuale:', 'check_commit_current': 'Stato attuale:', 'check_commit_old': 'Precedente:', 'check_commit_new': 'Nuovo:', 'check_commit_no_hash': 'Errore: nessun hash del commit trovato.', 'check_commit_up_to_date': 'Nessun nuovo commit trovato.', 'check_commit_new_found': 'Nuovo commit trovato!', 'check_commit_error': 'Errore durante il controllo:', 'check_commit_tooltip': "Clicca qui per verificare se è disponibile un nuovo commit nel repository Streamboard. Se viene trovato un nuovo commit, verrà visualizzato l'ultimo hash.", 'patch_creating': '🔨 Creazione della patch', 'patch_created': '✅ Patch creata', 'streamboard_preparing': '🔄 Preparazione di Streamboard', 'stream_master_head': "Ricerca dell'HEAD master esatto di {description} (timeout per sorgente: 35 s)...", 'stream_source_retry': 'Sorgente non raggiungibile, tentativo con la sorgente successiva: {candidate} ({error})', 'stream_source_check': 'Controllo della sorgente Streamboard: {url}', 'stream_source_alternative': 'Utilizzo della sorgente Streamboard alternativa: {url}', 'stream_source_failed': 'Sorgente Streamboard non riuscita: {url} ({error})', 'streamboard_updated': '✅ Streamboard aggiornato', 'emu_updated': '✅ OSCam-Emu aggiornato', 'streamboard_imported': '✅ Revisione Streamboard importata', 'patch_diff_created': '🔧 Diff della patch creato', 'patch_checked': '✅ Patch verificata correttamente', 'patch_header_created': '📝 Intestazione della patch inserita', 'oscam_emu_git_missing': '⚠️ Cartella OSCam-Emu Git non trovata: {path}', 'clean_done': '✅ Pulizia completata correttamente!', 'oscam_emu_git_patch_start': '🔹 Creazione della patch OSCam-Emu Git...', 'git_patch_success': '✅ Patch creata correttamente! Revisione Git: {rev}', 'cleaning_oscam_emu_git': '🔹 Svuotamento della cartella OSCam-Emu Git...', 'oscam_emu_git_deleted': '✅ Cartella OSCam-Emu Git eliminata correttamente.', 'oscam_emu_git_clearing': '🔹 Svuotamento della cartella OSCam-Emu Git...', 'oscam_emu_git_cleared': '✅ Pulizia completata correttamente!', 'cleanup_start': '🔹 Pulizia della directory di lavoro...', 'cleanup_success': '✅ Pulizia completata correttamente! ✨', 'showing_commits': 'ℹ️ Visualizzazione degli ultimi {count} commit'})

# Ergänze fehlende Keys aus EN nach DE
for key, value in TEXTS["en"].items():
    if key not in TEXTS["de"]:
        TEXTS["de"][key] = value

# Unbedingt einmalig vor GUI-Start aufrufen

# Korrektur der Platzhalter in PL und TR
TEXTS["pl"]["patch_emu_git_start"] = "🔹 Tworzenie patcha OSCam-Emu Git... (Ścieżka: {path})"
TEXTS["tr"]["patch_emu_git_start"] = "🚀 OSCam-Emu Git patch işlemi başlatılıyor... (Yol: {path})"

fill_missing_keys(TEXTS)

TEXTS["tr"]["patch_emu_git_start"] = "🔹 OSCam-Emu Git patch'i oluşturuluyor... (Yol: {path})"


TEXTS["gr"]['log_start_header'] = '--- OSCam Emu Patch Generator έκδοση v{} ---'
TEXTS["gr"]['info_text'] = 'Αυτό το εργαλείο είναι ένας ολοκληρωμένος διαχειριστής patch OSCam Emu.\n\nΛειτουργίες:\n- Δημιουργία patch: Δημιουργεί ένα patch από τον πηγαίο κώδικα του OSCam.\n- Ανανέωση patch: Ενημερώνει το υπάρχον patch.\n- Έλεγχος patch: Επαληθεύει αν το patch μπορεί να εφαρμοστεί σωστά.\n- Εφαρμογή patch: Εφαρμόζει το patch στο τοπικό αποθετήριο OSCam-Emu Git.\n- Συμπίεση patch: Συσκευάζει το patch σε αρχείο ZIP.\n- Αντίγραφο ασφαλείας patch: Δημιουργεί αντίγραφο του παλιού patch και το αντικαθιστά με τη νέα έκδοση.\n- Καθαρισμός φακέλου patch: Διαγράφει προσωρινά αρχεία από τον φάκελο patch (τα σημαντικά αρχεία παραμένουν).\n- Τροποποίηση OSCam-Emu Git: Εφαρμόζει το patch απευθείας στο αποθετήριο OSCam-Emu Git.\n- Καθαρισμός OSCam-Emu Git: Διαγράφει τον τοπικό φάκελο OSCam-Emu Git.\n- Μεταφόρτωση στο GitHub: Μεταφορτώνει το patch ή τον φάκελο OSCam-Emu Git στο GitHub.\n- Διαχείριση στοιχείων GitHub: Ρυθμίζει όνομα χρήστη, token, URL αποθετηρίου και branch.\n- Αλλαγή γλώσσας και χρώματος: Αλλάζει τη γλώσσα του γραφικού περιβάλλοντος και τα χρώματα των κουμπιών και της γραμμής προόδου.\n- Ένδειξη προόδου: Εμφανίζει την πρόοδο των ενεργειών στη γραμμή προόδου.\n- Εμφάνιση commits: Εμφανίζει τα πιο πρόσφατα commits από το τοπικό αποθετήριο.\n\n⚠️ Σημείωση: Κατά τη μεταφόρτωση patch αντικαθίσταται μόνο το `oscam-emu.patch`. Όλα τα υπόλοιπα αρχεία παραμένουν ανέπαφα.'
TEXTS["gr"]['check_commit_tooltip'] = 'Κάντε κλικ εδώ για να ελέγξετε αν υπάρχει νέο commit στο αποθετήριο Streamboard. Εάν βρεθεί νέο commit, θα εμφανιστεί το hash του τελευταίου commit.'

# FINAL_LANGUAGE_KEY_CLEANUP
# Bereinigt fehlerhafte Übersetzungsschlüssel und Texte.

# Leere Schlüssel entfernen
for _lang in ("it", "pl", "tr", "gr"):
    TEXTS[_lang].pop("", None)

# Italienisch
TEXTS["it"].pop("Informazioni / Aiuto", None)
TEXTS["it"]["info_tooltip"] = "Informazioni / Aiuto"
TEXTS["it"]["repo"] = "Repository"
TEXTS["it"]["active_conf"] = "🛠️ Configurazione attiva:"
TEXTS["it"]["check_tools_button"] = "🛠️ Verifica strumenti"
TEXTS["it"]["patch_emu_git_clone"] = "🌐 Clonazione di Streamboard..."

# Polnisch
TEXTS["pl"].pop("github_patch_uploaded\n", None)
TEXTS["pl"].pop("n o_update_found", None)
TEXTS["pl"]["github_patch_uploaded"] = "✅ Patch została pomyślnie przesłana: {patch_version}"
TEXTS["pl"]["no_update_found"] = "Nie znaleziono dostępnych aktualizacji."
TEXTS["pl"]["patch_emu_git_prepare"] = "🧹 Przygotowywanie środowiska roboczego..."
TEXTS["pl"]["config"] = "🛠️ Aktywna konfiguracja:"

# Turecki
for _key in ("g ithub_patch_uploaded", "github_patch_uploaded\n",
             "tools_read y", "patch_a uthor"):
    TEXTS["tr"].pop(_key, None)

TEXTS["tr"]["github_patch_uploaded"] = "✅ Patch başarıyla yüklendi: {patch_version}"
TEXTS["tr"]["tools_ready"] = "Gerekli tüm sistem araçları hazır."
TEXTS["tr"]["patch_author"] = "Patch yazarı"
TEXTS["tr"]["patch_emu_git_prepare"] = "🧹 Çalışma alanı hazırlanıyor..."

# Yunanca
for _key in ("pat ch_emu_git_clone", "info_tool tip"):
    TEXTS["gr"].pop(_key, None)

TEXTS["gr"]["patch_emu_git_clone"] = "🌐 Streamboard klonlanıyor..."
TEXTS["gr"]["info_tooltip"] = "Πληροφορίες / Βοήθεια"
TEXTS["gr"]["github_patch_uploaded"] = "✅ Το patch μεταφορτώθηκε με επιτυχία: {patch_version}"
TEXTS["gr"]["config"] = "🛠️ Ενεργή διαμόρφωση:"
TEXTS["gr"]["patch_author"] = "Συντάκτης patch"
TEXTS["gr"]["restart_tool_question"] = "Θέλετε να επανεκκινήσετε το εργαλείο τώρα;"

# ==========================================================
# FINAL TRANSLATION IMPROVEMENTS
# ==========================================================

# Deutsch
TEXTS["de"].update({
    "plugin_uptodate": "✅ Plugin ist aktuell (Version: {current})",
    "git_revision_failed": "⚠️ Git-Revision konnte nicht ermittelt werden: {error}",
    "update_download_failed": "❌ Download fehlgeschlagen: {error}",
    "update_extract_failed": "❌ Neue Version konnte nicht entpackt werden: {error}",
    "temp_repo_already_deleted": "Temporäres Repository nicht gefunden (bereits bereinigt): {path}",
    "lang_label": "Sprache",
    "dir_label": "Patch-Verzeichnis",
    "auto_update_label": "Automatische Updates",
})

# Italienisch
TEXTS["it"].update({
    "repo_label": "Repository",
    "repo": "Repository",
    "repository": "Repository",
})

# Polnisch
TEXTS["pl"].update({
    "log_sys_info": "System: {} {}",
})

# Türkisch
TEXTS["tr"].update({
    "net_online": "Çevrimiçi",
    "net_offline": "Çevrimdışı",
})

# Griechisch
TEXTS["gr"].update({
    "net_online": "Σε σύνδεση",
    "net_offline": "Εκτός σύνδεσης",
})

# --- OSCam Emu Git: einheitliche Übersetzungen für alle sechs Sprachen ---
_EMU_GIT_BUTTON_TRANSLATIONS = {
    "de": {
        "streamboard_checkout": "Streamboard Revision",
        "oscam_emu_revision": "OSCam-Emu Revision",
        "open_work_folder_button": "📁 Arbeitsordner",
        "open_temp_repo_button": "📁 Temp-Repo",
        "open_emu_git_button": "📁 Emu-Git",
        "check_tools_button": "🛠️ Tools prüfen",
        "modifier_button_text": "👤 Patch Autor",
        "repo_url_button": "🌐 Repo URL",
        "patch_online_download": "Patch Online laden",
        "check_commit_button": "🔄 Commit prüfen",
        "backup_button_text": "💾 Backup erstellen",
    },
    "en": {
        "streamboard_checkout": "Streamboard Revision",
        "oscam_emu_revision": "OSCam-Emu Revision",
        "open_work_folder_button": "📁 Working Folder",
        "open_temp_repo_button": "📁 Temp Repo",
        "open_emu_git_button": "📁 Emu Git",
        "check_tools_button": "🛠️ Check Tools",
        "modifier_button_text": "👤 Patch Author",
        "repo_url_button": "🌐 Repo URL",
        "patch_online_download": "Load Patch Online",
        "check_commit_button": "🔄 Check Commit",
        "backup_button_text": "💾 Create Backup",
    },
    "it": {
        "streamboard_checkout": "Revisione Streamboard",
        "oscam_emu_revision": "Revisione OSCam-Emu",
        "open_work_folder_button": "📁 Cartella di lavoro",
        "open_temp_repo_button": "📁 Repository temporaneo",
        "open_emu_git_button": "📁 Emu Git",
        "check_tools_button": "🛠️ Verifica strumenti",
        "modifier_button_text": "👤 Autore patch",
        "repo_url_button": "🌐 URL Repository",
        "patch_online_download": "Carica patch online",
        "check_commit_button": "🔄 Controlla commit",
        "backup_button_text": "💾 Crea backup",
        "copy_log_button": 'COPIA LOG',
        "copy_log_tooltip": 'Copia tutto il testo visibile della console negli appunti',
        "analyze_build_logs_button": 'ANALIZZA BUILD LOG',
        "analyze_build_logs_tooltip": 'Controlla il build log più recente per errori e avvisi comuni',
        "diagnostics_button": 'DIAGNOSTICA SISTEMA',
        "diagnostics_tooltip": 'Controlla sistema, cartelle degli strumenti e build log esistenti; non avvia una compilazione',
        "log_history_button": 'CRONOLOGIA BUILD LOG',
        "log_history_tooltip": 'Confronta i build log per stato, ora e indicatori di errore',
        "clear_console_button": 'SVUOTA CONSOLE',
        "clear_console_tooltip": 'Cancella solo il testo visibile della console; i file di log restano invariati',
        "cyber_center_button": 'OSCAM CONTROL CENTER',
        "cyber_center_tooltip": 'Centro per tutte le funzioni OSCam Control Center',
        "patch_diff_button": 'CONFRONTA PATCH',
        "patch_diff_tooltip": 'Confronta due file patch o commit Git',
        "achievement_button": '🏆 RISULTATI',
        "achievement_tooltip": 'Mostra i tuoi risultati e progressi OSCam',
        "ai_assistant_button": '🤖 ASSISTENTE IA',
        "ai_assistant_tooltip": 'Apri la chat IA per analisi delle patch e risoluzione dei problemi',
        "music_player_button": '🎚 Apri lettore',
        "music_player_tooltip": 'Apri il Cyber Music Player separato',
        'patch_copy_s3_ncam_tooltip': 'Copia oscam-emu.patch nella cartella patch S3-NCam-Bonecrew configurata.',
        'patch_copy_s4_tooltip': 'Copia oscam-emu.patch nella cartella patch S4 configurata.',
        'weather_button': '🌤 Mostra meteo',
        'weather_tooltip': 'Mostra il meteo attuale e le previsioni per 5 giorni',
        'log_button': '💾 Salva log',
        'log_tooltip': 'Salva il contenuto attuale del log in un file.',
        'music_button': '🎵 Attiva musica',
        'music_tooltip': 'Attiva o disattiva la musica di sottofondo dalla cartella sounds.',
        'music_title_tooltip': 'Seleziona un brano',
        'oscam_source_button': 'URL Git di OSCam',
        'oscam_source_tooltip': 'Seleziona la sorgente per Create Patch e OSCam-Emu-Git Patch',
        'console_panel_title': 'CONSOLE DI SISTEMA LIVE / STATO E LOG',
        "system_status": "STATO DEL SISTEMA:",
        "sound": "SUONO",
        "matrix_mode": "📟 MODALITÀ MATRIX",
        "theme_button": "🌓 TEMA",
        "language_box_tooltip": "Seleziona la lingua dell'interfaccia",
        "commit_spin_tooltip": "Imposta il numero di commit da visualizzare o analizzare",
        'work_folder_button': 'Cartella di lavoro',
        'temp_repo_button': 'Repo temporaneo',
        'emu_git_button': 'Emu Git',
        'patch_online_button': '🌐 Carica patch',
    "commit_check_button": '🔄 Controlla commit',
    "backup_button": '💾 Crea backup',
    "backup_tooltip": 'Crea backup/backup_gi.zip con lo stato attuale del progetto',
    "settings_title": 'Impostazioni',
    "patch_build_title": 'PATCH & COMPILAZIONE',
        'loading_config': 'Caricamento configurazione...',
        'config_ready': 'Configurazione pronta',
        'saved': 'Salvato!',
        'github_config_saved': '✅ Configurazione GitHub salvata.',
        'save': 'Salva',
        'cancel': 'Annulla',
        'color_theme_tooltip': "Scegli il tema colore dell'interfaccia",
        'live_system_monitor': 'LIVE | Monitor di sistema',
        "music_on": '🎵 Attiva musica',
        "music_off": '🎵 Disattiva musica',
        "music_toggle_tooltip": 'Attiva o disattiva la musica di sottofondo dalla cartella sounds.',
        'github_configuration_title': 'Configurazione GitHub',
        'final_label': '🛠️ Cosa costruiamo oggi?',
        'oscam_uptodate': 'OSCam Git è aggiornato.',
    },
    "pl": {
        "streamboard_checkout": "Rewizja Streamboard",
        "oscam_emu_revision": "Rewizja OSCam-Emu",
        "open_work_folder_button": "📁 Folder roboczy",
        "open_temp_repo_button": "📁 Repo tymczasowe",
        "open_emu_git_button": "📁 Emu Git",
        "check_tools_button": "🛠️ Sprawdź narzędzia",
        "modifier_button_text": "👤 Autor patcha",
        "repo_url_button": "🌐 URL repozytorium",
        "patch_online_download": "Pobierz patch online",
        "check_commit_button": "🔄 Sprawdź commit",
        "backup_button_text": "💾 Utwórz kopię zapasową",
        "copy_log_button": 'KOPIUJ LOG',
        "copy_log_tooltip": 'Kopiuje całą widoczną zawartość konsoli do schowka',
        "analyze_build_logs_button": 'ANALIZUJ BUILD LOG',
        "analyze_build_logs_tooltip": 'Sprawdź najnowszy build log pod kątem typowych błędów i ostrzeżeń',
        "diagnostics_button": 'DIAGNOSTYKA SYSTEMU',
        "diagnostics_tooltip": 'Sprawdź system, katalogi narzędzi i istniejące build logi; nie uruchamia kompilacji',
        "log_history_button": 'HISTORIA BUILD LOGÓW',
        "log_history_tooltip": 'Porównaj build logi według statusu, czasu i oznak błędów',
        "clear_console_button": 'WYCZYŚĆ KONSOLĘ',
        "clear_console_tooltip": 'Wyczyść tylko widoczną zawartość konsoli; pliki logów pozostaną bez zmian',
        "cyber_center_button": 'OSCAM CONTROL CENTER',
        "cyber_center_tooltip": 'Centrum wszystkich funkcji OSCam Control Center',
        "patch_diff_button": 'PORÓWNAJ PATCH-E',
        "patch_diff_tooltip": 'Porównaj dwa pliki patch lub commity Git',
        "achievement_button": '🏆 OSIĄGNIĘCIA',
        "achievement_tooltip": 'Wyświetl osiągnięcia i postępy OSCam',
        "ai_assistant_button": '🤖 ASYSTENT AI',
        "ai_assistant_tooltip": 'Otwórz czat AI do analizy patchy i rozwiązywania problemów',
        "music_player_button": '🎚 Otwórz odtwarzacz',
        "music_player_tooltip": 'Otwórz oddzielny Cyber Music Player',
        'patch_copy_s3_ncam_tooltip': 'Kopiuje oscam-emu.patch do skonfigurowanego folderu patch S3-NCam-Bonecrew.',
        'patch_copy_s4_tooltip': 'Kopiuje oscam-emu.patch do skonfigurowanego folderu patch S4.',
        'weather_button': '🌤 Pokaż pogodę',
        'weather_tooltip': 'Pokaż aktualną pogodę i prognozę na 5 dni',
        'log_button': '💾 Zapisz log',
        'log_tooltip': 'Zapisuje bieżący log do pliku.',
        'music_button': '🎵 Włącz muzykę',
        'music_tooltip': 'Włącza lub wyłącza muzykę z folderu sounds.',
        'music_title_tooltip': 'Wybierz utwór',
        'oscam_source_button': 'Adres Git OSCam',
        'oscam_source_tooltip': 'Wybierz źródło dla Create Patch i OSCam-Emu-Git Patch',
        'console_panel_title': 'KONSOLA SYSTEMOWA NA ŻYWO / STATUS I LOGI',
        "system_status": "STAN SYSTEMU:",
        "sound": "DŹWIĘK",
        "matrix_mode": "📟 TRYB MATRIX",
        "theme_button": "🌓 MOTYW",
        "language_box_tooltip": "Wybierz język interfejsu",
        "commit_spin_tooltip": "Ustaw liczbę commitów do wyświetlenia lub analizy",
        'work_folder_button': 'Folder roboczy',
        'temp_repo_button': 'Repo tymczasowe',
        'emu_git_button': 'Emu Git',
        'patch_online_button': '🌐 Pobierz patch',
    "commit_check_button": '🔄 Sprawdź commit',
    "backup_button": '💾 Utwórz kopię',
    "backup_tooltip": 'Tworzy backup/backup_gi.zip z aktualnym stanem projektu',
    "settings_title": 'Ustawienia',
    "patch_build_title": 'PATCH I BUDOWANIE',
        'loading_config': 'Ładowanie konfiguracji...',
        'config_ready': 'Konfiguracja gotowa',
        'saved': 'Zapisano!',
        'github_config_saved': '✅ Konfiguracja GitHub została zapisana.',
        'save': 'Zapisz',
        'cancel': 'Anuluj',
        'color_theme_tooltip': 'Wybierz motyw kolorystyczny interfejsu',
        'live_system_monitor': 'LIVE | Monitor systemu',
        "music_on": '🎵 Włącz muzykę',
        "music_off": '🎵 Wyłącz muzykę',
        "music_toggle_tooltip": 'Włączanie lub wyłączanie muzyki z folderu sounds.',
        'github_configuration_title': 'Konfiguracja GitHub',
        'final_label': '🛠️ Co dzisiaj tworzymy?',
        'oscam_uptodate': 'OSCam Git jest aktualny.',
    },
    "tr": {
        "streamboard_checkout": "Streamboard Sürümü",
        "oscam_emu_revision": "OSCam-Emu Sürümü",
        "open_work_folder_button": "📁 Çalışma klasörü",
        "open_temp_repo_button": "📁 Geçici depo",
        "open_emu_git_button": "📁 Emu Git",
        "check_tools_button": "🛠️ Araçları kontrol et",
        "modifier_button_text": "👤 Patch yazarı",
        "repo_url_button": "🌐 Repo URL",
        "patch_online_download": "Patch'i çevrimiçi yükle",
        "check_commit_button": "🔄 Commit kontrolü",
        "backup_button_text": "💾 Yedek oluştur",
        "copy_log_button": "LOG'U KOPYALA",
        "copy_log_tooltip": 'Konsolda görünen tüm çıktıyı panoya kopyala',
        "analyze_build_logs_button": "BUILD LOG'UNU ANALİZ ET",
        "analyze_build_logs_tooltip": 'En yeni build log dosyasını yaygın hata ve uyarılar için kontrol et',
        "diagnostics_button": 'SİSTEM TANILAMA',
        "diagnostics_tooltip": 'Sistemi, araç dizinlerini ve mevcut build loglarını kontrol et; derleme başlatmaz',
        "log_history_button": 'BUILD LOG GEÇMİŞİ',
        "log_history_tooltip": 'Tüm build loglarını duruma, zamana ve hata göstergelerine göre karşılaştır',
        "clear_console_button": 'KONSOLU TEMİZLE',
        "clear_console_tooltip": 'Yalnızca görünür konsol çıktısını temizle; log dosyaları değişmez',
        "cyber_center_button": 'OSCAM CONTROL CENTER',
        "cyber_center_tooltip": 'Tüm OSCam Control Center işlevlerinin merkezi',
        "patch_diff_button": "PATCH'LERİ KARŞILAŞTIR",
        "patch_diff_tooltip": "İki patch dosyasını veya Git commit'ini karşılaştır",
        "achievement_button": '🏆 BAŞARILAR',
        "achievement_tooltip": 'OSCam başarılarını ve ilerlemeni görüntüle',
        "ai_assistant_button": '🤖 YAPAY ZEKA ASİSTANI',
        "ai_assistant_tooltip": 'Patch analizi ve sorun giderme için yapay zeka sohbetini aç',
        "music_player_button": '🎚 Oynatıcıyı aç',
        "music_player_tooltip": "Ayrı Cyber Music Player'ı aç",
        'patch_copy_s3_ncam_tooltip': 'oscam-emu.patch dosyasını yapılandırılmış S3-NCam-Bonecrew patch klasörüne kopyalar.',
        'patch_copy_s4_tooltip': 'oscam-emu.patch dosyasını yapılandırılmış S4 patch klasörüne kopyalar.',
        'weather_button': '🌤 Hava durumunu göster',
        'weather_tooltip': 'Güncel hava durumunu ve 5 günlük tahmini göster',
        'log_button': '💾 Günlüğü kaydet',
        'log_tooltip': 'Geçerli günlük içeriğini bir dosyaya kaydeder.',
        'music_button': '🎵 Müziği aç',
        'music_tooltip': 'sounds klasöründeki arka plan müziğini açar veya kapatır.',
        'music_title_tooltip': 'Müzik parçası seç',
        'oscam_source_button': 'OSCam Git URL',
        'oscam_source_tooltip': 'Create Patch ve OSCam-Emu-Git Patch için kaynak seç',
        'console_panel_title': 'CANLI SİSTEM KONSOLU / DURUM VE GÜNLÜKLER',
        "system_status": "SİSTEM DURUMU:",
        "sound": "SES",
        "matrix_mode": "📟 MATRIX MODU",
        "theme_button": "🌓 TEMA",
        "language_box_tooltip": "Arayüz dilini seçin",
        "commit_spin_tooltip": "Görüntülenecek veya analiz edilecek commit sayısını belirleyin",
        'work_folder_button': 'Çalışma klasörü',
        'temp_repo_button': 'Geçici depo',
        'emu_git_button': 'Emu Git',
        'patch_online_button': '🌐 Patch yükle',
    "commit_check_button": '🔄 Commit kontrolü',
    "backup_button": '💾 Yedek oluştur',
    "backup_tooltip": 'Mevcut proje durumuyla backup/backup_gi.zip dosyasını oluşturur',
    "settings_title": 'Ayarlar',
    "patch_build_title": 'PATCH VE DERLEME',
        'loading_config': 'Yapılandırma yükleniyor...',
        'config_ready': 'Yapılandırma hazır',
        'saved': 'Kaydedildi!',
        'github_config_saved': '✅ GitHub yapılandırması kaydedildi.',
        'save': 'Kaydet',
        'cancel': 'İptal',
        'color_theme_tooltip': 'Arayüz renk temasını seçin',
        'live_system_monitor': 'CANLI | Sistem Monitörü',
        "music_on": '🎵 Müziği aç',
        "music_off": '🎵 Müziği kapat',
        "music_toggle_tooltip": 'sounds klasöründeki arka plan müziğini açıp kapatır.',
        'github_configuration_title': 'GitHub Yapılandırması',
        'final_label': '🛠️ Bugün ne oluşturuyoruz?',
        'oscam_uptodate': 'OSCam Git güncel.',
    },
    "gr": {
        "streamboard_checkout": "Έκδοση Streamboard",
        "oscam_emu_revision": "Έκδοση OSCam-Emu",
        "open_work_folder_button": "📁 Φάκελος εργασίας",
        "open_temp_repo_button": "📁 Προσωρινό repo",
        "open_emu_git_button": "📁 Emu Git",
        "check_tools_button": "🛠️ Έλεγχος εργαλείων",
        "modifier_button_text": "👤 Συντάκτης patch",
        "repo_url_button": "🌐 URL repo",
        "patch_online_download": "Φόρτωση patch online",
        "check_commit_button": "🔄 Έλεγχος commit",
        "backup_button_text": "💾 Δημιουργία αντιγράφου",
        "copy_log_button": 'ΑΝΤΙΓΡΑΦΗ LOG',
        "copy_log_tooltip": 'Αντιγραφή όλης της ορατής εξόδου της κονσόλας στο πρόχειρο',
        "analyze_build_logs_button": 'ΑΝΑΛΥΣΗ BUILD LOG',
        "analyze_build_logs_tooltip": 'Έλεγχος του πιο πρόσφατου build log για συνηθισμένα σφάλματα και προειδοποιήσεις',
        "diagnostics_button": 'ΔΙΑΓΝΩΣΗ ΣΥΣΤΗΜΑΤΟΣ',
        "diagnostics_tooltip": 'Έλεγχος συστήματος, φακέλων εργαλείων και υπαρχόντων build log· δεν ξεκινά μεταγλώττιση',
        "log_history_button": 'ΙΣΤΟΡΙΚΟ BUILD LOG',
        "log_history_tooltip": 'Σύγκριση όλων των build log ανά κατάσταση, ώρα και ενδείξεις σφαλμάτων',
        "clear_console_button": 'ΕΚΚΑΘΑΡΙΣΗ ΚΟΝΣΟΛΑΣ',
        "clear_console_tooltip": 'Εκκαθάριση μόνο της ορατής εξόδου· τα αρχεία log παραμένουν ανέπαφα',
        "cyber_center_button": 'OSCAM CONTROL CENTER',
        "cyber_center_tooltip": 'Κεντρικό σημείο για όλες τις λειτουργίες OSCam Control Center',
        "patch_diff_button": 'ΣΥΓΚΡΙΣΗ PATCH',
        "patch_diff_tooltip": 'Σύγκριση δύο αρχείων patch ή Git commit',
        "achievement_button": '🏆 ΕΠΙΤΕΥΓΜΑΤΑ',
        "achievement_tooltip": 'Προβολή των επιτευγμάτων και της προόδου OSCam',
        "ai_assistant_button": '🤖 ΒΟΗΘΟΣ AI',
        "ai_assistant_tooltip": 'Άνοιγμα συνομιλίας AI για ανάλυση patch και αντιμετώπιση προβλημάτων',
        "music_player_button": '🎚 Άνοιγμα αναπαραγωγής',
        "music_player_tooltip": 'Άνοιγμα του ξεχωριστού Cyber Music Player',
        'patch_copy_s3_ncam_tooltip': 'Αντιγράφει το oscam-emu.patch στον ρυθμισμένο φάκελο patch S3-NCam-Bonecrew.',
        'patch_copy_s4_tooltip': 'Αντιγράφει το oscam-emu.patch στον ρυθμισμένο φάκελο patch S4.',
        'weather_button': '🌤 Εμφάνιση καιρού',
        'weather_tooltip': 'Εμφάνιση τρέχοντος καιρού και πρόγνωσης 5 ημερών',
        'log_button': '💾 Αποθήκευση αρχείου καταγραφής',
        'log_tooltip': 'Αποθηκεύει το τρέχον αρχείο καταγραφής σε αρχείο.',
        'music_button': '🎵 Ενεργοποίηση μουσικής',
        'music_tooltip': 'Ενεργοποιεί ή απενεργοποιεί τη μουσική από τον φάκελο sounds.',
        'music_title_tooltip': 'Επιλογή μουσικού κομματιού',
        'oscam_source_button': 'OSCam Git URL',
        'oscam_source_tooltip': 'Επιλογή πηγής για Create Patch και OSCam-Emu-Git Patch',
        'console_panel_title': 'ΖΩΝΤΑΝΗ ΚΟΝΣΟΛΑ ΣΥΣΤΗΜΑΤΟΣ / ΚΑΤΑΣΤΑΣΗ ΚΑΙ ΑΡΧΕΙΑ ΚΑΤΑΓΡΑΦΗΣ',
        "system_status": "ΚΑΤΑΣΤΑΣΗ ΣΥΣΤΗΜΑΤΟΣ:",
        "sound": "ΗΧΟΣ",
        "matrix_mode": "📟 ΛΕΙΤΟΥΡΓΙΑ MATRIX",
        "theme_button": "🌓 ΘΕΜΑ",
        "language_box_tooltip": "Επιλέξτε τη γλώσσα του περιβάλλοντος",
        "commit_spin_tooltip": "Ορίστε τον αριθμό των commit προς εμφάνιση ή ανάλυση",
        'work_folder_button': 'Φάκελος εργασίας',
        'temp_repo_button': 'Προσωρινό repo',
        'emu_git_button': 'Emu Git',
        'patch_online_button': '🌐 Φόρτωση patch',
    "commit_check_button": '🔄 Έλεγχος commit',
    "backup_button": '💾 Δημιουργία αντιγράφου',
    "backup_tooltip": 'Δημιουργεί το backup/backup_gi.zip με την τρέχουσα κατάσταση του έργου',
    "settings_title": 'Ρυθμίσεις',
    "patch_build_title": 'PATCH & BUILD',
        'loading_config': 'Φόρτωση διαμόρφωσης...',
        'config_ready': 'Η διαμόρφωση είναι έτοιμη',
        'saved': 'Αποθηκεύτηκε!',
        'github_config_saved': '✅ Η διαμόρφωση GitHub αποθηκεύτηκε.',
        'save': 'Αποθήκευση',
        'cancel': 'Ακύρωση',
        'color_theme_tooltip': 'Επιλέξτε το χρωματικό θέμα της διεπαφής',
        'live_system_monitor': 'ΖΩΝΤΑΝΑ | Παρακολούθηση συστήματος',
        "music_on": '🎵 Ενεργοποίηση μουσικής',
        "music_off": '🎵 Απενεργοποίηση μουσικής',
        "music_toggle_tooltip": 'Ενεργοποίηση ή απενεργοποίηση μουσικής από τον φάκελο sounds.',
        'github_configuration_title': 'Διαμόρφωση GitHub',
        'final_label': '🛠️ Τι θα δημιουργήσουμε σήμερα;',
        'oscam_uptodate': 'Το OSCam Git είναι ενημερωμένο.',
    },
}

for _emu_lang, _emu_values in _EMU_GIT_BUTTON_TRANSLATIONS.items():
    TEXTS.setdefault(_emu_lang, {}).update(_emu_values)

del _EMU_GIT_BUTTON_TRANSLATIONS, _emu_lang, _emu_values


TEXTS["it"]["final_label"] = "🛠️ Cosa costruiamo oggi?"


TEXTS["it"]["final_label"] = "🛠️ Cosa costruiamo oggi?"
