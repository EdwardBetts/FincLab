Install Python 2.7, virtualenv and virtualenvwrapper on OS X Mavericks/Yosemite
==

[source](http://www.marinamele.com/2014/05/install-python-virtualenv-virtualenvwrapper-mavericks.html)
May 1, 2014 Marina Mele	

This post explains how to install a clean version of Python in a Mac OS X Mavericks/Yosemite.

You’ll also learn to install and use the virtualenv and virtualenvwrapper tools to create virtual environments for your projects.
Install Xcode and Homebrew

First of all, install Xcode if you don’t have it already. You can find it in the Apple Store.

Next, we need to install the Command Line Tools of Xcode. Open a Terminal and type:
$ xcode-select --install
	
$ xcode-select --install

this should trigger a pop-up window that will ask you to install the Command Line Tools. If you have some trouble installing these tools, you might find useful this post on Stackoverflow.

Next, we need to install Homebrew. In the Terminal, type this command line:
$ ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"

Note: The previous line updates often, so you may want to check the official site for the updated command line –> Homebrew.

Now, we need to insert the Homebrew directory at the top of the PATH environment variable. In this way, some Homebrew installations, like Python, will take precedence over stock OS X binaries. Open or create the file ~/.bash_profile and write:
export PATH=/usr/local/bin:$PATH
	
export PATH=/usr/local/bin:$PATH

Note: Usually, in Linux, Unix and Mac systems, the file .bash_profile is executed to configure your shell when you log in via console. When you are already logged in your machine and open a new terminal window, the file .bashrc is executed instead. However, Mac OS X is an exception, as its Terminal.app always runs a login shell by default in each new window, and calls the file .bash_profile. If you want to maintain two separate config files for login and non-login shells, you can set the common settings in .bashrc and import them in .bash_procfile with:
if [ -f ~/.bashrc ]; then
    source ~/.bashrc
fi
	
if [ -f ~/.bashrc ]; then
    source ~/.bashrc
fi

This script looks for the .bashrc file, and calls it if exists. Close your Terminal and open it again to make these changes effective.
Install Python 2.7

First of all, let’s see the path of the Python that comes installed with Mavericks/Yosemite by typing:
$ which python
	
$ which python

which should show /usr/bin/python . 

Now, we are ready to install Python 2.7 by typing:
$ brew install python
	
$ brew install python

The good thing about installing Python with Homebrew is that you also install pip and Distribute, which extend the packaging and installation facilities provided by the distutils in the standard library.

And now, the python path should be:
$ which python
/usr/local/bin/python
	
$ which python
/usr/local/bin/python

Finally, we need to add the new Python scripts directory to your PATH. Open again the .bash_profile file and add
export PATH=/usr/local/share/python:$PATH
	
export PATH=/usr/local/share/python:$PATH

Close and open your Terminal to apply these changes.
Install virtualenv and virtualenvwrapper

A good practice when working in a Python project is to use a virtual environment. This allows you to have all the packages needed in one place. It is more easy to share and maintain.

To install virtualenv type in your terminal:
$ pip install virtualenv
	
$ pip install virtualenv

Now, you can create a virtual environment with

$ virtualenv myenvironment
	
$ virtualenv myenvironment

which will create the folder myenvironment. To activate this environment type:
$ source myenvironemtn/bin/activate
$ source myenvironemtn/bin/activate

and to deactivate it, just type:
$ deactivate
$ deactivate

Wrapped Python

Moreover, I recommend you also install virtualenvwrapper, which is a set of extensions that allows you to activate and change environments more easily. To install it:
$ pip install virtualenvwrapper
$ pip install virtualenvwrapper

Next, create a folder that will contain all your virtual environments:
$ mkdir ~/.virtualenvs
$ mkdir ~/.virtualenvs

Open your .bashrc file and add:
export WORKON_HOME=~/.virtualenvs
source /usr/local/bin/virtualenvwrapper.sh

you can activate these changes by typing
$ source .bashrc
$ source .bashrc

or
$ source .bash_profile
$ source .bash_profile

if your .bash_profile calls the .bashrc, as explained earlier.

Now, you can create a virtual environment by typing:
$ mkvirtualenv myenvironment
$ mkvirtualenv myenvironment

which will create the folder ~/.virtualenvs/myenvironment, and it will be initially active.

You can change from one virtual environment to another by just typing:
$ workon myenvironment
$ workon myenvironment

Deactivate an environment with
$ deactivate
$ deactivate

Delete an environment with
$ rmvirtualenv myenvironment
$ rmvirtualenv myenvironment

And list the existing environments with
$ lsvirtualenv
$ lsvirtualenv

You can find more useful commands here.

Wooha! Now you’re ready to start working on your Python projects! 😉

Was it useful? Don’t miss all the thins you can learn here!

and please… give a g+1 and share!! Thanks!
