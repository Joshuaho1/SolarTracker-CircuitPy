
import time as tt
import board as brd
import math as m
from busio import I2C
from adafruit_datetime import datetime as dt, date,time
from circuitpython_csv import reader as csvreader
from adafruit_pcf8523 import PCF8523
from adafruit_lsm6ds.lsm6ds3 import LSM6DS3
from adafruit_lsm6ds import AccelRange
from digitalio import DigitalInOut,Direction
from analogio import AnalogIn as analin
import gc

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

def datadict(current_date): #Creates a dictionary of data using the Sundata2.csv and the current date
    data = {} #Create empty dictionary
    csv_file = 'Sundata2.csv' #Assigns the csv file name
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
            return -110 #Safe angle
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

def motormovement(dir): # Motor movement depending on if cw is true or false, j defines number of steps
    for j in range(1):
        #Turns rotor clockwise (when looking at rotor)
        if dir== 1:
            INI1.value = True
            tt.sleep(TimeOn)
            INI1.value = False
            tt.sleep(TimeDelay)

            INI2.value = True
            tt.sleep(TimeOn)
            INI2.value = False
            tt.sleep(TimeDelay)

            INI3.value = True
            tt.sleep(TimeOn)
            INI3.value = False
            tt.sleep(TimeDelay)

            INI4.value = True
            tt.sleep(TimeOn)
            INI4.value = False
            tt.sleep(TimeDelay)
            print("CW, Step", j)

        #Turns rotor counter-clockwise (when looking at rotor)
        elif dir==0:
            INI4.value = True
            tt.sleep(TimeOn)
            INI4.value = False
            tt.sleep(TimeDelay)

            INI3.value = True
            tt.sleep(TimeOn)
            INI3.value = False
            tt.sleep(TimeDelay)

            INI2.value = True
            tt.sleep(TimeOn)
            INI2.value = False
            tt.sleep(TimeDelay)

            INI1.value = True
            tt.sleep(TimeOn)
            INI1.value = False
            tt.sleep(TimeDelay)
            print("CCW, Step", j)
    dir = 2

def anglecalc(y,z): #Calculates the angle and signage depending on the quadrant the trough is in 0 deg at noon and 180/-180 at bottom of
    if (y > 0) & (z > 0): #1st quadrant
        ang = (m.degrees(m.atan(y/z))) #as is, translated to -90 to 0
    if (y < 0) & (z > 0): #2nd quadrant
        ang = (m.degrees(m.atan(y/z))) #as is, translated to 0 to 90
    if (y < 0) & (z < 0): #3rd quadrant
        ang = (m.degrees(m.atan(y/z)) - 180) #subtract 180 from value, translated to 90 to 180
    if (y > 0) & (z < 0): #4th quadrant
        ang = (m.degrees(m.atan(y/z)) + 180) #add 180 from value, translated to -180 to -90
    return ang

def rotmotor(angdiff, degstep): #Motor rotation with speed up section
    if abs(angdiff) > 10:
        stepn = m.floor(abs(angdiff/degstep))
        print(stepn)
        if angdiff < 0:
            for i in range(stepn):
                motormovement(1)
            tt.sleep(Timestep)
        else:
            for i in range(stepn):
                motormovement(0)
            tt.sleep(Timestep)
    else:
        if abs(angdiff) > allowerr:
            if angdiff < 0:
                motormovement(1)
                tt.sleep(Timestep)
            else:
                motormovement(0)
                tt.sleep(Timestep)

