#!/bin/bash
gunicorn -w 2 wsgi:app --timeout 180

