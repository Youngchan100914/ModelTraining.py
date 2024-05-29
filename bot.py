from time import time,sleep
from threading import Thread, Lock
from math import *
import pyautogui as py
import numpy as np
import random
from constants import Constants

class BotState:
    INITIALIZING = 0
    SEARCHING = 1
    MOVING = 2
    HIDING = 3
    ATTACKING = 4

class Brawlbot:
    tile_w = 24
    tile_h = 17
    midpoint_offset = Constants.midpoint_offset

    sharpCorner = Constants.sharpCorner
    centerOrder = Constants.centerOrder
    IGNORE_RADIUS = 0.5
    movement_screenshot = None
    screenshot = None
    INITIALIZING_SECONDS = 2
    results = []
    bushResult = []
    counter = 0
    direction = ["top","bottom","right","left"]
    current_bush = None
    last_player_pos = None
    last_closest_enemy = None
    border_size = 1
    stopped = True
    topleft = None
    avg_fps = 0
    enemy_move_key = None
    timeFactor = 1

    if sharpCorner: timeFactor = 1.05

    def __init__(self,windowSize,offsets,speed,attack_range) -> None:
        self.lock = Lock()

        self.speed = speed
        if attack_range >0 and attack_range <=4:
            range_multiplier = 1
            hide_multiplier = 1.3
        elif attack_range > 4 and attack_range <=7:
            range_multiplier = 0.85
            hide_multiplier = 1
        elif attack_range > 7:
            range_multiplier = 0.8
            hide_multiplier = 0.8

        self.alert_range = attack_range + 2
        self.attack_range = range_multiplier*attack_range
        self.gadget_range = 0.9*self.attack_range
        self.hide_attack_range = 3.5
        self.HIDINGTIME = hide_multiplier * 23
        
        self.timestamp = time()
        self.window_w = windowSize[0]
        self.window_h = windowSize[1]
        self.center_window = (self.window_w / 2, int((self.window_h / 2)+ self.midpoint_offset))

        self.tileSize = round((round(self.window_w/self.tile_w)+round(self.window_h/self.tile_h))/2)
        self.state = BotState.INITIALIZING

        self.offset_x = offsets[0]
        self.offset_y = offsets[1]

        self.player_index = 0
        self.bush_index = 1
        self.enemy_index = 2
        

    # translate a pixel position on a screenshot image to a pixel position on the screen.
    # pos = (x, y)
    # WARNING: if you move the window being captured after execution is started, this will
    # return incorrect coordinates, because the window position is only calculated in
    # the __init__ constructor.
    def get_screen_position(self, cordinate):
        return (cordinate[0] + self.offset_x, cordinate[1] + self.offset_y)

    def guess_storm_direction(self):
        x_direction = ""
        y_direction = ""
        if self.results:
            if self.results[self.player_index]:
                x_border = (self.window_w/self.tile_w)*self.border_size
                y_border = (self.window_h/self.tile_h)*self.border_size
                p0 = self.center_window
                p1 = self.results[self.player_index][0]
                xDiff , yDiff = tuple(np.subtract(p1, p0))
                if xDiff>x_border:
                    x_direction = self.direction[2]
                elif xDiff<-x_border:
                    x_direction = self.direction[3]
                if yDiff>y_border:
                    y_direction = self.direction[1]
                elif yDiff<-y_border:
                    y_direction = self.direction[0]
                return [x_direction,y_direction]
            else:
                return 2*[""]
        else:
            return 2*[""]
    
    def storm_movement_key(self):
        x = ""
        y = ""
        if self.results:
            if self.results[self.player_index]:
                direction = self.guess_storm_direction()
                if direction[0] == self.direction[2]:
                    x = "a"
                elif direction[0] == self.direction[3]:
                    x = "d"
                if direction[1] == self.direction[1]:
                    y = "w"
                elif direction[1] == self.direction[0]:
                    y = "s"
        if [x,y] == ["",""]:
            return []
        else:
            return [x,y]

    def get_quadrant_bush(self):
        length = 0
        direction = self.guess_storm_direction()
        for i in range(len(direction)):
            if len(direction[i]) > 0:
                length += 1
                index = i
        if length == 0:
            return False
        elif length == 1:
            single_direction = direction[index]
            # top
            if single_direction == self.direction[0]:
                return [[0,3],[2,3]]
            # bottom
            elif single_direction == self.direction[1]:
                return [[0,3],[0,1]]
            # right
            elif single_direction == self.direction[2]:
                return [[0,1],[0,3]]
            # left
            elif single_direction == self.direction[3]:
                return [[2,3],[0,3]]
        elif length == 2:
            # top right
            if direction == [self.direction[0],self.direction[2]]:
                return [[0,2],[1,3]]
            # top left
            elif direction == [self.direction[0],self.direction[3]]:
                return [[1,3],[1,3]]
            # bottom right
            elif direction == [self.direction[1],self.direction[2]]:
                return [[0,2],[0,2]]
            # bottom left
            elif direction == [self.direction[1],self.direction[3]]:
                return [[1,3],[0,2]]
        
    # bush method
    def ordered_bush_by_distance(self, index):
        if not(self.results[self.player_index]) or self.centerOrder:
            player_position = self.center_window
        else:
            player_position = self.results[self.player_index][0]
        def tile_distance(position):
            return sqrt(((position[0] - player_position[0])/(self.window_w/self.tile_w))**2 
                        + ((position[1] - player_position[1])/(self.window_h/self.tile_h))**2)
        # list of bush location is the in index 1 of results
        unfilteredResults = self.results[index]
        filteredResult = []
        # get quadrant
        quadrant = self.get_quadrant_bush()
        if quadrant:
            x_scale = self.window_w/3
            y_scale = self.window_h/3
            for x,y in unfilteredResults:
                # find bushes in the quadrant
                if ((x > quadrant[0][0]*x_scale and x <= quadrant[0][1]*x_scale)
                    and (y > quadrant[1][0]*y_scale and y <= quadrant[1][1]*y_scale)):
                    filteredResult.append((x,y))
            filteredResult.sort(key=tile_distance)
            if filteredResult:
                return filteredResult
        # if quadrant is False or filteredResult is empty
        if not(quadrant) or not(filteredResult):
            unfilteredResults.sort(key=tile_distance)
            return unfilteredResults
    
    def ordered_enemy_by_distance(self,index):
        # our character is always in the center of the screen
        # if player position in result is empty 
        # assume that player is in the middle of the screen
        if not(self.results[self.player_index]):
            player_position = self.center_window
        else:
            player_position = self.results[self.player_index][0]
        def tile_distance(position):
            return sqrt(((position[0] - player_position[0])/(self.window_w/self.tile_w))**2 
                        + ((position[1] - player_position[1])/(self.window_h/self.tile_h))**2)
        sortedResults = self.results[index]
        sortedResults.sort(key=tile_distance)
        return sortedResults
        
    def tile_distance(self,player_position,position):
        return sqrt(((position[0] - player_position[0])/(self.window_w/self.tile_w))**2 + ((position[1] - player_position[1])/(self.window_h/self.tile_h))**2)
    
    def find_bush(self):
        if self.results:
            self.bushResult = self.ordered_bush_by_distance(self.bush_index)
        if self.bushResult:
            return True
        else:
            return False
        

    def move_to_bush(self):
        if self.bushResult:
            # if len(self.bushResult) > 1:
            #     index = 1
            # else:
            #     index = 0
            x,y = self.bushResult[0]
            if not(self.results[self.player_index]):
                player_pos = self.center_window
            else:
                player_pos = self.results[self.player_index][0]
            tileDistance = self.tile_distance(player_pos,(x,y))
            x,y = self.get_screen_position((x,y))
            py.mouseDown(button=Constants.movement_key,x=x, y=y)
            moveTime = tileDistance/self.speed
            moveTime = moveTime * self.timeFactor
            print(f"Distance: {round(tileDistance,2)} tiles")
            return moveTime
    
    # enemy and attack method
    def attack(self):
        print("attacking enemy")
        attack_key = "e"
        py.press(attack_key)

    def gadget(self):
        print("activate gadget")
        gadget_key = "f"
        py.press(gadget_key)

    def hold_movement_key(self,key,time):
        with py.hold(key):
            sleep(time)

    def storm_random_movement(self):
        if self.storm_movement_key():
            move_keys = self.storm_movement_key()
        else:
            move_keys = ["w", "a", "s", "d"]
        random_move = random.choice(move_keys)
        hold_time = 1
        self.hold_movement_key(random_move,hold_time)
    
    def stuck_random_movement(self):
        move_keys = self.get_movement_key(self.bush_index)
        if not(move_keys):
            move_keys = ["w", "a", "s", "d"]
            move_keys = random.choice(move_keys)
        with py.hold(move_keys):
            sleep(1)

    def get_movement_key(self,index):
        # asign x and y direction
        x_key = ""
        y_key = ""
        if self.results:
            if self.results[self.player_index]:
                player_pos = self.results[self.player_index][0]
            # if player position in result is empty
            # assume that player is in the middle of the screen
            else:
                player_pos = self.center_window
            if self.results[index]:
                # enemy index
                if index == self.enemy_index:
                    p0 = self.enemyResults[0]
                elif index == self.bush_index:
                    p0 = self.bushResult[0]
                p1 = player_pos
                xDiff , yDiff = tuple(np.subtract(p1, p0))
                # right
                if xDiff>0:
                    x_key = "d"
                # left
                elif xDiff<0:
                    x_key = "a"
                # bottom
                if yDiff>0:
                    y_key = "s"
                # top
                elif yDiff<0:
                    y_key = "w"
                return [x_key,y_key]
        return []
    
    def enemy_random_movement(self):
        if not(self.enemy_move_key):
            move_keys = self.get_movement_key(self.enemy_index)
            if not(move_keys):
                move_keys = ["w", "a", "s", "d"]
                move_keys = random.choice(move_keys)
        else:
            move_keys = self.enemy_move_key
        with py.hold(move_keys):
            py.press("e",presses=2,interval=0.4)

    def enemy_distance(self):
        if self.results:
            # player coordinate
            if self.results[self.player_index]:
                player_pos = self.results[self.player_index][0]
            else:
                player_pos = self.center_window
            if self.results[self.enemy_index]:
                self.enemyResults = self.ordered_enemy_by_distance(self.enemy_index)
                if self.enemyResults:
                    enemyDistance = self.tile_distance(player_pos,self.enemyResults[0])
                    return enemyDistance
        return None
    
    def is_enemy_in_range(self):
        enemyDistance = self.enemy_distance()
        py.click()
        py.click()
        if enemyDistance:
            # ranges in tiles
            if (enemyDistance > self.attack_range
                and enemyDistance <= self.alert_range):
                self.enemy_move_key = self.get_movement_key(self.enemy_index)
            elif (enemyDistance > self.gadget_range 
                  and enemyDistance <= self.attack_range):
                self.attack()
                return True
            elif enemyDistance <= self.gadget_range:
                self.gadget()
                self.attack()
                return True
        return False

    def is_enemy_close(self):
        py.click()
        py.click()
        enemyDistance = self.enemy_distance()
        if enemyDistance:
            if enemyDistance <= self.hide_attack_range:
                self.gadget()
                self.attack()
                return True
        return False

    def is_player_damaged(self):
        for i in range(4):
            py.press('w')
        for i in range(4):
            py.press('a')
        for i in range(4):
            py.press('d')
            py.press('s')
        if self.topleft:
            width = abs(self.topleft[0] - self.bottomright[0])
            height = abs(self.topleft[1] - self.bottomright[1])
            w1 = int(self.topleft[0] + width/3)
            w2 = int(self.topleft[0] + 2*(width/3))
            h = int(self.topleft[1] - height/2)
            try:
                if (py.pixelMatchesColor(w1,h,(204, 34, 34),tolerance=20)
                    or py.pixelMatchesColor(w2,h,(204, 34, 34),tolerance=20)):
                    print(f"player is damaged")
                    return True
            except OSError:
                pass
        return False
    
    def have_stopped_moving(self):
        if self.results:
            if self.results[self.player_index]:
                player_pos = self.results[self.player_index][0]
                if self.last_player_pos is None:
                    self.last_player_pos = player_pos
                else:
                    # last player position is the same as the current
                    if self.last_player_pos == player_pos:
                        self.counter += 1
                        if self.counter == 2:
                            print("have stopped moving or stuck")
                            return True
                    else:
                        # reset counter
                        self.counter = 0
                    self.last_player_pos = player_pos
        return False

    def update_results(self,results):
        self.lock.acquire()
        self.results = results
        self.lock.release()
    
    def update_player(self,topleft,bottomright):
        self.lock.acquire()
        self.topleft = topleft
        self.bottomright =bottomright
        self.lock.release()

    def update_screenshot(self, screenshot):
        self.lock.acquire()
        self.screenshot = screenshot
        self.lock.release()

    def start(self):
        self.stopped = False
        self.loop_time = time()
        self.count = 0
        t = Thread(target=self.run)
        t.setDaemon(True)
        t.start()

    def stop(self):
        self.stopped = True
        # reset last player position
        self.last_player_pos = None

    def run(self):
        while not self.stopped:
            sleep(0.01)
            if self.state == BotState.INITIALIZING:
                # do no bot actions until the startup waiting period is complete
                if time() > self.timestamp + self.INITIALIZING_SECONDS:
                    # start searching when the waiting period is over
                    self.lock.acquire()
                    self.state = BotState.SEARCHING
                    self.lock.release()

            elif self.state == BotState.SEARCHING:
                success = self.find_bush()
                #if bush is detected
                if success:
                    print("found bush")
                    self.moveTime = self.move_to_bush()
                    self.lock.acquire()
                    self.timestamp = time()
                    self.state = BotState.MOVING
                    self.lock.release()
                #bush is not detected
                else:
                    print("Cannot find bush")
                    self.storm_random_movement()
                    # self.counter+=1
                
                if self.is_enemy_in_range():
                        self.lock.acquire()
                        self.state = BotState.ATTACKING
                        self.lock.release()

            elif self.state == BotState.MOVING:
                # when player is moving check if player is stuck
                if self.have_stopped_moving():
                    # cancel moving
                    py.mouseUp(button = Constants.movement_key)
                    self.stuck_random_movement()
                    # and search for bush again
                    self.lock.acquire()
                    self.state = BotState.SEARCHING
                    self.lock.release()
                #if player is stuck
                else:
                    sleep(0.15)

                if self.is_enemy_in_range():
                    self.lock.acquire()
                    self.state = BotState.ATTACKING
                    self.lock.release()
                # player successfully travel to the selected bush
                if time() > self.timestamp + self.moveTime:
                    py.mouseUp(button = Constants.movement_key)
                    print("Hiding")
                    self.lock.acquire()
                    # change state to hiding
                    self.timestamp = time()
                    self.state = BotState.HIDING
                    self.lock.release()
                    
            elif self.state == BotState.HIDING:
                if time() > self.timestamp + self.HIDINGTIME or self.is_player_damaged():
                    print("Changing state to search")
                    self.lock.acquire()
                    self.state = BotState.SEARCHING
                    self.lock.release()

                if self.centerOrder:
                    if self.is_enemy_close():
                        print("Enemy is nearby")
                        self.lock.acquire()
                        self.state = BotState.ATTACKING
                        self.lock.release()
                else:
                    if self.is_enemy_in_range():
                        print("Enemy in range")
                        self.lock.acquire()
                        self.state = BotState.ATTACKING
                        self.lock.release()
            elif self.state == BotState.ATTACKING:
                if self.is_enemy_in_range():
                    self.enemy_random_movement()
                else:
                    self.lock.acquire()
                    self.state = BotState.SEARCHING
                    self.lock.release()
                    
            self.fps = (1 / (time() - self.loop_time))
            self.loop_time = time()
            self.count += 1
            if self.count == 1:
                self.avg_fps = self.fps
            else:
                self.avg_fps = (self.avg_fps*self.count+self.fps)/(self.count + 1)