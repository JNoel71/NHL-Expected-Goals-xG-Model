import pandas as pd
from sklearn.metrics import log_loss, roc_auc_score
import matplotlib.pyplot as plt
import seaborn as sns

def calculateLLAUC(df,strength):
    """Calculate the log loss and auc given a dataframe and strength.

    Parameters:
        df - the dataframe containing the data.
        strength - the strength to calculate (0 == even strength, 1 == power play, -1 == shot handed, None == all strengths)

    Returns:
        logLoss - the log loss achieved.
        auc - the auc achieved.
    """

    #control for strengths
    if strength == 0:
        df = df[df['Strength'] == 0]
    elif strength == 1:
        df = df[df['Strength'] > 0]
    elif strength == -1:
        df = df[df['Strength'] < 0]

    #get the predicted and actual outcomes
    xG = df['xG']
    goals = df['Outcome']

    #calculate log loss and auc
    logLoss = log_loss(goals,xG)
    auc = roc_auc_score(goals,xG)

    return logLoss, auc

def benchmarkPersonalModel():
    """Benchmark xG data and output the results to the terminal."""
    #read in data
    df = pd.read_csv("xG Data/xGData2010-2021.csv")
    
    #set train and test sets
    dfTrain = df[df['Season'] <= 2020]
    dfTest = df[df['Season'] == 2021]

    #benchmark training data
    logLossTrainTotal, aucTrainTotal = calculateLLAUC(dfTrain,None)
    logLossTrainEV, aucTrainEV = calculateLLAUC(dfTrain,0)
    logLossTrainPP, aucTrainPP = calculateLLAUC(dfTrain,1)
    logLossTrainSH, aucTrainSH = calculateLLAUC(dfTrain,-1)

    print("Total Train Log Loss: " + str(logLossTrainTotal))
    print("Total Train AUC: " + str(aucTrainTotal))
    print("")

    print("EV Train Log Loss: " + str(logLossTrainEV))
    print("EV Train AUC: " + str(aucTrainEV))
    print("")

    print("PP Train Log Loss: " + str(logLossTrainPP))
    print("PP Train AUC: " + str(aucTrainPP))
    print("")

    print("SH Train Log Loss: " + str(logLossTrainSH))
    print("SH Train AUC: " + str(aucTrainSH))
    print("")

    #benchmark testing data
    logLossTestTotal, aucTestTotal = calculateLLAUC(dfTest,None)
    logLossTestEV, aucTestEV = calculateLLAUC(dfTest,0)
    logLossTestPP, aucTestPP = calculateLLAUC(dfTest,1)
    logLossTestSH, aucTestSH = calculateLLAUC(dfTest,-1)

    print("Total Test Log Loss: " + str(logLossTestTotal))
    print("Total Test AUC: " + str(aucTestTotal))
    print("")

    print("EV Test Log Loss: " + str(logLossTestEV))
    print("EV Test AUC: " + str(aucTestEV))
    print("")

    print("PP Test Log Loss: " + str(logLossTestPP))
    print("PP Test AUC: " + str(aucTestPP))
    print("")

    print("SH Test Log Loss: " + str(logLossTestSH))
    print("SH Test AUC: " + str(aucTestSH))
    print("")

def plotModel():
    """Plots model performance season-over-season using log loss and auc."""
    #read in the xG data
    df = pd.read_csv("xG Data/xGData2010-2021.csv")

    #get unique seasons and sort them
    seasons = list(df['Season'].unique())
    seasons.sort()

    #where log loss and auc performance will be stored
    llSeasonTotal = []
    aucSeasonTotal = []
    llSeasonEV = []
    aucSeasonEV = []
    llSeasonPP = []
    aucSeasonPP = []
    llSeasonSH = []
    aucSeasonSH = []

    #iterate over each season
    for i in seasons:
        #get shot estimates for the given season
        seasonDf = df[df['Season'] == i]

        #get total log loss and auc
        logLossTotal, aucTotal = calculateLLAUC(seasonDf,None)
        llSeasonTotal.append(logLossTotal)
        aucSeasonTotal.append(aucTotal)

        #calculate even strength log loss and auc
        logLossEV, aucEV = calculateLLAUC(seasonDf,0)
        llSeasonEV.append(logLossEV)
        aucSeasonEV.append(aucEV)

        #calculate power play log loss and auc
        logLossPP, aucPP = calculateLLAUC(seasonDf,1)
        llSeasonPP.append(logLossPP)
        aucSeasonPP.append(aucPP)

        #calculate shot handed log loss and auc
        logLossSH, aucSH = calculateLLAUC(seasonDf,-1)
        llSeasonSH.append(logLossSH)
        aucSeasonSH.append(aucSH)

    #create figure and subplots
    fig, (ax1, ax2) = plt.subplots(1,2)
    fig.suptitle('xG Performance over Time',fontsize = 20)
    fig.set_size_inches(16,8)

    #color palette
    colors = sns.color_palette("tab10", 4).as_hex()

    #plot AUC
    ax1.plot(seasons,aucSeasonTotal,label='Total',color=colors[0])
    ax1.plot(seasons,aucSeasonEV,label='Even Strength',color=colors[1])
    ax1.plot(seasons,aucSeasonPP,label='Power Play',color=colors[2])
    ax1.plot(seasons,aucSeasonSH,label='Penalty Kill',color=colors[3])
    ax1.set_title("AUC Performance",fontsize = 15)
    ax1.set_xlabel("Season")
    ax1.set_ylabel("AUC (Higher is better)")
    ax1.grid(color = 'grey', linestyle = '--', axis = 'y')

    #plot log loss
    ax2.plot(seasons,llSeasonTotal,label='Total',color=colors[0])
    ax2.plot(seasons,llSeasonEV,label='Even Strength',color=colors[1])
    ax2.plot(seasons,llSeasonPP,label='Power Play',color=colors[2])
    ax2.plot(seasons,llSeasonSH,label='Penalty Kill',color=colors[3])
    ax2.set_title("Log Loss Performance",fontsize = 15)
    ax2.set_xlabel("Season")
    ax2.set_ylabel("Log Loss (Lower is better)")
    ax2.grid(color = 'grey', linestyle = '--', axis = 'y')

    #plot legend
    handles, labels = ax1.get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper right')

    #save and show the figure
    plt.savefig("Plots/performance.png")
    plt.show()
   

benchmarkPersonalModel()
plotModel()