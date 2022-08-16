import time

import cv2
from base_camera import BaseCamera


class Camera(BaseCamera):
    video_source = 0

    def __init__(self, rtsp, name):
        Camera.set_video_source(rtsp)
        super(Camera, self).__init__(dev_name=name, rtsp=rtsp)

    @staticmethod
    def set_video_source(source):
        Camera.video_source = source

    @staticmethod
    def frames():
        camera = cv2.VideoCapture(Camera.video_source)
        camera.set(cv2.CAP_PROP_BUFFERSIZE, 3)
        camera.set(cv2.CAP_PROP_FPS, 25)
        # camera.set(cv2.CAP_PROP_POS_FRAMES, 100)
        # camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))

        if not camera.isOpened():
            raise RuntimeError('Could not start camera.')

        while True:
            # read current frame
            time.sleep(0.042)
            _, img = camera.read()

            # encode as a jpeg image and return it
            try:
                yield cv2.imencode('.jpg', img)[1].tobytes()
            except Exception:
                time.sleep(0.1)