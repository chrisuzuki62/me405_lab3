"""!
@file main.py
@brief    Runs the main program and creates all objects to rotate the motor the to desired angle  
@details  This program is to be installed and ran on the MicroPython board. It creates the class
          objects motor, controller, and encoder. The program runs a loop until the user types a
          value into the serial port starting the step response test. The motor will run to the desired
          angle which rely on the encoder and controller feedback to control the motor output.

@author Damond Li
@author Chris Or
@author Chris Suzuki
@date   27-Jan-2022 SPL Original file
@copyright (c) 2015-2021 by JR Ridgely and released under the GNU
    Public License, Version 2. 
"""

import gc
import pyb
import cotask
import task_share
import motor
import controller
import encoder
import utime
import struct
import time

def task_motor1 ():
    """!
    
    """
    # Enable motor
    mtr1.enable()
    
    while True:

        # Establish the desired gain and position
        ctr1.set_gain(gain1.get())
        ctr1.set_position(des_position1.get())

        # Run the controller every 10ms
        power = ctr1.update(enc1.read())
        mtr1.set_duty_cycle(power)

        yield (0)

def task_motor2 ():
    """!
    
    """
    # Enable motor
    mtr2.enable()
    
    while True:

        # Establish the desired gain and position
        ctr2.set_gain(gain2.get())
        ctr2.set_position(des_position2.get())

        # Run the controller every 10ms
        power = ctr2.update(enc2.read())
        mtr2.set_duty_cycle(power)
    
        yield (0)

def data_collect ():
    """!
    
    """
    while True:
        if encoder1.any():
            print(encoder1.get())
        
        yield (0)


# This code creates a share, a queue, and two tasks, then starts the tasks. The
# tasks run until somebody presses ENTER, at which time the scheduler stops and
# printouts show diagnostic information about the tasks, share, and queue.
if __name__ == "__main__":
    print ('\033[2JTesting ME405 stuff in cotask.py and task_share.py\r\n'
           'Press ENTER to stop and show diagnostics.')
    
    # Create a share and a queue to test function and diagnostic printouts
    gain1 = task_share.Share ('f', thread_protect = False, name = "Share Gain 1")
    gain2 = task_share.Share ('f', thread_protect = False, name = "Share Gain 2")
    
    des_position1 = task_share.Share ('h', thread_protect = False, name = "Share Position 1")
    des_position2 = task_share.Share ('h', thread_protect = False, name = "Share Position 2")
    
    encoder1 = task_share.Queue('i', 16, thread_protect = False, overwrite = False, name = "Queue Encoder 1")
    encoder2 = task_share.Queue('i', 16, thread_protect = False, overwrite = False, name = "Queue Encoder 2")

    duty_cycle1 = task_share.Share ('h', thread_protect = False, name = "Share PWM 1")
    duty_cycle2 = task_share.Share ('h', thread_protect = False, name = "Share PWM 2")
    
    gain1.put(0.1)
    gain2.put(0.1)
        
    des_position1.put(20000)
    des_position2.put(20000)
    
    # Create motor, encoder, and controller objects
    mtr1 = motor.Motor(1)
    mtr2 = motor.Motor(2)
    enc1 = encoder.Encoder(1)
    enc2 = encoder.Encoder(2)
    ctr1 = controller.Controller(encoder1)
    ctr2 = controller.Controller(encoder2)
    
    # Zero encoders
    enc1.zero()
    enc2.zero()

    # Create the tasks. If trace is enabled for any task, memory will be
    # allocated for state transition tracing, and the application will run out
    # of memory after a while and quit. Therefore, use tracing only for 
    # debugging and set trace to False when it's not needed
    task1 = cotask.Task (task_motor1, name = 'Motor 1 Task', priority = 1, 
                         period = 10, profile = True, trace = False)
    task2 = cotask.Task (task_motor2, name = 'Motor 2 Task', priority = 1, 
                         period = 10, profile = True, trace = False)
    task3 = cotask.Task (data_collect, name = 'Data Collect Task', priority = 0,
                         period = 10, profile = True, trace = False)
    cotask.task_list.append (task1)
    cotask.task_list.append (task2)
    cotask.task_list.append (task3)

    # Run the memory garbage collector to ensure memory is as defragmented as
    # possible before the real-time scheduler is started
    gc.collect ()

    # Run the scheduler with the chosen scheduling algorithm. Quit if any 
    # character is received through the serial port
    vcp = pyb.USB_VCP ()
    while not vcp.any ():
        cotask.task_list.pri_sched ()
        
    mtr1.disable()
    mtr2.disable()

    # Empty the comm port buffer of the character(s) just pressed
    vcp.read ()

    # Print a table of task data and a table of shared information data
#     print ('\n' + str (cotask.task_list))
#     print (task_share.show_all ())
#     print (task1.get_trace ())
#     print ('\r\n')
