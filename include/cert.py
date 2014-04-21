import sublime
import sublime_plugin
import os
import fnmatch
import re

from .settings import AndroidSettings

class AndroidCreateCertificateCommand(sublime_plugin.WindowCommand):
    settings = []
    package = ""
    path = ""
    dname = ""
    password = ""
    CN = OU = O = L = ST = C = ""
    keystore = ""

    def run(self):
        for folder in self.window.folders():
            buildxml = self.locatePath("build.xml", folder)
            if buildxml is not None:
                self.path = buildxml

                self.settings = AndroidSettings()
                if not self.settings.is_valid():
                    return

                manifest = os.path.join(self.path, "AndroidManifest.xml")
                self.package = self.findPackage(manifest)

                self.keystore = os.path.join(self.path, "%s.keystore" % self.package)
                if os.path.isfile(self.keystore):
                    if sublime.ok_cancel_dialog("Certificate (%s.keystore) already exists!\n\n" % self.package +
                        "Do you want to replace it?"):
                        self.passwordPrompt()

                else:
                    self.passwordPrompt()

    def generate(self):
        jdk_path = self.settings.get('jdk_path')
        # Delete existing keystore
        if os.path.isfile(self.keystore):
            os.remove(self.keystore)

        # Generate Certificate
        cmd = ["keytool", "-genkey", "-v",
            "-keystore", "%s.keystore" % self.package,
            "-alias", self.package,
            "-keyalg", "RSA",
            "-keysize", "2048", "-validity", "10000",
            # "-keypass", self.password,
            "-storepass", self.password,
            "-dname", self.dname]

        args = {
            "cmd": cmd,
            "working_dir": self.path,

            "env": {"JAVA_HOME": jdk_path},

            "path": os.environ["PATH"] + os.pathsep + jdk_path
        }
        self.window.run_command("exec", args)

        self.setProperties()

    def setProperties(self):
        #Set local.properties
        propertiesFile = os.path.join(self.path, "local.properties")
        if not os.path.isfile(propertiesFile):
            return
        properties = ""
        exist = False

        # keystore  = "key.store=%s.keystore\n" % (self.path + os.path.sep + self.package)
        keystore  = "key.store=%s.keystore\n" % self.package
        keystore += "key.alias=%s\n" % self.package
        keystore += "key.store.password=%s\n" % self.password
        keystore += "key.alias.password=%s" % self.password

        file = open(propertiesFile, 'r')
        lines = file.readlines()
        for line in lines:
            match = re.search("^key\.(store|alias)\.?(password)?=.*$", line)
            if match:
                if not exist:
                    exist = True
                    properties += keystore
            else:
                properties += line
        if not exist:
            properties += "\n" + keystore

        os.remove(propertiesFile)
        with open(propertiesFile, 'w') as file:
            file.write(properties)

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

    def passwordPrompt(self, text = ""):
        self.window.show_input_panel("Enter keystore password: " + text, "", self.passwordCheck, None, None)

    def passwordCheck(self, password):
        if len(password) < 6:
            self.passwordPrompt("Key password must be at least 6 characters")
        else:
            self.password = password
            self.window.show_input_panel("Re-enter new password: ", "", self.passwordConfirm, None, None)

    def passwordConfirm(self, password):
        if self.password != password:
            self.passwordPrompt("They don't match. Try again")
            self.password = ""
        else:
            self.promptCN()

    def promptCN(self):
        self.window.show_input_panel("What is your first and last name?", "", self.promptOU, None, None)

    def promptOU(self, text):
        self.CN = text
        self.window.show_input_panel("What is the name of your organizational unit?", "", self.promptO, None, None)

    def promptO(self, text):
        self.OU = text
        self.window.show_input_panel("What is the name of your organization?", "", self.promptL, None, None)

    def promptL(self, text):
        self.O = text
        self.window.show_input_panel("What is the name of your City or Locality?", "", self.promptST, None, None)

    def promptST(self, text):
        self.L = text
        self.window.show_input_panel("What is the name of your State or Province?", "", self.promptC, None, None)

    def promptC(self, text):
        self.ST = text
        self.window.show_input_panel("What is the two-letter country code for this unit?", "", self.checkC, None, None)

    def checkC(self, text):
        if re.match('^[a-zA-Z]{2}$', text) or re.match('^[a-zA-Z]{0}$', text):
            self.C = text
            self.confirmDName()
        else:
            self.window.show_input_panel("What is the two-letter country code for this unit?", "", self.checkC, None, None)

    def confirmDName(self):
        if self.CN != "" or self.OU != "" or self.O != "" or self.L != "" or self.ST != "" or self.C != "":
            if sublime.ok_cancel_dialog("Is CN=" + self.CN +
                ", OU=" + self.OU + ", O=" + self.O +
                ", L=" + self.L + ", ST=" + self.ST +
                ", C=" + self.C + " correct?"):
                self.dname = "CN=" + self.CN + ", OU=" + self.OU + ", O=" + \
                    self.O + ", L=" + self.L + ", ST=" + self.ST + ", C=" + self.C
                self.generate()
        else:
            if sublime.ok_cancel_dialog("Distinguished Name fields (CN, OU, ...) can't be empty!"):
                self.promptCN()