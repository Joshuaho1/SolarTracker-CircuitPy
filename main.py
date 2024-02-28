import time as tt
import board
import busio
import gc
import math as m
import pwmio
from digitalio import DigitalInOut, Direction
from adafruit_datetime import datetime as dt, date,time
from adafruit_lsm6ds.lsm6ds3 import LSM6DS3
from adafruit_lsm6ds import AccelRange
from adafruit_pcf8523.pcf8523 import PCF8523
from circuitpython_csv import reader as csvreader

def strptimeobj(date_string): #Function that takes a string and converts it into a datetime object
    year = int(date_string[0:4])
    month = int(date_string[5:7])
    day = int(date_string[8:10])
    hour = int(date_string[11:13])
    minute = int(date_string[14:16])
    second = int(date_string[17:19])
    #print(year,month,day,hour,minute,second)
    d = date(year,month,day) #Creates date object using adafruit date
    t = time(hour,minute,second) #Creates time object using adafruit time
    tme = dt.combine(d,t) #Uses the datetime library from adafruit to combine d and t into a datetime object
    return tme

def datadict(current_date): #Creates a dictionary of data using the solar data csv and the current date
    data = {} #Create empty dictionary
    csv_file = 'Huizhou Sundata.csv' #Assigns the csv file name
    with open(csv_file, "r") as file: #Opens CSV file
        reader = csvreader(file) #read CSV
        next(reader) #skip first row because of headers
        for row in reader: #for every row in the CSV
            row_datetime = row[1] #Keep entire datetime string
            row_date = row_datetime.split()[0] #Extract date from datetime string
            if row_date == current_date: #If the date is equal to the current date
                data[row_datetime] = float(row[2]) #Add the datetime and trough angle to the dictionary
    #print(data)
    keys = sorted(data.keys()) #Sort the keys into ascending order of time
    if not data:
        return False, data, keys
    else:
        return True, data, keys 

def datafetch(current_time): #Retrieves the trough angle based on the current time
    """
    Find the value in the dictionary 'data' that corresponds to the closest key to 'current_time'.
    Assumes that the keys in 'data' are sorted in ascending order.
    """
    if current_time <= keys[0]: #Evaluates if current time is less than earliest time in the dictionary
        return data[keys[0]] # If the current time is earlier than the earliest available time, return the earliest value
    if current_time > keys[-1]: #Evaluates if current time is after the latest time in the dictionary
        if current_date != keys[0].split()[0]: #If current date is not equal to the date in the dictionary then
            return 200 #Return 200, a code to tell program to retrieve next day's data
        else:
            return 0 #Safe angle
            return data[keys[-1]] # If the current time is later than the latest available time, return the latest value
    i = 0
    while current_time > keys[i]: #While the current time is greater than the time in the dictionary, increment i by 1
        i += 1
        # print(current_time)
        # print(keys[i])
    if current_time == keys[i]: #If current time is equal to a timestamp (key) in a dictionary
        return data[keys[i]] #Return the value
    else:
        # The closest time is either the key at index i or i-1, depending on which is closer
        bfkey = strptimeobj(keys[i-1]) #converts the i-1 key into a datetime object
        afkey = strptimeobj(keys[i]) #converts the i key into a datetime object
        currtimeobj = strptimeobj(current_time) #converts the current time into a datetime object
        dt1 = currtimeobj - bfkey #calculates the difference between current time and i-1 key time
        dt2 = afkey - currtimeobj #calculates the difference between the i key time and current time
        # print(bfkey) 
        # print(currtimeobj)
        # print(afkey)
        # print(dt1)
        # print(dt2)
        # print(i)
        if dt1 < dt2: #If the time is closer to i-1 key time then
            return data[keys[i-1]] #Return the value of key i-1
        else:
            return data[keys[i]] #Return the value of key i

def anglecalc1(x,y): #Calculates the angle and signage depending on the quadrant the trough is in 0 deg at noon and 180/-180 at bottom of
    if (x > 0) & (y > 0): #1st quadrant
        ang = (m.degrees(m.atan(x/y)) - 90) #as is, translated to -90 to 0
    if (x > 0) & (y < 0): #2nd quadrant
        ang = (m.degrees(m.atan(x/y)) + 90) #as is, translated to 0 to 90
    if (x < 0) & (y < 0): #3rd quadrant
        ang = (m.degrees(m.atan(x/y)) + 90) #subtract 180 from value, translated to 90 to 180
    if (x < 0) & (y > 0): #4th quadrant
        ang = (m.degrees(m.atan(x/y)) - 90) #add 180 from value, translated to -180 to -90
    return ang

