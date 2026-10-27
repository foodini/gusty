#!/usr/bin/bash

cd /home/flyfunston/gusty
source bin/activate
date >> renderer.out
./renderer.py >> renderer.out 2>&1
