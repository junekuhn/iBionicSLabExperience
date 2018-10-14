class PathModel:
    def __init__(self, tracks, height, width):
        self.tracks = tracks
        self.height = height
        self.width = width

    def getTracks(self):
        return self.tracks

    def getHeight(self):
        return self.height

    def getWidth(self):
        return self.width
