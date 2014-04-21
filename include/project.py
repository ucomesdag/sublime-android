import sublime
import sublime_plugin
import subprocess
import os
import fnmatch
import re

from .settings import AndroidSettings

#TODO: Clean this up
def getBuiltTargets():
    targets = []
    settings = AndroidSettings()
    if not settings.is_valid():
        return
    if settings.get('platform') == 'windows' :
        si = subprocess.STARTUPINFO()
        si.dwFlags = subprocess.STARTF_USESTDHANDLES | subprocess.STARTF_USESHOWWINDOW
    else:
        si = None
    sdk_path = settings.get('sdk_path')
    android_bin = settings.get('android_bin')
    proc = subprocess.Popen([os.path.join(sdk_path, android_bin), "list", "target", "-c"], shell=False, stdout=subprocess.PIPE, startupinfo=si)
    output = proc.stdout.read().decode('utf-8')
    proc.communicate()
    targets = output.split('\n')
    if targets is None:
        sublime.status_message( "Error: No android targets installed!" )
        sublime.message_dialog( "No android targets installed.\n\n" +
                "Please run  Android/SDK Tools/Launch SDK Manager\n" +
                "and install a \"SDK Platform\"." )
        return False
    return targets

class AndroidNewProjectCommand(sublime_plugin.WindowCommand):
    project_name = ""
    activity_name = ""
    package_name = ""
    project_path = ""
    build_target = ""
    targets = []
    settings = []

    def run(self):
        self.settings = AndroidSettings()
        if not self.settings.is_valid():
            return
        self.window.show_input_panel("Project name:", "", self.on_project_name_input, None, None)

    def on_project_name_input(self, text):
        if len(text) < 2:
            self.window.show_input_panel("Project name: Name too short!", "", self.on_project_name_input, None, None)
        else:
            if re.match('^[a-zA-Z0-9_]*$', text):
                self.project_name = text
                self.window.show_input_panel("Activity name:", self.project_name.lower(), self.on_activity_name_input, None, None)
            else:
                self.window.show_input_panel("Project name: Allowed characters are: a-z A-Z 0-9 _", "", self.on_project_name_input, None, None)

    def on_activity_name_input(self, text):
        self.activity_name = text
        self.window.show_input_panel("Package name:", "com." + self.project_name.lower(), self.on_package_name_input, None, None)

    def on_package_name_input(self, text):
        self.package_name = text
        android_projects = self.settings.get('default_android_project_dir')
        default_text = ""
        if not android_projects is None:
            default_text = android_projects + os.path.sep + self.project_name
        self.window.show_input_panel("Project path:", default_text, self.on_path_input, None, None)

    def on_path_input(self, text):
        self.project_path = text
        self.targets = getBuiltTargets()
        self.window.show_quick_panel(self.targets, self.on_target_selected)

    def on_target_selected(self, picked):
        if picked == -1:
            g = (i for i in self.targets if i.startswith("android")) # use "Google" for google api
            match = list(g)
            if match:
                target  =  match[0]
            else:
                target  =  self.targets[0]
            self.window.show_input_panel("Build target:", target, self.on_target_set, None, None)
        else:
            self.on_target_set(self.targets[picked])

    def on_target_set(self, target):
        if target == "":
            sublime.status_message( "Error: No android target selected!" )
            self.window.show_quick_panel(self.targets, self.on_target_selected)
        else:
            self.build_target = str(target)
            self.create_project()

    def create_project(self):
        self.window.run_command("show_panel", {"panel": "console"})
        ant_path = self.settings.get('ant_path')
        sdk_path = self.settings.get('sdk_path')
        jdk_path = self.settings.get('jdk_path')
        android_bin = self.settings.get('android_bin')
        print("Creating project (%s)" % self.project_path)

        # Create folder containing the project
        if not os.path.exists(self.project_path):
            os.makedirs(self.project_path)

        # Call android SDK to setup a new project
        args = {
            "cmd": [os.path.join(sdk_path, android_bin),
            "create", "project",
             "--target", self.build_target,
             "--name", self.project_name,
             "--path", self.project_path,
             "--activity", self.activity_name,
             "--package", self.package_name],

            "env": {"JAVA_HOME": jdk_path, "ANDROID_HOME": sdk_path},

            "path": os.environ["PATH"] +
                    os.pathsep + ant_path +
                    os.pathsep + jdk_path +
                    os.pathsep + os.path.join(sdk_path, "tools") +
                    os.pathsep + os.path.join(sdk_path, "platform-tools")
        }
        self.window.run_command("exec", args)

        new_project  = "{\n"
        new_project += "    \"folders\":\n"
        new_project += "    [\n"
        new_project += "        {\n"
        new_project += "            \"path\": \".\",\n"
        new_project += "            \"name\": \"%s\",\n" % self.project_name
        new_project += "            \"folder_exclude_patterns\": [],\n"
        new_project += "            \"file_exclude_patterns\": [\"*.sublime-project\", \"*.sublime-workspace\"]\n"
        new_project += "        }\n"
        new_project += "    ]\n"
        new_project += "}"
        project_file = os.path.sep.join([self.project_path, "%s.sublime-project" % self.project_name])
        with open(project_file, 'w') as file:
            file.write(new_project)
        #TODO: Fix opening the project.
        self.window.run_command('open_project', [project_file])
        sublime.active_window().open_file(project_file)

        self.window.new_file().run_command('android_show_readme', {"path": self.project_path})
        self.window.run_command('set_build_system', {"file": "Packages/Android/Android.sublime-build"})

