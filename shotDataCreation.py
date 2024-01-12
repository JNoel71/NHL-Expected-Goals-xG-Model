import pandas as pd
import numpy as np
from math import degrees, atan

def createTrainingFrame(lst):
    """Create a dataframe from a list of csv file names.

    Parameters:
        lst(list) - a list of strings which correspond to the files the frame will be comprised of.

    Returns:
        trainingFrame - a dataframe with all information from the games.
    """

    #read in the csv
    season = pd.read_csv(lst)

    #note playoff games
    season['isPlayoffs'] = season.apply(lambda x: 1 if x['Game_Id'] >= 30000  else 0, axis = 1)

    #create a unique Game_Id by adding the year the game took place to the current Game_Id string
    seasonString = i[21:25]
    season['season'] = seasonString
    season['Game_Id'] = seasonString + season['Game_Id'].astype(str)
    season = season.iloc[:,1:] #remove the index column

    #concatenate the frame together then sort by the Game_Id
    trainingFrame = season
    trainingFrame['Game_Id'] = trainingFrame['Game_Id'].astype(int)
    trainingFrame['season'] = trainingFrame['season'].astype(int)

    return trainingFrame

def standardizeLoc(x,y):
    """Standardize the X and Y locations to the right side of the rink.

    Parameters:
        x - the original x location.
        y - the original y location.
    
    Returns:
        x - the standardized x location.
        y - the standardized y location.
    """
    #Only change location if event takes place on left side of rink
    if x < 0:
        x = abs(x)
        y = -y

    return x,y

def standarizeX(row):
    """Standardize the X coordinate of a shot to the right side of the rink.

    Parameters:
        row - the entire row of the dataframe for the shot.
    
    Returns:
        x - the standardized coordinate
    """
    x = row['xC']
    zone = row['Ev_Zone']

    if zone == 'Def':
        if x > 0:
            x = -x
    elif zone == 'Neu':
        pass
    else:
        if x < 0:
            x = abs(x)
    
    return x

def standarizeY(row):
    """Standardize the Y coordinate of a shot to the right side of the rink.

    Parameters:
        row - the entire row of the dataframe for the shot.
    
    Returns:
        y - the standardized coordinate
    """
    x = row['xC']
    y = row['yC']
    zone = row['Ev_Zone']

    if zone == 'Def':
        if x > 0:
            x = -y
    elif zone == 'Neu':
        pass
    else:
        if x < 0:
            y = -y
    
    return y

def calculateDist(x1,y1,x2,y2):
    """Calculate the distance from one location to another.

    Parameters:
        x1 - the x coordinate of the first location.
        y1 - the y coordinate of the first location.
        x2 - the x coordinate of the second location.
        y2 - the y coordinate of the second location.
    
    Returns:
        d - distance between the two locations.
    """
    #calculate the distance from the net
    d = (((x2-x1)**2) + ((y2-y1)**2))**(1/2)

    return d

def calculateAngle(x1,y1,x2,y2):
    """Calculate the angle diffence from one location to another.

    Parameters:
        x1 - the x coordinate of the first location.
        y1 - the y coordinate of the first location.
        x2 - the x coordinate of the second location.
        y2 - the y coordinate of the second location.
    
    Returns:
        a - the angle between the two locations.
    """
    #instances where x is the same for both locations result in no angle change.
    if (x2-x1) != 0:
        a = degrees(atan((y2-y1)/(x2-x1)))
    else:
        a = 0

    return a

def checkRebound(x,y,team,time,angle,prevEv,prevTeam,prevTime,prevX,prevY):
    """Determine if a shot attempt was a rebound.

    Parameters:
        x - the x coordinate of the event.
        y - the y coordinate of the event.
        team - the team the event is associated with.
        time - the time of the event.
        angle - the angle of the event in relation to the net.
        prevEv - the type of the previous event.
        prevTeam - the team associated with the previous event.
        prevTime - the time of the previous event.
        prevX - the x coordinate of the previous event.
        prevY - the y coordinate of the previous event.
    
    Returns:
        rebound - was the shot attempt a rebound.
        angleDiff - the difference in angle between the shot attempts.
        distDiff - the difference in distance between the shot attempts.
        speed - the speed between the two events.
    """

    #if the previous event was a shot that followed another shot attempt in the last 3 seconds
    if (prevEv == 'SHOT') and (abs(prevTime-time) <= 3) and (prevTeam == team):

        #set rebound flag to 1
        rebound = 1

        #get the angle of the previous shot and distance between the 2 separate shot attempts.
        prevAngle = calculateAngle(prevX,prevY,89,0)
        distDiff = calculateDist(x,y,prevX,prevY)

        #account for divide by zero errors
        if abs(prevTime - time) == 0:
            speed = distDiff
        else:
            speed = distDiff/(abs(prevTime-time))

        #determine angle difference
        angleDiff = abs(angle-prevAngle)
    else:
        #set all variables to zero  or nan if shot attempt is not a rebound
        rebound = 0
        angleDiff = np.nan
        distDiff = np.nan
        speed = np.nan
    
    return rebound, angleDiff, distDiff, speed

