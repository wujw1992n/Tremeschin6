"""
===============================================================================

Purpose: Deals with building the final video according to the C++ data we get
from the block matching

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

from color import colors

import threading
import math
import time
import copy
import os


color = colors["processing"]


class Processing():
    def __init__(self, context, utils, controller, frame, video, waifu2x):

        debug_prefix = "[Processing.__init__]"

        self.context = context
        self.utils = utils
        self.controller = controller
        self.frame = frame
        self.video = video
        self.waifu2x = waifu2x

    # A generator which gives us the vectors for iterating over the upscaled residual
    def residual_vector_iterator_generator(self, columns, rows, width, height, bleed, block_size):

        debug_prefix = "[Processing.residual_vector_iterator_generator]"

        bleed *= 2
        block_size *= 2

        bleeded_block_size = block_size + (2*bleed)

        for y in range(rows):
            start_y = bleed + (bleeded_block_size * y)
            for x in range(columns):
                start_x = bleed + (bleeded_block_size * x)
                self.utils.log(color, 10, debug_prefix, "Yielding: [%s, %s]" % (start_y, start_x))
                yield (start_y, start_x)

    # Main routine on merging frames
    def run(self):

        debug_prefix = "[Processing.run]"

        residual_upscaled = self.frame(self.context, self.utils, self.controller)
        start_frame = self.frame(self.context, self.utils, self.controller)

        start_frame.new(self.context.resolution[0] * 2, self.context.resolution[1] * 2)

        if self.context.last_processing_frame > 0:
            start_frame.load_from_path_wait(self.context.resume_video_frame)

            self.utils.log(color, 1, debug_prefix, "Is resume session, deleting previous residuals")

            for i in range(self.context.last_processing_frame - 1):
                previous_residual = self.context.residual + "residual_" + self.utils.pad_zeros(i) + ".jpg"
                self.utils.delete_file(previous_residual)

        self.merged = start_frame

        # For each frame since the one we started with
        frame_number = self.context.last_processing_frame

        while True:

            # Wait for file to exist or quit if controller says so
            while True:
                if self.controller.stop == True:
                    self.utils.log(color, 1, debug_prefix, "Stopping processing as controller stop is True")
                    return 0
                if str(frame_number) in self.controller.block_match_data:
                    break
                if frame_number == self.context.frame_count:
                    break
                
                self.utils.log(color, 7, debug_prefix, "Waiting for frame_number [%s] in controller.block_match_data" % frame_number)
                time.sleep(0.5)

            working_data = self.controller.block_match_data[str(frame_number)]
            working_vector_ids = working_data["data"]
            working_type = working_data["type"]

            # print("working_data", working_data)
            # print("vector ids", working_vector_ids)

            self.utils.log(color, 9, debug_prefix, "[%s] Working vector ids:" % frame_number)
            self.utils.log(color, 9, debug_prefix, working_vector_ids)
           
            if (working_type == "blocks") and (not working_vector_ids == ['']):
                
                self.utils.log(color, 8, debug_prefix, "Merged image is from upscaled residual")

                # Each Waifu2x outputs the images in a different naming sadly
                residual_upscaled_file_path = self.waifu2x.get_residual_upscaled_file_path_output_frame_number(frame_number)

                residual_upscaled.load_from_path_wait(residual_upscaled_file_path)

                if self.controller.stop:
                    self.utils.log(color, 1, debug_prefix, "Quitting as controller said to stop")
                    return 0
                
                residual_dimensions = (residual_upscaled.width, residual_upscaled.height)

                # As we trim the bottom black portion of the image, there can be some weird blocks like
                # 44x48 resolution, so whenever that happens we just get the ceil of that number
                # as it'll be 0 < x < 1 for a (1, 1) block grid where 1 is x
                grid_dimensions = [
                    math.ceil( ((residual_dimensions[0]) / ( (self.context.bleed*2 + self.context.block_size)*2) ) ),
                    math.ceil( ((residual_dimensions[1]) / ( (self.context.bleed*2 + self.context.block_size)*2) ) )
                ]

                # columns, rows, width, height, bleed, block_size
                this_residual_vector_generator = \
                    self.residual_vector_iterator_generator(
                        grid_dimensions[0],
                        grid_dimensions[1],
                        residual_dimensions[0],
                        residual_dimensions[1],
                        self.context.bleed,
                        self.context.block_size
                    )

                # Loop every block vector
                for vector_id in working_vector_ids:
                    
                    # Get the two positions we copy to and from the residual upscaled and merged frame
                    residual_get_vector = next(this_residual_vector_generator)
                    position_where_vector = self.controller.vectors[vector_id]

                    self.utils.log(color, 10, debug_prefix, "residual vector: ", residual_get_vector)
                    self.utils.log(color, 10, debug_prefix, "position vector: ", position_where_vector)

                    # Use our data to make the merged image
                    self.merged.copy_from(
                        residual_upscaled.frame,
                        self.merged.frame,
                        [residual_get_vector[0], residual_get_vector[1]],
                        [position_where_vector[0], position_where_vector[1]],
                        [position_where_vector[2] - 1, position_where_vector[3] - 1]
                    )

                    # See the blocks being completed, useful for debug
                    # self.merged.save("merged/merged_frame_%s_vector_%s.png" % (frame_number, vector_id))

            else:
                # No vectors to substitute

                if working_type == "end":
                    self.utils.log(color, 8, debug_prefix, "Writing the same previous merged frame as working_type==exit")
                    break
                
                self.utils.log(color, 8, debug_prefix, "Writing the same previous merged frame as vectors==null")
            
            self.utils.log(color, 8, debug_prefix, "Writing merged image into pipe n=[%s]" % frame_number)

            # self.merged.save("merged/merged_frame_%s.png" % frame_number)
            # self.merged.save("merged/merged.png")

            self.video.ffmpeg.write_to_pipe(self.merged.frame)
            
            self.utils.log(color, 8, debug_prefix, "Wrote merged frame")

            # Update the last processed frame
            self.context.last_processing_frame = frame_number            

            self.utils.log(color, 8, debug_prefix, "Context last_processing_frame is now [%s]" % self.context.last_processing_frame)
            self.utils.log(color, 8, debug_prefix, "[FAILSAFE] Saving context vars if Dandere2x crashes")
            
            self.context.save_vars()

            frame_number += 1

        self.utils.log(color, 1, debug_prefix, "All merged images done, closing pipe")

        # Finished piping all the images we merged
        self.video.ffmpeg.close_pipe()

        self.controller.upscale_finished = True
        self.controller.exit()


if __name__ == "__main__":
    print("You shouldn't be running this file directly, Dandere2x is class based and those are handled by dandere2x.py which is controlled by dandere2x_cli.py or the upcoming GUI")
