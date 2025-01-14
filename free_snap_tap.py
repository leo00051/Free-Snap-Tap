from pynput import keyboard, mouse
from threading import Thread, Lock # to play aliases without interfering with keyboard listener
from os import system, startfile # to use clearing of CLI for better menu usage and opening config file
import sys # to get start arguments
import msvcrt # to flush input stream
from random import randint # randint(3, 9)) 
from time import time, sleep # sleep(0.005) = 5 ms
import pygetwindow as gw # to get name of actual window for focusapp function

from vk_codes import vk_codes_dict  #change the keys you need here in vk_codes_dict.py
from tap_keyboard import Key_Event, Key_Group, Key, Tap_Group

# global variables
DEBUG = False
DEBUG2 = False
PAUSED = False
MANUAL_PAUSED = False
STOPPED = False
MENU_ENABLED = True
CONTROLS_ENABLED = True
PRINT_VK_CODES = False

EXEC_ONLY_ONE_TRIGGERED_MACRO = False

# for focus setting
FOCUS_APP_NAME = None
FOCUS_THREAD_PAUSED = True
paused_lock = Lock()

# AntiCheat testing (ACT)
ACT_DELAY = True
ACT_MIN_DELAY_IN_MS = 2
ACT_MAX_DELAY_IN_MS = 10
ACT_CROSSOVER = False # will also force delay
ACT_CROSSOVER_PROPABILITY_IN_PERCENT = 50

# Alias delay between presses and releases
ALIAS_MIN_DELAY_IN_MS = ACT_MIN_DELAY_IN_MS 
ALIAS_MAX_DELAY_IN_MS = ACT_MAX_DELAY_IN_MS

# Define File name for saving of everything, can be any filetype
# But .txt or .cfg recommended for easier editing
FILE_NAME_ALL = 'FSTconfig.txt'

# Constants for key events
WM_KEYDOWN = [256,260] # _PRESS_MESSAGES = (_WM_KEYDOWN, _WM_SYSKEYDOWN)
WM_KEYUP = [257,261] # _RELEASE_MESSAGES = (_WM_KEYUP, _WM_SYSKEYUP)

# Control key combinations
EXIT_Combination = [35, 164]#35  # END key vkcode 35, ALT 164
TOGGLE_ON_OFF_Combination = [46, 164]  # DELETE key vkcode 46
MENU_Combination = [34, 164] # PAGE_DOWN

# Tap groups define which keys are mutually exclusive
# Key Groups define which key1 will be replaced by key2
# if a Key Group has more than 2 keys if will be handled als alias
tap_groups = []    # [Tap_Groups]
rebinds = {}       # Key_Event : Key_Event
rebind_triggers = []
macros = {}        # [Key_Group : Key_Group]  # triggers are the Keys to the Item Makro
macro_triggers = [] 

# hr = human readable form - saves the lines cleaned of comments and presorted
# these will be shown in menu, because internally they look a bit different (esp rebinds)
tap_groups_hr = [] 
rebinds_hr = [] 
macros_hr = []

# logging
alias_thread_logging = []

# collect all active keys here for recognition of key combinations
pressed_keys = set()
released_keys = set()

# toggle state tracker
toggle_state = {}
alias_toggle_lock = Lock()

# time_real = [time_real_last_pressed, time_real_last_released, time_real_released, time_real_pressed]
time_real = [{}, {}, {}, {}]
# time_simulated = [time_simulated_last_pressed, time_simulated_last_released, time_simulated_released, time_simulated_pressed]
time_simulated = [{}, {}, {}, {}]
# time_all = [time_all_last_pressed, time_all_last_released, time_all_released, time_all_pressed]
time_all = [{}, {}, {}, {}]

# Initialize the Controller
controller = keyboard.Controller()
mouse_controller = mouse.Controller()

controller_dict = {True: mouse_controller, False: controller}

mouse_vk_codes_dict = {1: mouse.Button.left, 
                       2: mouse.Button.right, 
                       4: mouse.Button.middle}
mouse_vk_codes = mouse_vk_codes_dict.keys()

# save point to recognise repeating real key input and stop evaluating it
last_real_ke = Key_Event(0,True)
# last_virtual_ke = Key_Event(0,True)


def add_key_press_state(vk_code):    
    pressed_keys.add(vk_code)    
    
def add_key_release_state(vk_code):
    released_keys.add(vk_code)
    try:
        pressed_keys.remove(vk_code)
    except KeyError as error:
        if DEBUG:
            print(f"release error: {error}")
    
def manage_key_states_by_event(key_event):
    vk_code, is_keydown, _ = key_event.get_all() 
    if is_keydown:
        add_key_press_state(vk_code)
    else:
        add_key_release_state(vk_code)

def remove_key_release_state(vk_code):
    try:
        released_keys.remove(vk_code)
    except KeyError as error:
        if DEBUG:
            print(f"release state error: {error}")

