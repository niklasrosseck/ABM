from mesa import Agent, Model
from mesa.space import MultiGrid
import random
import pygame

class Ship(Agent):
    def __init__(self, model, finish_pos, suspicious):
        super().__init__(model)
        self.suspicious = suspicious
        self.docked = False
        self.inspected = False
        self.time_in_dock = 0
        self.time_inspected = 0
        self.finish_pos = finish_pos

    def step(self):
        if not self.docked:
            if self.suspicious:
                self.move_to_security()
                if self.inspected:
                    if self.time_inspected < 20:
                        self.time_inspected += 1
                    else:
                        self.suspicious = False
                        self.move_to_dock()
            else:
                self.move_to_dock()
        else:
            if self.time_in_dock < 10:
                self.time_in_dock += 1
            else:
                self.move_to_finish()
    
    def move_to_dock(self):
        if self.pos in self.model.docks:
            self.docked = True
            print("Ship has docked.")
            return
        
        possible_steps = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False
        )
        
        possible_steps = [step for step in possible_steps
                          if step not in self.model.barrier_positions and self.model.grid.is_cell_empty(step)]
        
        free_docks = [dock for dock in self.model.docks if self.model.grid.is_cell_empty(dock)]

        if not possible_steps:
            print("No valid moves available. Staying in place.")
            return

        if self.pos[1] > 10:
            # Ships outside the barrier move towards entry point
            target_position = min(
                possible_steps,
                key=lambda step: min( 
                    abs(step[0] - entry_point[0]) + abs(step[1] - entry_point[1]) for entry_point in self.model.entry_points
            )
            )
        else:
            # Ships inside the barrier move towards the docks or wait if no dock is free
            if free_docks:
                closest_dock = min(free_docks, key=lambda dock: abs(self.pos[0] - dock[0]) + abs(self.pos[1] - dock[1]))
                target_position = min(
                    possible_steps,
                    key=lambda step: abs(step[0] - closest_dock[0]) + abs(step[1] - closest_dock[1]))
            else:
                print("Waiting near the dock. All docks are occupied.")
                return

        self.model.grid.move_agent(self, target_position)
        print(f"I am Ship {self.unique_id!s}.My position is {target_position}")
    
    def move_to_finish(self):
        if self.pos == self.finish_pos:
            print(f"Ship {self.unique_id!s} is finished")
            return  

        possible_steps = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        possible_steps = [step for step in possible_steps
                          if step not in self.model.barrier_positions and self.model.grid.is_cell_empty(step)]

        if not possible_steps:
            return
        
        if self.pos[1] < 10:
            # Ships inside the barrier move towards entry point
            target_position = min(
                possible_steps,
                key=lambda step: min( 
                    abs(step[0] - entry_point[0]) + abs(step[1] - entry_point[1]) for entry_point in self.model.entry_points
            )
            )
        else:
            target_position = min(possible_steps, key=lambda step: abs(step[0] - self.finish_pos[0]) + abs(step[1] - self.finish_pos[1]))

        self.model.grid.move_agent(self, target_position)
    
    def move_to_security(self):
        if self.pos in self.model.securities:
            self.inspected = True
            print("Inspection ongoing.")
            return
        
        free_security = [security for security in self.model.securities if self.model.grid.is_cell_empty(security)]
        
        possible_steps = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)

        possible_steps = [step for step in possible_steps
                          if step not in self.model.barrier_positions and self.model.grid.is_cell_empty(step)]

        if not possible_steps:
            print("No valid moves available. Staying in place.")
            return

        if self.pos[1] > 10:
            # Ships outside the barrier move towars entry
            target_position = min(
                possible_steps,
                key=lambda step: min( 
                    abs(step[0] - entry_point[0]) + abs(step[1] - entry_point[1]) for entry_point in self.model.entry_points
            )
            )
        else:
            # Inside the barrier ships move to the security or wait
            if free_security:
                closest_sec = min(free_security, key=lambda security: abs(self.pos[0] - security[0]) + abs(self.pos[1] - security[1]))
                target_position = min(
                    possible_steps,
                    key=lambda step: abs(step[0] - closest_sec[0]) + abs(step[1] - closest_sec[1]))
            else:
                print("Waiting near the security. All securities are occupied.")
                return


        self.model.grid.move_agent(self, target_position)
        print(f"I am Ship {self.unique_id!s}.My position is {target_position}")
        


class PortSecurityModel(Model):
    def __init__(self, width, height, n, security):
        super().__init__()  
        self.grid = MultiGrid(width, height, torus=False)
        self.docks = [(width // 3, 0), (width // 2, 0), (2 * width // 3, 0)]
        self.securities = [(0,5),(width-1,5)]
        self.entry_points = [(9,10),(10,10),(11,10)]
        self.barrier_positions = [(x, 10) for x in range(width) if x not in (9, 10, 11)]
        self.finish_positions = []

        last_row_positions = [(x, height - 1) for x in range(width)]
        spawn_positions = random.sample(last_row_positions, n)

        finish_positions = [(x, y) for x in range(width) for y in range(11,height)
                            if (x, y) not in self.docks and (x, y) not in self.barrier_positions]

        self.ships = []
        for i in range(n):
            if not finish_positions:
                print("Warning: Not enough unique finish positions for all ships!")
                break
    
            finish_pos = random.choice(finish_positions)
            finish_positions.remove(finish_pos)
            security_factor = random.random()
            suspicious = False
            if security_factor < security:
                suspicious = True
            ship = Ship(self,finish_pos,suspicious)  
            self.ships.append(ship)
            self.grid.place_agent(ship, spawn_positions[i])

    def step(self):
        self.agents.do("step")

#starter_model = PortSecurityModel(20,20, 2)
#for _ in range(20):
#   starter_model.step()

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
    security_image = pygame.image.load("Images/security.png")
    security_image = pygame.transform.scale(security_image, (grid_size, grid_size))
    dock_image = pygame.image.load("Images/Dock.png")
    dock_image = pygame.transform.scale(dock_image, (grid_size, grid_size))

    WHITE = (255, 255, 255)
    GRAY = (200, 200, 200)

    running = True
    while running:
        screen.fill(WHITE)

        for dock in model.docks:
            screen.blit(dock_image, (dock[0] * grid_size, dock[1] * grid_size))

        for barrier in model.barrier_positions:
            pygame.draw.rect(screen, GRAY, (barrier[0] * grid_size, barrier[1] * grid_size, grid_size, grid_size))

        for security in model.securities:
            screen.blit(security_image, (security[0] * grid_size, security[1] * grid_size))

        for ship in model.ships:
            screen.blit(ship_image, (ship.pos[0] * grid_size, ship.pos[1] * grid_size))
        
        pygame.display.update()
        clock.tick(10)  

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        model.step()

    pygame.quit()

model = PortSecurityModel(20, 20, 10, 0.5)
run_pygame(model)