#!/usr/bin/env bash

gunicorn --threads 4 "$@" requeuest:app