# file handling and hr display of groups
def load_groups(file_name):
    '''
    reads in the file and removes the commented out lines, keys and inline comments
    saves cleaned lines according to formatting in different containers;
    saved in vraibale_hr (human readable)
    '''
    global tap_groups_hr, rebinds_hr, macros_hr
    
    tap_groups_hr = []
    rebinds_hr = []
    macros_hr = []
    
    with open(file_name, 'r') as file:
        for line in file:
            if len(line) > 1:
                # strip all comments from line
                group = line.strip().replace(" ","").split(',')
                # ignore line if first char is a #
                if group[0][0] == '#':
                    pass
                else:
                    # remove commented out keys
                    cleaned_group = []
                    for key in group:
                        # ignore commented out keys
                        if key[0] != '#': 
                            # ignore comments after keys
                            cleaned_group.append(key.split('#')[0]) 
                        # if commented out key before :, add :
                        elif key.find(':') >= 0:
                            cleaned_group.append(':')
                            
                    cleaned_line = ','.join(cleaned_group)
                    
                    groups = cleaned_line.split(':')
                    
                    #sort cleaned groups into categories
                    # tap groups
                    if len(groups) == 1: 
                        tap_groups_hr.append(groups[0].split(','))
                    # rebinds and macros
                    elif len(groups) == 2:
                        trigger_group = groups[0].split(',')
                        key_group = groups[1].split(',')
                        # rebind
                        # if len(trigger_group) == 1 and len(key_group) == 1:
                        if len(key_group) == 1:
                            rebinds_hr.append([trigger_group, key_group[0]])
                        # macro
                        else:
                            macros_hr.append([trigger_group, key_group])
                        
def save_groups(file_name):
    """
    Save tap groups to a text file.
    Each line in the file represents a tap group with keys separated by commas.
    """
    global tap_groups_hr, rebinds_hr, macros_hr
    
    with open(file_name, 'w') as file:
        # tapgroups
        file.write("# Tap Groups\n")
        for tap_group in tap_groups_hr:
            # file.write(f"{tap_group}\n")
            file.write(', '.join(tap_group)+'\n')         
        # rebinds
        file.write("# Rebinds\n")
        for rebind in rebinds_hr:
            file.write(' : '.join([', '.join(rebind[0]),', '.join(rebind[1])]))
        # macros
        file.write("# Macros\n")
        for macro in macros_hr:
            file.write(' : '.join([', '.join(macro[0]),', '.join(macro[1])]))

def display_groups():
    """
    Display the current tap groups.
    """
    global tap_groups_hr, rebinds_hr, macros_hr
    print("# Tap Groups")
    for index, tap_group in enumerate(tap_groups_hr):
        # print(f"{tap_group}\n")
        print(f"[{index}] " + ', '.join(tap_group)+'')         
    # rebinds
    print("\n# Rebinds")
    for index, rebind in enumerate(rebinds_hr):
        # print(f"[{index}] " + ' : '.join([rebind[0], rebind[1]]))
        print(f"[{index}] " + ' : '.join([', '.join(rebind[0]), rebind[1]]))
    # macros
    print("\n# Macros")
    for index, macro in enumerate(macros_hr):
        print(f"[{index}] " + ' : '.join([', '.join(macro[0]),', '.join(macro[1])]))

def add_group(new_group, data_object):
    """
    Add a new tap group.
    """
    data_object.append(new_group)

def reset_tap_groups_txt():
    """
    Reset Tap Groups and save new tap_group.txt with a+d and w+s tap groups
    """
    global tap_groups_hr
    tap_groups_hr = []
    add_group(['a','d'], tap_groups_hr)
    add_group(['w','s'], tap_groups_hr)
    save_groups(FILE_NAME_ALL)

# initializing and convenience functions
def convert_to_vk_code(key):
    '''
    try to convert string input of a key into a vk_code based on vk_code_dict
    '''
    try:
        return vk_codes_dict[key]
    except KeyError:
        try:
            key_int = int(key)
            if 0 < key_int < 256:
                return key_int
        except ValueError as error:
            print(error)
            raise KeyError

