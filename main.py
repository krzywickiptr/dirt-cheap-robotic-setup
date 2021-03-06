# python3
#
# Copyright 2019 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Example using TF Lite to classify objects with the Raspberry Pi camera."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import os
import io
import time
import numpy as np
import picamera
import serial
import collections

from PIL import Image
from tflite_runtime.interpreter import Interpreter


def load_labels(path):
  with open(path, 'r') as f:
    return {i: line.strip() for i, line in enumerate(f.readlines())}


def set_input_tensor(interpreter, image):
  tensor_index = interpreter.get_input_details()[0]['index']
  input_tensor = interpreter.tensor(tensor_index)()[0]
  input_tensor[:, :] = image


def classify_image(interpreter, image, top_k=1):
  """Returns a sorted array of classification results."""
  set_input_tensor(interpreter, image)
  interpreter.invoke()
  output_details = interpreter.get_output_details()[0]
  output = np.squeeze(interpreter.get_tensor(output_details['index']))
  #print(output)

  # If the model is quantized (uint8 data), then dequantize the results
  if output_details['dtype'] == np.uint8:
    scale, zero_point = output_details['quantization']
    output = scale * (output - zero_point)

  ordered = np.argpartition(-output, top_k)
  return [(i, output[i]) for i in ordered[:top_k]]


def slides():
    from pynput.mouse import Button, Controller
    mouse = Controller()

    def wait_click():
        old = mouse.position
        while old == mouse.position:
            pass

    #os.system('DISPLAY=:0 feh --hide-pointer -x -q -B black -g 800x480 ~/matchit.png --scale-down --auto-zoom . &')
    #wait_click()
    os.system('DISPLAY=:0 feh --hide-pointer -x -q -B black -g 800x480 ~/makieta.png --scale-down --auto-zoom . &')
    wait_click()
    os.system('sleep 1 && killall feh &')


def main():
  parser = argparse.ArgumentParser(
      formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument(
      '--model', help='File path of .tflite file.', required=True)
  parser.add_argument(
      '--labels', help='File path of labels file.', required=True)
  args = parser.parse_args()

  labels = load_labels(args.labels)

  interpreter = Interpreter(args.model)
  interpreter.allocate_tensors()
  _, height, width, _ = interpreter.get_input_details()[0]['shape']


  print((height, width))
  history = collections.deque(maxlen=10)

  tty = serial.Serial(
    port='/dev/ttyUSB0',
    baudrate=115200,
    #parity=serial.PARITY_ODD,
    #stopbits=serial.STOPBITS_TWO,
    #bytesize=serial.SEVENBITS
  )

  tty.timeout = 0.1
  tty.writeTimeout = 0
  tty.setDTR(True)

  tty.close()
  tty.open()
  assert tty.isOpen()

  with picamera.PiCamera(resolution=(800, 480), framerate=30) as camera:
    slides()
    camera.start_preview()
    time.sleep(2)
    try:
      stream = io.BytesIO()
      for _ in camera.capture_continuous(
          stream, format='jpeg', use_video_port=True):
        stream.seek(0)
        image = Image.open(stream).convert('RGB').resize((width, height),
                                                         Image.ANTIALIAS)
        start_time = time.time()
        results = classify_image(interpreter, image)
        elapsed_ms = (time.time() - start_time) * 1000
        label_id, prob = results[0]
        if prob < 0.6:
          label_id = 1
        history.append(label_id)

        if len(history) == 10 and len(set(history)) == 1:
          def move(avalue):
            tty.write(b"A0\n")
            time.sleep(0.5)
            tty.write(b"C105\n")
            time.sleep(0.5)
            tty.write(b"D55\n")
            time.sleep(0.5)
            tty.write(b"B150\n")
            time.sleep(0.5)

            tty.write(b"C140\n")
            time.sleep(0.5)
            tty.write(b"D0\n")
            time.sleep(0.5)
            tty.write(f"A{avalue}\n".encode())
            time.sleep(0.5)
            tty.write(b"B90\n")
            time.sleep(2)
            tty.write(b"A90\n")
            time.sleep(0.5)

          if history[0] == 0: # nakretka
            move(70)

          if history[0] == 2: # papier
            move(110)
          history = collections.deque(maxlen=10)

        stream.seek(0)
        stream.truncate()
        camera.annotate_text_size = 48
        camera.annotate_foreground = picamera.Color(y=0, u=0, v=0)
        camera.annotate_background = picamera.Color(y=1, u=0, v=0)
        camera.annotate_text = '%s' % (labels[label_id])#, prob, elapsed_ms)
    finally:
      camera.stop_preview()
      tty.close()


if __name__ == '__main__':
  main()
