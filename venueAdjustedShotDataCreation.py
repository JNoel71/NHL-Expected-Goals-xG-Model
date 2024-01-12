import pandas as pd
from NHLArenaAdjuster import CoordinateAdjuster

def adjustDist(df):
    """Adjust shot distance using Ken Krzywicki's approach.

    Parameters:
        df - the dataframe of all shots.

    Returns:
        df - the updated dataframe.
    """

    #get all teams
    teams = dict.fromkeys(df.Team.unique(),0)

    #get average distance for both shots for and against at each stadium
    for i in df.Team.unique():
        avg = df[((df['Team'] == i) & (df['isHome'] == 1)) |
                 ((df['oppTeam'] == i) & (df['isHome'] == 0))]['Distance'].mean()
        teams[i] = avg

    #subtract average distance in stadium from distance
    df['adj'] = df.apply(lambda row: (row['Distance'] - teams[row['Team']]) if row['isHome'] == 1 else (row['Distance'] - teams[row['oppTeam']]), axis=1)
    
    return df

def adjustY(df):
    """Adjust Y coordinate using Ken Krzywicki's approach.

    Parameters:
        df - the dataframe of all shots.

    Returns:
        df - the updated dataframe.
    """
    
    #get all teams
    teams = dict.fromkeys(df.Team.unique(),0)

    #get average y for both shots for and against at each stadium
    for i in df.Team.unique():
        avg = df[((df['Team'] == i) & (df['isHome'] == 1)) |
                 ((df['oppTeam'] == i) & (df['isHome'] == 0))]['y'].mean()
        teams[i] = avg

    #subtract average y in stadium from y
    df['Yadj'] = df.apply(lambda row: (row['y'] - teams[row['Team']]) if row['isHome'] == 1 else (row['y'] - teams[row['oppTeam']]), axis=1)
    
    return df

def adjustX(df):
    """Adjust X coordinate using Ken Krzywicki's approach.

    Parameters:
        df - the dataframe of all shots.

    Returns:
        df - the updated dataframe.
    """

    #get all teams
    teams = dict.fromkeys(df.Team.unique(),0)

    #get average x for both shots for and against at each stadium
    for i in df.Team.unique():
        avg = df[((df['Team'] == i) & (df['isHome'] == 1)) |
                 ((df['oppTeam'] == i) & (df['isHome'] == 0))]['x'].mean()
        teams[i] = avg

    #subtract average x in stadium from x
    df['Xadj'] = df.apply(lambda row: (row['x'] - teams[row['Team']]) if row['isHome'] == 1 else (row['x'] - teams[row['oppTeam']]), axis=1)
    
    return df

def adjustShots(df):
    """Adjust Distances with the use of Shucker's and Curro's method.

    Parameters:
        df - the dataframe of all shots.

    Returns:
        shots - the adjusted shot coordinates.
    """

    #create arena, awayTeam, and awayshot features
    df['Arena'] = df.apply(lambda row: (row['Team']) if row['isHome'] == 1 else (row['oppTeam']), axis=1)
    df['AwayTeam'] = df.apply(lambda row: row['Team'] if row['isHome'] == 0 else row['oppTeam'], axis=1)
    df['AwayShot'] = df.apply(lambda row: False if row['isHome'] == 1 else True, axis=1)

    #adjust the coordinates
    ca = CoordinateAdjuster()
    df = df[['x','y','Arena','AwayTeam','AwayShot']]
    shots = ca.fit_transform(df)

    return shots
 
def main():
    """Read in shot data and venue adjust the coordinates and distance."""
    #Read in the data
    trainingFrame = pd.read_csv("Raw Data/shotData/NHLShotData2010-2021.csv")
    trainingFrame['Date'] = pd.to_datetime(trainingFrame['Date'],format='%Y-%m-%d')
    trainingFrame = trainingFrame.sort_values(by=['Date'])

    #do not include shots on empty nets or penalty shots
    trainingFrame = trainingFrame[trainingFrame['isEmptyNet'] == 0]
    trainingFrame = trainingFrame[trainingFrame['isPenaltyShot'] == 0]
    
    #encodings to be used in variables
    variableEncoding = {"ShotType":{"WRIST SHOT":1, "SNAP SHOT":2,"SLAP SHOT":3,"BACKHAND":4,"TIP-IN":5,"WRAP-AROUND":6,"DEFLECTED":7},
                        "LastEvent":{"HIT":1,"GIVE":2,"SHOT":3,"TAKE":4,"FAC":5,"MISS":6,"CHL":7,"BLOCK": 8,"GOAL":9,"PENL":10,
                        "PSTR":11,"STOP":12,"EISTR":13,"GEND":14,"PEND":15,"DELPEN":16},
                        "LastEventZone":{"None":0,"Off":1,"Def":2,"Neu":3}}
    
    #encode variables
    trainingFrame = trainingFrame.replace(variableEncoding)

    #drop NA
    trainingFrame = trainingFrame.dropna(subset=['x','y'])

    #adjust with Shucker's and Curro's method
    adjusted = adjustShots(trainingFrame)
    trainingFrame['AdjX'] = adjusted['xCord'].values
    trainingFrame['AdjY'] = adjusted['yCord'].values
    trainingFrame['AdjDist'] = trainingFrame.apply(lambda row: (((row['AdjX']-89)**2) + ((row['AdjY']-0)**2))**(1/2), axis=1)

    #adjust with Krzywicki's method
    trainingFrame = adjustDist(trainingFrame)
    trainingFrame = adjustX(trainingFrame)
    trainingFrame = adjustY(trainingFrame)

    trainingFrame.to_csv("Raw Data/shotData/NHLShotData2010-2021VenueAdjusted.csv",index=False)

main()