def initialize_groups():
    '''
    in new form there are rebinds and macros
    rebind are Key_Group -> Key_Event
    key_group are a list of Key_Event, Keys
    macros are Key_Group : key_Groups
    '''
    global tap_groups, rebinds, rebind_triggers, macros, macro_triggers
    
    tap_groups = []
    rebinds = {}
    rebind_triggers = []
    macros = {}
    macro_triggers = []
    
    def extract_data_from_key(key):
        #separate delay info from string
        if '|' in key:
            key, *delays = key.split('|')
            if DEBUG: 
                print(f"delays for {key}: {delays}")
            temp_delays = []
            # constraints = []
            for delay in delays:
                if delay.startswith('('):
                    # clean the brackets
                    delay = delay[1:-1]
                    # IDEA ##1
                    # could look for tr(, ts( or ta( in it to determine if it is a delay or constraint
                    temp_delays.append(delay)
                else:
                    temp_delays.append(int(delay))
            delays = temp_delays
            
        else:
            delays = [ALIAS_MAX_DELAY_IN_MS, ALIAS_MIN_DELAY_IN_MS]
            
        # if string empty, stop
        if key == '':
            return False
    
        # recognition of mofidiers +, - and #
        # only interpret it as such when more then one char is in key
        key_modifier = None
        if len(key) > 1: 
            if key[0] == '-':
                # down key
                key_modifier = 'down'
                key = key.replace('-','',1) # only replace first occurance
            elif key[0] == '+':
                # up key
                key_modifier = 'up'
                key = key.replace('+','',1)
            elif key[0] == '!':
                # up key
                key_modifier = 'up'
                key = key.replace('!','',1)
            elif key[0] == '^':
                # up key
                key_modifier = 'toggle'
                key = key.replace('^','',1)

        # convert string to actual vk_code
        vk_code = convert_to_vk_code(key)
            
        if key_modifier is None:
            new_element = (Key(vk_code, delays=delays, key_string=key))
        elif key_modifier == 'down':
            new_element = (Key_Event(vk_code, True, delays, key_string=key))
        elif key_modifier == 'up':
            new_element = (Key_Event(vk_code, False, delays, key_string=key))
        elif key_modifier == 'toggle':
            new_element = (Key_Event(vk_code, None, delays, key_string=key, toggle=True))
        return new_element
    
    # extract tap groups
    for group in tap_groups_hr:
        keys = []
        for key_string in group:
            key = convert_to_vk_code(key_string)
            keys.append(Key(key, key_string=key_string))
        tap_groups.append(Tap_Group(keys))  
         
    # extract rebinds
    for rebind in rebinds_hr:
        trigger_group, replacement_key = rebind
        
        # evaluate the given key strings
        new_trigger_group = []
        for key in trigger_group:
            new_element = extract_data_from_key(key)            
            if new_element is not False:
                new_trigger_group.append(new_element)
        replacement_key = extract_data_from_key(replacement_key)
        
        # check if any given key is a Key Instance - has to be treated differently just to 
        # be able to use v:8 instead of -v:-8 and +v:+8
        both_are_Keys = False
        if isinstance(new_trigger_group[0], Key) or isinstance(replacement_key, Key):
            # if one is Key Instance but the other Key_Event -> convert Key_Event into Key
            if not isinstance(new_trigger_group[0], Key):
                temp = new_trigger_group[0]
                new_trigger_group[0] = Key(temp.get_vk_code(), key_string=temp.get_key_string())    
            if not isinstance(replacement_key, Key):
                # TODO:
                # here toggle is lost in conversion
                if replacement_key.is_toggle():
                    pass # Key_Event.get_key_events() returns [ke, ke] - that should handle it
                else:
                    temp = replacement_key
                    replacement_key = Key(temp.get_vk_code(), key_string=temp.get_key_string())
            both_are_Keys = True
        
        trigger_key, *trigger_rest = new_trigger_group
        
        if not both_are_Keys:
            trigger_group = Key_Group(new_trigger_group)
            rebind_triggers.append(trigger_group)
            rebinds[trigger_group] = replacement_key
        
        else:
            trigger_events = trigger_key.get_key_events()
            replacement_events = replacement_key.get_key_events()
            for index in [0,1]:
                trigger_group = Key_Group([trigger_events[index]] + trigger_rest)
                rebind_triggers.append(trigger_group)
                rebinds[trigger_group] = replacement_events[index]
                  
    # extract macros         
    for macro in macros_hr:
        new_macro = []
        # trigger j = 0, key_group j = 1
        for index, key_group in enumerate(macro):
            new_key_group = Key_Group([])
            for key in key_group:
                new_element = extract_data_from_key(key)            
                if new_element is not False:
                    if isinstance(new_element, Key_Event):
                        new_key_group.append(new_element)
                    elif isinstance(new_element, Key):
                        key_events = new_element.get_key_events()
                        new_key_group.append(key_events[0])
                        # if not in trigger group - so Key Instances as triggers are handled correctly
                        if index == 1: 
                            new_key_group.append(key_events[1])
            new_macro.append(new_key_group)
        macro_triggers.append(new_macro[0])
        # trigger is the key to the to be played keygroup
        macros[new_macro[0]] = new_macro[1]
                      
def reload_all_groups():
    global FILE_NAME_TAP_GROUPS, tap_groups_hr
    # try loading tap groups from file
    try:
        load_groups(FILE_NAME_ALL)
    # if no tap_groups.txt file exist create new one
    except FileNotFoundError:
        reset_tap_groups_txt()
    initialize_groups()
    if DEBUG:
        print(f"tap_groups: {tap_groups}")
        print(f"rebinds: {rebinds}")
        print(f"macros: {macros}")

def delay(max = ALIAS_MAX_DELAY_IN_MS, min = ALIAS_MIN_DELAY_IN_MS, ):
    if min > max: 
        min,max = max,min
    sleep(randint(min, max) / 1000)

def get_key_code(is_mouse_key, vk_code):
    if is_mouse_key:
        key_code = mouse_vk_codes_dict[vk_code]
    else:
        key_code = keyboard.KeyCode.from_vk(vk_code)
    return key_code

def send_key_event(key_event, with_delay=False):
    
    def check_for_mouse_vk_code(vk_code):
        is_mouse_key = vk_code in mouse_vk_codes
        return is_mouse_key
    
    vk_code, is_press, delays = key_event.get_all()
    
    # replace delays with evaluated delay
    constraint_fulfilled, delays = check_constraint_fulfillment(key_event, get_also_delays=True)
    
    if constraint_fulfilled:
        if len(delays) == 0:
            delays = [ALIAS_MAX_DELAY_IN_MS, ALIAS_MIN_DELAY_IN_MS]
        elif len(delays) == 1:
            delays = delays*2
        elif len(delays) == 2:
            pass
        else:
            delays = delays[:2]
        
        is_mouse_key = check_for_mouse_vk_code(vk_code)
        key_code = get_key_code(is_mouse_key, vk_code)
        if is_press:
            controller_dict[is_mouse_key].press(key_code)
        else:
            controller_dict[is_mouse_key].release(key_code)

        if ACT_DELAY and with_delay: 
            delay(*delays)

