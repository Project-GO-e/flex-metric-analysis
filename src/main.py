from argparse import ArgumentParser
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from dataclass_binder import Binder

from config_converter import ExcelConverter
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
    parser.add_argument('-f', '--file', help="scenario definition file name. Toml and Excel formats accepted.")
    parser.add_argument('-b', '--baselines', action='store_true', help="get only the baselines from database")
    parser.add_argument('-w', '--wizard',  action='store_true', help="run fleximetrics wizard to explore the database contents")
    args = parser.parse_args()
    conf_file = args.file if args.file else CONFIG_FILE
    return CliArgs(Path(conf_file), args.baselines, args.wizard)

def flex_metrics_calculation(db_path: Path, conf: Config):
    try:
        FlexMetrics(conf, db_path).determine_flex_power(reduce_to_device_type=True).round(1).to_csv('out.csv', sep=';')
    except DataNotFoundException as e:
        print("ERROR: " + str(e))

def baselines_to_file(db_path: Path, conf: Config):
    try:
        baselines_df = FlexMetrics(conf, db_path).fetch_baselines()
        # Reduce the (hybrid) heat pump baseline profiles:
        hp_baseline = baselines_df.filter(regex="^hp-")
        if len(hp_baseline.columns) > 0:
            baselines_df.drop(list(hp_baseline), axis=1, inplace=True)
            baselines_df["hp"] = hp_baseline.sum(axis=1)
        hhp_baseline = baselines_df.filter(regex="^hhp-")
        if len(hhp_baseline.columns) > 0:
            baselines_df.drop(list(hhp_baseline), axis=1, inplace=True)
            baselines_df["hhp"] = hhp_baseline.sum(axis=1)
        baselines_df["all"] = baselines_df.sum(axis=1)
        baselines_df.round(1).to_csv(f"baselines.csv", sep=';')
    except DataNotFoundException as e:
        print("ERROR: " + str(e))

def read_config(config_file: Path) -> Config:
    if Path(args.conf_file).suffix == ".toml":
        try:
            conf = Binder(Config).parse_toml(config_file)
        except ValueError as e:
            print("Configuration invalid. " + str(e) +"\nExiting...")
            exit(1)
        except FileNotFoundError:
            print(f"Configuration file '{config_file}' not found." + "\nExiting...")
            exit(1)
    elif Path(args.conf_file).suffix == ".xlsx":
        try:
            conf = ExcelConverter(config_file=config_file).convert()
        except FileNotFoundError:
            print(f"Configuration file '{config_file}' not found." + "\nExiting...")
            exit(1)
    else:
        print("Unknown input file type. Please use a file with the toml or xlsx extension. Exiting...")
        exit(1)
    if not conf.is_valid():
        print("Configuration invalid. Exiting...")
        exit(1)
    return conf

if __name__ == "__main__":
    
    db_path = Path(DB_FILE) if Path(DB_FILE).exists() else Path("_internal") / DB_FILE
        
    args = parse_args()
    
    if args.wizard_mode:
        CliWizard(db_path).start()
    elif args.baselines_only:
        baselines_to_file(db_path, read_config(args.conf_file))
    else:
        flex_metrics_calculation(db_path, read_config(args.conf_file))
