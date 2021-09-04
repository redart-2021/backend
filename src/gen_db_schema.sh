#!/bin/bash

BROKER_URL=1 ./manage.py graph_models -E -g -X *Mixin,*Abstract,AbstractUser --arrow-shape vee -o ../db.png user main auth