def check_constraint_fulfillment(key_event, get_also_delays=False):
    fullfilled = True
    temp_delays = []
    delays = key_event.get_delays()
    for delay in delays:
        if isinstance(delay, int):
            temp_delays.append(delay)
        elif isinstance(delay, str):
            result = delay_evaluation(delay)
            if isinstance(result, bool):
                fullfilled = fullfilled and result
            if isinstance(result, int):
                temp_delays.append(result)
            else:
                print(f"! Constraint {delay} is not valid.")
                
    if get_also_delays:
        return fullfilled, temp_delays
    else:
        return fullfilled
            
def delay_evaluation(delay_eval):
    
    # first get vk_code and is_press
    def get_vk_code_and_press_from_keystring(key_string):
        vk_code, is_press = None, None
        # without modifier it will be interpreted as a release
        if key_string[0] not in ['-', '+']:
            is_press = False
        elif key_string[0] == '-':
            is_press = True
            key_string = key_string[1:]
        else:
            is_press = False  
            key_string = key_string[1:]
        vk_code = convert_to_vk_code(key_string)
        return vk_code, is_press
    
    def get_key_time_template(key_string, time_list):
        '''
        template for all press and release time functions -> time in ms
        '''
        _, _, time_released, time_pressed = time_list
        vk_code, is_press = get_vk_code_and_press_from_keystring(key_string)
        key_time = 0
        if is_press:
            try:
                key_time = time_released[vk_code]
                if DEBUG2:
                    print(f"vk_code: {vk_code} time released: {key_time}")
            except KeyError as error:
                print(f"time_release: no value yet for vk_code: {error}")     
                return 0
        else:
            try:
                key_time = time_pressed[vk_code]
                if DEBUG2:
                    print(f"vk_code: {vk_code} time pressed: {key_time}")
            except KeyError as error:
                print(f"time_press: no value yet for vk_code: {error}")
                return 0
        return key_time
    
    def tr(key_string):
        '''
        real press and release time function -> time in ms
        '''
        return get_key_time_template(key_string, time_real)
    
    def ts(key_string):
        '''
        simulated press and release time function -> time in ms
        '''
        return get_key_time_template(key_string, time_simulated)
    
    def ta(key_string):
        '''
        all combined (real and simulated) press and release time function -> time in ms
        '''
        return get_key_time_template(key_string, time_all)
    
    # hardcoded counterstrafe with a polynomial function to destribe acceleration
    def cs(key_string):
        x = tr(key_string)
        if x > 500:
            velocity = 250
        else:
            a = -0.001
            b = 0.97
            c = 12
            velocity = a*pow(x,2) + b*x + c
        # 100 ms at velo of 250 units/sec breaktime
        # just a guess for now
        breaktime = velocity * 100 / 250
        return round(breaktime)
        
    # hardcoded counterstrafe linear
    def csl(key_string):
        x = tr(key_string)
        if x > 500:
            breaktime = 100
        else:
            breaktime = x / (500/100)
        return round(breaktime)
    
    def p(key_string):
        vk_code, _ = get_vk_code_and_press_from_keystring(key_string)
        return vk_code in pressed_keys
    
    def r(key_string):
        return not p(key_string)   
            
    result = eval(delay_eval)
    if DEBUG2:
        print(f"evaluated {delay_eval} to: {result}")
    # if it is a number and if negativ change it to 0
    if isinstance(result, float):
        result = int(result)
    if isinstance(result, int):
        if result < 0:
            result = 0     

    return result

def set_key_times(key_event_time, vk_code, is_keydown, time_list):
    time_last_pressed, time_last_released, time_released, time_pressed = time_list
    if is_keydown:
        time_last_pressed[vk_code] = key_event_time
        try:
            time_released[vk_code] = time_last_pressed[vk_code] - time_last_released[vk_code]
            #print(f"time released: {time_released[vk_code]}")
        except KeyError as error:
            pass
            #print(f"no key yet for: {error}")     
    else:
        time_last_released[vk_code] = key_event_time
        try:
            time_pressed[vk_code] = time_last_released[vk_code] - time_last_pressed[vk_code]
            #print(f"time pressed: {time_pressed[vk_code]}")
        except KeyError as error:
            pass
            #print(f"no key yet for vk_code: {error}")
            
def get_next_toggle_state_key_event(key_event):
    global toggle_state
    vk_code, _, delays = key_event.get_all()
    with alias_toggle_lock:
        try:
            toggle_state[vk_code] = not toggle_state[vk_code]
        except KeyError:
            toggle_state[vk_code] = True
                            #replace it so it can be evaluated
        toggle_ke = Key_Event(vk_code, toggle_state[vk_code], delays)
    return toggle_ke

