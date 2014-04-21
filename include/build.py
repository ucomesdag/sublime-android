import sublime
import sublime_plugin
import os
import fnmatch
import re
import time

from Default.exec import ExecCommand

from .settings import AndroidSettings

class AndroidBuildDebugCommand(sublime_plugin.WindowCommand):
    settings = []
    def __init__(self, p):
        self.settings = AndroidSettings()
    def run(self):
        if self.settings.get('debug') == True:
            self.settings.set('debug', False)
        else:
            self.settings.set('debug', True)
    def is_checked(self):
        if self.settings.get('debug') == True:
            return True
        else:
            return False

class AndroidBuildOnSaveCommand(sublime_plugin.WindowCommand):
    settings = []
    def __init__(self, p):
        self.settings = AndroidSettings()
    def run(self):
        if self.settings.get('compile_on_save') == True:
            self.settings.set('compile_on_save', False)
        else:
            self.settings.set('compile_on_save', True)
    def is_checked(self):
        if self.settings.get('compile_on_save') == True:
            return True
        else:
            return False

class AndroidRunOnDeviceCommand(sublime_plugin.WindowCommand):
    settings = []
    def __init__(self, p):
        self.settings = AndroidSettings()
    def run(self):
        if self.settings.get('run_on_device') == True:
            self.settings.set('run_on_device', False)
        else:
            self.settings.set('run_on_device', True)
    def is_checked(self):
        if self.settings.get('run_on_device') == True:
            return True
        else:
            return False

