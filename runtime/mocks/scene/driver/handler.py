class Vid2scene:
    ...
    def _loop(self):
        ret, frame = self.vcap.read()
        while True:
            ret, frame = self.vcap.read()
            if self.md.moved(frame):
                frame = self.detect(frame)
                self.scene.put()

            cv2.waitKey(self.cap_interval)