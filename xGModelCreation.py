import pandas as pd
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split, KFold
from lightgbm import LGBMClassifier
import optuna
import optuna.integration.lightgbm as lgb
from sklearn.metrics import log_loss, roc_auc_score
from lightgbm import early_stopping
from lightgbm import log_evaluation

def tuning(df):
    """Tune the LGBM model with optuna.

    Parameters:
        df - the dataframe of shots.

    Returns:
        bestParams - the best hyperparameters found by the tuner.
    """
    #separate X and y
    newXDF = df.loc[:,df.columns != 'Outcome']
    newYDF = df['Outcome'].astype('int32')
    
    #set dataset for lightGBM in optuna
    dtrain = lgb.Dataset(newXDF, label=newYDF)

    #set basic parameters
    params = {
        "objective": "binary",
        "metric": "binary_logloss",
        "verbosity": -1,
        "boosting_type": "gbdt",
        "deterministic":True
    }

    #create the tuner
    tuner = lgb.LightGBMTunerCV(
        params,
        dtrain,
        folds=StratifiedKFold(n_splits=10),
        callbacks=[early_stopping(150), log_evaluation(150)],
        optuna_seed = 0,
        show_progress_bar = False
    )

    #run the tuner
    tuner.run()

    #print the best score and the best parameters found
    print("Best score:", tuner.best_score)
    bestParams = tuner.best_params
    print("Best params:", bestParams)
    print("  Params: ")
    for key, value in bestParams.items():
        print("    {}: {}".format(key, value))
    
    return bestParams

def cvPredict(classifier,df):
    """Predict shot outcomes with cross validation.

    Parameters:
        classifier - the model to be used in prediction.
        df - the dataframe of shots.

    Returns:
        ypred - the predictions for each shot.
    """
    #separate X and y
    x = df.loc[:,df.columns != 'Outcome']
    y = df['Outcome'].astype('int32')

    #use stratified cross validation to predict values
    kf = StratifiedKFold(n_splits=10)
    ypred = cross_val_predict(classifier,x,y,cv=kf,method='predict_proba')

    return ypred

def encodeStrength(strength):
    """Encode team strength as an integer.

    Parameters:
        strength - the string representing the strength of the team shooting.

    Returns:
        st - the integer representing the team strength (players for minus players against).
    """
    #split strength string and subtract values
    numbers = strength.split("v")
    st = int(numbers[0]) - int(numbers[1])
    return st

def encodeSpecialStrengths(strength):
    """Encode less common team strengths.

    Parameters:
        strength - the string representing the strength of the team shooting.

    Returns:
        code - the integer representing the special strength.
    """
    #default code is zero
    code = 0

    #set code based off strength
    if strength == '3v3':
        code = 1
    elif strength == '4v4':
        code = 2
    elif strength == '6v5':
        code = 3
    elif strength == '4v3':
        code = 4
    elif strength == '3v4':
        code = 5
    elif strength == '6v4':
        code = 6
    
    return code

