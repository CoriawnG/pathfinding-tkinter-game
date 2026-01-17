import random
import tkinter as tk
from collections import deque

# -----------------------------
# Constants
# -----------------------------
CELL_SIZE = 40
BASE_WIDTH = 10
BASE_HEIGHT = 8
ANIMATION_STEPS = 10  # smooth movement steps

# Tile types
WALL = "#"
PATH = "."
START = "S"
END = "E"
COIN = "C"

# Difficulty settings
DIFFICULTY_SETTINGS = {
    "Easy": {"wall_prob": 0.2, "enemies": 2, "time": 60, "coins": 5},
    "Medium": {"wall_prob": 0.3, "enemies": 3, "time": 45, "coins": 7},
    "Hard": {"wall_prob": 0.4, "enemies": 4, "time": 30, "coins": 10},
}

# -----------------------------
# Map generation
# -----------------------------
def generate_map(width, height, wall_prob, enemy_count, coin_count):
    game_map = [[PATH for _ in range(width)] for _ in range(height)]

    # Guaranteed path from start to end
    x, y = 0, 0
    path_cells = [(y, x)]
    while x < width - 1 or y < height - 1:
        if x < width - 1 and y < height - 1:
            x += 1 if random.random() < 0.5 else 0
            y += 1 if x == path_cells[-1][1] else 1
        elif x < width - 1: x += 1
        elif y < height - 1: y += 1
        path_cells.append((y, x))

    # Walls
    for i in range(height):
        for j in range(width):
            if (i, j) not in path_cells and random.random() < wall_prob:
                game_map[i][j] = WALL

    # Start and end
    game_map[0][0] = START
    game_map[height-1][width-1] = END

    # Coins
    placed = 0
    while placed < coin_count:
        cx, cy = random.randint(0,width-1), random.randint(0,height-1)
        if game_map[cy][cx]==PATH and (cy,cx) not in path_cells:
            game_map[cy][cx] = COIN
            placed +=1

    return game_map, path_cells

# -----------------------------
# BFS Pathfinding
# -----------------------------
def bfs_path(game_map, start, goal):
    width = len(game_map[0])
    height = len(game_map)
    queue = deque([start])
    visited = {tuple(start): None}
    while queue:
        current = queue.popleft()
        if current == goal: break
        x, y = current
        for dx, dy in [[0,1],[1,0],[0,-1],[-1,0]]:
            nx, ny = x+dx, y+dy
            if 0<=nx<width and 0<=ny<height and game_map[ny][nx] != WALL and (nx,ny) not in visited:
                queue.append([nx,ny])
                visited[(nx,ny)] = (x,y)
    path=[]
    node=tuple(goal)
    while node != tuple(start):
        if node not in visited: return []
        path.append(list(node))
        node = visited[node]
    path.reverse()
    return path

