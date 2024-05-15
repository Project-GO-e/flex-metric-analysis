from calendar import month_name
from collections import namedtuple
from typing import List

import numpy as np
import pandas as pd
from scipy import stats

CONFIG_DIR = 'data/SJV-PV-GM-input/'
GM_TYPE_FILE = 'GM-types GO-e.xlsx'
BUURT_FILE = 'buurt.xlsx'
SUNRISE_SUNSET_FILE = 'sunset-sunrise.csv'

GmContext = namedtuple("Context", "day_type month_idx, gm_type")

def readGM(filename): 
    return pd.read_excel(filename, header=0)


def find_zeroindex(distr_, distr_power_range, power_delta): 
    zeroindex = int(-distr_power_range[0]/power_delta)

    if zeroindex < 0 : zeroindex = 0

    return zeroindex


def normalize(d_, delta):
    return d_/(d_.sum()*delta)


def get_expectation_value(distribution, pr_min, pr_max, pdelta):
    sum = 0
    weight = 0 # distributions in this code are not necessarily normalized

    for i in range(0, distribution.size):
        sum += distribution[i] * (pr_min + i * pdelta)
        weight += distribution[i]

    return sum/weight


def get_daily_sjv_expectation_values(sjv_type, df, day_type, month) -> List[float]:
    expectation_values = []
    for i in range(1,97):
        expectation_values.append(get_single_SJV_Expectation_value(sjv_type, df, (day_type, month, i)))
    return expectation_values


def get_daily_pv_expectation_values(pv_type, df, sunrise_set, day_type, month) -> List[float]:
    return list(map(lambda x: get_single_PV_Expectaction_Value(pv_type, df, sunrise_set, GmContext(day_type, month, x), 1), range(1, 97)))
    # expectation_values = []
    # for i in range(1, 97):
    #     expectation_values.append(get_single_PV_Expectaction_Value(pv_type, df, (day_type, month, i),1))
    # return expectation_values


def get_single_SJV_Expectation_value(SJV_Type, df, context):
    dagtype = context[0]
    maand = context[1]
    kwartier = context[2]

    power_delta_ = 0.1
    # note: range below is specific for the SJV types.. adapt with care... the power_delta (see below) should match exactly with all ranges
    power_range = np.array([-6.0, 6.0, 121])
    
    gmrange = np.linspace(power_range[0],power_range[1],int(power_range[2]))

    GMparms = df.loc[df['Name'] == SJV_Type]

    gm_average = GMparms["Average[1]"]

    gm_average = gm_average / 0.98

    gm_std = GMparms["Deviation[1]"]

    distribution1 = stats.norm(loc = gm_average , scale=gm_std)

    # as per ph2ph, power is limited to max (average+3*std) over all 4 GM in case of sjv GMtype
    powermax = gm_average.values[0]+3*gm_std.values[0]

    #retrieve the daytype and monthly scale factors, for specified quarter and scale the PDF
    scale1 = GMparms[dagtype+"[1,"+str(kwartier)+"]"].values[0]
    scalem1 = GMparms["Month[1,"+str(maand)+"]"].values[0]

    distribution1_pdf = distribution1.pdf(gmrange)
    
    distribution1_pdf = normalize(distribution1_pdf, power_delta_)*scale1*scalem1
    
    distributionsum = distribution1_pdf.copy()

    # and do this for the other three distributions to create the mixture
    gm_average = GMparms["Average[2]"]

    gm_average = gm_average / 0.98

    gm_std = GMparms["Deviation[2]"]
    limit = gm_average.values[0]+3*gm_std.values[0]
    if limit> powermax : powermax = limit

    distribution2 = stats.norm(loc = gm_average, scale=gm_std)

    gm_average = GMparms["Average[3]"]

    gm_average = gm_average / 0.98

    gm_std = GMparms["Deviation[3]"]
    limit = gm_average.values[0]+3*gm_std.values[0]
    if limit > powermax : powermax = limit

    distribution3 = stats.norm(loc = gm_average, scale=gm_std)

    gm_average = GMparms["Average[4]"]

    gm_average = gm_average / 0.98

    gm_std = GMparms["Deviation[4]"]
    limit = gm_average.values[0]+3*gm_std.values[0]
    if limit > powermax : powermax = limit

    distribution4 = stats.norm(loc = gm_average, scale=gm_std)
        
    scale2 = GMparms[dagtype+"[2,"+str(kwartier)+"]"].values[0]
    scale3 = GMparms[dagtype+"[3,"+str(kwartier)+"]"].values[0]
    scale4 = GMparms[dagtype+"[4,"+str(kwartier)+"]"].values[0]

    scalem2 = GMparms["Month[2,"+str(maand)+"]"].values[0]
    scalem3 = GMparms["Month[3,"+str(maand)+"]"].values[0]
    scalem4 = GMparms["Month[4,"+str(maand)+"]"].values[0]

    distribution2_pdf = distribution2.pdf(gmrange)
    distribution2_pdf = normalize(distribution2_pdf, power_delta_)*scale2*scalem2
    distribution3_pdf = distribution3.pdf(gmrange)
    distribution3_pdf = normalize(distribution3_pdf, power_delta_)*scale3*scalem3
    distribution4_pdf = distribution4.pdf(gmrange)
    distribution4_pdf = normalize(distribution4_pdf, power_delta_)*scale4*scalem4


    distributionsum = distributionsum + distribution2_pdf + distribution3_pdf + distribution4_pdf

    zeroindex = int(power_range[0]*power_range[2]/(power_range[0]-power_range[1]))

    if powermax < power_range[1] : # set powermax limit   
        for i in range(int( (powermax*power_range[2] / (power_range[1]-power_range[0])))+zeroindex, distributionsum.size) : 
            distributionsum[i] = 0

    # set negative powers to zero
    for i in range(0,zeroindex) : 
        distributionsum[i] = 0    

    distributionsum = normalize (distributionsum, power_delta_)

    expection_value = get_expectation_value(distributionsum, power_range[0], power_range[1], power_delta_)

    return expection_value

