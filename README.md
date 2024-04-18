
# Fleximetrics

## Getting started

### Requirements

 - Python 3.10 or newer
 - Pip

Optional:
 - The Python module `venv`


### Setting up
If running in a virtual environment with the python module `venv`, run (on Unix based systmes):

> python -m venv .venv

> source .venv/bin/activate

Install dependencies:

> pip install -r requirements.txt

Make sure to put the input data in the `data` folder. If you're just using the flex metrics database, you'll only need the database file

### Running
```
usage: src/main.py [-h] [-f FILE] [-b] [-w]

Flex Metrics Tool

options:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  scenarion definition file name
  -b, --baselines       get only the baselines from database
  -w, --wizard          run fleximetrics wizard to explore the database contents
```
