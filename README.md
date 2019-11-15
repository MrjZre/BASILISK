# README  {#README}

### Basilisk ###

* [Summary of Basilisk](@ref cover)
* [Versions](http://hanspeterschaub.info/bskReleaseNotes.html)

### How do I get set up? ###
The following links contain installation instructions for the supported platforms:

- [Setup a macOS Development Environment](http://hanspeterschaub.info/bskHtml/Install/installOnMacOS.html)

- [Setup a Linux Development Environment](http://hanspeterschaub.info/bskHtml/Install/installOnLinux.html)

- [Setup a Windows Development Environment](http://hanspeterschaub.info/bskHtml/Install/installOnWindows.html)



### Basilisk Development guidelines ###

* [Coding Guidelines](@ref codingGuidelines)
* [Learn Markdown](https://bitbucket.org/tutorials/markdowndemo)


### Getting Started
To get started with Basilisk (BSK), several tutorial python files are provided in the installed package.  Within this web page documentation site, they are listed and discussed in the <a href="modules.html">Manual</a> tab.  The documentation lists the scenarios in an order that facilitates learning basic BSK features. In the source code they are stored under `src\examples\`. A good start would be to run `scenarioBasicOrbit.py`.

To play with the tutorials, it is suggested the user makes a copy of these tutorial files, and use the copies in order to learn, test and experiment. To copy them, first find the location of the Basilisk installation. After installing, you can find the installed location of Basilisk by opening a python interpreter and running:

```
import Basilisk
basiliskPath = Basilisk.__path__[0]
print(basiliskPath)
```

Now copy the folder `{basiliskPath}/src/examples` into a new folder, and change to that directory.

To run the default scenario 1 of scenarioBasicOrbit, in the directory of the copied tutorials, call the python script: `python3 scenarioBasicOrbit.py`


Now, when you want to use a tutorial, navigate inside that folder, and edit and execute the *copied* integrated tests.

<!--Any new BSK module development should not occur within the BSK folder as this will be updated rapidly.  Rather, new FSW algorithm or simulation coce modules should be created in a custom folder outside of the BSK directory.  A sample folder is provided named `BasiliskCustom` wich contains sample FSW and Simulation modules.-->

We are working on the ability to develop custom BSK modules outside of the Basilisk folder.  This will enable developers to safely write their own BSK modules and still be able to do a drop in replacement of future BSK releases.

To use the standalone 3D Visualization, download the [Vizard](https://hanspeterschaub.info/bskMain.html).  This is in development, but does provide a 3D view of many of the simulation states.  


### Who do I talk to? ###

- <mailto:basilisk-info@colorado.edu> - Use this email to request information about Basilisk, ask to be added as a test user, or provide suggestions
- <mailto:basilisk-bug@colorado.edu> - Use this email to send us info on bugs or issues.