class PID(object):
    def __init__(self, Kp , Ki , Kd, T, outputclamp):
        
        # Sampling time
        self.T = T # in seconds rule of thumb is 10x higher than the bandwidth of the system
        
        # Controller gains
        self.Kp, self.Ki, self.Kd = Kp, Ki, Kd

        # Output limits (Used to clamp output)
        self.limMin = -180
        self.limMax = 180

        # Derivative Time Constant (Low pass filter) in seconds
        self.tau = 0.00058

        # Controller "memory" stored values for following iteration
        self.integral = 0
        self.derivative = 0
        self.prev_error = 0
        self.prev_measure = 0

        # Controller output
        self.out = 0

        # Anti windup, Integrator clamp, Output clamp
        self.antiwindup = 1
        self.integratorclamp = 1
        self.outputclamp = outputclamp

    def update(self, setpoint, measurement):
        
        # Error signal
        error = setpoint - measurement

        # Proportional
        proportional = self.Kp * error

        # Integral
        self.integral += + 0.5 * self.Ki * self.T * (error + self.prev_error)

        # Anti Windup
        if self.antiwindup == 1:
            if (self.limMax > proportional):
                intlimMax = self.limMax - proportional
            else:
                intlimMax = 0.0

            if (self.limMin < proportional):
                intlimMin = self.limMin - proportional
            else:
                intlimMin = 0.0

        # Clamp Integrator
        if self.integratorclamp == 1:
            if (self.integral > intlimMax):
                self.integral = intlimMax
            elif (self.integral < intlimMin):
                self.integral = intlimMin

        # Derivative
        self.derivative = (2.0 * self.Kd * (measurement - self.prev_measure) + (2.0 * self.tau - self.T) * self.derivative) / (2.0 * self.tau + self.T) 
        
        # Output
        self.out = proportional + self.integral + self.derivative

        # Output limits
        if self.outputclamp == 1:
            if (self.out > self.limMax):
                self.out = self.limMax
            elif (self.out < self.limMin):
                self.out = self.limMin
        
        # Store error and measurement variables
        self.prev_error = error
        self.prev_measure = measurement

        # Return
        return self.out

#Establish I2C
myI2C = busio.I2C(board.SCL, board.SDA, frequency = 40000)
#myI2C = busio.I2C(board.IO17, board.IO18) 

#RTC initializations
rtc = PCF8523(myI2C)
days = ("Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday")
if False:   # change to True if you want to write the time!
    #                     year, mon, date, hour, min, sec, wday, yday, isdst
    t = tt.struct_time((2024,  1,   12,   12,  55,  5,    5,   12,    -1))
    # you must set year, mon, date, hour, min, sec and weekday
    # weekday: sunday = 0, monday = 1, tuesday = 2, etc
    # yearday is not supported, isdst can be set but we don't do anything with it at this time
    
    print("Setting time to:", t)     # uncomment for debugging
    rtc.datetime = t
    print()

#Dictionary initialization
flag = False

#Accelerometer initializations
sensorC = LSM6DS3(myI2C)
# Accel sensitivity setting
sensorC.accelerometer_range = AccelRange.RANGE_2G
#print("Accelerometer range set to: %d G" % AccelRange.string[sensorC.accelerometer_range])

#PWM initializations
pwm = pwmio.PWMOut(board.D18, frequency= 4000, duty_cycle=0)
direc = DigitalInOut(board.D17)
direc.direction = Direction.OUTPUT
vmax = 65535

#PID controller setup
pid = PID(Kp=70,Ki=10,Kd=20,T=0.00005, outputclamp=1)

while True:    
    #Time and Date
    rt = rtc.datetime #Retrieve date time info from RTC
    #rt = tt.localtime(tt.mktime(rt)) #Convert the datetime into a 
    year = rt.tm_year
    month = rt.tm_mon
    day = rt.tm_mday
    dayofweek = rt.tm_wday
    hours = rt.tm_hour #hours from RTC
    mins = rt.tm_min #mins from RTC
    seconds = rt.tm_sec #seconds from RTC
    current_time = '{:02}-{:02}-{:02} {:02}:{:02}:{:02}'.format(year,month,day,hours,mins,seconds) #Date needs to be in this format for it to access from the dictionary! do not change
    current_date = '{:02}-{:02}-{:02}'.format(year,month,day) # See above line

    if not flag:
        print('Date: %s %d/%02d/%d' % (days[dayofweek], day, month, year))
        print('Time: %02d:%02d:%02d' % (hours, mins, seconds))
        KB = gc.mem_free()/1024
        print('KB available: {0}'.format(KB))
        print('Please wait ~20 seconds, creating Dictionary from CSV data')
        start_time = tt.time()
        bool, data, keys = datadict(current_date)
        if bool:
            elapsed_time = tt.time() - start_time
            print('Elapsed time to create Dictionary: {0} s'.format(elapsed_time))
            gc.collect()
            KB = gc.mem_free()/1024
            print('KB available: {0}'.format(KB))
        else:
            print("Current date is not within range of the CSV data. Quitting")
            break
        flag = True

    #Accelerometer measured angle
    acceleration = sensorC.acceleration
    #print("Acceleration: X:{0:7.2f}, Y:{1:7.2f}, Z:{2:7.2f} m/s^2".format(*acceleration))
    accelanglepos = anglecalc1(sensorC.acceleration[0],sensorC.acceleration[1]) #Returns the angle based on the angelcalc function above (index 0,1,2 for x,y,z)
    tt.sleep(1)

    #SPA Data
    #setang = 0
    setang = datafetch(current_time) #Retrieve the corresponding trough angle given the current time
    if setang == 200: #Special case
        flag = False #Sets the flag = to False, which tells the program to remake the dictionary

    #Angle difference
    angdiff = setang - accelanglepos
    absangdiff = abs(setang - accelanglepos)
    print('Set Angle: {0:.3f} Current Angle: {1:.3f} Angle Difference: {2:.3f}'.format(setang, accelanglepos, angdiff))

    pidout = pid.update(setpoint=setang, measurement=accelanglepos)
    pidoutf = abs(pidout)/180 # Normalize to a range of 0 to 1
    print("PID output: {0:.2f} normalized: {1:.2f}".format(pidout,pidoutf))
    
    if absangdiff > 0.05:
        if angdiff < 0:
            direc.value = False
        else:
            direc.value = True

        # pwm.duty_cycle = max(round(pidoutf * vmax), round(motormin * vmax))
        pwm.duty_cycle = round(pidoutf * vmax)
        print("Duty Cycle: {0:.2f} DIREC.Value: {1}" .format(pidoutf, direc.value))
    
    print("")
    tt.sleep(1)
