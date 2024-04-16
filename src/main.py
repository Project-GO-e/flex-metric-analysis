from argparse import ArgumentParser
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from dataclass_binder import Binder

from db.data_not_found_exception import DataNotFoundException
from flex_metric_config import Config
from flex_metrics import FlexMetrics
from util.cli_wizard import CliWizard

DB_FILE: Final[str]="flex-metrics.db"
CONFIG_FILE: Final[str]="config.toml"


@dataclass
class CliArgs():
    conf_file: Path
    baselines_only: bool
    wizard_mode: bool
            

def write_toml_template():
    with open("config.toml.template", "w") as out:
        for line in Binder(Config).format_toml():
            print(line, file=out)

    
def parse_args() -> CliArgs:
    parser = ArgumentParser(prog="src/main.py", description="Flex Metrics Tool" )
    parser.add_argument('-f', '--file', help="configuration file name")
    parser.add_argument('-b', '--baselines', action='store_true', help="get only the baselines from database")
    parser.add_argument('-w', '--wizard',  action='store_true', help="run fleximetrics wizard to explore the database contents")
    args = parser.parse_args()
    conf_file = args.file if args.file else CONFIG_FILE
    return CliArgs(Path(conf_file), args.baselines, args.wizard)

def run_flex_metrics_calculation(db_path: Path, args: CliArgs):
    try:
        FlexMetrics(args.conf_file, db_path).determine_flex_power()
    except DataNotFoundException as e:
        print("ERROR: " + str(e))

def fetch_baselines(db_path: Path, args: CliArgs):
    try:
        FlexMetrics(args.conf_file, db_path).fetch_baselines().to_csv("baselines.csv")
    except DataNotFoundException as e:
        print("ERROR: " + str(e))


if __name__ == "__main__":
    
    db_path = Path(DB_FILE) if Path(DB_FILE).exists() else Path("_internal") / DB_FILE
        
    args = parse_args()
    
    if args.wizard_mode:
        CliWizard().start()
    elif args.baselines_only:
        fetch_baselines(db_path, args)
    else:
        run_flex_metrics_calculation(db_path, args)

        