class AndroidShowReadmeCommand(sublime_plugin.TextCommand):
    def run(self, edit, path = ""):
        self.view.set_name("readme.txt")
        self.view.settings().set("default_dir", path)
        self.view.insert(edit, 0, readme) # See at the bottom for the readme
        self.view.show(0)

class AndroidImportProjectCommand(sublime_plugin.WindowCommand):
    project_path = ""
    project_name = ""
    def run(self):
        self.window.run_command('prompt_open_folder')

        #   check for AndroidManifest.xml
        folder = sublime.active_window().folders()[0]
        self.project_path = self.locatePath("AndroidManifest.xml", folder)

        #check if android project (exclude the binary folder)
        if os.path.isfile(self.project_path + os.path.sep + "AndroidManifest.xml") and \
                not re.search(os.path.sep + "bin", self.project_path):
            self.settings = AndroidSettings()
            if not self.settings.is_valid():
                return

            # get app name from AndroidManifest.xml
            self.project_name = self.findActivity(self.project_path + os.path.sep + "AndroidManifest.xml").replace('.', '')

            # create a new sublime project file with appname and add folder
            new_project  = "{\n"
            new_project += "    \"folders\":\n"
            new_project += "    [\n"
            new_project += "        {\n"
            new_project += "            \"path\": \".\",\n"
            new_project += "            \"name\": \"%s\",\n" % self.project_name
            new_project += "            \"folder_exclude_patterns\": [],\n"
            new_project += "            \"file_exclude_patterns\": [\"*.sublime-project\", \"*.sublime-workspace\"]\n"
            new_project += "        }\n"
            new_project += "    ]\n"
            new_project += "}"
            project_file = os.path.sep.join([self.project_path, "%s.sublime-project" % self.project_name])
            with open(project_file, 'w') as file:
                file.write(new_project)
            #TODO: Fix opening the project.
            self.window.run_command('open_project', [project_file])
            sublime.active_window().open_file(project_file)

            # show readme
            self.window.run_command('android_show_readme', {"path": self.project_path})
            self.window.run_command('set_build_system', {"file": "Packages/Android/Android.sublime-build"})
            return
        # else error dialog no AndroidManifest.xml not found
        sublime.error_message( "Error: No android project found.\n\nAndroidManifest.xml not found." )

        return

    def findActivity(self, xmlFile):
        if not os.path.isfile(xmlFile):
            return
        file = open(xmlFile, 'r')
        lines = file.readlines()
        for line in lines:
            match = re.search("^\s*android:name=\"([\.a-zA-Z1-9]+)\"", line)
            if match:
                return match.group(1)

    def locatePath(self, pattern, root=os.curdir):
        for path, dirs, files in os.walk(os.path.abspath(root)):
            for filename in fnmatch.filter(files, pattern):
                return path