def set_toggle_state_to_curr_ke(key_event):
    vk_code, is_keydown, _ =  key_event.get_all()
    for key in toggle_state.keys():
        if key == vk_code:
            toggle_state[vk_code] = is_keydown
            
def release_all_toggles():
    for vk_code in toggle_state.keys():
        send_key_event(Key_Event(vk_code, False))
        toggle_state[vk_code] = False

def send_keys_for_tap_group(tap_group):
    """
    Send the specified key and release the last key if necessary.
    """
    # TODO remove delay from here, because it stops listener for the time of delay also ...
    key_to_send = tap_group.get_active_key()
    last_key_send = tap_group.get_last_key_send()
    
    if DEBUG: 
        print(f"last_key_send: {last_key_send}")
        print(f"key_to_send: {key_to_send}")
        
    key_code_to_send = keyboard.KeyCode.from_vk(key_to_send)
    key_code_last_key_send = keyboard.KeyCode.from_vk(last_key_send)
    
    # only send if key to send is not the same as last key send
    if key_to_send != last_key_send:
        if key_to_send is None:
            if last_key_send is not None:
                controller.release(key_code_last_key_send) 
            tap_group.set_last_key_send(None)            
        else:
            is_crossover = False
            if last_key_send is not None:
                # only use crossover when changinging keys, or else repeating will make movement stutter
                if key_to_send != last_key_send:
                    # only use crossover is activated and probility is over percentage
                    is_crossover = randint(0,100) > (100 - ACT_CROSSOVER_PROPABILITY_IN_PERCENT) and ACT_CROSSOVER # 50% possibility
                if is_crossover:
                    if DEBUG: 
                        print("crossover")
                    controller.press(key_code_to_send)
                else:
                    controller.release(key_code_last_key_send) 
                # random delay if activated
                if ACT_DELAY or ACT_CROSSOVER: 
                    delay = randint(ACT_MIN_DELAY_IN_MS, ACT_MAX_DELAY_IN_MS)
                    if DEBUG: 
                        print(f"delayed by {delay} ms")
                    sleep(delay / 1000) # in ms
            if is_crossover:
                controller.release(key_code_last_key_send) 
            else:
                controller.press(key_code_to_send) 
            tap_group.set_last_key_send(key_to_send)


