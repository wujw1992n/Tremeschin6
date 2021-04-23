"""
===============================================================================

Purpose: Set of utilities for Dandere2x, miscellaneous functions, algo logging

===============================================================================

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with
this program. If not, see <http://www.gnu.org/licenses/>.

===============================================================================
"""


# Utils is a file with mostly helpers and utilities hence its name

from inspect import currentframe
from color import color_by_name, rgb, fg, bg

import threading
import datetime
import shutil
import yaml
import time
import os


exitcolor = rgb(84, 209, 255)
color = color_by_name("li_blue")


class Utils():

    def __init__(self):
        self.ROOT = self.get_root()
        self.clean_set_log()


    # As we gotta close the file for exiting and potentially save session here?
    def exit(self):

        debug_prefix = "[Utils.exit]"

        self.log(exitcolor, debug_prefix, "Exiting...")

        self.log(exitcolor, debug_prefix, "Saving Context vars")

        self.context.save_vars()

        self.log(exitcolor, debug_prefix, "Send stop command to threads")
        self.context.stop = True

        self.log(exitcolor, debug_prefix, "Joining every thread")
        
        for threadname in self.context.threads:
            self.log(exitcolor, debug_prefix, "Joining thread: [%s]" % threadname)
            self.context.threads[threadname].join()
            self.log(exitcolor, debug_prefix, "Joined thread: [%s]" % threadname)
        
        self.log(exitcolor, debug_prefix, "Goodbye Dandere2x!!")
        
        exit()

    
    # On where the session name is set to "auto"
    def get_auto_session_name(self, input_file):

        debug_prefix = "[Utils.get_auto_session_name]"
        
        session_name = ''.join(input_file.split(".")[:-1])

        self.log(color, debug_prefix, "Session name is AUTO, setting it to: [%s]" % session_name)

        return session_name


    # As utils and context, controller are two separate classes
    def set_context(self, context):
        self.context = context

    def set_controller(self, controller):
        self.controller = controller


    # Get this file "absolute" path for relative reference
    def get_root(self):
        return os.path.dirname(os.path.abspath(__file__))


    # Get line number which this function is called, debugging
    def get_linenumber(self):
        return currentframe().f_back.f_lineno
    

    # Make directory if it does not exist
    def mkdir_dne(self, directory):

        debug_prefix = "[Utils.mkdir_dne]"

        if not os.path.isdir(directory):
            self.log(color, debug_prefix, "Directory does NOT exist, creating: [%s]" % directory)
            os.makedirs(directory)
        else:
            self.log(color, debug_prefix, "Directory already exists: [%s]" % directory)


    # Reset file (write empty) or create it
    def reset_file(self, filename):
        
        debug_prefix = "[Utils.reset_file]"

        if os.path.isfile(filename):
            self.log(color, debug_prefix, "File exists, reseting it: [%s]" % filename)
        else:
            self.log(color, debug_prefix, "File does NOT exist, creating empty: [%s]" % filename)
        
        with open(filename, "w") as f:
            f.write("")


    # Delete the file if it exists
    def delete_file(self, filename):

        debug_prefix = "[Utils.delete_file]"

        if os.path.isfile(filename):
            self.log(color, debug_prefix, "File exists, deleting it: [%s]" % filename)
            os.remove(filename)
        else:
            self.log(color, debug_prefix, "File does NOT exist")


    # Wrapper for self.mkdir_dne, checks the plain dirs from context
    def check_dirs(self):
        for directory in self.context.plain_dirs:
            self.mkdir_dne(directory)


    # Wrapper for self.reset_file, resets the plain files from context
    def reset_files(self):
        for item in self.context.plain_files:
            self.reset_file(item)

    
    # Deletes an directory, fail safe? Quits if 
    def reset_dir(self, directory):
        
        debug_prefix = "[Utils.reset_dir]"

        if os.path.isdir(directory):

            self.log(color, debug_prefix, "Removing dir: [%s]" % directory)

            shutil.rmtree(directory, ignore_errors=True)

            if os.path.isdir(directory):
                self.log(color, debug_prefix, "Error removing directory with ignore_errors=True, trying again")
                
                shutil.rmtree(directory, ignore_errors=False)

                if os.path.isdir(directory):
                    self.log(fg.li_red, debug_prefix, "COULD NOT REMOVE DIRECTORY: [%s]" % directory)
                    self.exit()
            
            self.log(color, debug_prefix, "Removed successfully")
        
        else:
            self.log(color, debug_prefix, "Directory exists, skipping... [%s]" % directory)


    # Debugging, show context static files
    def show_static_files(self):

        debug_prefix = "[Utils.show_static_files]"

        for item in self.context.plain_files:
            self.log(color, debug_prefix, "Static file: [%s]" % item)


    # Get operating system
    def get_os(self):

        debug_prefix = "[Utils.get_os]"

        # Not really specific but should work?
        if os.name == "posix":
            os_name = "linux"

        self.log(color, debug_prefix, "Got operating system:", os_name)
        return os_name


    # Return OS environment var like XDG_SESSION_TYPE or PATH
    def env_var(self, var):
        return os.environ[var]


    # Get the output of a commnd
    def command_output(self, command):
        return os.popen(command).read()
        

    # Wipe out logs.log file and set a self.logfile
    def clean_set_log(self):

        debug_prefix = "[Utils.clean_set_log]"

        logfilename = "logs.log"

        self.logfile = self.ROOT + os.path.sep + logfilename

        if os.path.isfile(self.logfile):
            print(color + debug_prefix, "Log file exists, deleting it: [%s]" % self.logfile, fg.rs)
            os.remove(self.logfile)
        else:
            print(color, debug_prefix, "Log file does NOT exist", fg.rs)

        with open(self.logfile, "w") as f:
            f.write("")

        self.log(color, debug_prefix, "Reseted log file")


    def log(self, color, *message):

        now = datetime.datetime.now().strftime("%d/%m/%Y-%H:%M:%S")

        processed_message = "[%s] " % now
        
        # Basically we define *message as an argument so we have to
        # "merge" it, ' '.join(everything)
        for index, item in enumerate(message):
            if isinstance(item, list) or isinstance(item, tuple):
                processed_message += " ".join(message[index]) + " "
            else:
                processed_message += str(item) + " "

        # As we add that extra space at the end, gotta remove it
        processed_message = processed_message[:-1]

        print (color + processed_message + fg.rs)

        with open(self.logfile, "a") as f:
            f.write(processed_message + "\n")


    # Safely load yaml file, just for cleaness of code
    def load_yaml(self, filename):

        debug_prefix = "[Utils.load_yaml]"

        self.log(color, debug_prefix, "Loading YAML file: [%s]" % filename)

        with open(filename, "r") as f:
            data = yaml.safe_load(f)
        return data


    # Save data to filename in yaml syntax
    def save_yaml(self, data, filename):

        debug_prefix = "[Utils.save_yaml]"

        self.log(color, debug_prefix, "Saving to YAML file: [%s]" % filename)

        with open(filename, "w") as f:
            yaml.dump(data, f)


    # This "follows" updating files, yields the new stuff written
    def updating_file(self, filename):
        ufile = open(filename, "r")
        ufile.seek(0,2)
        while True:
            if self.controller.stop: break
            line = ufile.readline()
            if not line:
                time.sleep(0.1)
                continue
            yield line
            

    # Check if context_vars file exist and returns the "resume" key value
    def check_resume(self):

        debug_prefix = "[Utils.check_resume]"

        self.log(color, debug_prefix, "Checking") 

        vars_file = self.context.context_vars

        if os.path.isfile(vars_file):
            
            data = self.load_yaml(vars_file)

            if "resume" in data:
                
                text = "True" if data["resume"] else "False"
                self.log(color, debug_prefix, "Resume key in session vars: [%s]" % text) 
                
                return data["resume"]
            
            self.log(color, debug_prefix, "Resume key not in session vars: [False]")
            return False
        else:
            self.log(color, debug_prefix, "Session vars file does not exist")
            return False

    
    # Waits until file exist or controller stop var is True
    def until_exist(self, path):

        debug_prefix = "[Utils.until_exist]"

        if self.context.loglevel >= 3:
            self.log(color, debug_prefix, "Waiting for file or diretory: [%s]" % path)

        while True:
            
            if os.path.exists(path) or self.controller.stop:
                if self.context.loglevel >= 3:
                    if self.controller.stop:
                        self.log(color, debug_prefix, "Quitting waiting: [%s]" % path)
                    else:
                        self.log(color, debug_prefix, "Waited done: [%s]" % path)
                
                break

            time.sleep(self.context.wait_time)


    # Rename file or directory
    def rename(self, old, new):

        debug_prefix = "[Utils.rename]"

        if self.context.loglevel >= 3:
            self.log(color, debug_prefix, "Renaming [%s] --> [%s]" % (old, new))

        os.rename(old, new)


    # Utility for string.replace(old, new) that substitutes with a dictionary
    def replace_by_dictionary(self, dictionary, replaced):

        # Debug info, show the original string to be replaced and the dictionary
        if self.context.loglevel >= 3:
            debug_prefix = "[Utils.replace_by_dictionary]"
            
            self.log(color, debug_prefix, "Replacing string [\"%s\"] with dictionary:" % replaced)

            for key in list(dictionary.keys()):
                self.log(color, "··· |", debug_prefix, "[\"%s\"] = [\"%s\"]" % (key, dictionary[key]))


        # Actually replace the string we want
        for key in list( dictionary.keys() ):
            replaced = replaced.replace(key, dictionary[key])


        if self.context.loglevel >= 3:
            self.log(color, debug_prefix, "Replaced string: [\"%s\"]" % replaced) 
        
        return replaced
