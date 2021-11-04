"""   Starting point for running the program. """
import os

from UUTrack.startMonitor import start
from multiprocessing import Process

if __name__ == '__main__':
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    #confDir = os.path.join(BASE_DIR, 'Config')  
    #confFile = 'Config_simulate.yml'
    #start(confDir, confFile)
#    p = Process(target = start, args=(confDir,confFile))
#    p.start()
#    p.join()