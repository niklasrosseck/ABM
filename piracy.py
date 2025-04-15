from mesa import Agent, Model
from mesa.space import MultiGrid
import numpy as np
import random
import pygame
import os
import pickle

if not os.path.exists("q_tables"):
    os.makedirs("q_tables")


ACTIONS = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1), (0, 0)]
LEARNING_RATE = 0.1
DISCOUNT_FACTOR = 0.9
EPSILON = 0.3

class QLearningAgent(Agent):
    def __init__(self, model):
        super().__init__(model)
        self.q_table = {}

    def save_q_table(self, filename):
        with open(filename, 'wb') as f:
            pickle.dump(self.q_table, f)

    def load_q_table(self, filename):
        try:
            with open(filename, 'rb') as f:
                self.q_table = pickle.load(f)
        except FileNotFoundError:
            self.q_table = {} 

    def get_state(self):
        return self.pos

    def choose_action(self):
        if random.uniform(0, 1) < EPSILON:  
            return random.choice(ACTIONS)
        state = self.get_state()
        if state not in self.q_table:
            self.q_table[state] = [0] * len(ACTIONS)
        return ACTIONS[np.argmax(self.q_table[state])]

    def update_q_value(self, state, action, reward, next_state):
        if state not in self.q_table:
            self.q_table[state] = [0] * len(ACTIONS)
        if next_state not in self.q_table:
            self.q_table[next_state] = [0] * len(ACTIONS)
        action_index = ACTIONS.index(action)
        old_value = self.q_table[state][action_index]
        future_value = max(self.q_table[next_state])
        new_value = old_value + LEARNING_RATE * (reward + DISCOUNT_FACTOR * future_value - old_value)
        self.q_table[state][action_index] = new_value
    
    def perceive_environment(self):
        visibility_range = self.model.get_visibility_range()
        visible_agents = []

        for dx in range(-visibility_range, visibility_range + 1):
            for dy in range(-visibility_range, visibility_range + 1):
                if abs(dx) + abs(dy) > visibility_range:  
                    continue
                nx, ny = self.pos[0] + dx, self.pos[1] + dy

                if self.model.grid.out_of_bounds((nx, ny)):
                    continue

                cell_contents = self.model.grid.get_cell_list_contents([(nx, ny)])
                for obj in cell_contents:
                    if obj is not self:
                        visible_agents.append(obj)

        return visible_agents
    
class Ship(QLearningAgent):
    def __init__(self, model):
        super().__init__(model)
        self.has_cargo = False
        self.load_q_table(f'q_tables/ship_{self.unique_id}.pkl')
        
    def step(self):
        if self.has_cargo:
            print("I have cargo")
        else:
            print("I have nothing")

        visible = self.perceive_environment()
        state = self.get_state()
        action = self.choose_action()
        new_pos = (max(0, min(self.pos[0] + action[0], self.model.grid.width - 1)),
                   max(0, min(self.pos[1] + action[1], self.model.grid.height - 1)))

        reward = -1  # Default penalty for movement
        if self.model.grid.is_cell_empty(new_pos):
            self.model.grid.move_agent(self, new_pos)
            if new_pos == self.model.docks[0] and not self.has_cargo:
                self.has_cargo = True
                reward += 500  # Reward for picking up cargo
            elif new_pos == self.model.docks[1]:
                if self.has_cargo:
                    self.has_cargo = False
                    reward += 20  # Reward for successful delivery
                else:
                    reward -= 1000  # Penalty for arriving without cargo
            
            if self.has_cargo:
                reward += 2


        for agent in self.model.grid.get_cell_list_contents([new_pos]):
            if isinstance(agent, Pirate):
                reward -= 10  # Penalized for being attacked by pirate

        self.update_q_value(state, action, reward, self.get_state())
        self.save_q_table(f'q_tables/ship_{self.unique_id}.pkl')


class Pirate(QLearningAgent):
    def __init__(self, model):
        super().__init__(model)
        self.captured_steps = 0
        self.load_q_table(f'q_tables/pirate_{self.unique_id}.pkl')

    def step(self):
        if self.captured_steps > 0:
            self.captured_steps -= 1
            return 
         
        visible = self.perceive_environment()
        state = self.get_state()
        action = self.choose_action()
        new_pos = (max(0, min(self.pos[0] + action[0], self.model.grid.width - 1)),
                   max(0, min(self.pos[1] + action[1], self.model.grid.height - 1)))

        reward = -1  # Default penalty for movement
        if self.model.grid.is_cell_empty(new_pos):
            self.model.grid.move_agent(self, new_pos)

        for agent in self.model.grid.get_cell_list_contents([new_pos]):
            if isinstance(agent, Ship) and agent.has_cargo:
                reward += 10  # Reward for stealing cargo
                agent.has_cargo = False
            if isinstance(agent, Security):
                reward += 10  # Penalized for being caught
                self.captured_steps += 10
                self.model.grid.move_agent(self, (random.randint(0, self.model.grid.width-1), random.randint(0, self.model.grid.height-1)))

        self.update_q_value(state, action, reward, self.get_state())
        self.save_q_table(f'q_tables/pirate_{self.unique_id}.pkl')