def checkFastbreak(x,y,team,time,prevTeam,prevTime,prevX,prevY,prevZone):
    """Determine if a shot attempt was on a fastbreak.

    Parameters:
        x - the x coordinate of the event.
        y - the y coordinate of the event.
        team - the team the event is associated with.
        time - the time of the event.
        angle - the angle of the event in relation to the net.
        prevTeam - the team associated with the previous event.
        prevTime - the time of the previous event.
        prevX - the x coordinate of the previous event.
        prevY - the y coordinate of the previous event.
        prevZone - the zone of the previous event.

    Returns:
        fastbreak - was the shot attempt on a fast break.
        speed - the speed between the previous event and the shot attempt.
    """
    #get relative previous zone
    zone = getRelativeZone(team,prevTeam,prevZone)

    #determine if event is a fastbreak
    if (((zone == 'Def') and (abs(prevTime-time) <= 5)) or ((zone == 'Neu') and (abs(prevTime-time) <= 3))):

        #set flag and calculate distance
        fastbreak = 1
        distDiff = calculateDist(x,y,prevX,prevY)

        #account for divide by zero errors
        if abs(prevTime - time) == 0:
            speed = distDiff
        else:
            speed = distDiff/(abs(prevTime-time))
    else:
        #set flags to zero and nan if not a fastbreak
        fastbreak = 0
        distDiff = np.nan
        speed = np.nan
    
    return fastbreak, distDiff, speed

def encodeStrength(st,team,homeTeam):
    """Encode the strength variable relative to the event team.

    Parameters:
        st - the strength string.
        team - the event team.
        homeTeam - the home team.

    Returns:
        strength - the adjusted strength variable.
    """

    #get strength relative to event team
    if team == homeTeam:
        strength = st[0] + "v" + st[2]
    else:
        strength = st[2] + "v" + st[0]
    
    return strength

def getRelativeZone(currentTeam,lastTeam,lastZone):
    """Calculate the relative zone of a past event.

    Parameters:
        currentTeam - the team the current event is associated with.
        lastTeam - the team the previous event is associated with.
        lastZone - the recorded zone of the previous event.

    Returns:
        lastZone - the zone of the previous event relative to the current team.
    """
    #get relative zone
    if currentTeam == lastTeam:
        pass
    else:
        if lastZone == "Neu":
            pass

        elif lastZone == "Off":
            lastZone = "Def"

        elif lastZone == "Def":
            lastZone = "Off"

        else:
            lastZone = "None"
    
    return lastZone
    