def main():
    """Main method which handles reading in shot data, defining a model, and outputing the results."""
    #read in data and get training years of 2010-2020
    trainingFrame = pd.read_csv("Raw Data/shotData/NHLShotData2010-2021VenueAdjusted.csv")
    trainingFrame = trainingFrame[(trainingFrame['Season'] <= 2020)]

    #drop shots without locations, shots on empty nets, and penalty shots
    trainingFrame = trainingFrame.dropna(subset=['x','y'])
    trainingFrame = trainingFrame[trainingFrame['isEmptyNet'] == 0]
    trainingFrame = trainingFrame[trainingFrame['isPenaltyShot'] == 0]

    #encode special strengths and strengths as integers
    trainingFrame['specialStrength'] = trainingFrame['Strength'].apply(encodeSpecialStrengths)
    trainingFrame['Strength'] = trainingFrame['Strength'].apply(encodeStrength)

    #store all columns in a writing frame
    writingFrame = trainingFrame
    
    #drop unneeded columns
    trainingFrame = trainingFrame.drop(['GameID','Team','oppTeam','shooter','goalie','isEmptyNet','isPenaltyShot',
        'P1For','P2For','P3For','P4For','P5For','P6For','P1Against','P2Against','P3Against','P4Against','P5Against',
        'P6Against','AwayPlayers','HomePlayers','AwayShot','AwayTeam','Arena','Date','Event',
        'rebound','fastbreak','Season','isPlayoffs','isHome'],axis=1)
    
    #reset indices
    trainingFrame = trainingFrame.reset_index(drop=True)

    #tune hyperparameters
    #params = tuning(trainingFrame)

    #the parameters chosen by the tuner 2010-2020
    params = {'objective': 'binary', 'metric': 'binary_logloss', 'verbosity': -1, 'boosting_type': 'gbdt', 'deterministic': True, 'feature_pre_filter': False, 'lambda_l1': 9.329199279226517, 'lambda_l2': 3.539645667371331e-08, 'num_leaves': 99, 'feature_fraction': 0.5479999999999999, 'bagging_fraction': 1.0, 'bagging_freq': 0, 'min_child_samples': 5}

    #params = {'objective': 'binary', 'metric': 'binary_logloss', 'verbosity': -1, 'boosting_type': 'gbdt', 'deterministic': True, 'feature_pre_filter': False, 'lambda_l1': 9.329199279226517, 'lambda_l2': 3.539645667371331e-08, 'num_leaves': 56, 'feature_fraction': 0.4, 'bagging_fraction': 1.0, 'bagging_freq': 0, 'min_child_samples': 100}

    #use cross-validation to get xG values for all shots
    proba = cvPredict(LGBMClassifier(**params),trainingFrame)

    #benchmark performance
    print("Writing Results:")
    print("Log Loss: " + str(log_loss(writingFrame['Outcome'],proba)))
    print("AUC: " + str(roc_auc_score(writingFrame['Outcome'],proba[:,1])))

    #add xG values to a writing frame
    writingFrame = writingFrame.assign(xG = proba[:, 1])

    #read in the testing frame, set season to 2021, get rid of empty net and penalty shots
    testingFrame = pd.read_csv("Raw Data/shotData/NHLShotData2010-2021VenueAdjusted.csv")
    testingFrame = testingFrame[testingFrame['Season'] == 2021]
    testingFrame = testingFrame[testingFrame['isEmptyNet'] == 0]
    testingFrame = testingFrame[testingFrame['isPenaltyShot'] == 0]

    #drop shots with no locations
    testingFrame = testingFrame.dropna(subset=['x','y'])

    #encode special strengths and strengths as integers
    testingFrame['specialStrength'] = testingFrame['Strength'].apply(encodeSpecialStrengths)
    testingFrame['Strength'] = testingFrame['Strength'].apply(encodeStrength)

    #store all columns in a writing frame
    testWritingFrame = testingFrame

    #drop unneeded columns
    testingFrame = testingFrame.drop(['GameID','Team','oppTeam','shooter','goalie','isEmptyNet','isPenaltyShot',
        'P1For','P2For','P3For','P4For','P5For','P6For','P1Against','P2Against','P3Against','P4Against','P5Against',
        'P6Against','AwayPlayers','HomePlayers','AwayShot','AwayTeam','Arena','Date','Event',
        'rebound','fastbreak','Season','isPlayoffs','isHome'],axis=1)
    
    #separate X and y for training
    trainX = trainingFrame.loc[:,trainingFrame.columns != 'Outcome']
    trainY = trainingFrame['Outcome'].astype('int32')

    #get test X
    testX = testingFrame.loc[:,testingFrame.columns != 'Outcome']

    #set parameters and fit model
    classifier = LGBMClassifier(**params)
    classifier.fit(trainX,trainY)

    #predict outcomes
    preds = classifier.predict_proba(testX)

    #use the writing frame to output results
    testWritingFrame = testWritingFrame.assign(xG = preds[:, 1])
    writingFrame = pd.concat([writingFrame,testWritingFrame])
    writingFrame.to_csv("xG Data/xGData2010-2021.csv",index=False)


main()