# -----------------------------
# Game class
# -----------------------------
class Game:
    def __init__(self, root, difficulty):
        self.root = root
        self.difficulty = difficulty
        self.width = BASE_WIDTH
        self.height = BASE_HEIGHT
        self.wall_prob = DIFFICULTY_SETTINGS[difficulty]["wall_prob"]
        self.enemy_count = DIFFICULTY_SETTINGS[difficulty]["enemies"]
        self.coin_count = DIFFICULTY_SETTINGS[difficulty]["coins"]
        self.time_left = DIFFICULTY_SETTINGS[difficulty]["time"]
        self.score = 0
        self.high_score = 0
        self.game_over = False
        self.paused = False
        self.enemies = []
        self.player_pos = [0,0]
        self.enemy_objects = []
        self.timer_id = None
        self.pause_button = None
        self.reset_game()

        # Bind keys
        root.bind("<Up>", lambda e: self.move_player(0,-1))
        root.bind("<Down>", lambda e: self.move_player(0,1))
        root.bind("<Left>", lambda e: self.move_player(-1,0))
        root.bind("<Right>", lambda e: self.move_player(1,0))
        root.bind("r", lambda e: self.restart())

    # -----------------------------
    # Reset / start game
    # -----------------------------
    def reset_game(self):
        self.game_over = False
        self.paused = False
        self.map, self.path_cells = generate_map(self.width,self.height,self.wall_prob,self.enemy_count,self.coin_count)
        self.player_pos = [0,0]
        self.canvas = tk.Canvas(self.root,width=self.width*CELL_SIZE,height=self.height*CELL_SIZE+50)
        self.canvas.pack()
        self.create_pause_button()
        self.time_left = DIFFICULTY_SETTINGS[self.difficulty]["time"]
        self.create_enemies()
        self.draw_map()
        self.start_timer()
        self.animate_enemies()

    # -----------------------------
    # Draw map
    # -----------------------------
    def draw_map(self):
        self.canvas.delete("all")
        for y in range(self.height):
            for x in range(self.width):
                cell = self.map[y][x]
                color = "white"
                if cell == WALL: color = "black"
                elif cell == START: color = "green"
                elif cell == END: color = "red"
                elif cell == COIN: color = "yellow"
                self.canvas.create_rectangle(
                    x*CELL_SIZE, y*CELL_SIZE,
                    (x+1)*CELL_SIZE, (y+1)*CELL_SIZE,
                    fill=color, outline="gray"
                )

        # Draw enemies
        for enemy in self.enemy_objects:
            x, y = enemy["pos"]
            self.canvas.create_rectangle(
                x, y,
                x+CELL_SIZE, y+CELL_SIZE,
                fill="orange", outline="gray"
            )

        # Draw player
        px, py = self.player_pos
        self.canvas.create_rectangle(
            px*CELL_SIZE, py*CELL_SIZE,
            (px+1)*CELL_SIZE, (py+1)*CELL_SIZE,
            fill="blue", outline="gray"
        )

        # Timer & score
        self.canvas.create_text(10,self.height*CELL_SIZE+15,anchor="w",
            text=f"Time: {self.time_left}s", font=("Helvetica",14), fill="black")
        self.canvas.create_text(10,self.height*CELL_SIZE+35,anchor="w",
            text=f"Score: {self.score}  High Score: {self.high_score}", font=("Helvetica",14), fill="black")

        if self.game_over:
            self.canvas.create_text(self.width*CELL_SIZE//2,self.height*CELL_SIZE//2,
                                    text="💀 GAME OVER 💀", font=("Helvetica",24), fill="red")
            self.canvas.create_text(self.width*CELL_SIZE//2,self.height*CELL_SIZE//2+30,
                                    text="Press 'R' to Retry", font=("Helvetica",16), fill="black")

    # -----------------------------
    # Player movement
    # -----------------------------
    def move_player(self, dx, dy):
        if self.game_over or self.paused: return
        new_x = self.player_pos[0]+dx
        new_y = self.player_pos[1]+dy
        if 0<=new_x<self.width and 0<=new_y<self.height and self.map[new_y][new_x] != WALL:
            self.player_pos = [new_x, new_y]

        # Collect coins
        if self.map[new_y][new_x] == COIN:
            self.score += 10
            self.map[new_y][new_x] = PATH
            self.animate_coin_collect(new_x, new_y)
            if self.score > self.high_score: self.high_score = self.score

        # Check collision with enemies
        for enemy in self.enemy_objects:
            ex, ey = int(enemy["pos"][0]//CELL_SIZE), int(enemy["pos"][1]//CELL_SIZE)
            if [ex, ey] == self.player_pos:
                self.flash_player()
                self.game_over = True
                self.root.after(300, self.draw_map)
                return

        # Check end
        if self.map[new_y][new_x] == END:
            self.score += 20
            self.width += 2
            self.height += 1
            self.canvas.destroy()
            self.reset_game()
            return

        self.draw_map()

    # -----------------------------
    # Coin collection animation
    # -----------------------------
    def animate_coin_collect(self, x, y):
        rect = self.canvas.create_oval(
            x*CELL_SIZE+10, y*CELL_SIZE+10,
            (x+1)*CELL_SIZE-10, (y+1)*CELL_SIZE-10,
            fill="gold", outline=""
        )
        self.root.after(200, lambda: self.canvas.delete(rect))

    # -----------------------------
    # Player flash on enemy hit
    # -----------------------------
    def flash_player(self):
        px, py = self.player_pos
        rect = self.canvas.create_rectangle(
            px*CELL_SIZE, py*CELL_SIZE,
            (px+1)*CELL_SIZE, (py+1)*CELL_SIZE,
            fill="red", outline="gray"
        )
        self.root.after(200, lambda: self.canvas.delete(rect))

    # -----------------------------
    # Pause button
    # -----------------------------
    def create_pause_button(self):
        if self.pause_button and self.pause_button.winfo_exists():
            self.pause_button.destroy()
        self.pause_button = tk.Button(self.root, text="Pause", command=self.toggle_pause)
        self.pause_button.pack()

    def toggle_pause(self):
        self.paused = not self.paused
        self.pause_button.config(text="Resume" if self.paused else "Pause")
        if not self.paused:
            self.animate_enemies()
            self.start_timer()

    # -----------------------------
    # Create enemy objects
    # -----------------------------
    def create_enemies(self):
        self.enemy_objects = []
        for _ in range(self.enemy_count):
            while True:
                ex, ey = random.randint(0,self.width-1), random.randint(0,self.height-1)
                if self.map[ey][ex] == PATH and [ex,ey] != self.player_pos:
                    break
            speed = random.randint(300,1000)
            self.enemy_objects.append({"pos":[ex*CELL_SIZE, ey*CELL_SIZE], "grid":[ex,ey], "speed":speed, "step":0})

    # -----------------------------
    # Animate enemies
    # -----------------------------
    def animate_enemies(self):
        if self.game_over or self.paused: return
        for enemy in self.enemy_objects:
            if enemy["step"] == 0:
                path = bfs_path(self.map, enemy["grid"], self.player_pos)
                if path: enemy["target"] = path[0]
                else: enemy["target"] = enemy["grid"]
                enemy["dx"] = (enemy["target"][0]-enemy["grid"][0])*CELL_SIZE/ANIMATION_STEPS
                enemy["dy"] = (enemy["target"][1]-enemy["grid"][1])*CELL_SIZE/ANIMATION_STEPS
                enemy["step"] = ANIMATION_STEPS

            enemy["pos"][0] += enemy["dx"]
            enemy["pos"][1] += enemy["dy"]
            enemy["step"] -= 1
            if enemy["step"] == 0:
                enemy["grid"] = enemy["target"]

            ex, ey = int(enemy["pos"][0]//CELL_SIZE), int(enemy["pos"][1]//CELL_SIZE)
            if [ex, ey] == self.player_pos:
                self.flash_player()
                self.game_over = True
                self.root.after(300, self.draw_map)
                return

        self.draw_map()
        self.root.after(50, self.animate_enemies)

    # -----------------------------
    # Timer
    # -----------------------------
    def start_timer(self):
        if self.game_over or self.paused: return
        if self.time_left>0:
            self.time_left -=1
            self.draw_map()
            self.timer_id = self.root.after(1000, self.start_timer)
        else:
            self.game_over = True
            self.draw_map()

    # -----------------------------
    # Restart game
    # -----------------------------
    def restart(self):
        if self.game_over:
            self.canvas.destroy()
            self.reset_game()

# -----------------------------
# Difficulty selection
# -----------------------------
def main():
    root = tk.Tk()
    root.title("Smooth Pathfinding Game")
    tk.Label(root,text="Select Difficulty:", font=("Helvetica",16)).pack(pady=10)
    def start_game(diff):
        for w in root.winfo_children(): w.destroy()
        Game(root,diff)
    for diff in DIFFICULTY_SETTINGS.keys():
        tk.Button(root,text=diff,font=("Helvetica",14), width=10, command=lambda d=diff:start_game(d)).pack(pady=5)
    root.mainloop()

if __name__=="__main__":
    main()
