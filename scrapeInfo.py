import requests
import json
import pandas as pd

#read the shotData
shotData = pd.read_csv("Raw Data/shotData/NHLShotData2010-2021.csv")

#where dataframe rows will be stored
player_info = []

#iterate through the shotData shooter IDs
for ID in shotData['shooter'].unique():

    #is the ID is missing continue
    if pd.isna(ID):
        continue
    else:
        #make sure the id is a string
        player_id = str(int(float(ID)))

    #ensure player id is a string
    player_id = str(int(float(ID)))
    
    #get player info
    data = requests.get(f'https://api-web.nhle.com/v1/player/{player_id}/landing')
    
    #if successful
    if data.status_code == 200:
        #load the json
        jsonFile = json.loads(data.text)
        
        #extract information on handedness and position
        shoots_catches = jsonFile.get('shootsCatches', None)
        position = jsonFile.get('position', None)
        
        #add info to the list
        player_info.append([player_id, shoots_catches, position])

        print(f"Successfully retrieved data for player {player_id}")
    else:
        #handle the case where the API request failed
        print(f"Failed to retrieve data for player {player_id}")

#create and save the dataframe as a csv
df = pd.DataFrame(player_info, columns=['player_ID', 'shootsCatches', 'position'])
df.to_csv("Raw Data/info/NHLInfo.csv", index=False)