class Security(QLearningAgent):
    def __init__(self, model):
        super().__init__(model)
        self.load_q_table(f'q_tables/security_{self.unique_id}.pkl')

    def step(self):
        visible = self.perceive_environment()
        state = self.get_state()
        action = self.choose_action()
        new_pos = (max(0, min(self.pos[0] + action[0], self.model.grid.width - 1)),
                   max(0, min(self.pos[1] + action[1], self.model.grid.height - 1)))

        reward = -1  # Default penalty for movement
        if self.model.grid.is_cell_empty(new_pos):
            self.model.grid.move_agent(self, new_pos)

        for agent in self.model.grid.get_cell_list_contents([new_pos]):
            if isinstance(agent, Pirate):
                reward += 10  # Reward for catching pirate

        self.update_q_value(state, action, reward, self.get_state())
        self.save_q_table(f'q_tables/security_{self.unique_id}.pkl')

class PortSecurityModel(Model):
    def __init__(self, width, height, num_ships, num_pirates, num_security):
        super().__init__()
        self.grid = MultiGrid(width, height, False)
        self.docks = [(0, 0), (width-1, height-1)]  
        self.ships = []
        self.pirates = []
        self.securities = []
        self.weather = "sunny"
        self.weather_states = ["sunny", "cloudy", "rainy", "stormy"]
        self.weather_counter = 0

        for _ in range(num_ships):
            ship = Ship(self)
            self.ships.append(ship)
            self.grid.place_agent(ship, (random.randint(0, width-1), random.randint(0, height-1)))

        for _ in range(num_pirates):
            pirate = Pirate(self)
            self.pirates.append(pirate)
            self.grid.place_agent(pirate, (random.randint(0, width-1), random.randint(0, height-1)))

        for _ in range(num_security):
            security = Security(self)
            self.securities.append(security)
            self.grid.place_agent(security, (random.randint(0, width-1), random.randint(0, height-1)))
    
    def update_weather(self):
        self.weather = random.choices(self.weather_states, weights=[0.4, 0.3, 0.2, 0.1], k=1)[0]
    
    def get_visibility_range(self):
        return {"sunny": 4,"cloudy": 3,"rainy": 2,"stormy": 1}[self.weather]

    def step(self):
        if self.weather_counter >= 5:
            self.update_weather()
            self.weather_counter = 0
        else:
            self.weather_counter += 1
        
        self.agents.shuffle_do("step")


def run_pygame(model):
    pygame.init()
    grid_size = 40  
    width = model.grid.width
    height = model.grid.height
    screen = pygame.display.set_mode((width * grid_size, height * grid_size))
    pygame.display.set_caption("Port Security Simulation")
    clock = pygame.time.Clock()

    # Images
    ship_image = pygame.image.load("Images/ship.png")
    ship_image = pygame.transform.scale(ship_image, (grid_size, grid_size))
    dock_image = pygame.image.load("Images/Dock.png")
    dock_image = pygame.transform.scale(dock_image, (grid_size, grid_size))

    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    BLUE = (0, 0, 255)

    running = True
    while running:
        screen.fill(WHITE)

        for dock in model.docks:
            screen.blit(dock_image, (dock[0] * grid_size, dock[1] * grid_size))

        for ship in model.ships:
            screen.blit(ship_image, (ship.pos[0] * grid_size, ship.pos[1] * grid_size))

        for pirate in model.pirates:
            pygame.draw.circle(screen, RED, (pirate.pos[0] * grid_size, pirate.pos[1] * grid_size), radius=10)

        for security in model.securities:
            pygame.draw.circle(screen, BLUE, (security.pos[0] * grid_size, security.pos[1] * grid_size), radius=10)
        
        pygame.display.update()
        clock.tick(10)  

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        model.step()

    pygame.quit()

model = PortSecurityModel(20, 20, 2, 2, 2)
run_pygame(model)