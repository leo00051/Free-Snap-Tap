# Free Snap Tap: Universal Keyboard Snap Tap with Tap Groups, Rebinds (Key Replacements), Macros (Aliases) and custom adjustable delay for each key.

**Works as of V0.8.0 without triggering Valve Anti Cheat (if delays are not set too short :-) )**

**Only works on Windows.**

A minimalistic Python-based Snap Tapping program compatible with all keyboards and supports:
- Adjustable Tap Groups (mutually exclusive keys with Snap Tap functionality)
- Key Rebinds/Replacements - replaced keys which can also be evaluated by Tap Groups/Macros
- Macros (Aliases, Null binds) - supports key combinations, key prohibition and played keys have no interference with Tap Group Keys
- Custom delay for every key event that helps to NOT be recognized as input automation because the input is not as perfect
  - see [### Example Use Cases for Aliases (to show what is possible right now)](https://github.com/wasiejen/Free-Snap-Tap?tab=readme-ov-file#examplesfor-aliases-to-show-what-is-possible-right-now)
- With Autofocus option: to only be active if a certain active window is in focus (see # Configuration)
- programmable delays and time constraints for macros
- With simple Command Line Interface (CLI)

<img width="900" alt="FST" src="https://github.com/user-attachments/assets/6160fa32-e598-448f-bd67-7ef0cd02b081">

_pic1: CLI Menu_

All Tap Groups, Rebinds and Macros/Aliases are saved in an external file (default `FSTconfig.txt`) and can be edited directly.

**Tap Groups** 
- Mutually exclusive keys - the most recent key press will always be prioritized; constantly pressed keys will be repressed if others keys are released again (snap tap).
- Multiple Keys separated by commas - `w,s`,`a,d` or `1,2,3,4`. Each key without modifiers.

**Rebinds** 
- Directly replaces one key with another and suppress the original key. Windows keys, caps_lock and other keys can be remapped. Helpful for games that do not or only partly support rebinding ingame.
- 2 keys separates by `:`. `c : ctrl`, `+p : +mouse_right`. Replacement key will be evaluated in Tap Groups and in Triggers for Macros. Source/Trigger Key will be suppressed and not evaluated.

**Macros/Aliases** 
- A trigger will play a sequence of key_events (presses, releases) with custom delay for each key. Supports key prohibition - key not allowed to be pressed to trigger the trigger combination.
- 2 Key Groups (Keys separated by comma) separated by `:`. 
- First group will be the trigger combination (one key or more), second group is the key sequence to be played. 

Comments work with `#` for line comment, single key commenting out and comment after key sequence.
String representation or vk-codes (virtual keyboard codes — list in vk_codes.py file) can also be used. 

## Examples for Tap Groups

- Movement Left/Right (Tap Group `a, d` and/or `left_arrow, right_arrow`)
- Movement Forward/Backward (Tap Group `w, s` and/or `up_arrow, down_arrow`)
- Leaning to the sides (Tap Group `e, q`)
- Fast weapon switching (Tap Group `1, 2, 3, 4`)
- Flight/Space Sim:
  - Throttle Up/Down
  - Movement Up/Down (Tap Group `r, f`)
  - Yaw Left/Right
  - Pitch Up/Down
  - Roll Left/Right

## Examples for Key Replacements

- `windows_left : left_control` 
- `< : left_shift`
- `-t : +t` , `+t : -t` - press t will be rebind to release t and release t to press t (input reversal) same as `t : !t`

## Examples for Aliases (to show what is possible right now)

- `-k :  p|10,  o|5,  i|15|3`: when `k` is pressed , send `p` with a max delay of 10 ms, then `o` with max delay of 5 ms, then `i` with min delay of 3 ms and max of 10 ms (order of delays via `|` is free - it fetches the smaller one as min and the bigger one as max)
- `+o :r,e,v,e,r,s,e,d,-left_shift,w,o,r,l,d,+left_shift`: when `o` is released -> writes/sends "reversedWORLD"
- `-- :-+,++,+mouse_left, +mouse_right`: when `-` is pressed sends a `+` press and release, and only sends the release of `mouse_left` button and `mouse_right` button
- `+- :o,k # inline comments work also`: when `-` is released -> writes/sends "ok"
- `h : h, e, #l, l, o # here key commented out`: when `h` is pressed -> writes/sends "helo"
- `-n : suppress`: n press will be suppressed, n release still be send

#### New with 9.0: key combinations and prohibited keys (e.g. !ctrl)
- `-space, !ctrl: -space|125|125, -ctrl|325|325, +ctrl|0|0, +space|0|0`: when space is pressed and **control is not pressed** (e.g. crouched) will jump, delay 125ms, crouch for 325 ms and releases both (for counterstrike with default bindings)
  - useful to then add the single key tap groups `ctrl` and `space` - macros will not interfere with tap groups if the keys they play contradicts the state of a tap group 
- `+d, !ctrl, !space: +d|15|5, -a|100|100, +a|0|0`: when d is released and **control and space are not pressed** then release d, wait 5-15ms, make counter strafe by pressing a for 100 ms and then releasing without further delay after

#### New with 9.2: toggle option (^ modifier) in rebinds and macros
- Rebind: `left_shift: ^left_shift` - each press of shift will on one press toggle shift to pressed state and with another press to released state
- Macro: `r, !left_shift: ^right_mouse` - r will toggle the right mouse between pressed and released with each tap (press and release) - will not be triggered if shift is pressed
  - if macro only has one element as sequence there will be no delay used even if given
  - can also be used in key sequences `r, !left_shift: ^ctrl|50|50, ^left_mouse|50|50, ...` 
    - but if that is useful is an entire different question ;-)

#### New with 9.3: dynamic evaluation of delays - programmable delays dependent on key press and release times

```bash
# Example Config file: for testing remove most of the explaining comments - something the program is not liking xD
# Tap Groups
a,d
w,s

# Rebinds
left_windows : left_control
< : left_shift
caps_lock : shift
c : ^left_control     # toggle for left control on c
v : suppress  

# Macros
# automatic counter strafing when w key released
# will not trigger if crouched (!ctrl), jumping (!space) or opposite key is pressed
# (tr("+w")>100): will only trigger if movement key was pressed for at least 100 ms
# (cs("+w")): counterstrafe will be dynamically adjusted based on time of pressed movement key 
# cs() is a hard coded function that uses a polynomial function to approximate the acceleration ingame and calculate the needed length for a counterstrafe to come to a stop
+w|(tr("+w")>100), !s, !ctrl, !space  :  +w|15|5, -s|(cs("+w")), +s|0|0
+s|(tr("+s")>100), !w, !ctrl, !space  :  +s|15|5, -w|(cs("+s")), +w|0|0
+a|(tr("+a")>100), !d, !ctrl, !space  :  +a|15|5, -d|(cs("+a")), +d|0|0
+d|(tr("+d")>100), !a, !ctrl, !space  :  +d|15|5, -a|(cs("+d")), +a|0|0

# jump with crouch: will not trigger if ctrl is pressed (!ctrl)
# will only trigger if space press was 125-400 ms long and the crouch will go at most to 600 ms after the initial space press
+space|(125<tr("+space")<400), !ctrl : +space, -ctrl|(600-tr("+space")), +ctrl|0|0 

# automatic application of healing syringe and switch back to last weapon
# (125<tr("+x")<900): will not be triggered if tapped really quickly or hold over 900 ms
# the longest it will be waiting to release x is 900ms after x was pressed (900-tr("+x")) to make sure it is equipped fully
+x|(125<tr("+x")<800) : +x|(1000-tr("+x")), -left_mouse|700|700, +left_mouse|0|0, q
```

- Dynamic evaluation is instead used of set delays behind the `|` of a key. e.g. `+w|(tr("+w")>100)`
- Evaluation defined by a formula in brackets `()`
  - **As a part of the trigger combination will check if the condition in the evaluation is True**
    - Will be handled separately from attached key and both checked separately
  - **As part of the played key sequence it has to return a number that will be used as delay in ms** 
    - If result is negative will return 0
  - **`""` or `''` are needed**  -> `tr("+w")` will give out the length of the last key press for key w, and `tr("-w")` will give out the length of time between a release and a press - so length of release/ time since it was last activated
- Time functions 
  - `tr()` - Callable for last **real key** press and release time with `tr("+/-key")`. 
    - also rebinds are here - only the replaced keys without the trigger/source key
  - `ts()` - Only observes **simulated keys** (keys send by macros) 
    - (tap groups in real and simulated due to there handling in the program)
  - `ta()` - Combines **both real and simulated** input to generate a combined times for **"all"** key events
- Other function:
  - `cs()` - Counterstrafe based on a polynomial function - everything over 500 ms is handled as max velocity and returns 100 ms as delay for the counterstafe.
  - `csl()` - Counterstrafe based on a linear function (polynomial works better in my opinion)
- All normal python code is able to be evaluated:
  - so keep in mind: all Trigger functions must evaluate to bool (True or False) and all played keys must result in a number

## Key Modifier explanation:
#### **for rebinds and macros**
- `` nothing in front of a key is synchronous input (press is a press, release is a release)
- `-` in front of a key is a press (down without up)
- `+` in front of a key is a release (up without down)
- `#` in front of a key, comments that key out and will not be used
- `^` in front of a key, will toggle the key state between pressed and released on key_down (rebind) or on trigger activation (macro)
#### **only for rebinds**
- `!` in front of a key is a release and a key (reversed synchronous input)
#### **only for macros**
- `!` in front of a key in the first key group means (trigger group) will be seen as `prohibited key` - if that key is pressed, the trigger will not trigger ^^
- `|` after a key is the the max delay for this single key (e.g. `-k|10` -> press k with a max delay of 10)
- `|*max*|*min*` after a key defines min and max delay (e.g. `-k|10|2` or `-k|2|10` -> press k with a max delay of 10 and min delay of 2)
- `|(formula)` after a key: 
  - as part of a trigger group must result in True or False and forms a time constraint that needs to be fulfilled before activating
  - as part of a played key sequence (macro) it has to return a number that will be used as a set delay
  - time functions usable: `tr()`, `ts()`, `ta()`
  - e.g. as trigger:  `+w|(tr("+w")>100)` - evaluated to: (tr("+w")=(length of pressed time for w key) must be > 100 ms to be activated
  - e.g. as played key: `-ctrl|(600-tr("+space"))` - control will be pressed and then the delay will wait for 600-tr("+space")=(length of time space was pressed) ms

Key Modifiers do not work in Tap groups and will be ignored.

## Delay-Settings
- Delays are random between a min and a max time in ms
- Default delays for the Tap_Groups is set to 2 ms for min and 10 ms for max (py file)
  - Can be changed in py file or the min and max can be set via the start argument `-delay="number, number"`.
- Delays are used after each key event (press and release), so a key press has 2 delays
- Aliases use the same delay as Tap_Groups per default
  - Only if the keys are given some other delay via `*key*|*number*|*number*` will these be overwritten for this specific key event (not this key in general).

## Controls

- **Toggle Pause:** Press the `ALT + DELETE` key to pause or resume the program.
  - resuming will reload key and tap groups from files
- **Stop Execution:** Press the `ALT + END` key to stop the program.
- **Return to Menu:** Press the `ALT + PAGE_DOWN` key to return to the menu.

You can change the control key combinations in the py file under # Control key combination.

## Configuration

Start Options: (add to the bat(ch) file or in a link after the *path*\free_snap_tap.exe)
-  `-nomenu` skips the menu and will be directly active
-  `-file="filename"`: (with or without "): custom save file
-  `-debug`: print out some debug info
-  `-nocontrols`: to start it without the controls on `DEL`, `END` and `PAGE_DOWN`keys enabled- start -  
-  `-tapdelay="number, number"`: sets the default min and max delay of "number,number" ms for Tap_Groups
-  `-aliasdelay="number, number"`: sets the default min and max delay of "number,number" ms for Macros/Aliases
-  `-crossover="number"`: sets the probability of "number" percent for a crossover (can be set in a range of 0-100)
   - A crossover is key event reversal with delay - press and release are overlapping the time of delay
-  `-nodelay`: deactivates delay and crossover
-  `-focusapp="part of the app name"`: Script only activate evaluation of key events if the defined window with the given name is in focus.
   - e.g. for Counterstrike, `-focusapp=count` is enough to recognize it (not case sensitive)
   - can be manually overwritten by Control on ALT+DEL key combination (to activate outside and deactivate inside focus app)
  
### Example batch file
Example is for use with CMD, for PowerShell replace ^ with \` for multi line start arguments.
To Use the exe replace line `python .\free_snap_tap.py ^` with `.\free_snap_tap.exe ^`.
Uncomment lines by removing `::` in front of the start arguments.

```bash
@echo off
.\free_snap_tap.exe ^
::-debug ^
::-file=FSTconfig.txt ^
-crossover=20 ^
-tapdelay=5,2 ^
-aliasdelay=5,2 ^
::-nomenu ^
::-nocontrols ^
::-nodelay ^
::-focusapp=count 

pause
```

## Current Version Information

**V0.9.4**

- NEW:
  - formula evaluation now extended to rebind trigger
    - `c|(p("0")) : ctrl` - only rebind c to ctrl if 0 is pressed
      - in combination with toggle function `0 : ^0` the 0 key can be toggled and the rebinds for a set of keys then change with just one key press or while just holding the key. (that is a functionality I always wanted to have in MMOs :-) - rebind everthing with a button press)
  - 2 new evaluation functions to be usable
    - `p("key")` - checks if the key is **P**ressed (current real key press)
    - `r("key")` - checks if the key is **R**eleased - literally `not p()`
  - multiple formula can now be added to any key and will be evaluated
    - `+w|(not p("s"))|(tr("+w")>100)` - only trigger on +w if +s is not pressed and w was pressed for at least 100 ms
  - False/True Evaluation now also usable in played keys of macro
    - `+s|(not p("s"))|100|100` - only release s if s is not pressed (current real key press) and if played will delay for 100 ms (100ms max and 100 ms min)
      - delays can still be added as numbers but only the first 2 will be used for min and max random delay
    - `-s|(r("w"))|(cs("+w"))` - only press s if w is released (current real key state) and then use custom delay defined by the function cs("+w")

- Bugfixes:
  - Macros triggered with every key event when trigger was fulfilled even if key event was not part of the trigger - bug introduced in V0.9.3 by fixing non evaluation of formula if there was only one key in trigger group
  - If time of a key in a formula was not pressed before could lead to an undefined state - will now return 0/False if no valid value for time pressed or time released exist yet

- QOL:
  - removed '"unknown start argument: ", arg' outputs if start arguments were commented out in batch file. Now ':' or '#' will be seen as commenting out and the argument that is still received will not be printed out any more
  - toggle modifier '^' was not shown in display of rebinds
  - toggle state will now be overwritten by actual manual input of the same key - behavior is now no longer independent of real key press/release state as before
  - toggle states will be reseted and toggled keys released if manual paused or focusapp paused

**V0.9.3**
- See: #### New with 9.3: dynamic evaluation of delays - programmable delays dependent on key press and release times

**V0.9.2**
- See: #### New with 9.2: toggle option (^ modifier) in rebinds and macros

**V0.9.1**
- Bugfix: Tracked released keys were not removed from states list and every key event could trigger macros that used key releases as triggers.

**V0.9.0**

- NEW: Key combinations for Macros/Aliases
- NEW: Key prohibition via `! notation` for trigger key combination of a macro
    - see example down below
- NEW: simplified CLI Menu 
    - now with option to directly open the config file in your default txt editor
    - (didn't want to further support that cumbersome edit option) :-)
- NEW: One file now for all settings
    - NEW: start argument `-file=*filename*`
    - start argument `-tapfile=` and -`keyfile=` removed
- NEW: Changed formatting of rebinds and macros
    - now uses `:` to differentiate between key groups
      - for Rebinds: `left_windows : ctrl`
      - for Macros: `+w, !left_control : +w|15|5, -s|100|100, +s|0|0 `
- NEW: Controls are now default activated per `ALT+Control key` combination
- NEW: nearly completely rewritten :-)
- probably some more things I have just forgotten to mention ^^

  #### Example

  - `+d, !ctrl, !space: +d|15|5, -a|100|100, +a|0|0`: when d is released and **control and space are not pressed** then release d, wait 5-15ms, make counter strafe by pressing a for 100 ms and then releasing without further delay after
      - the fun part is now you could define `+d, -space, !ctrl: +d|15|5, -a|150|150, +a|0|0` with different counter strafe duration which will only be applied if you jump and release the movement key

## How Free Snap Tap Works 

Snap Tapping is a feature that enhances your keyboard's responsiveness by prioritizing the most recent key input when multiple keys are pressed simultaneously. Here’s how it operates:

1. **Intercepting Keyboard Input:** The program monitors the keys defined in the Tap Groupings. When you press any of these keys, the program intercepts the input.
2. **Suppressing Original Input:** Instead of allowing the original key press to be sent directly to your computer, the program suppresses it. This means the original input is not immediately processed by your system or application.
3. **Sending Idealized Input:** The program then determines the ideal input based on the most recent key press. For example, if you press `A` and then `D` without releasing `A`, the program will prioritize `D` and if you release `D`, `A` will be pressed again as long it is pressed. This idealized input is then sent to your system, ensuring that the most recent direction is registered.

## Easy Usage

- Download the executable from the actual [releases](https://github.com/wasiejen/Free-Snap-Tap/releases).
- Start via `free_snap_tap.exe` or the provided bat(ch) file and a Command Line Interface will open with further explanations.
- to customize the start with many options see `# Configuration`. Example batch file can also be found there.
- To start from the menu hit [Enter].
- Have fun. :-)

### AntiVir False Positives
- The exe is offered to simplify the usage, it may get a false positive from some antivirus tools and be detected as a Trojan. The reason for that seems to be the packaging as an executable that triggers these antivirus software and leads to false positives. See Discussion #12.
  - Option 1: if recognized as Trojan - whitelist it in your antivir.
  - Option 2: instead use the py file - See `# Installation` for more info

## Installation

1. **Install Python:** Ensure Python 3.6 or higher is installed on your system. You can download it from [python.org](https://www.python.org/).
2. **Install `pynput` Package:** Open your terminal or command prompt and run:

```bash
pip install pynput
```

or navigate to the Free-Snap-Tap repo folder and type in:

```bash
pip install -r requirements.txt
```

3. **Starting the Program:**

    3.1 **Option A: directly:** By  clicking/executing the `example_batch_file.bat` file.

    3.2 **Option B: via Command Line:** Start a Command Line/Terminal, navigate to the folder containing the .py file and use one of the following commands:

```bash
./example_batch_file.bat
```

or navigate to the Free-Snap-Tap repo folder and type in:

```bash
python ./free_snap_tap.py
```

## On Linux 

Not working due to no support of selective key suppression in Linux OS.

## On MacOS - **Not supported atm**

Compared to Linux the selective event suppression is possible, but it uses another listener constructor and gets other data than the win32_event_filter which is used here. Since this conversion/switch/alternative is not implemented yet, the program will not work on MacOS. But there might be a fix for that in the future.

## On Feedback:

Feel free to give feedback. This program is a fun project to me to get more comfortable with GitHub and testing out some things in Python. :-)
If you have wishes or ideas what to add, just `create a issue` or `start a discussion` with a description and use cases of the feature.

### Version History

**V0.8.5**
- NEW: Tap Groups have always priority before Alias execution
  - Alias will be played as normal but only key events that are not interfering with the actual state of the tap group will be send
  - following example does now work without interfering with actual real input and the function of the tap group
```bash
+w, +w|5|2, -s|25|15, +s|0|0   #stop_forward
+s, +s|5|2, -w|25|15, +w|0|0   #stop_back
+a, +a|5|2, -d|25|15, +d|0|0   #stop_left
+d, +d|5|2, -a|25|15, +a|0|0   #stop_right
```
- Tap delay and Alias delay can now be adjusted separately via the 2 start arguments:
  - `-tapdelay=8,2`  and `-aliasdelay=8,2` (min delay 2ms and max delay 8 ms)
  - replaces `-delay=`
- To easier find the name name for `-focusapp`: if focusapp (with any name) is activated and the evaluation of key events is auto paused then the active windows name will be printed into the command line and updated with every change of the active window. 

**V0.8.4**
- NEW: Auto Focus on a active Window specified by part of the name of the app/game/program
  - script will only evaluate keyboard input when a window with this name is in focus
  - `-focusapp=*part of the app name*` - e.g. for Counterstrike, only Count is enough to recognize it
  - control on Del now also pauses Auto focus, so evaluation can be activated outside of app or deactivated in app.
  - auto focus will restart with restarting script from menu again
  - when resumed the tap and key group files will be reloaded and so changes in them applied
  - only active when this start argument is used
 
**V0.8.3**
- NEW: threading for Alias execution
  - prevents original key to be send because of long delay before actual suppression takes place
  - prevents interfering with real input
- not much else :-D

**V0.8.2**

- delays were applied one key later - should now work correctly
- removed my notes from py file :-)
- vk_codes.py now contains key codes
- vk_code print (menu option 7) is now much more verbose and helpful :-D
- when using controls:
  - resume will now reload tap and key files 
  - (so tap out of game, change groups, save and resume in game will reload groups)

**V0.8.1**

- delay is now active as default
  - `-nodelay` start argument can be used to disable delay and crossover
- min max delay per start argument settable
  - `-delay=20,10`
- comments now work in the group files
  - use `#` to set a comment
  - line comment `#.....`
  - comment out some keys `..., h , #e, l, #l, o,... -> hlo`
  - comment after key sequence `a,d # sidestepping tap group`
- reverse now marked with `!` instead of `#` (used now for commenting)
- option to suppress key events via key group (with 2 keys only)
  - `-n, suppress` -> n press will be suppressed, n release still be send

**V0.8.0**

Tested on new VAC policy and working so far without being kicked for input automation.
Use delay of at least 5 ms, better a more to be on the save side and do not spam snap tap extremely often in 2 seconds or you will still be kicked. ;-)

