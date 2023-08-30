
import pandas as pd
import matplotlib.pyplot as plt


BASELINE_DIR='data/baseline/'
SHIFTED_DIR='data/shifted/'

EXPERIMENT='pc46651_flexwindowduration48_congestionstart2020-06-03T1745_congestionduration16'

df_baseline = pd.read_csv(BASELINE_DIR + EXPERIMENT + '.csv', sep=';', decimal=',')
df_shifted = pd.read_csv(SHIFTED_DIR + EXPERIMENT + '.csv', sep=';', decimal=',')

df_baseline = df_baseline.loc[263].drop("Unnamed: 0")
df_shifted = df_shifted.loc[263].drop("Unnamed: 0")

mask = df_baseline != 0.0

baseline_wo_zeros = df_baseline.iloc[mask.values]
shifted_wo_zeros = df_shifted.iloc[mask.values]

flex_metric = (baseline_wo_zeros - shifted_wo_zeros) / baseline_wo_zeros

print("Mean: " + str(flex_metric.mean()))
print("std: " + str(flex_metric.std()))

x=df_baseline.iloc[mask.values].values
y=flex_metric.values * x
plt.figure(1)

plt.hist(y, 40)

plt.figure(2)
plt.scatter(x,y)
plt.xlabel('X-axis')
plt.ylabel('Y-axis')
plt.title("A simple line graph")
plt.show()