# event evaluation
def win32_event_filter(msg, data):
    """
    Filter and handle keyboard events.
    """
    global PAUSED, MANUAL_PAUSED, STOPPED, MENU_ENABLED
    global last_real_ke, last_virtual_ke, toggle_state
    #global time_real_last_pressed, time_real_last_released
    global time_real, time_simulated, time_all
    
    def is_simulated_key_event(flags):
        return flags & 0x10

    def is_press(msg):
        if msg in WM_KEYDOWN:
            return True
        if msg in WM_KEYUP:
            return False

    def check_for_combination(vk_codes):                 
        all_active = True
        for vk_code in vk_codes:
            if isinstance(vk_code, str):
                vk_code = convert_to_vk_code(vk_code)
            all_active = all_active and vk_code in pressed_keys
        return all_active
    
    def is_trigger_activated(current_ke, trigger_group):
        keys = trigger_group.get_key_events()
        # only trigger on the first key_event in trigger group
        # so only if that key is pressed the trigger can be activated
        if current_ke != keys[0]:    
            return False      
                 
        activated = True
        for key in keys:                         
            if key.get_is_press():
                activated = activated and key.get_vk_code() in pressed_keys
            else:
                activated = activated and key.get_vk_code() not in pressed_keys
                
        # first check every other given trigger before evaluating constraints    
        if activated:
            for key in keys:
                if not activated:
                    return False
                activated = activated and check_constraint_fulfillment(key)
        return activated
        
    
    key_replaced = False
    alias_fired = False
    real_key_repeated = False
    vk_code = data.vkCode
    key_event_time = data.time
    is_keydown = is_press(msg)
    is_simulated = is_simulated_key_event(data.flags)
    
    current_ke = Key_Event(vk_code, is_keydown)
    _activated_triggers = []
    _played_triggers = []
    
    ##1
    if PRINT_VK_CODES or DEBUG:
    # if True:
        print(f"time: {data.time}, vk_code: {vk_code} - {"press  " if is_keydown else "release"} - {"simulated" if is_simulated else "real"}")

    # check for simulated keys:
    if not is_simulated: # is_simulated_key_event(data.flags):
        
        # stop repeating keys from being evaluated
        if last_real_ke == current_ke:
            # listener.suppress_event() 
            real_key_repeated = True
        last_real_ke = current_ke
        
        # here best place to start tracking the timings of presses and releases
        if not real_key_repeated:
            set_key_times(key_event_time, vk_code, is_keydown, time_real)
            set_key_times(key_event_time, vk_code, is_keydown, time_all)       
        
        key_release_removed = False        
        if current_ke not in rebinds.keys():
            manage_key_states_by_event(current_ke)
            if DEBUG:
                print(f"pressed key: {pressed_keys}, released keys: {released_keys}")

        # Replace some Buttons :-D
        if not PAUSED and not PRINT_VK_CODES:
            
            '''REBINDS HERE'''
            # check for rebinds and replace current key event with replacement key event
            for trigger_group in rebind_triggers:
                
                if is_trigger_activated(current_ke, trigger_group):
                    try:
                        replacement_ke = rebinds[trigger_group]
                        old_ke = current_ke
                        current_ke = replacement_ke
                        key_replaced = True
                    except KeyError as error:
                        if DEBUG:
                            print(f"rebind not found: {error}")
                            print(rebinds)
                            
                    if key_replaced:
                        # if key is supressed
                        if current_ke.get_vk_code() == 0:
                            listener.suppress_event()  
                            
                        # if key is to be toggled
                        if current_ke.is_toggle():
                            if old_ke.get_is_press():
                                current_ke = get_next_toggle_state_key_event(current_ke)
                            else:
                                # key up needs to be supressed or else it will be evaluated 2 times each tap
                                listener.suppress_event()  
                                
            '''TOGGLE STATE'''
            # reset toggle state of key manually released - so toggle will start anew by pressing the key
            set_toggle_state_to_curr_ke(current_ke)
            
            '''STOP REPEATED KEYS HERE'''        
            # prevent evaluation of repeated key events
            # not earliert to keep rebinds and supression intact - toggling can be a bit fast if key is pressed a long time
            if not real_key_repeated:
                ### collect active keys
                if key_replaced:
                    manage_key_states_by_event(current_ke)
                    if DEBUG:
                        print(f"replaced a key: pressed key: {pressed_keys}, released keys: {released_keys}")
                
                '''MACROS HERE'''
                # check for macro triggers     
                _activated_triggers = []     
                for trigger_group in macro_triggers:
                    if is_trigger_activated(current_ke, trigger_group):                         
                        _activated_triggers.append(trigger_group)  
                        if DEBUG:
                            print(f"trigger group {trigger_group} activated")
            
                # remove triggers from played that are not activated any more
                # cleaned_triggers = []         
                # for trigger in _played_triggers:
                #     if trigger in _activated_triggers:
                #         cleaned_triggers.append(trigger)
                # _played_triggers = cleaned_triggers    
            
                # play trigger if not already played
                for trigger in _activated_triggers:
                    # if trigger not in _played_triggers:
                    #     _played_triggers.append(trigger)
                    #     if DEBUG:
                    #         print(f"added trigger to played triggers: {_played_triggers}")
                        # as help to later supress startin event AFTER it goes through the tap_groups
                    alias_fired = True
                    key_sequence = macros[trigger].get_key_events()
                    # only spawn a thread for execution if more than one key event in to be played key sequence
                    if len(key_sequence) > 1:
                        thread = Alias_Thread(key_sequence)
                        thread.start() 
                    else:
                        key_event = key_sequence[0]
                        if key_event.is_toggle():
                            key_event = get_next_toggle_state_key_event(key_event)
                        send_key_event(key_event)
                    if DEBUG:
                        print("> playing makro:", trigger)
                        
                    if EXEC_ONLY_ONE_TRIGGERED_MACRO:
                        break
                
                
                '''PREVENT NEXT KEY EVENT FROM TRIGGERING OLD EVENTS'''               
                # to remove the key from released_keys after evaluation of triggers
                # so can only trigger once
                if not is_keydown:
                    remove_key_release_state(current_ke.get_vk_code())  
                    key_release_removed = True          

        if CONTROLS_ENABLED:                  
            # # Stop the listener if the MENU combination is pressed
            if check_for_combination(MENU_Combination):
                MENU_ENABLED = True
                print('\n--- Stopping - Return to menu ---')
                listener.stop()

            # # Stop the listener if the END combination is pressed
            elif check_for_combination(EXIT_Combination):
                print('\n--- Stopping execution ---')
                listener.stop()
                STOPPED = True
                exit()

            # Toggle paused/resume if the DELETE combination is pressed
            elif check_for_combination(TOGGLE_ON_OFF_Combination):
                if PAUSED:
                    reload_all_groups()
                    print("--- reloaded ---")
                    print('--- manuelly resumed ---')
                    with paused_lock:
                        PAUSED = False
                        MANUAL_PAUSED = False
                    # pause focus thread to allow manual overwrite and use without auto focus
                    if FOCUS_APP_NAME is not None: 
                        focus_thread.pause()
                    #reset_key_states()
                else:
                    print('--- manually paused ---')
                    with paused_lock:
                        PAUSED = True
                        MANUAL_PAUSED = True
                        release_all_toggles()
                    # restart focus thread when manual overwrite is over
                    if FOCUS_APP_NAME is not None: 
                        focus_thread.restart()
                    #reset_key_states()

        '''TAP GROUP EVALUATION HERE'''
        # Snap Tap Part of Evaluation
        # Intercept key events if not PAUSED
        if not PAUSED and not PRINT_VK_CODES:
            vk_code, is_keydown, _ = current_ke.get_all()
            if DEBUG: 
                print("#0")
                print(tap_groups)               
                print(vk_code, is_keydown)               
            for tap_group in tap_groups:
                if vk_code in tap_group.get_vk_codes():
                    if DEBUG: 
                        print(f"#2 {vk_code}")
                    if key_replaced is True:
                        key_replaced = False
                    tap_group.update_tap_states(vk_code, is_keydown) 

                    # send keys
                    send_keys_for_tap_group(tap_group)
                    listener.suppress_event()
                    break
        
        # if replacement happened suppress source key event   
        if key_replaced is True:
            send_key_event(current_ke)
            listener.suppress_event()
        
        # supress event that triggered an alias - done here because it should also update tap groups before
        if alias_fired is True:
            listener.suppress_event()
            
        # to remove the key from released_keys after evaluation of triggers
        # so can only trigger once
        if not is_keydown and not key_release_removed:
            remove_key_release_state(current_ke.get_vk_code()) 
    
    # here arrive all key_events that will be send - last place to intercept
    # here the interception of interference of alias with tap groups is realized
    if is_simulated:
        
        # TODO:
        # should simulated keys also be rebound according to rebinds?
        
        for tap_group in tap_groups:
            vk_codes = tap_group.get_vk_codes()
            if vk_code in vk_codes:
                active_key = tap_group.get_active_key()
                # if None all simulated keys are allowed - so no supression
                if active_key is None:
                    pass
                else:
                    if active_key == vk_code:
                        # is active key -> only press allowed
                        if not is_keydown:
                            listener.suppress_event()
                    # not the active key -> only release allowed
                    else: 
                        if is_keydown:
                            listener.suppress_event()
                            
        # save time of simulated and send keys
        set_key_times(key_event_time, vk_code, is_keydown, time_simulated)
        set_key_times(key_event_time, vk_code, is_keydown, time_all)
            
