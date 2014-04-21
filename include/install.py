import sublime
import sublime_plugin
import os
import fnmatch
import re

from .settings import AndroidSettings

class AndroidInstallCommand(sublime_plugin.WindowCommand):
    settings = []

    def run(self):
        for folder in self.window.folders():
            buildxml = self.locatePath("build.xml", folder)
            if buildxml is not None:
                path = buildxml

                self.settings = AndroidSettings()
                if not self.settings.is_valid():
                    return

                buildxml = os.path.join(path, "build.xml")
                projectName = self.findProject(buildxml)

                if self.settings.get('debug'):
                    apk = projectName + "-debug.apk"
                else:
                    # apk = projectName + "-release-unsigned.apk"
                    apk = projectName + "-release.apk"

                apk_path = os.path.join(path, "bin", apk)
                sdk_path = self.settings.get('sdk_path')
                adb_bin = self.settings.get('adb_bin')
                if os.path.isfile(apk_path):
                    args = {
                        "cmd": [os.path.join(sdk_path, adb_bin), "-d", "install", apk_path]
                    }
                    self.window.run_command("exec", args)
                else:
                    sublime.message_dialog( "Install failed because %s was not found!\n\nPlease run build and try again." % apk )

    def locatePath(self, pattern, root=os.curdir):
        for path, dirs, files in os.walk(os.path.abspath(root)):
            for filename in fnmatch.filter(files, pattern):
                return path

    def findProject(self, xmlFile):
        if not os.path.isfile(xmlFile):
            return
        file = open(xmlFile, 'r')
        lines = file.readlines()
        for line in lines:
            match = re.search("<project ?.* name=\"([\.\ a-zA-Z1-9]+)\"", line)
            if match:
                return match.group(1)

class AndroidUninstallCommand(sublime_plugin.WindowCommand):
    settings = []

    def run(self):
        self.settings = AndroidSettings()
        if not self.settings.is_valid():
            return
        for folder in self.window.folders():
                path = self.locatePath("AndroidManifest.xml", folder)
                if path is not None:
                   manifest = os.path.join(path, "AndroidManifest.xml")
        if manifest is not None:
            package = self.findPackage(manifest)
            sdk_path = self.settings.get('sdk_path')
            adb_bin = self.settings.get('adb_bin')
            args = {
                "cmd": [os.path.join(sdk_path, adb_bin), "uninstall", package]
            }
            self.window.run_command("exec", args)

    def locatePath(self, pattern, root=os.curdir):
        for path, dirs, files in os.walk(os.path.abspath(root)):
            for filename in fnmatch.filter(files, pattern):
                return path

    def findPackage(self, xmlFile):
        if not os.path.isfile(xmlFile):
            return
        file = open(xmlFile, 'r')
        lines = file.readlines()
        for line in lines:
            match = re.search("package=\"([\.a-zA-Z1-9]+)\"", line)
            if match:
                return match.group(1)