def get_single_PV_Expectaction_Value(GMname, df, sunrise_set, context, installed_power_):
    dagtype = context[0]
    maand = context[1]
    kwartier = context[2]

    pdelta = 0.1
    # note: range below is specific for the SJV types.. adapt with care... the power_delta (see below) should match exactly with all ranges
    power_range = np.array([-6.0, 6.0, 121])

    # since PV has 100% correlation, if there would be more nodes, 
    # than all powers should be multiplied by the numner of nodes, 
    # but we are interested in just a single one, so nodes = 1
    nodes = 1

    max_power = 0   #kW
    installed_power = installed_power_ * nodes #kW

    GMparms = df.loc[df['Name'] == GMname]

    pv_power_range = power_range.copy()
    pv_power_range[0]= power_range[0]*nodes
    pv_power_range[1]= power_range[1]*nodes
    pv_power_range[2]= (power_range[2]-1)*nodes+1

    gmrange = np.linspace(pv_power_range[0],pv_power_range[1],int(pv_power_range[2]))
 
    trendday = GMparms["Trend"+dagtype+"["+str(kwartier)+"]"].values[0]
    trendmonth = GMparms["TrendMonth["+str(maand)+"]"].values[0]
    gm_average = GMparms["Average[1]"].values[0]+trendday*trendmonth

    gm_average = gm_average*installed_power/100
    gm_std = GMparms["Deviation[1]"].values[0]*installed_power/100

    distnorm = stats.norm(loc = gm_average , scale=gm_std)
    prob_day = GMparms[dagtype+"[1,"+str(kwartier)+"]"].values[0]
    prob_month = GMparms["Month[1,"+str(maand)+"]"].values[0]
    prob_time = context[2] >= sunrise_set.loc[month_name[context[1]].lower()]['sunrise'] and context[2] <= sunrise_set.loc[month_name[context[1]].lower()]['sunset']
    probactive = prob_day*prob_month * prob_time

    if probactive>1 : probactive = 1

    distnorm_pdf = distnorm.pdf(gmrange)

    zeroindex = find_zeroindex (distnorm_pdf, pv_power_range, pdelta)

    for i in range(int(max_power/pdelta)+zeroindex, distnorm_pdf.size) : 
        distnorm_pdf[i] = 0

    distnorm_pdf = normalize (distnorm_pdf, pdelta)

    distnorm_pdf = probactive * distnorm_pdf

    # chance that no sun is shining, hence 0 power
    distnorm_pdf[zeroindex] = (1-probactive)/pdelta

    return get_expectation_value(distnorm_pdf, power_range[0], power_range[1], pdelta)



def main() :
    buurtdf = readGM(CONFIG_DIR + BUURT_FILE)
    GMdf = readGM(CONFIG_DIR + GM_TYPE_FILE)

    sunset_rise = pd.read_csv(CONFIG_DIR + SUNRISE_SUNSET_FILE, delimiter=';', index_col=0)

    # Daytype, month, PTU of the day
    context = ("Workday", 1, 48)

    for i in range(len(buurtdf)):
        node = buurtdf.loc[i]
        if (node.loc['GMtype'] == 'SJV'):
            expectation_value = get_single_SJV_Expectation_value(node.loc['GMname'], GMdf, context)
            print(node.loc['GMtype'] + "/" + node.loc['GMname'] + " - Expectation value: " + str(expectation_value))
        elif (node.loc['GMtype'] == 'PV'):
            expectation_value = get_single_PV_Expectaction_Value(node.loc['GMname'], GMdf, sunset_rise, context, node.loc['installed_power'])
            print(node.loc['GMtype'] + "/" + node.loc['GMname'] + " - Expectation value: " + str(expectation_value))


if __name__ == "__main__":
    main()