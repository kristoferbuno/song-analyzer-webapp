#!/bin/bash
gunicorn -w 2 wsgi:app --timeout 180 --bind 0.0.0.0:8000
