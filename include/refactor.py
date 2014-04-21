import sublime
import sublime_plugin
import os
import fnmatch
import re

class AndroidRefactorStringCommand(sublime_plugin.WindowCommand):
    text = ""
    tag = ""
    region = None
    edit = None

    def run(self):
        #check if android project
        folder = sublime.active_window().folders()[0]
        path = self.locatePath("AndroidManifest.xml", folder)
        if path is not None and os.path.isfile(path + os.path.sep + "AndroidManifest.xml"):

            view = self.window.active_view()

            sels = view.sel()
            new_sels = []
            for sel in sels:
                begin = sel.a
                end = sel.b
                line_begin = view.full_line(sel.a).a
                line_end = view.full_line(sel.b).b
                while view.substr(begin) != '"' and begin >= line_begin:
                    if begin == line_begin:
                        return
                    begin -= 1
                begin += 1
                while view.substr(end) != '"' and end <= line_end:
                    if end == line_end:
                        return
                    end += 1
                new_sels.append(sublime.Region(begin, end))
            for sel in new_sels:
                self.text = view.substr(sel)
                self.tag = self.slugify(view.substr(sel))
                self.region = sel
                sublime.active_window().show_input_panel("String name:", self.tag, self.on_done, None, None)

    def on_done(self, text):
        self.tag = text
        self.add_to_strings_xml(self.text, self.tag)

    def slugify(self, str):
        str = str.lower()
        return re.sub(r'\W+', '_', str)

    def add_to_strings_xml(self, text, tag):
        for folder in sublime.active_window().folders():
            stringsxml = self.locatePath("strings.xml", folder)
            if stringsxml is not None:
                stringsxml += "/strings.xml"
                file = open(stringsxml, 'r')
                strings_content = file.read()
                file.close()
                file = open(stringsxml, 'w')
                new_block = '<string name="' + tag + '">' + text + '</string>'
                strings_content = strings_content.replace("</resources>", "\t" + new_block + "\n</resources>")
                file.write(strings_content)
                file.close()

                if self.window.active_view():
                    args = {"begin": self.region.begin(), "end": self.region.end(), "tag": self.tag}
                    self.window.active_view().run_command("android_replace_with_tag", args )

    def locatePath(self, pattern, root=os.curdir):
        for path, dirs, files in os.walk(os.path.abspath(root)):
            for filename in fnmatch.filter(files, pattern):
                return path

class AndroidReplaceWithTagCommand(sublime_plugin.TextCommand):
    def run(self, edit, begin, end, tag):
        self.view.replace(edit, sublime.Region(begin, end), "@string/" + tag)