def LDR(): #LDR functionality as feedback
    #Photocell assigned
    volthreshold = 0.165 #0.15 is 4.5% of 3.3V 0.165 is 5% of 3.3V
    voltsA = phtcellA.value / 65535 * phtcellA.reference_voltage
    voltsB = phtcellB.value / 65535 * phtcellB.reference_voltage
    voldiff = voltsA - voltsB    
    print('VoltsA: {:.3f} VoltsB: {:.3f} Voldiff: {:.3f}'.format(voltsA,voltsB,voldiff))
    if abs(voldiff) > volthreshold:
        if voltsA > voltsB:
            print('WARNING: Voltage A greater than Voltage B by {:.2f}%'.format(abs(voldiff)*100/voltsB))
            while abs(voldiff) > volthreshold:
                accelanglepos = anglecalc(sensorC.acceleration[1],sensorC.acceleration[2])
                voltsA = phtcellA.value / 65535 * phtcellA.reference_voltage
                voltsB = phtcellB.value / 65535 * phtcellB.reference_voltage
                voldiff = voltsA - voltsB
                if (setang + 0.25) > accelanglepos > (setang - 0.25):
                    motormovement(1)
                else:
                    break
            return 200
        if voltsB > voltsA:
            print('WARNING: Voltage B greater than Voltage A by {:.2f}%'.format(abs(voldiff)*100/voltsA))
            while abs(voldiff) > volthreshold:
                accelanglepos = anglecalc(sensorC.acceleration[1],sensorC.acceleration[2])
                voltsA = phtcellA.value / 65535 * phtcellA.reference_voltage
                voltsB = phtcellB.value / 65535 * phtcellB.reference_voltage
                voldiff = voltsA - voltsB
                if (setang + 0.25) > accelanglepos > (setang - 0.25):
                    motormovement(0)
                else:
                    break
            return 300
    return 0

#Establish I2C
myI2C = I2C(brd.SCL, brd.SDA) 

#RTC initializations
rtc = PCF8523(myI2C)
days = ("Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday")
if False:   # change to True if you want to write the time!
    #                     year, mon, date, hour, min, sec, wday, yday, isdst
    t = tt.struct_time((2023,  4,   20,   15,  2,  5,    5,   55,    -1))
    # you must set year, mon, date, hour, min, sec and weekday
    # weekday: sunday = 0, monday = 1, tuesday = 2, etc
    # yearday is not supported, isdst can be set but we don't do anything with it at this time
    
    print("Setting time to:", t)     # uncomment for debugging
    rtc.datetime = t
    print()

#Accelerometer initializations
sensorC = LSM6DS3(myI2C)
# Accel sensitivity setting
sensorC.accelerometer_range = AccelRange.RANGE_2G
#print("Accelerometer range set to: %d G" % AccelRange.string[sensorC.accelerometer_range])

# Initialize analog input connected to photocell.
phtcellA = analin(brd.A1)
phtcellB = analin(brd.A2)

# Accelerometer calibration values
CW_END = 9.81
CCW_END = -9.81
Center = 0

#Setting rotation speed for motormovement()
TimeOn = 0.005
TimeDelay = 0.005

#Motor initializations
# Setting pin and output direction for motors
INI1= DigitalInOut(brd.D10)
INI1.direction = Direction.OUTPUT
INI2 = DigitalInOut(brd.D11)
INI2.direction = Direction.OUTPUT
INI3 = DigitalInOut(brd.D12)
INI3.direction = Direction.OUTPUT
INI4 = DigitalInOut(brd.D13)
INI4.direction = Direction.OUTPUT

#Dictionary initialization
flag = False

#Threshold values
allowerr = 0.15 #degree
degstep = 0.65 #degree per turn of the motor
Timestep = 0.1 
slphour = 3600
#Sleep = tt.sleep(slphour)

while True:
    #Time and Date
    rt = rtc.datetime #Retrieve date time info from RTC
    rt = tt.localtime(tt.mktime(rt)) #Convert the datetime into a 
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
    accelanglepos = anglecalc(sensorC.acceleration[1],sensorC.acceleration[2]) #Returns the angle based on the angelcalc function above
    #print('X: {0} Y: {1} Z: {2}'.format(sensorC.acceleration[0],sensorC.acceleration[1],sensorC.acceleration[2]))

    #SPA Data
    setang = datafetch(current_time) #Retrieve the corresponding trough angle given the current time
    if setang == 200: #Special case
        flag = False #Sets the flag = to False, which tells the program to remake the dictionary
    gc.collect()

    #Calculate difference in set angle and measured angle, then move the motor
    angdiff = setang - accelanglepos
    print('Set Angle: {0:.3f} Current Angle: {1:.3f} Angle Difference: {2:.3f}'.format(setang, accelanglepos, angdiff))
    rotmotor(angdiff, degstep)
    print(current_time)

    #LDR
    # if angdiff <= allowerr:
    #     ildr = LDR()
    
    gc.collect()
    tt.sleep(2) 