def main(files):
    """Create all shot data from pbp data."""
    #the columns to be stored
    cols = ['GameID','Date','Season','isPlayoffs','isEmptyNet','isPenaltyShot','isStrongSide','Event','x','y','Team','oppTeam','Strength','isHome','GameTime','PeriodTime','Distance','Angle','ShotType',
            'GoalDiff','LastEvent','LastEventDistance','LastEventZone','LastEventAngle','LastEventSpeed','TimeSinceLastEvent',
            'rebound', 'reboundAngDiff', 'reboundDistDiff', 'reboundSpeed','fastbreak','fastbreakDistance','fastbreakSpeed','goalie','shooter',
            'P1For','P2For','P3For','P4For','P5For','P6For','P1Against','P2Against','P3Against','P4Against','P5Against',
            'P6Against','AwayPlayers','HomePlayers','Outcome']

    #create the dataframe from the input csv'
    trainingFiles = files
    
    #create the full training frame
    trainingFrame = createTrainingFrame(trainingFiles)
    trainingFrame['Date'] = pd.to_datetime(trainingFrame['Date'],format='%Y-%m-%d')
    trainingFrame = trainingFrame.replace('PHX','ARI')
    playerFrame = pd.read_csv("Raw Data/info/NHLInfo.csv")

    #standardize x and y
    trainingFrame["xS"] = trainingFrame.apply(standarizeX,axis=1)
    trainingFrame["yS"] = trainingFrame.apply(standarizeY,axis=1)
    
    #list that holds dictionaries to be turned into dataframe
    rowList = []

    #use iterframe to speed up iteration
    iterTrainingFrame = trainingFrame
    iterTrainingFrame = iterTrainingFrame.reset_index(drop=True)
    iterShotFrame = iterTrainingFrame[((iterTrainingFrame['Event'] == 'SHOT') |
                                        (iterTrainingFrame['Event'] == 'GOAL') |
                                        (iterTrainingFrame['Event'] == 'MISS'))]
    
    #create empty net variable
    iterShotFrame['isEmptyNet'] = iterShotFrame.apply(lambda x: 1 if ((x['Ev_Team'] == x['Home_Team']) and (pd.isnull(x['Away_Goalie']))) or 
                                                             ((x['Ev_Team'] == x['Away_Team']) and (pd.isnull(x['Home_Goalie'])))
                                                          else 0, axis = 1)

    #iterate through all games
    for row in iterShotFrame.itertuples():
        #store the row containing info about the last event
        index = row.Index
        lastIndex = index - 1
        lastEvent = iterTrainingFrame.iloc[[index - 1]]
        
        #do not include shootouts
        if (row.isPlayoffs == 0) and (row.Period > 4):
            continue

        #Identify Penalty Shots
        if 'Penalty Shot' in row.Description:
            penaltyShot = 1
        else:
            penaltyShot = 0

        #collect basic info on the event
        gameID = row.Game_Id
        season = str(row.Game_Id)[0:4]
        playoffs = row.isPlayoffs
        emptyNet = row.isEmptyNet
        event = row.Event
        team = row.Ev_Team
        time = row.Seconds_Elapsed
        period = row.Period
        date = row.Date
        strength = encodeStrength(row.Strength,team,row.Home_Team)

        #calculate the current time played
        gameTime = time + ((period-1)*1200)

        #get info on the last event
        lastEventType = lastEvent['Event'].values[0]

        #account for delayed penalties missing coordinates
        if lastEventType == 'DELPEN':
            lastEvent = trainingFrame.iloc[[index - 2]]

        #get info about last event
        lastEventTeam = lastEvent['Ev_Team'].values[0]
        lastEventX = lastEvent['xC'].values[0]
        lastEventY = lastEvent['yC'].values[0]
        lastEventStandardX = lastEvent['xS'].values[0]
        lastEventStandardY = lastEvent['yS'].values[0]
        lastEventZone = lastEvent['Ev_Zone'].values[0]
        lastEventPeriod = lastEvent['Period'].values[0]
        lastEventTime = lastEvent['Seconds_Elapsed'].values[0]
        
        #get time difference between events
        if period == lastEventPeriod:
            timeSinceLastEvent = abs(time - lastEventTime)
        else:
            timeSinceLastEvent = 1200

        #get relative zone
        lastEventZone = getRelativeZone(team,lastEventTeam,lastEventZone)

        #determine opposing team:
        if team == row.Home_Team:
            oppTeam = row.Away_Team
        else:
            oppTeam = row.Home_Team
            
        #basic shot data
        x = row.xS
        y = row.yS
        distance = calculateDist(x,y,89,0)
        distanceDiffLastEvent = calculateDist(row.xC,row.yC,lastEventX,lastEventY)
        angle = calculateAngle(x,y,89,0)
        angleDiffLastEvent = calculateAngle(lastEventX,lastEventY,row.xC,row.yC)

        #account for divide by zero errors
        if timeSinceLastEvent == 0:
            speedDiff = distanceDiffLastEvent
        else:
            speedDiff = distanceDiffLastEvent/timeSinceLastEvent

        #get player info
        player = playerFrame[playerFrame['id'] == row.p1_ID]
        hand = player['shootsCatches'].values
        
        #determine if shot was on dominate side
        if len(hand) == 0:
            strongSide = np.nan 
        elif hand[0] == 'R':
            if y >= 0:
                strongSide = 1
            else:
                strongSide = 0
        elif hand[0] == 'L':
            if y <= 0:
                strongSide = 1
            else:
                strongSide = 0

        #determine shot type
        shotType = row.Type

        #get the needed frame
        gameFrame = iterTrainingFrame[(iterTrainingFrame['Game_Id'] == gameID) & (iterTrainingFrame['Period'] == row.Period)]
        
        #account for events that take place before period start
        if lastIndex not in gameFrame.index:
            rebound = np.nan
            reboundAngDiff = np.nan
            reboundDistDiff = np.nan
            reboundSpeed = np.nan
            
            fastbreak = np.nan
            fastbreakDistance = np.nan
            fastbreakSpeed = np.nan
        else:
            #check for rebound shots
            rebound, reboundAngDiff, reboundDistDiff, reboundSpeed = checkRebound(x,y,
                                                                                team,
                                                                                row.Seconds_Elapsed,
                                                                                angle,
                                                                                lastEventType,
                                                                                lastEventTeam,
                                                                                lastEventTime,
                                                                                lastEventStandardX,
                                                                                lastEventStandardY)

            #check for fastbreaks
            fastbreak, fastbreakDistance, fastbreakSpeed = checkFastbreak(row.xC,row.yC,
                                                    team,
                                                    row.Seconds_Elapsed,
                                                    lastEventTeam,
                                                    lastEventTime,
                                                    lastEventX,
                                                    lastEventY,
                                                    lastEventZone)

        #collect score
        homeScore = row.Home_Score
        awayScore = row.Away_Score

        #assign score for and against
        if team == row.Home_Team:
            scoreFor = homeScore
            scoreAgainst = awayScore
            home = 1
            goalie = row.Home_Goalie_Id
        else:
            scoreFor = awayScore
            scoreAgainst = homeScore
            home = 0
            goalie = row.Away_Goalie_Id

        #determine shooter and each individual player on the ice
        shooter = row.p1_ID
        if home:
            p1For = row.homePlayer1_id
            p2For = row.homePlayer2_id
            p3For = row.homePlayer3_id
            p4For = row.homePlayer4_id
            p5For = row.homePlayer5_id
            p6For = row.homePlayer5_id

            p1Against = row.awayPlayer1_id
            p2Against = row.awayPlayer2_id
            p3Against = row.awayPlayer3_id
            p4Against = row.awayPlayer4_id
            p5Against = row.awayPlayer5_id
            p6Against = row.awayPlayer5_id
        else:
            p1For = row.awayPlayer1_id
            p2For = row.awayPlayer2_id
            p3For = row.awayPlayer3_id
            p4For = row.awayPlayer4_id
            p5For = row.awayPlayer5_id
            p6For = row.awayPlayer5_id

            p1Against = row.homePlayer1_id
            p2Against = row.homePlayer2_id
            p3Against = row.homePlayer3_id
            p4Against = row.homePlayer4_id
            p5Against = row.homePlayer5_id
            p6Against = row.homePlayer5_id

        #count number of players on the ice
        awayPlayers = row.Away_Players
        homePlayers = row.Home_Players
        
        #calculate score differential
        scoreDiff = scoreFor - scoreAgainst

        #add all data
        data = [gameID,
                date,
                season,
                playoffs,
                emptyNet,
                penaltyShot,
                strongSide,
                event,
                x,
                y,
                team,
                oppTeam,
                strength,
                home,
                gameTime,
                time,
                distance,
                angle,
                shotType,
                scoreDiff,
                lastEventType,
                distanceDiffLastEvent,
                lastEventZone,
                angleDiffLastEvent,
                speedDiff,
                timeSinceLastEvent,
                rebound, 
                reboundAngDiff, 
                reboundDistDiff, 
                reboundSpeed,
                fastbreak, 
                fastbreakDistance,
                fastbreakSpeed,
                goalie,
                shooter,
                p1For,
                p2For,
                p3For,
                p4For,
                p5For,
                p6For,
                p1Against,
                p2Against,
                p3Against,
                p4Against,
                p5Against,
                p6Against,
                awayPlayers,
                homePlayers]

        #determine outcome of the shot
        if event == 'GOAL':
            data.append(1)
        else:
            data.append(0)

        d = dict(zip(cols,data))
        rowList.append(d)
        
        print(gameID)

    finalDF = pd.DataFrame.from_dict(rowList)
    finalDF.to_csv("Raw Data/shotData/NHLShotData"+str(files[21:25])+".csv",index=False)


