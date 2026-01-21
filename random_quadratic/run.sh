#!/bin/bash -l


ml gurobi/13.0
ml gams/52.2.0

export GRB_LICENSE_FILE=$HOME/gurobi.lic

python batch_run.py
