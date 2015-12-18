# Sublime Android #

This is a pluging for Android development with [Sublime Text 3](http://www.sublimetext.com/3).

It automates basic tasks like:

* creating new projects
* refactor strings
* snippets
* build
* build on save
* create certificates
* install apk's
* uninstall apk's
* run on device
* run adb shell
* run logcat
* access sdk tools

It should work on windows/osx/linux.

## Recent Changes ##

###0.2###

* Added snippets
* Fixed running adb shell from the menu

###0.1###

* Added string refactoring
* Added project import
* Fixed readme not showing on new project creation
* Fixed new project and import project missing subfolders

###0.0###

* First version

## Requirements ##

* [Android SDK](http://developer.android.com/sdk/index.html)
* [Ant](http://ant.apache.org/) (needed for compiling Android applications).

## Installing

**Linux:**

 1. Download: https://bitbucket.org/allyourco_de/sublime-android/get/master.zip
 2. Unzip the content to ~/.config/sublime-text-3/Packages/sublime-android

-or-

```
cd ~/.config/sublime-text-3/Packages
git clone git@bitbucket.org:allyourco_de/sublime-android.git sublime-android
```

**Windows:**

 1. Download: https://bitbucket.org/allyourco_de/sublime-android/get/master.zip
 2. Unzip the content to "%UserProfile%\AppData\Sublime Text 3\Packages\sublime-android"

-or-

```
cd "%UserProfile%\AppData\Sublime Text 3\Packages"
git clone git@bitbucket.org:allyourco_de/sublime-android.git sublime-android
```

## Credits & Acknowledgments

Original work: [@uint9](http://9bitscience.blogspot.com/2012/06/sublime-text-2-android-plugin.html)
Inspired by and snippets from: [Andrew](http://github.com/Korcholis/Andrew)