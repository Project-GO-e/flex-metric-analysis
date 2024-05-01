

from pathlib import Path
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from db.baselines_dao import BaselineDao
from db.flex_devices_dao import FlexDevicesDao
from experiment.experiment_description import DeviceType



class CliWizard():
    '''Utily class to explore in an interactive way the contents of the database'''

    def __init__(self, db_file: Path) -> None:
        if not db_file.exists():
            print("Database file is missing. Cannot run the flex metrics tool.\nExiting...")
            exit(1)
        else:
            self.engine = create_engine(f"sqlite:///{db_file}", echo=False)

    def __select_yes_no(question) -> bool:
        yn = input(f"\n{question} (Y/n) ")
        if yn.lower() in ['yes', 'y', '', 'no', 'n']:
            return yn.lower() in ['yes', 'y', '']
        else:
            return CliWizard.__select_yes_no("Please answer only with Yes (Y) or no (n). ")

    def __select_option(question, options) -> Any:
        if len(options) == 0:
            raise Exception("No options for question '" + question + "'")
        print(f"\n{question}")
        for i,d in enumerate(map(lambda x: str(x), options), 1):
            print(f"\t{i:2d}. {d}")
        idx = int(input(f"\nProvide [{1}..{len(options)}]: "))
        return options[idx - 1]

    def __read_profile(question, profile_length=None):
        invalid_input = True
        while invalid_input:
            profile = input(f"{question} Provide comma-separated values, e.g. 106.5,15.8,... ")
            profile_list = profile.split(sep=',')
            if profile_length is not None and len(profile_list) != profile_length:
                print(f" => Invalid input. Length of input is {len(profile_list)} but expected is {profile_length}.")
            else:
                invalid_input = False
        return list(map(lambda x: float(x.strip()), profile_list))

    def start(self) -> None:
        with Session(self.engine) as session:
            doa = BaselineDao(session)
            device_types = doa.get_device_types()
            device_type = CliWizard.__select_option("The following device are known. For which device do you want to explore the data: ", device_types)
            typical_day = CliWizard.__select_option(f"Typical days for {device_type}: ", doa.get_typical_days(device_type=device_type))
            group = CliWizard.__select_option(f"Groups for {device_type}: ", doa.get_groups(device_type=device_type, typical_day=typical_day))
            fm_doa = FlexDevicesDao(session)
            cong_starts = fm_doa.get_congestion_start(device_type=device_type, typical_day=typical_day, group=group)
            if len(cong_starts) > 0 and CliWizard.__select_yes_no(f"The database contains flexmetrics for {device_type}. Would you like to explore the congestion start and durations? "):
                fm_doa = FlexDevicesDao(session)
                cong_starts = fm_doa.get_congestion_start(device_type=device_type, typical_day=typical_day, group=group)
                cong_starts.sort()
                cong_start = CliWizard.__select_option(f"Choose congestion start time for '{device_type}' and the selection you made above:", cong_starts)
                cong_durations = fm_doa.get_congestion_duration(cong_start=cong_start, device_type=device_type, typical_day=typical_day, group=group)
                cong_durations.sort()
                cong_dur = CliWizard.__select_option(f"Choose congestion start duration for '{device_type}' and the selection you made above:", cong_durations)
            else:
                print(f"No flex metrics available for device type {device_type}.")

        print("\nThanks for using the wizard. Here follows a line that you can put in your excel config for the asset you selected.")
        excel_device_type = 'baseload' if device_type == DeviceType.SJV else str(device_type).lower()
        print(f"\n{excel_device_type},{typical_day},{group}\n")