#the files to be used for creation
files = ["Raw Data/pbp/nhl_pbp_20102011.csv",
        "Raw Data/pbp/nhl_pbp_20112012.csv",
        "Raw Data/pbp/nhl_pbp_20122013.csv",
        "Raw Data/pbp/nhl_pbp_20132014.csv",
        "Raw Data/pbp/nhl_pbp_20142015.csv",
        "Raw Data/pbp/nhl_pbp_20152016.csv",
        "Raw Data/pbp/nhl_pbp_20162017.csv",
        "Raw Data/pbp/nhl_pbp_20172018.csv",
        "Raw Data/pbp/nhl_pbp_20182019.csv",
        "Raw Data/pbp/nhl_pbp_20192020.csv",
        "Raw Data/pbp/nhl_pbp_20202021.csv",
        "Raw Data/pbp/nhl_pbp_20212022.csv"]


#create file for each year 
for i in files:  
    main(i)

#created training files
train = ["NHLShotData2010.csv","NHLShotData2011.csv","NHLShotData2012.csv","NHLShotData2013.csv","NHLShotData2014.csv",
        "NHLShotData2015.csv","NHLShotData2016.csv","NHLShotData2017.csv","NHLShotData2018.csv",
        "NHLShotData2019.csv","NHLShotData2020.csv","NHLShotData2021.csv"]

#create a joined file 
trainingFrame = pd.DataFrame()
for i in train:
    data = pd.read_csv("Raw Data/shotData/"+i, index_col=False)
    trainingFrame = pd.concat([data,trainingFrame],axis=0)

trainingFrame.to_csv("Raw Data/shotData/NHLShotData2010-2021.csv",index=False)
