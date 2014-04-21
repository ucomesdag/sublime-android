import sublime
import sublime_plugin
import os

from .settings import AndroidSettings

class AndroidAdbShellCommand(sublime_plugin.WindowCommand):
    settings = []

    def run(self):
        self.settings = AndroidSettings()
        if not self.settings.is_valid():
            return
        # Check if Terminal is installed http://wbond.net/sublime_packages/terminal
        if not os.path.exists(os.path.join(sublime.packages_path(), "Terminal")):
            sublime.message_dialog( "Sublime Terminal package is not installed.\n\n" +
                "Use Package Control to install it or download it from:\n" +
                "http://wbond.net/sublime_packages/terminal" )
        else:
            sdk_path = self.settings.get("sdk_path")
            adb_bin = self.settings.get("adb_bin")
            platform = self.settings.get("platform")
            # The following is only tested on ubuntu
            param = ''
            if platform == 'windows': param = ''
            elif platform == 'darwin': param = '-x'
            elif platform == 'linux':
                ps = 'ps -eo comm | grep -E "gnome-session|ksmserver|' + \
                    'xfce4-session" | grep -v grep'
                wm = [x.replace("\n", '') for x in os.popen(ps)]
                if wm:
                    if wm[0] == 'gnome-session': param = '-x'
                    elif wm[0] == 'xfce4-session': param = '-x'
                    elif wm[0] == 'ksmserver': param = '-x'
                else: param = '-e'
            args = {
                "parameters": [param, os.path.join(sdk_path, adb_bin), "shell"]
            }
            self.window.run_command("open_terminal", args)

# Runs ADB Logcat, given a filter in the format tag:priority
# tag = the name of the system component where the message came from
# priority = one of the following characters:
#             V - Verbose
#             D - Debug
#             I - Info
#             W - Warning
#             E - Error
#             F - Fatal
#             S - Silent (nothing is printed)
# Read more at http://developer.android.com/guide/developing/tools/adb.html#outputformat
class AndroidAdbLogcatCommand(sublime_plugin.WindowCommand):
    settings = []

    def run(self):
        self.settings = AndroidSettings()
        if not self.settings.is_valid():
            return
        self.window.show_input_panel("Filter (tag:priority)", "System.out:I *:S", self.on_input, None, None)

    def on_input(self, text):
        sdk_path = self.settings.get("sdk_path")
        adb_bin = self.settings.get("adb_bin")
        script_path = os.path.join(sublime.packages_path(), "Android", "")
        logcat_script = self.settings.get("logcat_script")

        if not self.settings.is_valid():
            return
        args = {
            "cmd": [os.path.join(script_path, logcat_script),
            text, os.path.join(sdk_path, adb_bin)]
        }
        self.window.run_command("exec", args)