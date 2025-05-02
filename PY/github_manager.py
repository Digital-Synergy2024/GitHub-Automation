import customtkinter as ctk  # type: ignore
import sys
import traceback
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
import platform  # Needed for path joining and explorer/finder opening

# First attempt to handle the CTkListbox import
# type: ignore[import] - Tell Pylance to ignore this import error
try:
    from CTkListbox import CTkListbox  # type: ignore
except ImportError:
    try:
        from customtkinter_listbox import CTkListbox  # type: ignore
    except ImportError:
        # Create a fallback implementation using regular CTkFrame if CTkListbox is not available
        print("[DEBUG] CTkListbox not found. Creating fallback implementation.")

        class CTkListbox(ctk.CTkScrollableFrame):
            """Fallback implementation of CTkListbox if the package is not found."""

            def __init__(self, master, **kwargs):
                super().__init__(master, **kwargs)
                self.items = []
                self.buttons = []
                self.selection = None
                self.callback = None
                self.bound_event = None  # Store the event type that was bound

            def insert(self, index, item):
                if index == "end":
                    index = len(self.items)
                self.items.insert(index, item)
                button = ctk.CTkButton(self, text=item, anchor="w",
                                       fg_color="transparent", hover_color=("#CCCCCC", "#333333"))
                button.configure(command=lambda b=button,
                                 i=index: self._select_item(i))
                button.pack(fill="x", pady=1)
                self.buttons.insert(index, button)

            def delete(self, start, end=None):
                if end == "end" or end is None:
                    end = len(self.items) - 1

                for i in range(end, start - 1, -1):
                    if i < len(self.buttons):
                        self.buttons[i].destroy()
                        self.buttons.pop(i)
                        self.items.pop(i)

            def get(self, index):
                return self.items[index]

            def curselection(self):
                return self.selection

            def bind(self, event, callback):
                self.callback = callback
                self.bound_event = event  # Store the event type

            def _select_item(self, index):
                # Reset all buttons to default color
                for btn in self.buttons:
                    btn.configure(fg_color="transparent")

                # Highlight selected button
                self.buttons[index].configure(fg_color=("#AAAAAA", "#444444"))
                self.selection = index

                # Call the callback if bound
                if self.callback and self.bound_event == "<<ListboxSelect>>":
                    self.callback()

import subprocess
import requests  # type: ignore
import os
import shutil
import logging
import time
import json
from multiprocessing import freeze_support

print("[DEBUG] Script started.")
print(f"[DEBUG] Current working directory: {os.getcwd()}")

# Create a log file in the desktop folder to ensure it's writable
log_path = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "debug.log")
print(f"[DEBUG] Log file path: {log_path}")

try:
    logging.basicConfig(filename=log_path, level=logging.ERROR,
                        format="%(asctime)s %(levelname)s: %(message)s")
    logging.error("[DEBUG] Logging initialized.")
except Exception as log_ex:
    print(f"[DEBUG] Logging setup failed: {log_ex}")

licenses = {
    "MIT": "mit",
    "Apache 2.0": "apache-2.0",
    "GPLv3": "gpl-3.0",
    "BSD 2-Clause": "bsd-2-clause",
    "BSD 3-Clause": "bsd-3-clause",
    "No License": ""
}

# Defer CTk initialization until main() is called
# ctk.set_appearance_mode("dark")  # Options: "dark", "light", "system"
# ctk.set_default_color_theme("blue")  # Options: "blue", "green", "dark-blue"


def append_to_console(text):
    # Clear previous content before adding new status message
    output_label.configure(state="normal")
    output_label.delete("1.0", "end")  # Clear the textbox
    output_label.insert("end", text + "\n")
    output_label.see("end")
    output_label.configure(state="disabled")


