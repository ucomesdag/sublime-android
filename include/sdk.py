import sublime_plugin
import subprocess
import os

from .settings import AndroidSettings

class AndroidOpenSdkCommand(sublime_plugin.WindowCommand):
    settings = []
    def run(self):
        self.settings = AndroidSettings()
        sdk_path = self.settings.get("sdk_path")
        android_bin = self.settings.get("android_bin")
        platform = self.settings.get("platform")
        if not self.settings.is_valid():
            return
        if platform == 'windows' :
            subprocess.Popen([os.path.join(sdk_path, android_bin), "sdk"], creationflags=0x08000000, shell=False)
        else:
            subprocess.Popen([os.path.join(sdk_path, android_bin), "sdk"], shell=False)

class AndroidOpenAvdCommand(sublime_plugin.WindowCommand):
    settings = []
    def run(self):
        self.settings = AndroidSettings()
        sdk_path = self.settings.get("sdk_path")
        android_bin = self.settings.get("android_bin")
        if not self.settings.is_valid():
            return
        if platform == 'windows' :
            subprocess.Popen([os.path.join(sdk_path, android_bin), "avd"], creationflags=0x08000000, shell=False)
        else:
            subprocess.Popen([os.path.join(sdk_path, android_bin), "avd"], shell=False)

class AndroidOpenDdmsCommand(sublime_plugin.WindowCommand):
    settings = []
    def run(self):
        self.settings = AndroidSettings()
        sdk_path = self.settings.get("sdk_path")
        ddms_bin = self.settings.get("ddms_bin")
        if not self.settings.is_valid():
            return
        if platform == 'windows' :
            subprocess.Popen([os.path.join(sdk_path, ddms_bin)], creationflags=0x08000000, shell=False)
        else:
            subprocess.Popen([os.path.join(sdk_path, ddms_bin)], shell=False)
