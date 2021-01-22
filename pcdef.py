#  Power class defining parameters
charge_maximum   = 0   # maximum charge (pC) allowed in a window
charge_window    = 1   # window of 910kHz timeslots
interval_minimum = 2   # minimum interval between bunches

pcdef = [ (1,0,0),                 # PC0: no beam allowed
          (300,91000,91000),       # PC1: 300pC per 0.1sec, max 10Hz bunch rate
          (300*910000,910000,1) ]  # PC2: 300nC per second, no max rate