def display_menu():
    """
    Display the menu and handle user input
    """
    global PRINT_VK_CODES, DEBUG, DEBUG2
    PRINT_VK_CODES = False
    invalid_input = False
    text = ""
    while True:       
        # clear the CLI
        if not DEBUG:
            system('cls||clear')
        if invalid_input:
            print(text)
            print("Please try again.\n")
            invalid_input = False
            text = ""
        display_groups()
        print('\n------ Options -------')
        print("0. Toggle debugging output for V0.9.3 formula evaluation.")
        print(f"1. Open file:'{FILE_NAME_ALL}' in your default editor.")
        print("2. Reload everything from file.")
        print("3. Print virtual key codes to identify keys.")
        print("4. End the program/script.", flush=True)
        
        sys.stdout.flush()

        # Try to flush the buffer
        while msvcrt.kbhit():
            msvcrt.getch()

        choice = input("\nHit [Enter] to start or enter your choice: " )

        if choice == '0':
            DEBUG2 = not DEBUG2
        elif choice == '1':
            startfile(FILE_NAME_ALL)
        elif choice == '2':
            reload_all_groups()   
        elif choice == '3':
            PRINT_VK_CODES = True
            break
        elif choice == '4':
            exit()
        elif choice == '':
            break
        else:
            text = "Error: Invalid input."
            invalid_input = True

def check_start_arguments():
    global DEBUG, MENU_ENABLED, CONTROLS_ENABLED
    global FILE_NAME_ALL
    global ACT_DELAY, ACT_CROSSOVER, ACT_CROSSOVER_PROPABILITY_IN_PERCENT
    global ACT_MAX_DELAY_IN_MS, ACT_MIN_DELAY_IN_MS
    global ALIAS_MIN_DELAY_IN_MS, ALIAS_MAX_DELAY_IN_MS
    global FOCUS_APP_NAME, EXEC_ONLY_ONE_TRIGGERED_MACRO
    
    def extract_delays(arg):
        try:
            delays = [int(delay) for delay in arg.replace(' ','').split(',')]
        except Exception:
            print("invalid delay - needs to be a number(s), seperated by comma")
        if len(delays) > 2:
            delays = delays[:2] # keep only first 2 numbers
        valid_delays = []
        for delay in delays:
            if 0 < delay <= 1000:
                valid_delays.append(delay)
            else:
                print("delay not in range 0<delay<=1000 ms")
        return sorted(valid_delays)
    
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            # if commented out do nothing
            if arg[0] == ':' or '#':
                pass
            if DEBUG: 
                print(arg)
            # enable debug print outs
            if arg == "-debug":
                DEBUG = True
            # start directly without showing the menu
            elif arg == "-nomenu":
                MENU_ENABLED = False
            # use custom tap groups file for loading and saving
            elif arg[:6] == '-file=' and len(arg) > 6:
                FILE_NAME_ALL = arg[6:]
                if DEBUG: 
                    print(FILE_NAME_ALL)
            # Start with controls disabled
            elif arg == "-nocontrols":
                CONTROLS_ENABLED = False
            elif arg == "-delay":
                ACT_DELAY = True
            elif arg[:10] == "-tapdelay=" and len(arg) > 10:
                ACT_DELAY = True
                ACT_MIN_DELAY_IN_MS, ACT_MAX_DELAY_IN_MS = extract_delays(arg[10:])
                print(f"Tap delays set to: min:{ACT_MIN_DELAY_IN_MS}, max:{ACT_MAX_DELAY_IN_MS}")
            elif arg[:12] == "-aliasdelay=" and len(arg) > 12:
                ACT_DELAY = True
                ALIAS_MIN_DELAY_IN_MS, ALIAS_MAX_DELAY_IN_MS = extract_delays(arg[12:])
                print(f"Alias delays set to: min:{ALIAS_MIN_DELAY_IN_MS}, max:{ALIAS_MAX_DELAY_IN_MS}")
            elif arg == "-crossover":
                ACT_CROSSOVER = True          
            elif arg[:11] == "-crossover=" and len(arg) > 11:
                ACT_CROSSOVER = True    
                try:
                    probability = int(arg[11:])
                except Exception:
                    print("invalid probability - needs to be a number")
                if 0 <= probability <= 100:
                    ACT_CROSSOVER_PROPABILITY_IN_PERCENT = probability
                else:
                    print("probability not in range 0<prob<=100 %")
            elif arg == "-nodelay":
                ACT_DELAY = False
                ACT_CROSSOVER = False
                print("delay+crossover deactivated")
            elif arg[:10] == "-focusapp="  and len(arg) > 10:
                FOCUS_APP_NAME = arg[10:]
                print(f"focusapp active: looking for: {FOCUS_APP_NAME}")
            elif arg == "-exec_one_macro":
                EXEC_ONLY_ONE_TRIGGERED_MACRO = True
            else:
                print("unknown start argument: ", arg)
                
