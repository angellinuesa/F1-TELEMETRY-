class PlaybackController:

    def __init__(self, max_frame):

        self.frame = 0

        self.playing = True

        self.max_frame = max_frame

        self.playback_speed = 1

    def update(self):

        if self.playing:

            self.frame += self.playback_speed

        if self.frame > self.max_frame:
            self.frame = 0

    def toggle_pause(self):

        self.playing = not self.playing

    def restart(self):
        self.frame = 0

    def rewind(self, frames=60):
        self.frame = max(0, self.frame - frames)

    def forward(self, frames=60):
        self.frame = min(self.max_frame, self.frame + frames)

    def increase_speed(self):
        self.playback_speed = min(8, self.playback_speed * 2)

    def decrease_speed(self):
        self.playback_speed = max(0.25, self.playback_speed / 2)