def check_github_login():
    """
    Check if the user is logged into GitHub CLI.
    If not, show a dialog with login instructions.
    Returns True if logged in, False otherwise.
    """
    try:
        # Check GitHub CLI login status
        result = subprocess.run(
            'gh auth status', shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("[DEBUG] GitHub CLI: Already logged in.")
            return True
        else:
            print("[DEBUG] GitHub CLI: Not logged in.")
            return False
    except Exception as e:
        print(f"[DEBUG] Error checking GitHub login: {e}")
        return False


def show_login_instructions():
    """Show a dialog with instructions for logging into GitHub CLI"""
    login_window = ctk.CTkToplevel()
    login_window.title("GitHub Login Required")
    login_window.geometry("700x500")
    login_window.grab_set()  # Make the window modal

    # Instructions frame
    frame = ctk.CTkFrame(login_window)
    frame.pack(fill="both", expand=True, padx=20, pady=20)

    # Header
    ctk.CTkLabel(frame, text="GitHub CLI Login Required",
                font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(0, 10))

    # Instructions
    instructions = """
    To use GitHub Manager, you need to authenticate with GitHub CLI:

    1. You will be prompted to login via your web browser.
    2. GitHub CLI will ask which account to login with - choose GitHub.com
    3. Select HTTPS as your preferred protocol
    4. Authenticate with your browser when prompted
    5. When asked to authenticate with your GitHub credentials, choose 'Login with a web browser'
    6. Copy the one-time code shown and paste it in the browser when prompted
    7. Authorize GitHub CLI to access your account

    If you encounter any issues:
    • Ensure you have a valid GitHub account
    • Check that GitHub CLI is properly installed
    • Visit github.com/cli/cli for troubleshooting

    Click "Login Now" below to start the authentication process.
    """

    instructions_text = ctk.CTkTextbox(frame, height=300, width=650)
    instructions_text.pack(fill="both", expand=True, padx=10, pady=10)
    instructions_text.insert("0.0", instructions)
    instructions_text.configure(state="disabled")

    def start_login_process():
        login_window.withdraw()  # Hide the window while logging in

        # Create a new window for the login process
        terminal_window = ctk.CTkToplevel()
        terminal_window.title("GitHub CLI Login")
        terminal_window.geometry("600x400")
        terminal_window.grab_set()

        output_text = ctk.CTkTextbox(terminal_window, height=300, width=550)
        output_text.pack(fill="both", expand=True, padx=10, pady=10)
        output_text.insert("0.0", "Starting GitHub login process...\n\n")

        def run_login():
            try:
                process = subprocess.Popen('gh auth login',
                                         shell=True,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE,
                                         text=True)

                # Poll process for new output until finished
                while True:
                    output = process.stdout.readline() if process.stdout else ""
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        output_text.insert("end", output)
                        output_text.see("end")
                        terminal_window.update_idletasks()

                # Get the return code
                return_code = process.poll()
                output_text.insert(
                    "end", f"\nProcess completed with return code: {return_code}\n")

                if return_code == 0:
                    output_text.insert(
                        "end", "\nLogin successful! You can now close this window and start using GitHub Manager.")
                else:
                    output_text.insert(
                        "end", "\nLogin failed. Please try again or check GitHub CLI installation.")

                # Add close button
                ctk.CTkButton(terminal_window, text="Close",
                            command=lambda: [terminal_window.destroy(), login_window.destroy()]).pack(pady=10)

            except Exception as e:
                output_text.insert(
                    "end", f"\nError during login process: {e}\n")
                ctk.CTkButton(terminal_window, text="Close",
                            command=terminal_window.destroy).pack(pady=10)

        # Run in a separate thread to avoid freezing the UI
        import threading
        threading.Thread(target=run_login, daemon=True).start()

    # Buttons
    button_frame = ctk.CTkFrame(frame)
    button_frame.pack(fill="x", pady=10)

    ctk.CTkButton(button_frame, text="Login Now",
                command=start_login_process,
                fg_color="#1e90ff",
                hover_color="#1565c0").pack(side="left", padx=10)

    ctk.CTkButton(button_frame, text="Cancel",
                command=lambda: [login_window.destroy(), sys.exit(0)]).pack(side="left", padx=10)


def run_command(command):
    global output_label
    append_to_console(f"[ACTION] {command}")
    try:
        result = subprocess.run(command, shell=True,
                                capture_output=True, text=True, check=True)
        output_text = result.stdout if result.stdout else "Command executed successfully."
        append_to_console(output_text)
    except subprocess.CalledProcessError as e:
        output_text = f"Error executing command:\n{e}\n{e.stderr}"
        append_to_console(output_text)
        send_discord_log(command, output_text)


def select_folder():
    folder = ctk.filedialog.askdirectory()
    folder_selected.set(folder)


def send_discord_log(action, result):
    webhook_url = webhook_entry.get()
    if webhook_url:
        data = {
            "content": f"🔹 **GitHub Action Logged**\n📝 **Action:** `{action}`\n📜 **Result:** `{result}`"}
        requests.post(webhook_url, json=data)


def backup_repo(repo_name, repo_path):
    backup_path = os.path.join(repo_path, "repo_backup")
    shutil.copytree(repo_path, backup_path, dirs_exist_ok=True)
    append_to_console(f"🔄 Backup created for {repo_name}")


def process_repositories():
    folder_path = folder_selected.get()
    custom_message = commit_message_entry.get()
    privacy_setting = privacy_var.get()
    selected_license = license_var.get()
    add_readme_flag = add_readme_var.get()
    add_gitignore_flag = add_gitignore_var.get()
    mode = repo_mode_var.get()  # Get the selected repository mode
    # Added debug
    print(f"[DEBUG] process_repositories called with mode: {mode}")

    if not folder_path:
        append_to_console("⚠️ Please select a folder first.")
        # Added debug
        print("[DEBUG] Exiting process_repositories: No folder selected.")
        return
    if not custom_message:
        append_to_console("⚠️ Please enter a commit message.")
        # Added debug
        print("[DEBUG] Exiting process_repositories: No commit message.")
        return

    # Get the current GitHub username
    try:
        print("[DEBUG] Getting GitHub username...")  # Added debug
        result = subprocess.run('gh api user', shell=True,
                                capture_output=True, text=True, check=True)
        user_info = json.loads(result.stdout)
        github_username = user_info.get('login')
        if not github_username:
            append_to_console(
                "⚠️ Could not determine GitHub username. Please make sure you're logged in with 'gh auth login'")
            # Added debug
            print(
                "[DEBUG] Exiting process_repositories: Could not get GitHub username.")
            return
        print(f"[DEBUG] GitHub username: {github_username}")  # Added debug
    except Exception as e:
        append_to_console(f"⚠️ Error getting GitHub username: {e}")
        # Added debug
        print(
            f"[DEBUG] Exiting process_repositories: Error getting GitHub username: {e}")
        return

    append_to_console("Processing...")
    root.update_idletasks()

    # Skip these special directories
    skip_dirs = ['.git', 'build', 'dist', '__pycache__',
        '.github', '.vscode', 'repo_backup', 'node_modules']

    # Single repository mode
    if mode == "single":
        print("[DEBUG] Entering single repository mode.")  # Added debug

        # Sanitize the folder name to create a valid GitHub repo name
        base_repo_name = os.path.basename(folder_path)
        repo_name = base_repo_name.replace(
            " ", "-")  # Replace spaces with hyphens

        repo_path = folder_path
        # Added debug
        print(
            f"[DEBUG] Single mode - Original Folder Name: {base_repo_name}, Sanitized Repo Name: {repo_name}, Repo Path: {repo_path}")

        is_git_repo = os.path.isdir(os.path.join(repo_path, '.git'))
        # Added debug
        print(f"[DEBUG] Single mode - Is Git Repo: {is_git_repo}")

        if not is_git_repo:
            append_to_console(f"Initializing {repo_name}...")
            root.update_idletasks()
            # Added debug
            print(f"[DEBUG] Single mode - Initializing {repo_name}...")

            print("[DEBUG] Single mode - Creating backup...")  # Added debug
            # Use sanitized name for backup consistency if desired
            backup_repo(repo_name, repo_path)

            try:
                # 1. Initialize git repository
                # Added debug
                print("[DEBUG] Single mode - Running git init...")
                run_command(f'cd "{repo_path}" && git init')

                # 2. Create remote repository first (using sanitized name)
                append_to_console(
                    f"Creating GitHub repo for {repo_name}...")
                root.update_idletasks()
                # Added debug
                print("[DEBUG] Single mode - Running gh repo create...")
                # Use sanitized name
                create_cmd = f'cd "{repo_path}" && gh repo create "{repo_name}" --{privacy_setting}'
                license_key = licenses.get(selected_license, "")
                if license_key:
                    create_cmd += f' --license "{license_key}"'
                if add_readme_flag:
                    create_cmd += " --add-readme"
                # Added debug
                print(f"[DEBUG] Single mode - Create command: {create_cmd}")
                run_command(create_cmd)

                # 3. Add remote origin (using sanitized name)
                append_to_console(
                    f"Setting up remote for {repo_name}...")
                root.update_idletasks()
                # Use sanitized name
                remote_url = f'https://github.com/{github_username}/{repo_name}.git'
                # Added debug
                print(
                    f"[DEBUG] Single mode - Running git remote add origin {remote_url}...")
                run_command(
                    f'cd "{repo_path}" && git remote add origin {remote_url}')

                # 4. Ensure git identity is configured (required for stash/commit operations)
                try:
                    print("[DEBUG] Single mode - Checking git identity configuration...")
                    # Check for user name
                    name_result = subprocess.run('git config --global user.name', shell=True, 
                                               capture_output=True, text=True)
                    # Check for user email
                    email_result = subprocess.run('git config --global user.email', shell=True, 
                                                capture_output=True, text=True)
                    
                    if not name_result.stdout.strip() or not email_result.stdout.strip():
                        append_to_console("⚠️ Git identity not fully configured. Using placeholder values...")
                        # Set temporary identity values for this repository only (not global)
                        subprocess.run(f'cd "{repo_path}" && git config user.name "GitHub Manager User"', shell=True)
                        subprocess.run(f'cd "{repo_path}" && git config user.email "githubmanager@example.com"', shell=True)
                except Exception as e:
                    print(f"[DEBUG] Single mode - Error checking git identity: {e}")
                    # Continue anyway, the subsequent operations will show more specific errors if needed

                # 5. Handle README and License files from remote
                if add_readme_flag or license_key:
                    print("[DEBUG] Single mode - Handling potential remote files...")
                    try:
                        # Try to pull first without stashing
                        print("[DEBUG] Single mode - Running git pull origin main --allow-unrelated-histories...")
                        pull_result = subprocess.run(
                            f'cd "{repo_path}" && git pull origin main --allow-unrelated-histories', 
                            shell=True, capture_output=True, text=True)
                        
                        if pull_result.returncode != 0:
                            print("[DEBUG] Single mode - Pull failed, trying with stash...")
                            # Only if pull fails, try the stash approach
                            subprocess.run(f'cd "{repo_path}" && git stash', shell=True)
                            run_command(
                                f'cd "{repo_path}" && git pull origin main --allow-unrelated-histories')
                    except Exception as e:
                        print(f"[DEBUG] Single mode - Error during pull: {e}")
                        append_to_console("⚠️ Could not pull remote files. Continuing with local files...")
                        # Continue anyway, we'll force push if needed

                # 6. Stage all local files
                # Added debug
                print("[DEBUG] Single mode - Running git add . ...")
                run_command(f'cd "{repo_path}" && git add .')

                # 7. Commit local files
                # Added debug
                print("[DEBUG] Single mode - Running git commit...")
                # Use --allow-empty in case pull already brought in changes and add . staged nothing new
                run_command(
                    f'cd "{repo_path}" && git commit --allow-empty -m "{custom_message}"')

                # 8. Set the main branch and push
                append_to_console(
                    f"Pushing project files for {repo_name}...")
                root.update_idletasks()
                # Added debug
                print("[DEBUG] Single mode - Running git branch -M main...")
                run_command(f'cd "{repo_path}" && git branch -M main')
                # Added debug
                print("[DEBUG] Single mode - Running git push -u origin main...")
                run_command(f'cd "{repo_path}" && git push -u origin main')

                append_to_console(
                    f"✅ Repository {repo_name} created and pushed successfully.")
                # Added debug
                print(
                    f"[DEBUG] Single mode - Repository {repo_name} created successfully.")

            except Exception as e:
                append_to_console(
                    f"❌ Error processing {repo_name}: {str(e)}")
                # Added debug
                print(
                    f"[DEBUG] Single mode - Error processing {repo_name}: {e}")
                # Log the full traceback for detailed error info
                logging.error(
                    f"Error processing single repo {repo_name}: {traceback.format_exc()}")
        else:
            append_to_console(
                f"Skipping {repo_name}: Already a git repository.")
            # Added debug
            print(
                f"[DEBUG] Single mode - Skipping {repo_name}: Already a git repository.")

    # Multiple repositories mode (original behavior)
    elif mode == "multi":
        print("[DEBUG] Entering multiple repositories mode.")  # Added debug
        # ... (rest of the multi-mode code remains unchanged) ...
        # Ensure multi-mode also has a final completion message
        append_to_console("✅ Multi-repository processing complete.")
        print("[DEBUG] Multi-mode processing complete.")  # Added debug
    else:
        print(f"[DEBUG] Unknown mode selected: {mode}")  # Added debug
        append_to_console(f"⚠️ Unknown mode selected: {mode}")

    print("[DEBUG] Exiting process_repositories function.")  # Added debug


def archive_repo():
    repo_name = repo_entry.get()
    # Add --yes flag for non-interactive execution
    run_command(f'gh repo archive "{repo_name}" --yes')


def restore_repo():
    repo_name = repo_entry.get()
    # Add --yes flag for non-interactive execution
    run_command(f'gh repo unarchive "{repo_name}" --yes')


def list_github_repos():
    try:
        result = subprocess.run('gh repo list --limit 1000',
                                shell=True, capture_output=True, text=True, check=True)
        repos = result.stdout.strip().split('\n')
        return repos
    except subprocess.CalledProcessError as e:
        return [f"Error: {e.stderr}"]


def refresh_repo_list():
    repos = list_github_repos()
    repo_listbox.delete(0, "end")
    for repo in repos:
        repo_listbox.insert("end", repo)


selected_repo = None


def on_repo_select(event=None):
    global selected_repo
    selection = repo_listbox.curselection()
    if selection is not None:  # CTkListbox returns an integer, not a list/tuple
        # Handle the case where selection is an integer (from CTkListbox package)
        try:
            if isinstance(selection, int):
                selected_repo = repo_listbox.get(selection).split()[0]
            else:
                # Original behavior for our fallback implementation
                selected_repo = repo_listbox.get(selection[0]).split()[0]
        except (TypeError, IndexError, AttributeError) as e:
            print(f"[DEBUG] Error in selection handling: {e}")
            selected_repo = None
    else:
        selected_repo = None


def pull_selected_repo():
    if selected_repo:
        run_command(
            f'gh repo clone {selected_repo} temp_repo && cd temp_repo && git pull && cd .. && rmdir /s /q temp_repo')
        append_to_console(f"Pulled latest for {selected_repo}")
    else:
        append_to_console(
            "Please select a repository from the list.")


def push_selected_repo():
    if not selected_repo:
        append_to_console("⚠️ Please select a repository from the list first.")
        return

    # 1. Ask user to select the local folder to push
    append_to_console(f"Select the LOCAL folder containing the content to push to {selected_repo}.")
    local_folder_to_push = filedialog.askdirectory(
        title=f"Select LOCAL folder to force push to {selected_repo}"
    )

    if not local_folder_to_push:
        append_to_console("❌ Push cancelled: No local folder selected.")
        return

    # 2. Show a strong confirmation dialog
    confirm = messagebox.askyesno(
        "Confirm Force Push",
        f"⚠️ WARNING! ⚠️\n\nThis will COMPLETELY OVERWRITE the remote repository '{selected_repo}' "
        f"with the contents of the local folder:\n'{local_folder_to_push}'\n\n"
        "All existing history and files on GitHub will be replaced.\n\n"
        "Are you absolutely sure you want to proceed?",
        icon='warning'
    )

    if not confirm:
        append_to_console("❌ Force push cancelled by user.")
        return

    append_to_console(f"🚀 Starting force push of '{local_folder_to_push}' to '{selected_repo}'...")
    root.update_idletasks()

    temp_clone_dir = None  # Initialize variable
    try:
        # 3. Create a temporary directory for cloning
        temp_base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_push_clones")
        os.makedirs(temp_base_path, exist_ok=True)
        repo_local_name = selected_repo.split('/')[-1]  # Get repo name like 'GitHub-Automation'
        temp_clone_dir = os.path.join(temp_base_path, f"{repo_local_name}_{int(time.time())}")
        
        append_to_console(f"Cloning {selected_repo} to temporary directory...")
        run_command(f'gh repo clone {selected_repo} "{temp_clone_dir}"')

        # 4. Clear the temporary clone directory (except .git)
        append_to_console("Clearing temporary clone directory...")
        for item in os.listdir(temp_clone_dir):
            item_path = os.path.join(temp_clone_dir, item)
            if item == '.git':
                continue
            try:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
            except Exception as e:
                append_to_console(f"⚠️ Warning: Could not remove {item_path}: {e}")

        # 5. Copy content from the user's selected local folder
        append_to_console(f"Copying content from {local_folder_to_push}...")
        shutil.copytree(local_folder_to_push, temp_clone_dir, dirs_exist_ok=True)

        # 6. Perform Git operations: add, commit, force push
        append_to_console("Staging, committing, and force pushing...")
        git_command_base = f'cd "{temp_clone_dir}" && '
        run_command(git_command_base + 'git add .')
        commit_message = f"Force push content from local folder via GitHub Manager"
        run_command(git_command_base + f'git commit --allow-empty -m "{commit_message}"')
        run_command(git_command_base + 'git push --force origin main') 

        append_to_console(f"✅ Successfully force pushed local content to {selected_repo}.")

    except Exception as e:
        append_to_console(f"❌ Error during force push: {e}")
        logging.error(f"Force push error for {selected_repo}: {traceback.format_exc()}")
    finally:
        # 7. Clean up the temporary directory
        if temp_clone_dir and os.path.exists(temp_clone_dir):
            append_to_console("Cleaning up temporary directory...")
            try:
                time.sleep(1)  # Short delay before cleanup
                shutil.rmtree(temp_clone_dir, ignore_errors=True)
            except Exception as e:
                append_to_console(f"⚠️ Failed to fully clean up temp directory {temp_clone_dir}: {e}")


def main():
    print("[DEBUG] Entered main() function.")
    global root, output_label, webhook_entry, repo_entry, commit_message_entry, folder_selected, privacy_var, license_var, add_readme_var, add_gitignore_var, repo_listbox, repo_mode_var
    try:
        ctk.set_appearance_mode("dark")  # Options: "dark", "light", "system"
        # Options: "blue", "green", "dark-blue"
        ctk.set_default_color_theme("blue")

        root = ctk.CTk()
        root.title("GitHub Manager")
        root.geometry("800x700")

        # Check GitHub CLI login status at startup
        print("[DEBUG] Checking GitHub CLI login status at startup...")
        if not check_github_login():
            print(
                "[DEBUG] User is not logged into GitHub CLI. Showing login instructions.")
            # Schedule the login check after the main window is drawn
            root.after(100, lambda: show_login_instructions())
        else:
            print("[DEBUG] User is already logged into GitHub CLI.")

        tabview = ctk.CTkTabview(root)
        tabview.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Main Tab ---
        main_tab = tabview.add("Main")

        # Repository Mode Selection
        mode_frame = ctk.CTkFrame(main_tab)
        mode_frame.pack(pady=5, padx=10, fill="x")
        ctk.CTkLabel(mode_frame, text="Repository Mode:", font=ctk.CTkFont(
            size=14, weight="bold")).pack(side="left", padx=5)

        repo_mode_var = ctk.StringVar(value="multi")
        ctk.CTkRadioButton(mode_frame, text="Multiple Repositories (from subfolders)",
                           variable=repo_mode_var, value="multi").pack(side="left", padx=10)
        ctk.CTkRadioButton(mode_frame, text="Single Repository",
                           variable=repo_mode_var, value="single").pack(side="left", padx=10)

        folder_frame = ctk.CTkFrame(main_tab)
        folder_frame.pack(pady=10, padx=10, fill="x")
        ctk.CTkButton(folder_frame, text="Select Project Folder",
                      command=select_folder).pack(side="left", padx=5)
        folder_selected = ctk.StringVar()
        folder_label = ctk.CTkLabel(
            folder_frame, textvariable=folder_selected, width=400, anchor="w")
        folder_label.pack(side="left", padx=5, fill="x", expand=True)

        webhook_frame = ctk.CTkFrame(main_tab)
        webhook_frame.pack(pady=5, fill="x", padx=10)
        ctk.CTkLabel(webhook_frame, text="Discord Webhook URL (Optional):").pack(
            side="left")
        webhook_entry = ctk.CTkEntry(webhook_frame, width=350)
        webhook_entry.pack(side="left", expand=True, fill="x", padx=5)

        commit_frame = ctk.CTkFrame(main_tab)
        commit_frame.pack(pady=5, fill="x", padx=10)
        ctk.CTkLabel(commit_frame, text="Initial Commit Message:").pack(
            side="left")
        commit_message_entry = ctk.CTkEntry(commit_frame, width=350)
        commit_message_entry.insert(0, "Initial commit")
        commit_message_entry.pack(side="left", expand=True, fill="x", padx=5)

        options_frame = ctk.CTkFrame(main_tab)
        options_frame.pack(pady=10, padx=10, fill="x")
        ctk.CTkLabel(options_frame, text="New Repository Options", font=ctk.CTkFont(
            size=16, weight="bold")).pack(anchor="w", pady=(0, 8))
        privacy_frame = ctk.CTkFrame(options_frame)
        privacy_frame.pack(anchor="w", pady=2)
        ctk.CTkLabel(privacy_frame, text="Visibility:").pack(
            side="left", padx=5)
        privacy_var = ctk.StringVar(value="private")
        ctk.CTkRadioButton(privacy_frame, text="Private",
                           variable=privacy_var, value="private").pack(side="left")
        ctk.CTkRadioButton(privacy_frame, text="Public",
                           variable=privacy_var, value="public").pack(side="left")
        license_frame = ctk.CTkFrame(options_frame)
        license_frame.pack(anchor="w", pady=2)
        ctk.CTkLabel(license_frame, text="License:").pack(side="left", padx=5)
        license_var = ctk.StringVar(value="No License")
        license_dropdown = ctk.CTkComboBox(license_frame, variable=license_var, values=list(
            licenses.keys()), width=180, state="readonly")
        license_dropdown.set("No License")
        license_dropdown.pack(side="left")
        extras_frame = ctk.CTkFrame(options_frame)
        extras_frame.pack(anchor="w", pady=2)
        add_readme_var = ctk.BooleanVar()
        add_gitignore_var = ctk.BooleanVar()
        ctk.CTkCheckBox(extras_frame, text="Add README",
                        variable=add_readme_var).pack(side="left", padx=5)
        # ctk.CTkCheckBox(extras_frame, text="Add .gitignore", variable=add_gitignore_var).pack(side="left", padx=5)
        ctk.CTkButton(main_tab, text="Create Repositories and Push", command=process_repositories,
                      fg_color="#1e90ff", hover_color="#1565c0", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=15)
        archive_frame = ctk.CTkFrame(main_tab)
        archive_frame.pack(pady=10, padx=10, fill="x")
        ctk.CTkLabel(
            archive_frame, text="Repo Name (e.g., owner/repo):").pack(side="left", padx=5)
        repo_entry = ctk.CTkEntry(archive_frame, width=250)
        repo_entry.pack(side="left", padx=5)
        ctk.CTkButton(archive_frame, text="Archive", command=archive_repo,
                      fg_color="#ff7043", hover_color="#b71c1c").pack(side="left", padx=2)
        ctk.CTkButton(archive_frame, text="Restore", command=restore_repo,
                      fg_color="#66bb6a", hover_color="#1b5e20").pack(side="left", padx=2)
        output_label = ctk.CTkTextbox(
            main_tab, 
            height=120, 
            fg_color=("#333", "#333"),  # Dark background in both modes
            text_color=("#ffffff", "#ffffff"),  # White text in both modes
            corner_radius=8
        )
        output_label.insert("end", "Welcome to GitHub Manager!\nAll actions and results will appear here.\n\n")
        output_label.configure(state="disabled")
        output_label.pack(pady=10, padx=10, fill="both", expand=True)

        # --- Repositories Tab ---
        repos_tab = tabview.add("Repositories")
        repo_list_frame = ctk.CTkFrame(repos_tab)
        repo_list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        repo_listbox = CTkListbox(repo_list_frame, width=60, height=20)
        repo_listbox.pack(side="left", fill="both", expand=True)
        repo_listbox.bind("<<ListboxSelect>>", on_repo_select)
        repo_button_frame = ctk.CTkFrame(repo_list_frame)
        repo_button_frame.pack(side="left", fill="y", padx=5)
        ctk.CTkButton(repo_button_frame, text="Refresh List",
                      command=refresh_repo_list).pack(pady=5, fill="x")
        ctk.CTkButton(repo_button_frame, text="Pull Selected",
                      command=pull_selected_repo).pack(pady=5, fill="x")
        ctk.CTkButton(repo_button_frame, text="Push Selected",
                      command=push_selected_repo).pack(pady=5, fill="x")

        # --- Instructions Tab ---
        instructions_tab = tabview.add("Instructions")
        instructions_text = ctk.CTkTextbox(
            instructions_tab, wrap="word", width=750, height=650)
        instructions_text.pack(fill="both", expand=True, padx=10, pady=10)
        instructions_text.insert("0.0", """
# GitHub Manager - Complete User Guide

## Prerequisites
Before using GitHub Manager, please ensure you have:
1. **GitHub CLI (gh)** installed on your system
   - Download from: https://cli.github.com/
   - Run `gh auth login` in your command prompt and follow the instructions to authenticate
   - If you've already authenticated, you can check your status with: `gh auth status`

## Getting Started

### Initial Setup
1. **Login to GitHub CLI**:
   - Open command prompt and run: `gh auth login`
   - Follow the prompts to authenticate with your GitHub account
   - If you've already authenticated, you can check your status with: `gh auth status`

### Main Tab Features

#### Repository Mode
The application supports two modes:
- **Multiple Repositories Mode**: Creates a separate GitHub repository for each subfolder in your selected folder
- **Single Repository Mode**: Creates a single GitHub repository from your selected folder

#### Creating a Single GitHub Repository
1. **Select "Single Repository" mode** at the top of the main tab
2. **Select Project Folder**:
   - Click the "Select Project Folder" button
   - Choose the folder you want to convert into a GitHub repository
3. Configure other options (commit message, visibility, license, README)
4. Click "Create Repositories and Push" to create and push your repository

#### Creating Multiple GitHub Repositories
1. **Select "Multiple Repositories (from subfolders)" mode** at the top of the main tab
2. **Select Project Folder**:
   - Click the "Select Project Folder" button
   - Choose a folder that contains multiple sub-folders (each sub-folder will become a separate repository)
   - Note: Special folders like `.git`, `build`, `dist`, `__pycache__` will be automatically skipped

3. **Discord Webhook** (Optional):
   - Enter a Discord webhook URL to receive notifications about actions performed
   - This will send detailed logs to your Discord channel

4. **Initial Commit Message**:
   - Enter the message you want to use for the initial commit of each repository
   - Default is "Initial commit"

5. **Repository Options**:
   - **Visibility**: Choose between Private (only you can see it) or Public (everyone can see it)
   - **License**: Select an open source license to apply to your repositories
   - **Add README**: Check this to automatically create a README.md file in each repository

6. **Create Repositories**:
   - Click "Create Repositories and Push" to start the process
   - The tool will:
     a. Initialize Git in each folder
     b. Create a backup in case of errors
     c. Create a GitHub repository for each folder
     d. Push the local content to GitHub
   - Progress and results will be shown in the output area

#### Archiving/Restoring Repositories
1. Enter the repository name in the format `username/repository`
2. Click "Archive" to archive or "Restore" to unarchive the repository
3. Note: You must have owner permissions for the repository

### Repositories Tab Features

1. **Refresh List**:
   - Click to load all repositories associated with your GitHub account
   - This shows repositories you own or have access to

2. **Managing Repositories**:
   - Select any repository from the list by clicking on it
   - **Pull Selected**: Downloads the latest changes from the selected repository
   - **Push Selected**: Pushes any local changes to the selected repository

## Common Workflows

### Creating a Single Repository
1. Select "Single Repository" mode
2. Select the folder containing your project
3. Choose appropriate options (visibility, license, etc.)
4. Click "Create Repositories and Push"
5. Your repository will be created and pushed to GitHub

### Creating a Multi-Project GitHub Portfolio
1. Select "Multiple Repositories (from subfolders)" mode
2. Organize your projects into a main folder with sub-folders for each project
3. In each project folder, ensure you have all files you want to include
4. Open GitHub Manager and select the main folder
5. Choose appropriate options (visibility, license, etc.)
6. Click "Create Repositories and Push"
7. All your projects will be available on GitHub with proper structure

### Troubleshooting

#### Common Issues and Solutions:
1. **"Command gh not found" error**:
   - Ensure GitHub CLI is installed correctly
   - Add GitHub CLI to your system PATH
   - Restart the application after installation

2. **Authentication Failures**:
   - Re-run `gh auth login` in your command prompt
   - Check your internet connection
   - Verify your GitHub account has not hit rate limits

3. **Repository Creation Fails**:
   - Ensure you don't already have repositories with the same names
   - Check that folder names don't contain special characters not allowed in GitHub repository names
   - Verify you have permissions to create repositories in your GitHub account

4. **Push/Pull Errors**:
   - Check your internet connection
   - Ensure you have proper permissions for the repository
   - Verify there are no conflicting changes

## Best Practices
1. Always create a backup of your projects before mass-creating repositories
2. Use meaningful commit messages
3. Choose appropriate licenses based on your project needs
4. For large projects, consider creating repositories individually with custom settings

## Advanced Usage
1. **Custom Git Configuration**: Set your git configuration before using the tool with:
   ```
   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com"
   ```

2. **Customizing Repositories After Creation**:
   - Visit your repositories on github.com to:
     - Add detailed descriptions
     - Set up project boards
     - Configure branch protection rules
     - Add collaborators

## Support and Feedback
If you encounter issues or have suggestions, please report them at:
https://github.com/Digital-Synergy2024/github-manager/issues

""")
        instructions_text.configure(state="disabled")

        refresh_repo_list()

        root.mainloop()
    except Exception as e:
        tb = traceback.format_exc()
        logging.error(tb)
        print("\n--- An error occurred! ---\n", tb)
        try:
            import tkinter.messagebox as mb
            mb.showerror(
                "Critical Error", f"A critical error occurred. See debug.log for details.\n\n{e}")
        except Exception:
            pass


if __name__ == "__main__":
    freeze_support()
    try:
        main()
    except Exception as e:
        tb = traceback.format_exc()
        print("[DEBUG] Exception in __main__ block:", tb)
        try:
            logging.error(tb)
        except Exception as log_ex:
            print(f"[DEBUG] Logging error: {log_ex}")
        try:
            import tkinter.messagebox as mb
            mb.showerror(
                "Critical Error", f"A critical error occurred. See debug.log for details.\n\n{e}")
        except Exception:
            pass
