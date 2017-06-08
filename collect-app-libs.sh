#!/bin/bash

CAT=$1

python3 app-scraper.py $CAT > $CAT-collect.out