# Compiles code and builds a signed, debug/release package
class AndroidBuildCommand(sublime_plugin.WindowCommand):
    settings = []
    targets = []
    cmd = []
    path = ""
    build_target = ""
    quiet = False

    def run(self, cmd = [], file_regex = "", line_regex = "", working_dir = "",
            encoding = "utf-8", env = {}, quiet = False, kill = False,
            # Catches "path" and "shell"
            **kwargs):

        self.settings = AndroidSettings()

        path = working_dir
        if os.path.isfile(os.path.join(working_dir, "AndroidManifest.xml")):
            self.path = working_dir
        else:
            for folder in self.window.folders():
                path = self.locatePath("AndroidManifest.xml", folder)
                if path is not None:
                   self.path = path

        #check if android project
        if os.path.isfile(os.path.join(self.path, "AndroidManifest.xml")):
            self.settings = AndroidSettings()
            if not self.settings.is_valid():
                return
            self.path = path
            self.quiet = quiet
            self.run_on_device = self.settings.get('run_on_device')
            self.checkBuildXML()

    def runQuiet(self):
        self.settings = AndroidSettings()
        if not self.settings.is_valid():
            return
        self.quiet = True
        self.run_on_device = False
        self.checkBuildXML()

    def checkBuildXML(self):
        for folder in self.window.folders():
            buildxml = self.locatePath("build.xml", folder)
            if buildxml is not None:
                self.path = buildxml
        # Checks for build.xml and if needed generates it
        if not os.path.isfile(os.path.join(self.path, "build.xml")):
            if sublime.ok_cancel_dialog("The file build.xml doesn't exist and needs to be\n" +
                                        "created for ant to run.\n\n" +
                                        "Do you want it to be created automatically?"):
                if self.build_target == "": #TODO: Check the properties file.
                    self.targets = getBuiltTargets()
                    self.window.show_quick_panel(self.targets, self.selectedBuildTarget)
                else:
                    self.createBuildXML()
        else:
            self.build()

    def selectedBuildTarget(self, picked):
        if picked == -1:
            g = (i for i in self.targets if i.startswith("android")) # use "Google" for defaulting to google api
            match = list(g)
            if match:
                target  =  match[0]
            else:
                target  =  self.targets[0]
            self.window.show_input_panel("Build target:", target, self.setBuildTarget, None, None)
        else:
            self.setBuildTarget(self.targets[picked])

    def setBuildTarget(self, target):
        if target == "":
            sublime.status_message( "Error: No android target selected!" )
            self.window.show_quick_panel(self.targets, self.selectedBuildTarget)
        else:
            self.build_target = str(target)
            self.createBuildXML()

    def createBuildXML(self):
        # Call android SDK to update the project
        # args = {
        #     "cmd": [self.settings.sdk + android_bin,
        #     "update", "project",
        #     "--target", "\"%s\""%self.build_target,
        #     "--path", self.path]
        # }
        # self.window.run_command("exec", args)
        self.cmd = [self.settings.sdk + android_bin,
            "update", "project",
            "--target", "\"%s\"" % self.build_target,
            "--path", "\"%s\"" % self.path]
        self.build()

    def build(self):
        self.settings = AndroidSettings()
        ant_path = self.settings.get('ant_path')
        sdk_path = self.settings.get('sdk_path')
        jdk_path = self.settings.get('jdk_path')
        ant_bin = self.settings.get('ant_bin')
        run_script = self.settings.get('run_script')
        debug = self.settings.get('debug')
        run_on_device = self.settings.get('run_on_device')
        plugin_path = os.path.join(sublime.packages_path(), "Android")

        buildxml = os.path.join(self.path, "build.xml")
        manifest = os.path.join(self.path, "AndroidManifest.xml")
        projectName = self.findProject(buildxml)
        package = self.findPackage(manifest)
        activity = self.findActivity(manifest)

        if package is None and activity is None:
            return
        component = package + "/" + activity

        if run_on_device and not debug:
            # Check for certificate before build & install in release mode
            properties = os.path.join(self.path, "local.properties")
            keystore = self.findKeystore(properties)
            if keystore is None or not os.path.isfile(os.path.join(self.path, keystore)) and not os.path.isfile(keystore):
                sublime.message_dialog( "You need to generate a certificate first for signing and installing in release mode!" )
                return

        cmd = []
        if self.cmd:
            cmd.extend(self.cmd)
            cmd.append("&&")
        if run_on_device:
            cmd.extend([ant_bin, "uninstall"])
            cmd.append("&&")
        if debug:
            cmd.extend([ant_bin, "debug"])
        else:
            cmd.extend([ant_bin, "release"])
        if run_on_device:
            cmd.append("install")
            cmd.append("&&")
            cmd.extend(["adb", "shell", "am", "start", "-a", "android.intent.action.MAIN", "-n", component])

        args = {
            "cmd": [os.path.join(plugin_path, run_script)] + cmd,
            "working_dir": self.path,

            "env": {"JAVA_HOME": jdk_path, "ANDROID_HOME": sdk_path},

            "path": os.environ["PATH"] +
                    os.pathsep + ant_path +
                    os.pathsep + jdk_path +
                    os.pathsep + os.path.join(sdk_path, "tools") +
                    os.pathsep + os.path.join(sdk_path, "platform-tools"),

            "quiet": self.quiet
        }
        self.window.run_command("android_exec", args)
        if self.quiet:
            sublime.active_window().run_command("hide_panel")

    def findProject(self, xmlFile):
        if not os.path.isfile(xmlFile):
            return
        file = open(xmlFile, 'r')
        lines = file.readlines()
        for line in lines:
            match = re.search("<project ?.* name=\"([\.\ a-zA-Z1-9]+)\"", line)
            if match:
                return match.group(1)

    def findActivity(self, xmlFile):
        if not os.path.isfile(xmlFile):
            return
        file = open(xmlFile, 'r')
        lines = file.readlines()
        for line in lines:
            match = re.search("^\s*android:name=\"([\.a-zA-Z1-9]+)\"", line)
            if match:
                return match.group(1)

    def findPackage(self, xmlFile):
        if not os.path.isfile(xmlFile):
            return
        file = open(xmlFile, 'r')
        lines = file.readlines()
        for line in lines:
            match = re.search("package=\"([\.a-zA-Z1-9]+)\"", line)
            if match:
                return match.group(1)

    def findKeystore(self, properiesFile):
        if not os.path.isfile(properiesFile):
            return
        file = open(properiesFile, 'r')
        lines = file.readlines()
        for line in lines:
            match = re.search("^key.store=(.*)$", line)
            if match:
                return match.group(1)

    def locatePath(self, pattern, root=os.curdir):
        for path, dirs, files in os.walk(os.path.abspath(root)):
            for filename in fnmatch.filter(files, pattern):
                return path

