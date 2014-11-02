import sublime
import os
import imp
#import platform

#TODO: Check if java and ant is installed.
#TODO: Check if android project (build.xml and AndroidManifest.xml) else disable plugin

def get_platform():
    platform = sublime.platform() #Stopped working in sublime text 3 beta (fixed in build 3011)
    #platform = platform.system().lower().replace('darwin', 'osx')
    return platform

def get_settings_file(platform):
    args = {
                'windows': "Android (Windows).sublime-settings",
                'osx': "Android (OSX).sublime-settings",
                'linux': "Android (Linux).sublime-settings"
            }
    return args[platform]

class AndroidSettings():
    platform = get_platform()
    settings_file = get_settings_file(platform)
    settings = {
                'platform': platform,
                'ant_path': "",
                'jdk_path': "",
                'sdk_path': "",
                'logcat_script': os.path.sep.join(["scripts", "logcat"]),
                'run_script': os.path.sep.join(["scripts", "run"]),
                'adb_bin': os.path.sep.join(["platform-tools", "adb"]),
                'android_bin': os.path.sep.join(["tools", "android"]),
                'ddms_bin': os.path.sep.join(["tools", "ddms"]),
                'ant_bin': 'ant',
                'java_bin': os.path.sep.join(["bin", "java"]),
                'debug': True,
                'compile_on_save': True,
                'run_on_device': True,
                'default_android_project_dir': ""
            }

    if platform == 'windows' :
        settings['adb_bin'] += '.exe'
        settings['logcat_script'] += '.bat'
        settings['run_script'] += '.bat'
        settings['android_bin'] += '.bat'
        settings['ddms_bin'] += '.bat'
        settings['ant_bin'] += '.bat'
        settings['java_bin'] += '.exe'
    else:
        settings['logcat_script'] += '.sh'
        settings['run_script'] += '.sh'

    def __init__(self):
        # Get ANT and JAVA locations from settings OR environment variables.
        self.settings['ant_path'] =  os.path.normcase(sublime.load_settings(self.settings_file).get('ant_bin'))
        if "ANT_HOME" in os.environ and os.environ["ANT_HOME"] != '' and self.settings['ant_path'] is None:
            self.settings['ant_path'] = os.path.normcase(os.path.join(os.environ["ANT_HOME"], 'bin'))

        self.settings['jdk_path'] = os.path.normcase(sublime.load_settings(self.settings_file).get('jdk_bin'))
        if "JAVA_HOME" in os.environ and os.environ["JAVA_HOME"] != '' and self.settings['jdk_path'] is None:
            self.settings['jdk_path'] = os.path.normcase(os.environ["JAVA_HOME"])

        self.settings['sdk_path'] = os.path.normcase(sublime.load_settings(self.settings_file).get('android_sdk'))
        self.settings['default_android_project_dir'] = sublime.load_settings(self.settings_file).get('default_android_project_dir')
        self.settings['debug'] = sublime.load_settings(self.settings_file).get('debug')
        self.settings['compile_on_save'] = sublime.load_settings(self.settings_file).get('compile_on_save')
        self.settings['run_on_device'] = sublime.load_settings(self.settings_file).get('run_on_device')

    def is_valid(self):
        if self.settings['ant_path'] is None or self.settings['sdk_path'] is None or self.settings['jdk_path'] is None:
            sublime.error_message( "Error: Path settings are incorrect.\n\nPlease set the correct path in Android/Preferences." )
            return False

        if not ( os.path.exists(self.settings['ant_path']) and \
                 os.path.isfile(os.path.join(self.settings['ant_path'], self.settings['ant_bin'])) ):
            sublime.error_message( "Error: Apache Ant path is incorrect.\n\nPlease set the correct path in Android/Preferences." )
            return False

        if not ( os.path.exists(self.settings['jdk_path']) and \
                 os.path.isfile(os.path.join(self.settings['jdk_path'], self.settings['java_bin'])) ):
            sublime.error_message( "Error: JDK path is incorrect.\n\nPlease set the correct path in Android/Preferences." )
            return False

        if not ( os.path.exists(self.settings['sdk_path']) and \
                 os.path.isfile(os.path.join(self.settings['sdk_path'], self.settings['adb_bin'])) and \
                 os.path.isfile(os.path.join(self.settings['sdk_path'], self.settings['android_bin'])) ):
            sublime.error_message( "Error: Android SDK path is incorrect.\n\nPlease set the correct path in Android/Preferences." )
            return False
        return True

    def set(self, name, value):
        self.settings[name] = value
        sublime.load_settings(self.settings_file).set(name, value)
        sublime.save_settings(self.settings_file)

    def get(self, name):
        return self.settings[name]