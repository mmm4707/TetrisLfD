"""
STATE = GAME STATE
OBSERVATION = OBSERVATION

NB! MARIUS, STATE != OBSERVATION
"""

# Marius
# TODO fikse rotering, evt velge en blokk som formen roterer rundt
# Felles
# TODO diskuter config, mtp gravity (realtime game til turnbased)

import pygame as pg
import pygame.font
import copy
import numpy as np
import sys

from pathlib import Path
mod_path = Path(__file__).parent

from enviorment.actions import Action
from enviorment.shapes import Shape
from enviorment.colors import Color

class Tetris():

    def __init__(self):
        
        self.config = {
            'hard_drop': 1, # Action.DOWN goes all the way down
            'gravity': 0    # Piece moves down after all moves
        }
        
        self.cell_size = 25
        self.game_margin_top = 40
        self.game_margin_left = 40
        self.info_margin_left = 450

        self.window_height = self.window_width = 600
        
        # Standard Tetris layout
        self.game_rows = 20
        self.game_columns = 10
        
        pg.init()
        pg.display.set_caption('TETRIS')

        self.screen = pg.display.set_mode((self.window_height, self.window_width))
        self.clock = pg.time.Clock()
        self.screen.fill(Color.BLACK)
        self.font = pg.font.Font(None, 36)

        self.start_position = [0, 3]
        self.position = copy.deepcopy(self.start_position)
        self.highscore = 0
        self.score = None
        self.attempt = 0
        
        self.background = pg.image.load(str(mod_path) + '/sprites/background.png')
        self.background = pg.transform.scale(self.background, (self.window_height, self.window_width))

    def reset(self):
        self.state = [[0 for _ in range(self.game_columns)] for _ in range(self.game_rows)]
        
        # Start position
        shape1, self.current_piece, self.current_rotation = self.new_shape()
        shape2, self.next_piece, self.next_rotation = self.new_shape()
            
        self.current_shape = self.get_blocks_from_shape(shape1, self.current_piece, self.start_position)
        self.next_shape = self.get_blocks_from_shape(shape2, self.next_piece, self.start_position)
        
        if self.score is not None:
            if self.score > self.highscore:
                self.highscore = self.score
        
        self.score = 0
        self.attempt += 1

        return self.state, 0, False, ''

    def get_blocks_from_shape(self, shape, piece, offset=[0, 0]):
        blocks = []

        for i, row in enumerate(shape):
            for j, cell in enumerate(row):
                if cell != '0':
                    blocks.append([j, i])

        # normalize
        lower_y = min([y for y, x in blocks])
        lower_x = min([x for y, x in blocks])
        
        if offset == self.start_position:
            offset = copy.deepcopy(self.start_position)
            offset[1] += 0 if piece == 0 else 1

        return [[y-lower_y+offset[0], x-lower_x+offset[1]] for y, x in blocks]

    def check_collision_down(self, shape):
        for y, x in shape:
            if (y + 1) >= self.game_rows or self.state[(y + 1)][x] != 0:
                return True
        return False

    def new_shape(self):
        piece = np.random.randint(len(Shape.ALL))
        rotation = 0
        shape = Shape.ALL[piece][rotation]
        return shape, piece, rotation
    
    def check_cleared_lines(self):
        reward = 0
        
        for i, row in enumerate(self.state):           
            if 0 not in row:
                del self.state[i] # magi elns, vet ikke. men det funker fjell
                self.state.insert(0, [0 for _ in range(self.game_columns)])
                reward += 1

        return reward
    
    def check_loss(self):
        return sum([self.state[y][x] for y, x in self.current_shape]) != 0
            
    def step(self, action):
        reward = 0
        done = False
        info = ''
        placed = False # if current piece lands on another or bottom

        next_position = copy.deepcopy(self.current_shape)

        if action == Action.DOWN:

            if self.config['hard_drop']:
                collision = self.check_collision_down(next_position)
                while not collision:
                    next_position = [[y+1, x] for y, x in next_position]
                    collision = self.check_collision_down(next_position)
                   
                placed = True

            else:
                if not self.check_collision_down(next_position):
                    next_position = [[y+1, x] for y, x in next_position]
                else:
                    placed = True

        elif action == Action.LEFT:
        
            for y, x in next_position:
                if (x - 1) < 0 or self.state[y][(x - 1)] != 0:
                    break
            else:
                next_position = [[y, x-1] for y, x in next_position]

        elif action == Action.RIGHT:
            
            for y, x in next_position:
                if (x + 1) >= self.game_columns or self.state[y][(x + 1)] != 0:
                    break
            else:
                next_position = [[y, x+1] for y, x in next_position]

        elif action == Action.ROTATE:
            current_posistion = next_position
            self.current_rotation = (self.current_rotation - 1) % len(Shape.ALL[self.current_piece])
            new_rotation = Shape.ALL[self.current_piece][self.current_rotation]
            next_position = self.get_blocks_from_shape(new_rotation, self.current_piece, self.current_shape[0])
            for y, x in next_position:
                if x >= self.game_columns or y >= self.game_rows or self.state[y][x] != 0:
                    next_position = current_posistion
                    break

        elif action == Action.WAIT:
            if not self.config['gravity']:
                if not self.check_collision_down(next_position):
                    next_position = [[y+1, x] for y, x in next_position]
                else:
                    placed = True
        
        if self.config['gravity']:
            # go down one tile after all moves
            if not self.check_collision_down(next_position):
                next_position = [[y+1, x] for y, x in next_position]
            else:
                placed = True

        if placed:
            for block in next_position:
                self.state[block[0]][block[1]] = self.current_piece + 1
                
            self.current_shape = self.next_shape
            self.current_piece = self.next_piece
            self.current_rotation = self.next_rotation
                
            shape, self.next_piece, self.next_rotation = self.new_shape()
            self.next_shape = self.get_blocks_from_shape(shape, self.next_piece, self.start_position)
            done = self.check_loss()
        else:
            self.current_shape = next_position
            
        reward += self.check_cleared_lines()
        self.score += reward

        # TODO format state + shape for DQN model
        return self.state, reward, done, info

    def render(self, manual=0):
        self.screen.fill((1, 26, 56))
        #self.screen.blit(self.background, (0, 0, self.window_height, self.window_width))
        
        # draw game window border
        rect = pg.Rect(self.game_margin_left - 1, 
                       self.game_margin_top  - 1,
                       self.game_columns * self.cell_size + 2, 
                       self.game_rows    * self.cell_size + 2)
        
        pg.draw.rect(self.screen, Color.WHITE, rect, 1)
        
        # draw cells
        for i, row in enumerate(self.state):
            for j, cell in enumerate(row):

                color = Color.BLACK if cell == 0 else Shape.COLORS[cell - 1]
                
                rect = pg.Rect(self.game_margin_left + j * self.cell_size, 
                               self.game_margin_top  + i * self.cell_size, 
                               self.cell_size, 
                               self.cell_size)

                pg.draw.rect(self.screen, color, rect, 0)
                
                if cell == 0:
                    pg.draw.rect(self.screen, (30, 30, 30), rect, 1)

        # draw drop preview
        temp_shape = copy.deepcopy(self.current_shape)
        collision = self.check_collision_down(temp_shape)
        while not collision:
            temp_shape = [[y+1, x] for y, x in temp_shape]
            collision = self.check_collision_down(temp_shape)
            
        for block in temp_shape:
            rect = pg.Rect(self.game_margin_left + block[1] * self.cell_size, 
                           self.game_margin_top  + block[0] * self.cell_size, 
                           self.cell_size, 
                           self.cell_size)
            
            color = list(Shape.COLORS[self.current_piece])
            color = tuple([c-200 if c > 200 else c-100 if c > 100 else 0 for c in color])
            
            pg.draw.rect(self.screen, color, rect, 0)

        # draw current shape
        for block in self.current_shape:

            rect = pg.Rect(self.game_margin_left + block[1] * self.cell_size, 
                           self.game_margin_top  + block[0] * self.cell_size, 
                           self.cell_size, 
                           self.cell_size)
            
            pg.draw.rect(self.screen, Shape.COLORS[self.current_piece], rect, 0)
            
        # draw info
        next_preview = [self.game_columns * self.cell_size + 80 + self.game_margin_left,
                        self.game_margin_top]
        
        rect = pg.Rect(next_preview[0], 
                       next_preview[1],
                       self.cell_size * 6, 
                       self.cell_size * 5)
        
        pg.draw.rect(self.screen, Color.BLACK, rect, 0)
        
        rect = pg.Rect(next_preview[0] - 1, 
                       next_preview[1] - 1,
                       self.cell_size * 6 + 2, 
                       self.cell_size * 5 + 2)
        
        pg.draw.rect(self.screen, Color.WHITE, rect, 1)
                
        for block in self.next_shape:
            center_y = 1 if self.next_piece == 0 else 0
            
            rect = pg.Rect(next_preview[0] + (block[1] - 2) * self.cell_size, 
                           next_preview[1] + (block[0] + 1 + center_y) * self.cell_size, 
                           self.cell_size, 
                           self.cell_size)
            
            pg.draw.rect(self.screen, Shape.COLORS[self.next_piece], rect, 0)
            
        score_text = self.font.render(("Score: "+ str(self.score)), 1, Color.WHITE)
        score_textRect = score_text.get_rect() 
        score_textRect.center = (self.info_margin_left, 200)
        
        highscore_text = self.font.render(("Highscore: "+ str(self.highscore)), 1, Color.WHITE)
        highscore_textRect = highscore_text.get_rect() 
        highscore_textRect.center = (self.info_margin_left, 240) 
        
        attempt_text = self.font.render(("Attempts: "+ str(self.attempt)), 1, Color.WHITE)
        attempt_textRect = attempt_text.get_rect() 
        attempt_textRect.center = (self.info_margin_left, 280) 
        
        self.screen.blit(score_text, score_textRect) 
        self.screen.blit(highscore_text, highscore_textRect)
        self.screen.blit(attempt_text, attempt_textRect)
        
        done = False
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
                
            if manual and event.type == pg.KEYDOWN:
                if event.key == pg.K_LEFT:
                    _, _, done, _ = self.step(Action.LEFT)
                if event.key == pg.K_RIGHT:
                    _, _, done, _ = self.step(Action.RIGHT)
                if event.key == pg.K_DOWN:
                    _, _, done, _ = self.step(Action.DOWN)
                if event.key == pg.K_UP:
                    _, _, done, _ = self.step(Action.ROTATE)  
                if event.key == pg.K_SPACE:
                    _, _, done, _ = self.step(Action.WAIT)             

        pg.display.update()
        return done