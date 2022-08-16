import time
import threading
try:
    from greenlet import getcurrent as get_ident
except ImportError:
    try:
        from thread import get_ident
    except ImportError:
        from _thread import get_ident


class CameraEvent(object):
    """An Event-like class that signals all active clients when a new frame is
    available.
    """
    def __init__(self):
        self.events = {}

    def wait(self):
        """Invoked from each client's thread to wait for the next frame."""
        ident = get_ident()
        if ident not in self.events:
            # this is a new client
            # add an entry for it in the self.events dict
            # each entry has two elements, a threading.Event() and a timestamp
            self.events[ident] = [threading.Event(), time.time()]
        return self.events[ident][0].wait()

    def set(self):
        """Invoked by the camera thread when a new frame is available."""
        now = time.time()
        remove = None
        for ident, event in self.events.items():
            if not event[0].isSet():
                # if this client's event is not set, then set it
                # also update the last set timestamp to now
                event[0].set()
                event[1] = now
            else:
                # if the client's event is already set, it means the client
                # did not process a previous frame
                # if the event stays set for more than 5 seconds, then assume
                # the client is gone and remove it
                if now - event[1] > 5:
                    remove = ident
        if remove:
            del self.events[remove]

    def clear(self):
        """Invoked from each client's thread after a frame was processed."""
        self.events[get_ident()][0].clear()


class BaseCamera(object):
    thread = {}  # background thread that reads frames from camera
    frame = {}  # current frame is stored here by background thread
    last_access = {}  # time of last client access to the camera
    event = {}

    def __init__(self, rtsp, dev_name):

        """Start the background camera thread if it isn't running yet."""
        self.uname = "{cam}_{dev}".format(cam=dev_name, dev=rtsp)
        print(self.uname)
        BaseCamera.event[self.uname] = CameraEvent()
        if self.uname not in BaseCamera.thread:
            BaseCamera.thread[self.uname] = None
        if BaseCamera.thread[self.uname] is None:
            BaseCamera.last_access[self.uname] = time.time()

            # start background frame thread
            BaseCamera.thread[self.uname] = threading.Thread(target=self._thread, args=(self.uname, ))
            BaseCamera.thread[self.uname].start()

            # wait until first frame is available
            while self.get_frame() is None:
                time.sleep(0.1)

    def get_frame(self):
        """Return the current camera frame."""
        BaseCamera.last_access[self.uname] = time.time()

        # wait for a signal from the camera thread
        BaseCamera.event[self.uname].wait()
        BaseCamera.event[self.uname].clear()

        return BaseCamera.frame[self.uname]

    @staticmethod
    def frames():
        """"Generator that returns frames from the camera."""
        raise RuntimeError('Must be implemented by subclasses.')

    @classmethod
    def _thread(cls, uname):
        """Camera background thread."""
        print('Starting camera thread.')
        frames_iterator = cls.frames()
        for frame in frames_iterator:
            BaseCamera.frame[uname] = frame
            BaseCamera.event[uname].set()  # send signal to clients
            time.sleep(0.1)

            # if there hasn't been any clients asking for frames in
            # the last 2 seconds then stop the thread
            if time.time() - BaseCamera.last_access[uname] > 0.3:
                frames_iterator.close()
                print('Stopping camera thread due to inactivity.')
                break
        BaseCamera.thread[uname] = None