readme = """\
Android projects are the projects that eventually get built into an .apk file
that you install onto a device. They contain things such as application
source code and resource files.

Some are generated for you by default, while others should be created if
required. The following directories and files comprise an Android project:

src/
    Contains your stub Activity file, which is stored at
    src/your/package/namespace/ActivityName.java All other source code files
    (such as .java or .aidl files) go here as well.
bin/
    Output directory of the build. This is where you can find the final .apk
    file and other compiled resources.
jni/
    Contains native code sources developed using the Android NDK. For more
    information, see the Android NDK documentation.
gen/
    Contains the Java files generated by ADT, such as your R.java file and
    interfaces created from AIDL files.
assets/
    This is empty. You can use it to store raw asset files. Files that you
    save here are compiled into an .apk file as-is, and the original filename
    is preserved. You can navigate this directory in the same way as a
    typical file system using URIs and read files as a stream of bytes using
    the the AssetManager. For example, this is a good location for textures
    and game data.
res/
    Contains application resources, such as drawable files, layout files,
    and string values. See Application Resources for more information.
res/anim/
    For XML files that are compiled into animation objects. See the Animation
    resource type.
res/color/
    For XML files that describe colors. See the Color Values resource type.
res/drawable/
    For bitmap files (PNG, JPEG, or GIF), 9-Patch image files, and XML files
    that describe Drawable shapes or a Drawable objects that contain multiple
    states (normal, pressed, or focused). See the Drawable resource type.
res/layout/
    XML files that are compiled into screen layouts (or part of a screen).
    See the Layout resource type.
res/menu/
    For XML files that define application menus. See the Menus resource type.
res/raw/
    For arbitrary raw asset files. Saving asset files here instead of in
    the assets/ directory only differs in the way that you access them. These
    files are processed by aapt and must be referenced from the application
    using a resource identifier in the R class. For example, this is a good
    place for media, such as MP3 or Ogg files.
res/values/
    For XML files that are compiled into many kinds of resource. Unlike other
    resources in the res/ directory, resources written to XML files in this
    folder are not referenced by the file name. Instead, the XML element type
    controls how the resources is defined within them are placed into
    the R class.
res/xml/
    For miscellaneous XML files that configure application components.
    For example, an XML file that defines a androidcreen,
    AppWidgetProviderInfo, or Searchability Metadata. See Application
    Resources for more information about configuring these application
    components.
libs/
    Contains private libraries.
AndroidManifest.xml
    The control file that describes the nature of the application and each
    of its components. For instance, it describes:
    - certain qualities about the activities, services, intent receivers,
      and content providers
    - what permissions are requested; what external libraries are needed
    - what device features are required, what API Levels are supported
      or required
    See the AndroidManifest.xml documentation for more information
project.properties
    This file contains project settings, such as the build target. This file
    is integral to the project, so maintain it in a source revision control
    system. To edit project properties in Eclipse, right-click the project
    folder and select Properties.
local.properties
    Customizable computer-specific properties for the build system. If you
    use Ant to build the project, this contains the path to the SDK
    installation. Because the content of the file is specific to the
    local installation of the SDK, the local.properties should not be
    maintained in a source revision control system. If you use Eclipse,
    this file is not used.
ant.properties
    Customizable properties for the build system. You can edit this file to
    override default build settings used by Ant and also provide the location
    of your keystore and key alias so that the build tools can sign your
    application when building in release mode. This file is integral to
    the project, so maintain it in a source revision control system.
    If you use Eclipse, this file is not used.
build.xml
    The Ant build file for your project. This is only applicable for projects that you build with Ant."""