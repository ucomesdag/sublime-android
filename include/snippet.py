import sublime
import sublime_plugin
import os

from .settings import AndroidSettings

class AndroidInsertSnippetCommand(sublime_plugin.TextCommand):
    snippets = []
    snippetsHeaders = []
    settings = []

    def run(self, text):
        self.settings = AndroidSettings()
        self.snippets = self.getSnippets()
        self.snippetsHeaders = self.stripFileExt(self.snippets)
        self.view.window().show_quick_panel(self.snippetsHeaders, self.on_done, sublime.MONOSPACE_FONT)
        return

    def getSnippets(self):
        snippet_path = os.path.join(sublime.packages_path(), "Android", "snippets")
        snippets = os.listdir(snippet_path)
        snippets.sort()
        return snippets

    def stripFileExt(self, files):
        filenames = []
        for filename in files:
            filenames.append(os.path.splitext(filename)[0])
        return filenames

    def on_done(self, index):
        if index < 0:
            return
        snippet = self.snippets[index]
        self.view.run_command('insert_snippet', {"name": "Packages/Android/snippets/" + snippet})

class AndroidExploreSnippets(sublime_plugin.WindowCommand):
    def run(self):
        self.window.run_command('open_dir', {"dir": "$packages/Android/snippets/"})
        return