import re
from datetime import datetime, time, timedelta
from pathlib import Path

import pandas as pd

INPUT_BASELINE_DIR="data/baselines_hp"
INPUT_FLEX_PROFILES_DIR="data/flex_profiles_hp"

OUTPUT_BASELINE_DIR="data/hp/baselines/"
OUTPUT_SHIFTED_DIR="data/hp/shifted/"

DATETIME_FORMAT='%Y-%m-%dT%H%M'

FORCE_OVERWRITE=False


# for baseline in Path(INPUT_BASELINE_DIR).glob('baselines*'):
#     print(f"Loading baseline for {baseline.stem}")
#     baselines_df= pd.read_csv(baseline, index_col=0, parse_dates=True)
#     baselines_df.to_csv(OUTPUT_BASELINE_DIR + "/" + baseline.name, sep=';')

convert_cnt = 0
files_written=0

for exp_path in Path(INPUT_FLEX_PROFILES_DIR).iterdir():
    if (re.fullmatch("infeasible_profile_nrs.*", exp_path.stem)):
        with open(exp_path) as infeasible_profile:
            amount_infeasible = len(infeasible_profile.readlines())
            print(f"Experiment with {amount_infeasible} infeasible profiles")
    elif (re.fullmatch("flex_profiles.*", exp_path.stem)):
        df = pd.read_csv(exp_path, index_col=0, parse_dates=True)
        flex_window_start :datetime = df.index[0]
        ptu_duration: timedelta = df.index[1] - df.index[0]
        flex_window_duration :int = len(df.index)
        cong_start_ptu = int(re.findall('start\d*', exp_path.stem)[0].removeprefix("start"))
        cong_start: datetime = datetime.combine(flex_window_start.date(), time.min) + ptu_duration * cong_start_ptu
        cong_dur = re.findall('dur\d*', exp_path.stem)[0].removeprefix("dur")
        exp_type=re.findall('.*\+start', exp_path.stem)[0].removeprefix('flex_profiles+').removesuffix('+start')
        new_name=(f"{exp_type}_flexwindowstart{flex_window_start.strftime(DATETIME_FORMAT)}_"
                    f"flexwindowduration{flex_window_duration}_"
                    f"congestionstart{cong_start.strftime(DATETIME_FORMAT)}_"
                    f"congestionduration{cong_dur}")
                
        out_path = Path(OUTPUT_SHIFTED_DIR + new_name + ".csv")
        if not out_path.exists() or FORCE_OVERWRITE:
            df.to_csv(out_path, sep=';' )
            files_written += 1
        convert_cnt+=1
        if convert_cnt % 100 == 0:
            print(f"Converted {convert_cnt} experiments. {convert_cnt - files_written} already existed")
print(f"Converted {convert_cnt} experiments. {convert_cnt - files_written} already existed")