# Theading 
class Alias_Thread(Thread):
    '''
    execute macros/alias in its own threads so the delay is not interfering with key evaluation
    '''
    def __init__(self, key_sequence):
        Thread.__init__(self)
        self.daemon = True
        self.key_events = key_sequence
        
    def run(self):     
        try:   
            # Key_events ans Keys here ...
            for key_event in self.key_events:
                alias_thread_logging.append(f"{time() - starttime:.5f}: Send virtual key: {key_event.get_key_string()}")
                
                if key_event.is_toggle():
                    key_event = get_next_toggle_state_key_event(key_event)
                    
                send_key_event(key_event, with_delay=True)
        except Exception as error:
            alias_thread_logging.append(error)
            
class Focus_Thread(Thread):
    '''
    Thread for observing the active window and pause toggle the evaluation of key events
    can be manually overwritten by Controls on DEL
    reloads key and tap files on resume
    '''

    def __init__(self, focus_app_name):
        Thread.__init__(self)
        self.stop = False
        self.daemon = True
        self.focus_app_name = focus_app_name.lower()

    def run(self):
        global PAUSED, MANUAL_PAUSED, paused_lock, FOCUS_THREAD_PAUSED
        last_active_window = ''
        while not self.stop:
            try:
                active_window = gw.getActiveWindow().title
            except AttributeError:
                pass
            if FOCUS_THREAD_PAUSED is False and MANUAL_PAUSED is False:
                if active_window.lower().find(self.focus_app_name) >= 0:
                    if PAUSED:
                        try:
                            #reset_key_states()
                            reload_all_groups()
                            print("--- reloaded ---")
                            print('--- auto focus resumed ---')
                            with paused_lock:
                                PAUSED = False
                        except Exception:
                            print('--- reloading of groups files failed - not resumed, still paused ---')
                else:
                    if not PAUSED:
                        with paused_lock:
                            PAUSED = True
                            release_all_toggles()
                        print('--- auto focus paused ---')
                    # print out active window when paused and it changes
                    # to help find the name :-D
                    else:
                        if last_active_window != active_window:
                            print(f"> Active Window: {active_window}")
                            last_active_window = active_window
            sleep(0.5)

    def pause(self):
        global FOCUS_THREAD_PAUSED
        with paused_lock:
            FOCUS_THREAD_PAUSED = True

    def restart(self):
        global FOCUS_THREAD_PAUSED, MANUAL_PAUSED
        if FOCUS_THREAD_PAUSED:
            with paused_lock:
                FOCUS_THREAD_PAUSED = False
                MANUAL_PAUSED = False

    def end(self):
        self.stop = True
         

def main():
    global listener
    global focus_thread
     # check if start arguments are passed
    check_start_arguments()

    # try loading tap groups from file
    reload_all_groups()

    if DEBUG:
        print(f"tap_groups_hr: {tap_groups_hr}")
        print(f"tap_groups: {tap_groups}")


    if FOCUS_APP_NAME is not None:
        focus_thread = Focus_Thread(FOCUS_APP_NAME)
        focus_thread.start()

    while not STOPPED:
        reset_key_states()
        release_all_toggles()
               
        if MENU_ENABLED:
            if FOCUS_APP_NAME is not None:
                focus_thread.pause()
            display_menu()
        else:
            display_groups()

        print('\n--- Free Snap Tap started ---')
        print('--- toggle PAUSED with ALT+DELETE key ---')
        print('--- STOP execution with ALT+END key ---')
        print('--- enter MENU again with ALT+PAGE_DOWN key ---')
        if FOCUS_APP_NAME is not None:
            focus_thread.restart()
        
        with keyboard.Listener(win32_event_filter=win32_event_filter) as listener:
            listener.join()
            
        sleep(1)

    if FOCUS_APP_NAME is not None:
        focus_thread.end()
    sys.exit(1)

def reset_key_states():
    global pressed_keys, released_keys
    pressed_keys = set()
    released_keys = set()
    
if __name__ == "__main__":
    starttime = time()   # for alias thread event logging
    main()
    
    
# **** ... this is a long file xD