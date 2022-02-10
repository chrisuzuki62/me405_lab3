"""!
@file main.py
@brief    Runs the main program and creates all objects to run a desired step response to a specified posiiton.
@details  This program is to be installed and ran on the MicroPython board. It creates the class
          objects motor, controller, and encoder. The program runs a loop until the user types a
          value into the serial port starting the step response test. The motor will run to the desired
          angle which rely on the encoder and controller feedback to control the motor output.

@author Damond Li
@author Chris Or
@author Chris Suzuki
@date   9-Feb-2022 SPL Original file
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
    @brief      Task for motor 1
    @details    This task is responsible for setting the gain and desired position in the controller
                and sets a corresponding duty cycle in the motor driver for motor 1. This task also adds data for
                the encoder and time to their respective queues.
    """
    # Enable motor
    mtr1.enable()
    
    while True:
        # Establish the desired gain and position for motor 1
        ctr1.set_gain(gain1.get())
        ctr1.set_position(des_position1.get())

        # Read encoder data and set duty cycle based on encoder reading
        enc1_read = enc1.read()
        power = ctr1.update(enc1_read)
        mtr1.set_duty_cycle(power)
        
        # Put time 1 data into the queue only if the queue is not full
        if not time1.full():
            time1.put(ctr1.get_time())
        # Put encoder 1 data into the queue only if the queue is not full
        if not encoder1.full():
            encoder1.put(enc1_read)

        yield (0)

def task_motor2 ():
    """!
    @brief      Task for motor 2
    @details    This task is responsible for setting the gain and desired position in the controller
                and sets a corresponding duty cycle in the motor driver for motor 2.
    """
    # Enable motor
    mtr2.enable()
    
    while True:

        # Establish the desired gain and position
        ctr2.set_gain(gain2.get())
        ctr2.set_position(des_position2.get())

        # Read encoder data and set duty cycle based on encoder reading
        power = ctr2.update(enc2.read())
        mtr2.set_duty_cycle(power)
    
        yield (0)

def data_collect ():
    """!
    @brief      Data collection task
    @details    This task is responsible for printing time and encoder data in a specified format to
                pc_com.py to be plotted if there is data in the queue. 
    """
    while True:    
    
        # If data is present in the encoder 1 queue, print data
        if encoder1.any():
            # Print data 
            print(str(time1.get()) + "," + str(encoder1.get()))
        
        yield (0)


# This code creates shares for gain, desired position, and duty cycle and queues for time
# and encoder data. The tasks run for the condition that specifies the time limit set at 2 seconds.
# The tasks begin running with any input. 
if __name__ == "__main__":
    
    print ('\033[2JPress ENTER to begin\r\n'
           '')
        
    # Create shares for gain
    ## A shares object handling the gain for the first controller
    gain1 = task_share.Share ('f', thread_protect = False, name = "Share Gain 1")
    ## A shares object handling the gain for the second controller
    gain2 = task_share.Share ('f', thread_protect = False, name = "Share Gain 2")
    
    # Create shares for desired position
    ## A shares object handling the desired position for the first controller
    des_position1 = task_share.Share ('h', thread_protect = False, name = "Share Position 1")
    ## A shares object handling the desired position for the second controller
    des_position2 = task_share.Share ('h', thread_protect = False, name = "Share Position 2")
    
    # Create queue for encoder reading
    ## A queues object storing the positional data from controller 1
    encoder1 = task_share.Queue('i', 16, thread_protect = False, overwrite = False, name = "Queue Encoder 1")
    
    # Create queue for time data
    ## A queues object storing the time data from controller 1
    time1 = task_share.Queue('i', 16, thread_protect = False, overwrite = False, name = "Queue Time 1")

    # Create shares for duty cycle
    ## A shares object handling the duty cycle for motor 1
    duty_cycle1 = task_share.Share ('h', thread_protect = False, name = "Share PWM 1")
    ## A shares object handling the duty cycle for motor 2
    duty_cycle2 = task_share.Share ('h', thread_protect = False, name = "Share PWM 2")
    
    # Set values for gain for each motor
    gain1.put(0.1)
    gain2.put(0.1)
       
    # Set values for desired position for each motor
    des_position1.put(20000)
    des_position2.put(20000)
    
    # Create motor, encoder, and controller objects
    
    ## Motor object for motor 1
    mtr1 = motor.Motor(1)
    ## Motor object for motor 2
    mtr2 = motor.Motor(2)
    ## Encoder object for encoder 1
    enc1 = encoder.Encoder(1)
    ## Encoder object for encoder 2
    enc2 = encoder.Encoder(2)
    ## Controller object for motor 1 and encoder 1
    ctr1 = controller.Controller()
    ## Controller object for motor 2 and encoder 2
    ctr2 = controller.Controller()

    while True:
        
        # Zero both encoders
        enc1.zero()
        enc2.zero()
        
        # Set gain for motors 1 and 2
        gain1.put(0.1)
        gain2.put(0.1)
        
        # Set desired position for motors 1 and 2
        des_position1.put(20000)
        des_position2.put(20000)
        
        # Wait for an input through the serial port
        input()
        
        # Establish the initial reference time
        start_time = utime.ticks_ms()
        
        # Create task objects for the motor tasks and data collection task and set the period.
        # Establishes the tasks for cooperatively scheduled tasks in a multitasking system using cotask.py
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

        # Run the scheduler with the chosen scheduling algorithm. Quit if 2 seconds is reached
        vcp = pyb.USB_VCP ()
        
        # Runs the step response for 2 seconds
        while utime.ticks_diff(utime.ticks_ms(), start_time)/1000 < 2:
            cotask.task_list.pri_sched ()
        
        # Disable motors at end of run
        mtr1.disable()
        mtr2.disable()

        # Empty the comm port buffer of the character(s) just pressed
        vcp.read ()
        
        # Clear time and encoder queues at completion of run
        time1.clear()
        encoder1.clear()
        
        # Resets the number of runs in the controller 
        ctr1.zero_runs()
        ctr2.zero_runs()
        
        # Printing 'DATA' indicates that the data collection has been completed
        print("DATA")
