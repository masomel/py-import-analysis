#!/bin/bash

LIST=$1

python3 lib-scraper.py $LIST > $LIST-lib-collect.out 2>&1
