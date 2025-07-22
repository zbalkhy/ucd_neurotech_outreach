from floatTheOrb import FloatTheOrb
from visualizing import Plotter
import pygame
from multiprocessing import Process

if __name__ == "__main__":
    floatTheOrb = FloatTheOrb()
    plotter = Plotter(400, 128)
    
    plotter.plot()
    #floatTheOrb.Run()
    #a = Process(target=plotter.plot)
    #b = Process(target=floatTheOrb.Run)
    #a.start()
    #b.start()
    #a.join()
    #b.join()
    
   


