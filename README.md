# Solar Tracker for Microcontroller in CircuitPython
#### Video Demo:  <https://youtu.be/7qAp7ESOeI4>
#### Description: This project's goal was to create code that allows a microcontroller to track the position of the sun over a period of time and then control a device's movement to track the sun's position at the same time.

## Overview
This project covers using a microcontroller to actuate a device to track the movement of the Sun. There are several files required for this project which are listed below:
- SPA downloader.py - Script that downloads Solar Position Data from NREL's SPA Calculator
- main.py - Code used by the microcontroller to interface with the sensors and motor

If everything is working accordingly, you should have a device that can track the path of the sun at any location on Earth.

The physical setup of this requires the following components:
- Microcontroller
- Accelerometer
- Motor
- Motor Driver

Optional to the setup:
- Light Detection Resistors (For additional feedback on position of the device)

The software setup utilizes the following languages:
- Python (Used for connecting to the Solar Position Algorithm)
- CircuitPython (Subset of Python tailored for microcontrollers)

## SPA downloader.py - Retrieving Solar Position Data
In general, this script connects to the [National Renewable Energy Laboratory's (NREL) Solar Positioning Algorithm (SPA) Calculator](https://midcdmz.nrel.gov/solpos/spa.html), inputs the specific parameters to the user's desired location, and then downloads the data to a csv file specified by the user.

I chose to connect to the NREL SPA Calculator API rather than recreate the calculation from scratch for a number of reasons. Firstly, the calculation of the zenith and azimuth angle are very techinical. They invovle a large number of parameters and an extensive number of equations in order to achieve high accuracy and precision data. I thought it was more efficient to utilize the work already done by NREL to achieve a better outcome.

Firstly, the user is required to provide a multitude of values for various parameters. The most notable values include longitude, latitude, and the timezone of the desired location. The script takes these parameters and builds a url with them as this is how NREL's SPA calculator's API is accessed. The script then saves the response from the website to a pandas dataframe to be processed.

The processing of the file involves calculating the device angle. This is the optimal angle that the device will rotate to at a given time to match the sun's trajectory. This is done in the following code:
```
# Calculations for Trough Angle
Sx = np.tan(np.deg2rad(np.abs(90 - df['Topocentric zenith angle']))) #calculate the X term of atan2
Sy = np.sin(np.deg2rad(df['Top. azimuth angle (eastward from N)'])) #calculate the Y term of atan2
df['Trough angle'] = 90 - np.rad2deg(np.arctan2(Sx, Sy)) #Create a new column name Trough angle
```
`np` is used here as a shortcut for the `numpy` library in python. Subsequently, the date and time need to be processed because we only need data for when the sun is overhead. This is done through finding the corresponding time of the sunrise and sunset and then adding all the angle values between those times to a new dataframe. This is the code that processes the data:
```
for date in unique_dates: #Loops through all dates within unique_dates
    sunrise = df.loc[df['Date (M/D/YYYY)'] == date, 'Local sunrise time'].iloc[0] #Retrieves sunrise time based on the unique date, the first value in the sunrise column
    sunset = df.loc[df['Date (M/D/YYYY)'] == date, 'Local sunset time'].iloc[0] #Retreieves sunset time based on the unique date, the first value in the sunset column
    sunriset, adjsunrise = fracconv(sunrise) #Converts from fractional hour to string format sunrise time and adjusted sunrise time
    sunsett, adjsunset = fracconv(sunset) #Converts from fractional hour to string format sunset time and adjusted sunset time
    adjsunrise_datetime = pd.to_datetime(date + ' ' + adjsunrise, format='%m/%d/%Y %H:%M:%S') #Converts from string format to datetime object
    adjsunset_datetime = pd.to_datetime(date + ' ' + adjsunset, format='%m/%d/%Y %H:%M:%S') #Converts from string format to datetime object
    df1 = df[df['Date (M/D/YYYY)'] == date] #Filters for that specific date's rows
    df1 = df1[(df1['Date (YYYY-MM-DD) Time (HH:MM:SS)'] >= adjsunrise_datetime) & (df1['Date (YYYY-MM-DD) Time (HH:MM:SS)'] <= adjsunset_datetime)] #Compares and filters the data based on the adjsunrise_datetime and adjsunset_datetime objects
    result = pd.concat([result,df1], ignore_index=True) #Compile the filtered data into a new dataframe
```
There is a function called `francconv(t)` which accepts fractional hour as an input and converts it to a string format of time. This is needed to match the date time format that the microcontroller will use to retrieve the correct angle. The function returns both the sunrise/sunset times as well as an adjusted time- set 10 minutes before sunrise or 10 minutes after sunset. The purpose of the adjusted time was to ensure the complete capture of any sun exposure. The dataframe is then filtered to only include values that come just before sunrise and just after sunset.

Once the data processing is complete, the results are stored in a new dataframe and then saved to a CSV file. It then needs to be moved to the microcontroller's storage so that it can be accessed.

## Main.py - Microcontroller
This program is what the microcontroller uses to retrieve the data, store the data, and actuate the motor to drive the device. Firstly, `main.py` requires an additional CircuitPython library not included in the standard package. To get the code working, you will need to download and install the `adafruit_lsm6ds` library on your board. This library is catered for use with the accelerometer. This program is also designed to be used with a DC stepper motor. For use with a DC motor, please refer to the PID.py section

The structure of `main.py` in essence is a `while True:` loop and with the proper intializations prior to the loop. Much of the functionality has been abstracted into several functions which are intialized in the file as well. This was to keep the `while True:` loop as simple as possible and make it easier to access certain functions.

There are a number of initializations that need to be established before the `while True:` loop can run. The I2C needs to be established so that the microcontroller board can connect to the accelerometer. The accelerometer also needs to be calibrated so that it can determine the angle accordingly. The LDRs (if being used) need their analog inputs to be set. The stepper motor also needs the pins to be intialized accordingly. Lastly, some threshold and constant values need to be defined before the loop begins.

Functions initialized prior to the `while True:` loop:

`strptimeobj(date_string)` is a function that takes a datetime string object and converts it into a datetime object. It does this by first separating the various characters within the datetime string object into their respective parts (eg. year, month, day, hour, etc.). Subsequently it combines them into two different objects, a date and a time object from the `adafruit_datetime` library. The function then returns a single date time object combining both the date and time.

`datadict(current_date)` is a function that creates a dictionary from the csv data on the microcontroller's storage. The function initializes an empty dictionary and then opens the corresponding file with the data from the SPA calculator. This iterates over each row in the CSV and checks if the date matches the current date of the day. If it does, the datetime and device angle are added to the dictionary.

`datafetch(current_time)` is a function that retrieves the corresponding device angle for the current time. It checks if the current time is earlier than the earliest entry or later than the latest entry and returns outcomes for both of those situations. Then it loops over the keys in the dictionary, as these are the timestamps for which there are device angles. If the current time is greater than the time in the current key, it increments the loop counter by one until the closest time is reached. If the current time is exactly equal to the time in the key of the dictionary, then the device angle is returned. If not (which is often the case as the data is by the minute), then a linear interpolation is performed between the upper and lower bound and that result is returned.

`motormovement(dir)` is a function specifically for the stepper motor. It accepts a boolean input, if `dir` is equal to one, it tells the motor to move in the clockwise direction (when facing the motor). This is done by setting the motor pin values to `True` and then turning them off to `False` in ascending order from pin 1 to pin 4. What this does is it energizes the magnet inside of the stepper motor thereby rotating the rotor of the motor. Alternatively if `dir` is equal to zero, the pins are energized in descending order rotating the motor counterclockwise. There is probably a better way to energize the pins and iterate over them but I have not figured out a better way to do this yet.

`anglecalc(y,z)` is a function that calculates the angle and signage of the angle from the accelerometer readings. Since the accelerometer measures gravity in x, y, and z directions, it has to be processed in order to obtain an "angle measurement". This is done by taking the inverse tangent function of the y and z gravitational measurements and converting it to degrees. Note that this method is orientation specific, if the accelerometer is mounted differently, you may need to use the x and y or x and z directions instead. Some further processing needs to be done because instead of a 360 degree field of rotation, the desired range is -180 to 180. This is so that the zero angle means the device would be facing normal to the ground. The final value returned is an angle measurement in degrees.

`rotmotor(angdiff, degstep)` is a function that helps accelerate the motor rotation. Since the previous motor movement function only loops over the motor pins once, this function improves upon that. The function receives two inputs, `angdiff` and `degstep`. `angdiff` refers to the difference between the measured angled and the desired angle, which is determined in the `while True:` loop. `degstep` refers to the degree angle change per one call of `motormovement`. This is a numerical value that is determined empirically, although there is probably a method to calculate this precisely. Thus, if `angdiff` is greater than 10 then the function calculates a number of counts by dividing `angdiff` by `degstep`. Then the function calls `motormovement` through a for loop for that number of counts. If `angdiff` is less than `allowerr` (the allowable error threshold), then it only calls `motormovement` once.

`LDR()` is a function for the operation of the Light Detection Resistors. The LDR's work by comparing a voltage between the two LDRs. If there is a significant voltage difference (a voltage above a set threshold) between the two LDRs, then the function will call `motormovement`. The `LDR()` function will continually check the difference between the two until the voltage difference is below the set threshold. Physically, when the voltage reading is similar between the LDRs, then both LDRs would be exposed to the same conditions. Ideally that means they are both under the same exposure of light. Note that this relies on a physical setup tailored for sun tracking. For example, placing a wall between the two LDR so that one LDR can be shaded when the device is not normal to the sunray trajectories. [LDR Photovoltaic Solar Tracker](https://www.instructables.com/LDR-Photovoltaic-Solar-Tracker/) is a good resource for more information.

As for the `while True:` loop, it first retrieves the time and date from the clock onboard the microcontroller. It then builds the `current_time` and `current_date` datetime objects used in the prior functions. Then the loop checks if `flag` is False. If it is, then it does the following:

```
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
```

This section creates the dictionary from which the microcontroller retrieves date, time, and angle data from. `flag` is set to True at the end of it so that upon subsequent iterations of the `while True` loop, it is not called. This section also calls the `datadict(current_date)` function to build the dictionary.

Following the completion of the dictionary, the current angle position is calculated for the device. This is done through calling the `anglecalc(y,z)` function. Then the desired angle is retrieved using the `datafetch(current_time)` function. `angdiff` is calculated between the desired angle and the current position and the result is printed to the terminal window. `rotmotor(angdiff, degstep)` is then called so the motor is actuated. Lastly, the `LDR()` function is called for the final method of control for the device.
