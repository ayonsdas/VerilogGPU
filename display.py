import struct
import sys
from typing import TextIO
import imageio
import cv2

import numpy as np

from float_binary_converter import binary_to_float

class Display:
    def __init__(self) -> None:
        self.output_width = 256
        self.output_height = 256

        # Create a 256x256x4 NumPy array with half-precision floating-point numbers
        # The 4 channels represent: Red, Green, Blue, and Depth
        self.images = []
    def print_stream_data(self, stream: TextIO) -> None:
        image = np.zeros((self.output_height, self.output_width, 4), dtype=np.float16)
        while True:
            buffer = stream.read(7)
            if not buffer:
                break
            if buffer == "publish":
                self.images.append(image[:, :, :3])
                image = np.zeros((self.output_height, self.output_width, 4), dtype=np.float16)
                buffer = ""
                print("published ", len(self.images))
            
            bitcount = 32*16*4 + 32 + 1*16*2 # 4 vectors of 32 floats, 1 vector mask, 2 uints
            chunk = buffer + stream.read(bitcount - len(buffer))
            if not chunk:
                break
            data = int(chunk, 2).to_bytes(bitcount//8, byteorder='big')
            # float_data = np.frombuffer(data[:16], dtype=np.float16)
            # bool_data = np.frombuffer(data[16:32], dtype=np.bool)
            # uint_data = np.frombuffer(data[16:], dtype=np.uint16)
            # print(float_data, uint_data)
            float16_data = [] # struct.unpack('16f', data[:16*4])
            for i in range(32*4):
                float16_data.append(binary_to_float(chunk[i*16:(i+1)*16]))
            # skip 32x4x2 bytes of float data
            uint32_data = struct.unpack('>I', data[32*4*2:32*4*2+4])
            # extract bools from each bit of the uint32
            bool_data = [bool(uint32_data[0] & (1 << i)) for i in range(32)]
            # extract 2 uint16 from data
            uint16_data = struct.unpack('>HH', data[32*4*2+4:32*4*2+4+4])

            # print(uint16_data)

            # # the first 32 floats are the red values
            # reds = float_data[:32]
            # # the next 32 floats are the green values
            # greens = float_data[32:64]
            # # the next 32 floats are the blue values
            # blues = float_data[64:96]
            # # the next 32 floats are the depth values
            # depths = float_data[96:128]
            # # the 
            # # the first uint is the x coordinate
            # x = uint_data[0]
            # # the second uint is the y coordinate
            # y = uint_data[1]

            # the first 32 floats are the red values
            reds = float16_data[:32]
            reds.reverse()
            # the next 32 floats are the green values
            greens = float16_data[32:64]
            greens.reverse()
            # the next 32 floats are the blue values
            blues = float16_data[64:96]
            blues.reverse()
            # the next 32 floats are the depth values
            depths = float16_data[96:128]
            depths.reverse()
            # the bools represent the mask
            mask = bool_data
            mask.reverse()
            # the first uint is the x coordinate
            x = uint16_data[0]
            # the second uint is the y coordinate
            y = uint16_data[1]

            # write the data to the display, considering mask
            # self.data[y, x, 0] = reds
            # self.data[y, x, 1] = greens
            # self.data[y, x, 2] = blues
            # self.data[y, x, 3] = depths
            for i in range(32):
                if mask[i] and x >= 0 and y >= 0 and x+i < 256 and y < 256:
                    image[y, x+i, 0] = reds[i]
                    image[y, x+i, 1] = greens[i]
                    image[y, x+i, 2] = blues[i]
                    image[y, x+i, 3] = depths[i]
            
            # notify wrote screen at x, y
            # print(f'wrote screen at {x}, {y}')
        # self.images.append(image)
    
    def write(self, basename) -> None:
        if (len(self.images) == 1):
            self.write_to_png(basename)
        else:
            self.write_to_mp4(basename)
    
    def write_to_mp4(self, basename: str) -> None:
        output_video_filename = basename + ".mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')

        # Set the frame size and FPS
        frame_size = (self.output_height, self.output_width)
        fps = 60

        # Create the video writer object
        video_writer = cv2.VideoWriter(output_video_filename, fourcc, fps, frame_size)

        # Loop through the images and write each one to the video
        for image in self.images:
            # Convert the image to uint8 and split into color channels
            data = np.clip(np.clip(image, 0, 1) * 255, 0, 255).astype(np.uint8)
            r = data[:, :, 0]
            g = data[:, :, 1]
            b = data[:, :, 2]
            # Merge the color channels into a BGR image
            frame = cv2.merge((b, g, r))
            # Write the frame to the video
            video_writer.write(frame)

        # Release the video writer object
        video_writer.release()

    # write the data to a file
    def write_to_png(self, basename: str) -> None:
        # remove the depth channel
        # self.data = self.data[:, :, :3]
        # convert the data to 8-bit unsigned integers
        data = np.clip(self.images[0] * 255, 0, 255).astype(np.uint8)
        # write the data to a PNG file
        imageio.imwrite(basename + '.png', data)


def main() -> None:
    display = Display()
    # feed stdin to the display
    display.print_stream_data(sys.stdin)
    # write the display to a PNG file
    display.write('output')

if __name__ == '__main__':
    main()