class AndroidBuildOnSave(sublime_plugin.EventListener):
    settings = []
    timestamp = ""
    filepath = ""
    filename = ""

    def on_post_save(self, view):
        #check if android project
        folder = sublime.active_window().folders()[0]
        path = self.locatePath("AndroidManifest.xml", folder)
        if path is not None and os.path.isfile(os.path.join(path, "AndroidManifest.xml")):
            #let's see if project wants to be autobuilt.
            should_build = AndroidSettings().get('compile_on_save')
            if should_build == 1:
                self.filename = "build.prop"
                self.resetTimeStamp()
                self.setTimestamp()
                sublime.active_window().active_view().set_status('Android', 'Project build started')
                AndroidBuildCommand(sublime.active_window()).runQuiet()
                self.on_build()

    def on_build(self, i=0, dir=1):
        if self.timestamp == self.getTimestamp() and sublime.active_window().active_view().get_status('Android') != "":
            before = i % 8
            after = (7) - before
            if not after:
                dir = -1
            if not before:
                dir = 1
            i += dir
            sublime.active_window().active_view().set_status('Android', 'Building project [%s=%s]' % \
                (' ' * before, ' ' * after))
            sublime.set_timeout(lambda: self.on_build(i, dir), 25)
            return
        else:
            sublime.active_window().active_view().set_status('Android', 'Project build succesfully')
            sublime.set_timeout(lambda: self.on_done(), 5000)

    def on_done(self):
         sublime.active_window().active_view().erase_status('Android')

    def locatePath(self, pattern, root=os.curdir):
        for path, dirs, files in os.walk(os.path.abspath(root)):
            for filename in fnmatch.filter(files, pattern):
                return path

    def setFilePath(self):
        if self.filepath == "":
            folder = sublime.active_window().folders()[0]
            path = self.locatePath(self.filename, folder)
            if path is not None:
                self.filepath = os.path.sep.join([path, self.filename])

    def setTimestamp(self):
        self.setFilePath()
        if self.filepath != "":
            self.timestamp = self.getTimestamp()

    def getTimestamp(self):
        if self.filepath != "":
            return str(os.path.getmtime(self.filepath))
        else:
            self.setFilePath()
            return ""

    def resetTimeStamp(self):
        self.filepath = ""
        self.timestamp = ""

class AndroidCleanCommand(sublime_plugin.WindowCommand):
    settings = []
    def run(self):
        for folder in self.window.folders():
            buildxml = self.locatePath("build.xml", folder)
            if buildxml is not None:
                self.settings = AndroidSettings()
                ant_path = self.settings.get('ant_path')
                sdk_path = self.settings.get('sdk_path')
                jdk_path = self.settings.get('jdk_path')
                ant_bin = self.settings.get('ant_bin')
                path = buildxml
                args = {
                    "cmd": [ant_bin, "clean"],
                    "working_dir": path,

                    "env": {"JAVA_HOME": jdk_path, "ANDROID_HOME": sdk_path},

                    "path": os.environ["PATH"] +
                            os.pathsep + ant_path +
                            os.pathsep + jdk_path +
                            os.pathsep + os.path.join(sdk_path, "tools") +
                            os.pathsep + os.path.join(sdk_path, "platform-tools"),
                }
                self.window.run_command("android_exec", args)

    def locatePath(self, pattern, root=os.curdir):
        for path, dirs, files in os.walk(os.path.abspath(root)):
            for filename in fnmatch.filter(files, pattern):
                return path

class AndroidExecCommand(ExecCommand):
    def finish(self, proc):
        self.window.run_command("refresh_folder_list")
        sublime.active_window().active_view().erase_status('Android')

        if not self.quiet:
            elapsed = time.time() - proc.start_time
            exit_code = proc.exit_code()
            if exit_code == 0 or exit_code == None:
                self.append_string(proc,
                    ("[Finished in %.1fs]" % (elapsed)))
            else:
                self.append_string(proc, ("[Finished in %.1fs with exit code %d]\n"
                    % (elapsed, exit_code)))
                self.append_string(proc, self.debug_text)

        if proc != self.proc:
            return

        errs = self.output_view.find_all_results()
        if len(errs) == 0:
            sublime.status_message("Build finished")
            sublime.active_window().active_view().set_status('Android', 'Project build succesfully')
        else:
            sublime.status_message(("Build finished with %d errors") % len(errs))
            sublime.active_window().active_view().set_status('Android', 'Project build with errors')
        sublime.set_timeout(lambda: self.on_done(), 4000)

    def on_done(self):
        sublime.active_window().active_view().erase_status('Android')