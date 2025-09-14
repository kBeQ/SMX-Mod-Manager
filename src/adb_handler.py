# --- Filename: adb_handler.py ---
import subprocess
import os
from tkinter import messagebox
import zipfile
import tempfile
import shutil

class AdbHandler:
    def __init__(self, controller):
        self.controller = controller

    def is_device_connected(self):
        """Checks if a device is connected and authorized via ADB."""
        stdout, _ = self.send_adb_command_with_output("devices")
        if stdout is None:
            return False
        lines = stdout.strip().splitlines()
        return len(lines) > 1 and any("device" in line and "unauthorized" not in line for line in lines[1:])

    def is_game_process_running(self, package_name):
        """Checks if the specified game package process is running on the device."""
        stdout, _ = self.send_adb_command_with_output(f"shell pidof {package_name}")
        return stdout is not None and stdout.strip() != ""

    def directory_exists(self, path, log_func=None):
        """Checks if a directory exists on the device."""
        command = f"shell if [ -d '{path}' ]; then echo 'exists'; else echo 'not_exists'; fi"
        stdout, stderr = self.send_adb_command_with_output(command)
        if log_func and stderr:
            log_func(f"Error checking directory '{path}': {stderr.strip()}")
        return stdout is not None and "exists" in stdout.strip()

    def launch_game_activity(self, package_name, activity_name, log_func):
        full_activity = f"{package_name}/{activity_name}"
        log_func(f"Attempting to launch game: {full_activity}")
        self.send_adb_command(f"shell am start -n {full_activity}", log_func)

    def force_stop_package(self, package_name, log_func):
        log_func(f"Attempting to force-stop game: {package_name}")
        self.send_adb_command(f"shell am force-stop {package_name}", log_func)

    def list_device_files(self, path):
        command = f"shell find '{path.strip()}' -maxdepth 1"
        stdout, stderr = self.send_adb_command_with_output(command)
        if stdout is None and stderr is not None:
            self.controller.frames["Mod Manager"].console_log(f"ADB command failed for path '{path}': {stderr}")
            return None
        if stderr and "unauthorized" in stderr:
            messagebox.showerror("Device Unauthorized", "Could not connect. Please accept the 'Allow USB Debugging' prompt.")
            return None
        if stderr and "No such file or directory" not in stderr:
            self.controller.frames["Mod Manager"].console_log(f"ADB Find Error for path '{path}': {stderr.strip()}")
        if not stdout: return []
        lines = [line.strip() for line in stdout.splitlines() if line.strip()]
        if len(lines) <= 1: return []
        content_paths = lines[1:]
        basenames = [p.split('/')[-1] for p in content_paths]
        return basenames

    def pull_file(self, device_path, local_path):
        _, stderr = self.send_adb_command_with_output(f'pull "{device_path.strip()}" "{local_path.strip()}"')
        return not stderr
    
    # --- MODIFIED: This function now handles unzipping from a source .zip file ---
    def push_mod(self, source_zip_path, device_folder_name, target_dir, log_func):
        if not os.path.exists(source_zip_path) or not zipfile.is_zipfile(source_zip_path):
            log_func(f"ERROR: Source path is not a valid zip file: {source_zip_path}")
            raise ValueError("Invalid source zip file.")

        temp_dir = tempfile.mkdtemp(prefix="smx_mod_")
        log_func(f"  - Unzipping mod to temporary location...")
        try:
            with zipfile.ZipFile(source_zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Find the "middleman folder" inside the unzipped contents
            extracted_items = os.listdir(temp_dir)
            # Ignore macOS specific hidden folders that can interfere
            extracted_items = [item for item in extracted_items if item != '__MACOSX']

            if len(extracted_items) != 1 or not os.path.isdir(os.path.join(temp_dir, extracted_items[0])):
                log_func("ERROR: Zip file must contain a single folder with the mod contents.")
                log_func(f"       Found: {extracted_items} in the root of the zip.")
                raise ValueError("Zip file structure is incorrect. It must contain one middleman folder.")
                
            content_folder_path = os.path.join(temp_dir, extracted_items[0])
            
            log_func(f"  - Found mod content folder: '{extracted_items[0]}'")
            log_func(f"  - Creating parent folder '{device_folder_name}' on device sdcard...")
            self.send_adb_command(f"shell mkdir \"/sdcard/{device_folder_name}\"", log_func)
            
            log_func(f"  - Pushing mod contents into parent folder...")
            self.send_adb_command(f'push "{content_folder_path}" "/sdcard/{device_folder_name}/"', log_func)

            log_func(f"  - Moving mod into game directory...")
            self.send_adb_command(f'shell mv "/sdcard/{device_folder_name}" "{target_dir}"', log_func)

        finally:
            log_func(f"  - Cleaning up temporary files...")
            shutil.rmtree(temp_dir)

    def delete_device_folder(self, folder_path, log_func):
        self.send_adb_command(f"shell rm -r \"{folder_path}\"", log_func)

    def send_adb_command(self, command, log_func):
        try:
            adb_path = self.controller.ADB_PATH
            if not adb_path:
                log_func("ERROR: ADB Path is not set. Cannot send command.")
                return
                
            full_command = f'"{adb_path}" {command}'
            process = subprocess.Popen(full_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW, encoding='utf-8')
            stdout, stderr = process.communicate()
            if stdout: log_func(stdout.strip())
            if stderr and "No such file or directory" not in stderr:
                log_func(f"ERROR: {stderr.strip()}")
        except Exception as e:
            log_func(f"Failed to run command: {e}")
            raise e

    def send_adb_command_with_output(self, command):
        try:
            adb_path = self.controller.ADB_PATH
            if not adb_path:
                return None, "ERROR: ADB Path is not set. Cannot send command."

            full_command = f'"{adb_path}" {command}'
            process = subprocess.Popen(full_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW, encoding='utf-8')
            stdout, stderr = process.communicate(timeout=10)
            return stdout, stderr
        except Exception as e:
            return None, str(e)