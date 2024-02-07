
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

def anglecalc2(y,z): #Reverse orientation Calculates the angle and signage depending on the quadrant the trough is in 0 deg at noon and 180/-180 at bottom of
    if (y > 0) & (z > 0): #1st quadrant
        ang = (m.degrees(m.atan(y/z)) - 180) #as is, translated to -90 to 0
    if (y > 0) & (z < 0): #2nd quadrant
        ang = (m.degrees(m.atan(y/z))) #as is, translated to 0 to 90
    if (y < 0) & (z < 0): #3rd quadrant
        ang = (m.degrees(m.atan(y/z))) #subtract 180 from value, translated to 90 to 180
    if (y < 0) & (z > 0): #4th quadrant
        ang = (m.degrees(m.atan(y/z)) + 180) #add 180 from value, translated to -180 to -90
    return ang








def interpolater(current_time,wday,yday,isdst,rt): #interpolater function for the SPA data
    for i in range(len(data) - 1): #data refers to the data[] that contains the loaded SPA data into microcontroller's ram
        if data[i]['date_time'] <= current_time <= data[i + 1]['date_time']: #Check if current time is within the range
            # Interpolate the trough angle based on the current date and time 
            date_time_1 = strptime(data[i]['date_time'], "%Y-%m-%d %H:%M:%S", wday,yday,isdst) #strptime is defined function in main.py, it strips a string time format and returns a time struct
            date_time_2 = strptime(data[i + 1]['date_time'], "%Y-%m-%d %H:%M:%S", wday,yday,isdst)
            x1 = time.mktime(date_time_1) #time.mktime creates a unix timestamp from a timestruct, i.e. date_time_1
            x2 = time.mktime(date_time_2) 
            y1 = data[i]['trough_angle'] #Assigns the value of y1 to the ith value of trough_angle
            y2 = data[i + 1]['trough_angle']
            m = (y2 - y1) / (x2 - x1) #Calculates slope for interpolation
            b = y1 - m * x1 #Calculates the y intercept
            x = time.mktime(rt) #converts rt (current time) into unix timestamp
            y = m * x + b #linear formula
            print('x1: {0} x2: {1} y1: {2} y2: {3} m: {4} b: {5} x: {6} y: {7}'.format(x1,x2,y1,y2,m,b,x,y))
            return y #Return the interpolated trough angle
    print('Current time not in range, check the data file\n') #If the current time isnt in range, print 
    return 180

setang = interpolater(current_time,wday,yday,isdst,rt) #Interpolater function call

anglepos = (m.asin((sensorC.acceleration[1] / CW_END))) * (180/m.pi) #Angle measurement using 1 axis, most definitely wrong
accelanglepos = (m.degrees(m.atan((sensorC.acceleration[1]/sensorC.acceleration[2])))) #angle measurement using 2 axes 

#Index the hour from data
    for i in range(dtlength):
        if hours == dt[i]:
            idx = i
    setang = Troughang[idx]

 """
    # Check if it's time to call the receive_file() function again
    if time.monotonic() - last_time >= interval:
        receive_file()
        last_time = time.monotonic()

    # Your main program code goes here
    pass
    """


def strptimeobj(date_string):
    year = int(date_string[0:4])
    month = int(date_string[5:7])
    day = int(date_string[8:10])
    hour = int(date_string[11:13])
    minute = int(date_string[14:16])
    second = int(date_string[17:19])
    #print(year,month,day,hour,minute,second)
    d = date(year,month,day)
    t = time(hour,minute,second)
    tme = dt.combine(d,t)
    return tme


def datafetcher(current_time_obj):
    # open the CSV file
    with open("Sundata2.csv", "r") as f:
        csv_reader = csvreader(f)

        # skip the header row
        next(csv_reader)

        # loop through the rows and find the closest matching date/time
        closest_time = None
        closest_angle = None
        closest_time_diff = None
        for row in csv_reader:
            row_time = strptimeobj(row[1])
            time_diff = current_time_obj - row_time
            if closest_time_diff is None or abs(time_diff.total_seconds()) < abs(closest_time_diff.total_seconds()):
                closest_time = row_time
                closest_angle = float(row[2])
                closest_time_diff = time_diff

        # print the closest trough angle
        if closest_time is not None:
            print("Closest Trough Angle:", closest_angle)
        else:
            print("No matching data found")


