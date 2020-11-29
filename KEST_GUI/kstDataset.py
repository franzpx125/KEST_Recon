import numpy

class kstDataset():

    def __init__(self, low, high, flat_low=None, flat_high=None, \
                 mode='2COL', acq_mode=False, source_file='', \
                 crop = [0,0,0,0]):
   
        self.mode = mode
        self.acq_mode = acq_mode
        self.source_file = source_file

        self.low = low
        self.high = high
        self.flat_low = flat_low
        self.flat_high = flat_high