- NEW: updated random delay and crossover to tap_groups to simulate a more natural (or harder to detect) way to use snap tap
  - works with the new policy of Valve Anti Cheat (VAC)
  - start_argument `-delay=*time_in_ms*` will set the max delay to time_in_ms.
    - overwrites the default of max = 10 ms delay
    - min delay value of 2 ms can be changed in py file if needed
    - crossover will also use this as delay
  - start_argument `-crossover=*probability*` will set the probability of a crossover (release will be send now and based on delay the new key press will be send later)
    - to have another way to simulate a form of imperfect snap tap to circumvent VAC
      
- NEW: introduces Aliases aka Null binds that are specifically designed with customizable random delays for each key event
  -  to define in Key_Groups as groups with more than 2 keys.
  -  mouse output for mouse_left, mouse_right, mouse_middle works
  -  NEW: key event modifiers that changes how the key will be evaluated
    - `-` in front a the key - as first key, following keys will only executed when key pressed, else only send key press (no key release send)
    - `+` in front a the key - as first key, following keys will  only executed when key released, else only send key release (no key press send)
    - `-` in front a the key - as first key, following keys will  only executed when key pressed, else only send key press (no key release)
    - ` ` (nothing/empty/space) in front a the key - as first key, following keys will be `executed on key press and release!!`, else send a key press and release
  - NEW: delay per key (not for first key = trigger)
    - random delay will default to 2 ms min and 10 ms max (in py file changeable) and uses the same delay as defined by start_argument `-delay=*time_in_ms*`
    - `+l, -left_shift|20|10, h|10,e|5,l|50,l,o, +left_shift` will print HELLO when l is released with varying delay for key events: left_shift, h, e and l
      - `*modifier**key*|*delay_in_ms*` marks the delay that will be set as max delay
      - `*modifier**key*|*delay1_in_ms*|*delay1_in_ms*` marks the delay that will be set as max and min delay (order is free - uses the bigger one as max and smaller as min)
 
