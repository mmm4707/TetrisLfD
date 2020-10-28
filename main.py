from enviorment.tetris import Tetris

import csv
import numpy as np
import time
from Imitation.data_handler import *

env = Tetris({'reduced_shapes': 1})

def main(manual=1):

    if manual:
        while 1:
            env.reset()
            done = False
            while not done:
                state, action, done = env.render(1)
                if state and action:
                    write_data(state, action)
    else:
        scores = []
        epoch = 100_000
        
        for e in range(epoch):
            
            if not e%500:
                print(e)
            
            score = 0
            state, reward, done, info = env.reset()
            
            while not done:
                
                action = env.action_sample             
                state, reward, done, info = env.step(action)
                
                env.render()
                time.sleep(0.1 if e < 2 else 0)
                
                score += reward
                
            if score != 0:
                scores.append(score)
                
        print(scores)

if __name__ == "__main__":
    main()
