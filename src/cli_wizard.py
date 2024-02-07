

from datetime import time

import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from db.flex_metrics_dao import FlexMetricsDao
from experiment_description import DeviceType

DB_FILE="ev-hp-flex-metrics.db"

def select_yes_no(question) -> bool:
    yn = input(f"\n{question} (Y/n) ")
    # TODO some valition and check on 'no'
    return yn.lower() in ['yes', 'y', '']


def select_option(question, options):
    print(f"\n{question}")
    for i,d in enumerate(map(lambda x: str(x), options), 1):
        print(f"\t{i:2d}. {d}")
    idx = int(input(f"\nProvide [{1}..{len(options)}]: "))
    return options[idx - 1]


def read_profile(question, profile_length=None):
    invalid_input = True
    while invalid_input:
        profile = input(f"{question} Provide comma-separated values, e.g. 106.5,15.8,... ")
        profile_list = profile.split(sep=',')
        if profile_length is not None and len(profile_list) != profile_length:
            print(f" => Invalid input. Length of input is {len(profile_list)} but expected is {profile_length}.")
        else:
            invalid_input = False
    return list(map(lambda x: float(x.strip()), profile_list))

engine = create_engine(f"sqlite:///{DB_FILE}", echo=False)

with Session(engine) as session:
    doa = FlexMetricsDao(session)
    ev_typical_days = doa.get_typical_days(DeviceType.EV)
    hp_typical_days = doa.get_typical_days(DeviceType.HP)
    ev_groups = doa.get_groups_for_device_type(DeviceType.EV)
    hp_groups = doa.get_groups_for_device_type(DeviceType.HP)
    cong_start_times = doa.get_congestion_start()
    cong_start_times.sort()
    ev_groups.sort()
    hp_groups.sort()
    cong_start: time = select_option("When does the congestion start?", cong_start_times)
    cong_durations = doa.get_congestion_duration(cong_start)
    cong_durations.sort()
    cong_dur = select_option("How long the congestion take?", cong_durations)
    print("[TODO] Offer to provide more house types")

print("Scenario input:")
ev_group = select_option("Which PC4 area for EV charging session to use?", ev_groups)
ev_typical_day = select_option("Choose EV typical day: ", ev_typical_days)
hp_typical_day = select_option("Choose HP typical day: ", hp_typical_days)
hp_group = select_option("Which house types for heat pumps to use?", hp_groups)
average_load_per_type_available = select_yes_no("Are the average load values for all flexible asset types available from the load flow calculations?")

if average_load_per_type_available:
    ev_baseline = read_profile("EV total load profile.", cong_dur)
    hp_baseline = read_profile("Heat pump total load profile.", cong_dur)
    with Session(engine) as session:
        doa = FlexMetricsDao(session)
        ev_flex_metrics = doa.get_flex_metrics(asset_type=DeviceType.EV, cong_start=cong_start, cong_dur=cong_dur, group=ev_group, typical_day=ev_typical_day)
        hp_flex_metrics = doa.get_flex_metrics(asset_type=DeviceType.HP, cong_start=cong_start, cong_dur=cong_dur, group=hp_group, typical_day=hp_typical_day)
    
    ev_flex = np.array(ev_flex_metrics) * np.array(ev_baseline)
    print("EV flex" + str(ev_flex))
    hp_flex = np.array(hp_flex_metrics) * np.array(hp_baseline)
    print("HP flex" + str(hp_flex))
    print("Flex Power: " + str(ev_flex + hp_flex))
else:
    print('[TODO] Fetching the non-flexible load expected values per PTU...')
    nr_ev = input(f"How many electric vehicles: ")
    nr_hp = input(f"How many heat pumps: ")

print("Thanks")