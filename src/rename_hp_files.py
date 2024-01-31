import re
from datetime import datetime, time, timedelta
from pathlib import Path

import pandas as pd

INPUT_DIR="data/hp-input"
SHIFTED_OUTPUT_DIR="data/hp/shifted/"
BASELINE_OUTPUT_DIR="data/hp/baselines/"

DATETIME_FORMAT='%Y-%m-%dT%H%M'

baseline = next(Path(INPUT_DIR).glob('baselines*'))
print(baseline)
baseline_df = pd.read_csv(baseline, index_col=0, parse_dates=True)

convert_cnt = 0
for exp_path in Path(INPUT_DIR).iterdir():
    if (re.fullmatch("flex_profiles.*", exp_path.stem)):
        df = pd.read_csv(exp_path,index_col=0, parse_dates=True)
        flex_window_start :datetime = df.index[0]
        ptu_duration: timedelta = df.index[1] - df.index[0]
        flex_window_duration :int = len(df.index)
        cong_start_ptu = int(re.findall('start\d*', exp_path.stem)[0].removeprefix("start"))
        cong_start: datetime = datetime.combine(flex_window_start.date(), time.min) + ptu_duration * cong_start_ptu
        cong_dur = re.findall('dur\d*', exp_path.stem)[0].removeprefix("dur")
        type=re.findall('.*\+start', exp_path.stem)[0].removeprefix('flex_profiles+').removesuffix('+start')
        new_name=(f"{type}_flexwindowstart{flex_window_start.strftime(DATETIME_FORMAT)}_"
                    f"flexwindowduration{flex_window_duration}_"
                    f"congestionstart{cong_start.strftime(DATETIME_FORMAT)}_"
                    f"congestionduration{cong_dur}")
        df.to_csv(SHIFTED_OUTPUT_DIR + new_name + ".csv", sep=';' )
        baseline_df[df.index[0]:df.index[-1]].to_csv(BASELINE_OUTPUT_DIR + new_name + ".csv", sep=';')
        convert_cnt+=1
print(f"Converted {convert_cnt} experiments")

