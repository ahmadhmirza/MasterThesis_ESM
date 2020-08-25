# -*- coding: utf-8 -*-
"""
Created on Mon, May 28 12:12:12 2020
@author: Ahmad H. Mirza
scriptVersion = 1.0..0
"""

#TODO: Add API Key generation to this script as well.
from flask import current_app as app
import json
from datetime import datetime
import secrets
import os
""" 
Initialization of all the necessary paths required for the script to run.
"""
from . import ML_GUI_constants as MLC
