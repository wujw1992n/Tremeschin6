"""
===============================================================================

        Dandere2x - Fast Waifu2x Upscale!!

Purpose: The most abstract script, deals with connecting all the others

Creates all the classes we need, checks, verifies, connects them, setup
and run Dandere2x.

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

from color import rgb, color_by_name

from d2xcpp import Dandere2xCPPWraper
from vp import VapourSynthWrapper
from controller import Controller
from processing import Processing
from d2xmath import D2XMath
from context import Context
from waifu2x import Waifu2x
from frame import Frame
from video import Video
from utils import Utils
from core import Core

import argparse
import time
import os


color = rgb(200, 255, 80)
phasescolor = rgb(84, 255, 87)
ROOT = os.path.dirname(os.path.abspath(__file__))


class Dandere2x():
    def __init__(self, args):
        self.args = args

        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # NOTE DEBUG/DEVELOPMENT PURPOSES ONLY
        os.system("sh dandere2x_cpp_tremx/linux_compile_full.sh")
        #exit()

    # This function loads up the "core" variables and objects
    def load(self):

        debug_prefix = "[Dandere2x.load]"

        self.utils = Utils()

        self.utils.log(phasescolor, "# # [Load phase] # #")
        self.utils.log(color, debug_prefix, "Created Utils()")

        # Communication between files, static
        self.utils.log(color, debug_prefix, "Creating Context()")
        self.context = Context(self.utils)

        # Communication between files, depends on runtime
        self.utils.log(color, debug_prefix, "Creating Controller()")
        self.controller = Controller(self.utils, self.context)

        # Let Utils access Controller
        self.utils.log(color, debug_prefix, "Giving Utils, Controller")
        self.utils.set_controller(self.controller)

        # Let Utils access Context
        self.utils.log(color, debug_prefix, "Giving Utils, Context")
        self.utils.set_context(self.context)

        # Deals with Video related stuff
        self.utils.log(color, debug_prefix, "Creating Video()")
        self.video = Video(self.context, self.utils, self.controller)

        # Our upscale wrapper, on which the default is Waifu2x
        self.utils.log(color, debug_prefix, "Creating Waifu2x()")
        self.waifu2x = Waifu2x(self.context, self.utils, self.controller)

        # Math utils, specific cases for Dandere2x
        self.utils.log(color, debug_prefix, "Creating D2XMath()")
        self.math = D2XMath(self.context, self.utils)

        # Dandere2x C++ wrapper
        self.utils.log(color, debug_prefix, "Creating Dandere2xCPPWraper()")
        self.d2xcpp = Dandere2xCPPWraper(self.context, self.utils, self.controller, self.video)

        # Deals with images, mostly numpy wrapper and special functions like block substitution
        self.utils.log(color, debug_prefix, "Creating Frame()")
        self.frame = Frame(self.context, self.utils, self.controller)

        # "Layers" of processing before the actual upscale from Waifu2x
        self.utils.log(color, debug_prefix, "Creating Processing()")
        self.processing = Processing(self.context, self.utils, self.controller, self.frame, self.video, self.waifu2x)

        # On where everything is controlled and starts
        self.utils.log(color, debug_prefix, "Creating Core()")
        self.core = Core(self.context, self.utils, self.controller, self.waifu2x, self.d2xcpp, self.processing)

        # Vapoursynth wrapper
        self.utils.log(color, debug_prefix, "Creating VapourSynthWrapper()")
        self.vapoursynth_wrapper = VapourSynthWrapper(self.context, self.utils, self.controller)

    # This function mainly configures things before upscaling and verifies stuff,
    # sees if it's a resume session, etc
    def setup(self):

        self.utils.log(phasescolor, "# # [Setup phase] # #")

        debug_prefix = "[Dandere2x.setup]"

        # Set and verify Waifu2x
        self.utils.log(color, debug_prefix, "Setting corresponding Waifu2x")
        self.waifu2x.set_corresponding()

        self.utils.log(color, debug_prefix, "Verifying Waifu2x")
        self.waifu2x.verify()

        self.utils.log(color, debug_prefix, "Generating run command from Waifu2x")
        self.waifu2x.generate_run_command()

        # Warn the user and log mindisk mode
        if self.context.mindisk:
            self.utils.log(color, debug_prefix, "[MINDISK] [WARNING] MINDISK MODE [ON]")
        else:
            self.utils.log(color, debug_prefix, "[MINDISK] [WARNING] MINDISK MODE [OFF]")

        # Check if context_vars file exist and is set to be resume
        # If force argument is set, force not resume session
        if not self.args["force"]:
            self.utils.log(color, debug_prefix, "Checking if is Resume session")
            self.context.resume = self.utils.check_resume()
        else:
            self.utils.log(rgb(255,100,0), debug_prefix, "FORCE MODE ENABLED, FORCING RESUME=FALSE")
            self.context.resume = False

        # NOT RESUME SESSION, delete previous session, load up and check directories
        if not self.context.resume:

            # Log and reset session directory
            self.utils.log(color_by_name("li_red"), debug_prefix, "NOT RESUME SESSION, deleting session [%s]" % self.context.session_name)
            self.utils.reset_dir(self.context.session)

            # Check dirs
            self.utils.log(color, debug_prefix, "Checking directories")
            self.utils.check_dirs()

            # Reset files
            self.utils.log(color, debug_prefix, "Reseting files")
            self.utils.reset_files()

            # Debugging, show static files
            self.utils.log(color, debug_prefix, "Showing static files")
            self.utils.show_static_files()

            # Get video info
            self.utils.log(color, debug_prefix, "Getting video info")
            self.video.get_video_info()

            self.utils.log(color, debug_prefix, "Showing video info")
            self.video.show_info()

            # DEPRECATED
            # Set block size and a valid input resolution
            # self.utils.log(color, debug_prefix, "Setting block_size")
            # self.math.set_block_size()

            # DEPRECATED
            # self.utils.log(color, debug_prefix, "Getting valid input resolution")
            # self.math.get_a_valid_input_resolution()

            # Save vars of context so d2x_cpp can use them and we can resume it later
            self.utils.log(color, debug_prefix, "Saving Context vars to file")
            self.context.save_vars()

            # Apply pre vapoursynth filter
            if self.context.use_vapoursynth:

                # Apply pre filter
                self.vapoursynth_wrapper.apply_filter(
                    self.context.vapoursynth_pre,
                    self.context.input_file,
                    self.context.vapoursynth_processing
                )

                # As we applied pre filter, our input video is now the processed one by vapoursynth
                self.context.input_file = self.context.vapoursynth_processing

                # # As something like a transpose can modify the video resolution we get the new info

                # Get video info
                self.utils.log(color, debug_prefix, "Getting new video info [Vapoursynth can modify resolution]")
                self.video.get_video_info()

                self.utils.log(color, debug_prefix, "Showing new video info")
                self.video.show_info()

                # If we have already applied pre noise with ffmpeg, delete the old noisy file
                if self.context.apply_pre_noise:
                    if self.context.mindisk:
                        self.utils.log(color, debug_prefix, "[MINDISK] Deleting noisy video [%s]" % self.context.noisy_video)
                        self.utils.delete_file(self.context.noisy_video)
                    else:
                        self.utils.log(color, debug_prefix, "Mindisk mode OFF, DO NOT delete noisy video [%s]" % self.context.noisy_video)

            # Welp we don't need to add previous upscaled video if we're just starting
            self.video.ffmpeg.pipe_one_time(self.utils.get_partial_video_path())

        # IS RESUME SESSION, basically load instructions from the context saved vars
        else:
            self.utils.log(color_by_name("li_red"), debug_prefix, "IS RESUME SESSION")

            self.utils.log(color, debug_prefix, "[FAILSAFE] DELETING RESIDUAL, UPSCALE DIR AND PLUGINS INPUT FILE")

            self.utils.reset_dir(self.context.residual)
            self.utils.reset_dir(self.context.upscaled)

            self.utils.reset_file(self.context.d2x_cpp_plugins_out)

            self.utils.log(color, debug_prefix, "[FAILSAFE] REGENERATING DIRS")
            self.utils.check_dirs()

            self.utils.log(color, debug_prefix, "Loading Context vars from context_vars file")
            self.context.load_vars_from_file(self.context.context_vars)

            self.video.save_last_frame_of_video_ffmpeg(self.utils.get_last_partial_video_path(), self.context.resume_video_frame)

            self.video.ffmpeg.pipe_one_time(self.utils.get_partial_video_path())

    # Here's the core logic for Dandere2x
    def run(self):

        debug_prefix = "[Dandere2x.run]"

        self.d2xcpp.generate_run_command()

        # Only write the debug video just for fun
        if self.context.write_only_debug_video:
            self.context.mindisk = False
            self.d2xcpp.generate_run_command()
            self.utils.log(color, debug_prefix, "WRITE ONLY DEBUG VIDEO SET TO TRUE, CALLING CPP AND QUITTING")
            self.context.last_processing_frame = 0
            self.d2xcpp.run()
            self.controller.exit()
            return 0

        self.d2xcpp.generate_run_command()

        # As now we get into the run part of Dandere2x, we don't really want to log
        # within the "global" log on the root folder so we move the logfile to session/log.log
        self.utils.move_log_file(self.context.logfile)

        # DEPRECATED Set out current position on video and the input
        # DEPRECATED self.video.frame_extractor.setup_video_input(self.context.input_file)
        # DEPRECATED self.video.frame_extractor.set_current_frame(self.context.last_processing_frame)

        self.utils.log(phasescolor, "# # [Run phase] # #")

        self.core.parse_whole_cpp_out()

        self.core.start()

        self.core.get_d2xcpp_vectors()

        # Show the user we're still alive

        since_started = 0

        while True:
            if self.controller.stop:
                break

            if self.controller.upscale_finished:
                break

            self.utils.log(color, debug_prefix, "Time since started: %s" % since_started)

            if since_started == 50000:
                self.context.resume = True
                self.context.save_vars()
                self.controller.exit()
                return 0

            since_started += 1
            time.sleep(1)

        # When we exit the while loop either we finished or we stopped
        if self.controller.upscale_finished:

            # If we finished in a single run time
            partials = len(os.listdir(self.context.partial))

            if partials == 1:
                self.utils.move(self.context.partial + "0.mkv", self.context.upscaled_video)

            elif partials > 1:
                # If we have two or more partials video
                self.video.ffmpeg.concat_video_folder_reencode(self.context.partial, self.context.upscaled_video)

                # Delete the partial dir
                self.utils.reset_dir(self.context.partial)

            else:
                self.utils.log(color, debug_prefix, "No partials were found in [%s]" % self.context.partial)
                return -1

            # Apply post vapoursynth filter as the upscale finished
            if self.context.use_vapoursynth:

                self.utils.log(color, debug_prefix, "APPLYING POST VAPOURSYNTH FILTER")

                if self.context.use_vapoursynth:
                    self.vapoursynth_wrapper.apply_filter(
                        self.context.vapoursynth_pos,
                        self.context.upscaled_video,
                        self.context.vapoursynth_processing
                    )

                    # Make the processed one the new upscaled
                    self.utils.delete_file(self.context.upscaled_video)
                    self.utils.rename(self.context.vapoursynth_processing, self.context.upscaled_video)

            # Migrate audio tracks from the original video to the new one
            self.video.ffmpeg.copy_videoA_audioB_to_other_videoC(
                self.context.upscaled_video,
                self.context.input_file,
                self.context.joined_audio
            )

            # Delete old only upscaled video as migrated tracks
            self.utils.delete_file(self.context.upscaled_video)
            self.utils.rename(self.context.joined_audio, self.context.output_file)

            self.controller.exit()

            # Happy upscaled video :)

        else:
            # Save progress for later resuming
            self.context.save_vars()


if __name__ == "__main__":

    # Create ArgumentParser
    args = argparse.ArgumentParser(description='Optional arguments for Dandere2x')

    # # Arguments

    # Force deletion of session, don't resume
    args.add_argument('-f', '--force', required=False, action="store_true", help="Forces deletion of session")

    # Parse args and make dictionary
    args = args.parse_args()

    args = {
        "force": args.force
    }

    # Run Dandere2x

    d2x = Dandere2x(args)
    d2x.load()
    d2x.setup()

    try:
        d2x.run()
    except KeyboardInterrupt:
        print("KeyboardInterrupt catched, saving and exiting..")
        d2x.controller.exit()
        d2x.context.resume = True
        d2x.context.save_vars()