See [### Example Use Cases for Aliases (to show what is possible right now)](https://github.com/wasiejen/Free-Snap-Tap?tab=readme-ov-file#example-use-cases-for-aliases-to-show-what-is-possible-right-now) for how it might look like
 
- updated reverse key replacement
  - `#` in front a the key - does nothing to first key, as second key send a release when key pressed and a press when key released
 
- activation of crossover now forces delay to be active (with default settings 2ms and 10 ms in py file)

**V0.7.0**
- fixed a bug due which the key replacement was never send

Some measures to lighten the precision of snap tap to maybe circumvent some Anti Cheat.
- NEW: random delay for snap tap 
  - Start argument `-delay=50` for max delay of 50 ms (can be set in a range of 1-500)
  - Without the start argument no delay will be used
- NEW: crossover of input for snap tap
  - Start argument `-crossover=50` for a probability of 50% (can be set in a range of 0-100)
  - I call "crossover" the act of releasing one key before the press - but just simulated. In a way to simulate a too early release of one key before the press of the actual pressed key (immediate release of last key and delay of pressed key as result). 
  - Same random delay used as defined by -delay="number"
  - Without the start argument no crossover will be used

**V0.6.0**
- NEW: Key Replacements will now be tracked in tap groups
- NEW: Menu option: 7. Print vk_codes to identify keys
  - Will print out the corresponding vk_codes of a key event. Useful for finding your own vk_codes when used with different keyboard_layouts. 
- Added requirements.txt - see #19
- Removed exe from repo and put it into releases: see #19
- Some edits in README.md

**V0.5.1**
- Fixed direct interpretation of number strings, e.g. `1`, `2`, ... as a vk_code. Fixed by first looking up in dict if a string entry for that number exists and if not then cast it as an int an use it directly as a vk_code.

**V0.50**
- Fixed not working -txt= start argument; changed it to: 
  - `-tapfile=` replaces `-txt=`
- NEW: Starting argument for custom key replacement file
  - `-keyfile=`
- NEW: Control for returning to the menu on `PAGE_DOWN` key
- NEW: Mouse Buttons (1: left, 2: right, 4: middle) can now be the output key of a key replacement pair
- NEW: key replacements can now reverse there output
  - declared by just using a `-` before any or both keys in the key pair
  - (e.g. `k, -k` or `-k, -k`  would reverse the press of k to a release and vise versa)
    - originally intended for the right mouse button (looking around) in MMO's 
      - e.g. `k, 2` / `k, mouse_right` to simulate a right mouse click with a keyboard key `k`
      - e.g. `k, -2` then reverses to output and lets me lock the right mouse button on release of key `k`
    - but can also be used for toggling auto movement on and off with another key (e.g. `left_windows, -w`)
- removed implementation parts of the attempt to make it work on Linux
  - most of the functionality was not working due to the Linux limitation of not being able to suppress events

**V0.40**
- NEW: Management of key replacements
    - I had the functionality to suppress keys, so why not replace some.
    - Managed in the same manner as the tap groupings
- Better or more complete error handling in the menu
    - if someone still finds a way to crash the program via the menu, then congratulations :-D
- Linux user will not see the new key replacement options
    - selective key suppression is simply not working on Linux

**V0.37**
- bug fix where program control were not working due to changed key up and down recognition introduced in V0.36
- first Linux test implementation
    - feedback needed - might not work due to still using win32_event_filter, but now without suppression of key events for Linux
 
**V0.36**
- corrected a bug where the ALT key and (ALT GR) changes the msg values for up and down keys (really weird behavior)

**V0.35**
- fixed bug that disabled snap tapping in V0.34

**V0.34**
- added start argument `-nocontrols` to start it without the controls `DEL` and `END` enabled

**V0.32**
- added option to load and save tap groupings to custom files.
  - add `-txt=` followed with filename (e.g. -txt=starcitizen.txt) to the bat file or the link to the execution file
- small edits in py file
- some comments

**V0.31:**
- added small fixes
  - no handling of a single key in multiple tap Groups any more - resulted in strange behavior
- added option to start without menu
  - just ad -nomenu or use prepared bat file to start directly with defined Tap Groupings in tap_groups.txt

**V0.3:**
- Added CLI UI to manage tap groupings.
- `tap_groups.txt` is used to save actual tap groupings, can be edited by hand if needed.

**V0.22:**
- Renamed to Free Snap Tap.

**V0.2:**
- Now special keys like Ctrl, Space, Alt, Win, Numpad keys, F-keys usable in Tap Groups.
- Just use the string representation (found in py_file in vk_codes dict) or directly the vk-codes. Mixing of both in the same Tap Group is possible.
- Added an icon! :-D (icons created by Vector Squad - Flaticon)
