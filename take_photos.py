from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import io
import time
import numpy as np
import picamera
import sys

from PIL import Image
from tflite_runtime.interpreter import Interpreter

def main():
  width, height = (224, 224)

  if len(sys.argv) < 2:
    print(f"usage: {sys.argv[0]} class_name")
    sys.exit(1)
  
  i = 0
    
  with picamera.PiCamera(resolution=(640, 480), framerate=0.5) as camera:
    camera.start_preview()
    try:
      stream = io.BytesIO()
      for _ in camera.capture_continuous(stream, format='jpeg', use_video_port=True):
        stream.seek(0)
        image = Image.open(stream).convert('RGB').resize((width, height), Image.ANTIALIAS)

        image.save(f"{sys.argv[1]}{i}.jpg")
        i += 1
        print(f"Took {i}-th photo.")

        stream.seek(0)
        stream.truncate()

    finally:
      camera.stop_preview()


if __name__ == '__main__':
  main()