def datafetch(data, current_time_obj):
    """Returns the trough angle closest to the current time"""
    closest_time_diff = None
    closest_angle = None
    for row in data:
        print(row[0])
        rowdatetime = strptimeobj(row[1])
        row_time = rowdatetime[0]
        time_diff = row_time - current_time_obj
        if closest_time_diff is None or time_diff < closest_time_diff:
            closest_time_diff = time_diff
            closest_angle = float(row['Trough angle'])
    return closest_angle

def datadict(current_date):
    data = {}
    csv_file = 'Sundata2.csv'
    with open(csv_file, "r") as file:
        reader = csvreader(file)
        next(reader)
        for row in reader:
            row_datetime = row[1] #Keep entire datetime string
            row_date = strptimeobj(row[1])
            row_datestr = str(row_date[0])
            if row_date[1] == current_date:
                #data.append({'date_time':row[1],'trough_angle':float(row[2])}) 
                data[row_datestr] = float(row[2])
    #print(data)
    return data

def datafetch(data, current_time_obj):
    data = {strptimeobj(k): v for k,v in data.items()}

    # Find the closest date/time in the dictionary to the current time
    closest_time = min(data.keys(), key=lambda x: abs(x[0].total_seconds() - current_time_obj.total_seconds()))

    # Retrieve the corresponding trough angle
    closest_angle = data[closest_time]

    return closest_angle

# Initialize analog input connected to photocell.
photocellA = analin(brd.A1)
photocellB = analin(brd.A2)
print('absDIFFERENCE: {0} valA: {1} valB: {2}'.format(absDIFFERENCE, valA, valB))

# Function that converts from analog value to voltage.
def analog_voltage(adc):
    return adc.value / 65535 * adc.reference_voltage

#Photocell assigned
valA = photocellA.value
valB = photocellB.value
voltsA = analog_voltage(photocellA)
voltsB = analog_voltage(photocellB)
Threshold = 300
# Calculate the differences between LDR A and B, if the difference is greater than the threshold then move the motor in the desired direction. Include a timestep after
valdiff = valA - valB
absDIFFERENCE = abs(valdiff)


voltsA = phtcellA.value / 65535 * phtcellA.reference_voltage
voltsB = phtcellB.value / 65535 * phtcellB.reference_voltage

    threshold = 2000 #Needs to be calibrated based on the LDRs
    valA = phtcellA.value
    valB = phtcellB.value
    valdiff = valA - valB
    pdiffA = abs(valdiff)/valA * 100
    pdiffB = abs(valdiff)/valB * 100
print('ValA: {:} ValB: {:} Valdiff: {:} PdiffA: {:.2f}% PdiffB: {:.2f}%'.format(valA,valB,valdiff,pdiffA,pdiffB))
#LDR
    if (pdiffA > 5) | (pdiffB > 5):
        if valdiff > 0:
            print('LDR A is {0:.2f}%% greater than LDR B'.format(pdiffA))
            while abs(valdiff) > threshold:
                valA = phtcellA.value
                valB = phtcellB.value
                valdiff = valA - valB
                print('Valdiff: {:.2f}'.format(valdiff))
                motormovement(1)
            err = 200
        if valdiff < 0:
            print('LDR B is {0:.2f}%% greater than LDR A'.format(pdiffB))
            while abs(valdiff) > threshold:
                valA = phtcellA.value
                valB = phtcellB.value
                valdiff = valA - valB
                print('Valdiff: {:.2f}'.format(valdiff))
                motormovement(0)
            err = 300
        sparesec = 60 - seconds
        print('LDRs are within threshold')
        #print('sleeping for the next {:.2f} seconds'.format(sparesec))
        #tt.sleep(sparesec)
        return err