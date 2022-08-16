#!/usr/bin/env python
import time

from flask import Flask, render_template, Response

from rtsp import rtsp_stolovaya, rtsp3_parkovka, rtsp2_servernaya

import camera_opencv

app = Flask(__name__)

@app.route('/servernaya')
def index1():
    """Video streaming home page."""
    return render_template('servernaya.html')


@app.route('/stolovaya')
def index():
    """Video streaming home page."""
    return render_template('stolovaya.html')


@app.route('/parkovka')
def index2():
    """Video streaming home page."""
    return render_template('parkovka.html')



def gen(camera):
    """Video streaming generator function."""
    yield b'--frame\r\n'
    while True:
        try:
            frame = camera.get_frame()
            yield b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n--frame\r\n'
        except Exception:
            time.sleep(0.1)


@app.route('/video_feed_stolovaya')
def video_feed_stolovaya():

    return Response(gen(camera_opencv.Camera(rtsp_stolovaya, 'stol')),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/video_feed_servernaya')
def video_feed_servernaya():

    return Response(gen(camera_opencv.Camera(rtsp2_servernaya, 'serv')),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/video_feed_parkovka')
def video_feed_parkovka():
    return Response(gen(camera_opencv.Camera(rtsp3_parkovka, 'park')),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    from waitress import serve

    serve(app, host="0.0.0.0", port=5000)
