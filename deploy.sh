#!/bin/bash

set -ex

git stash
git pull --rebase
git stash pop || true

./dc build
./dc run --rm worker python manage.py migrate
./dc up -d
