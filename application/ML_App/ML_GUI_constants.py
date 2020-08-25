# -*- coding: utf-8 -*-
"""
Created on Mon, May 28 12:12:12 2020
@author: Ahmad H. Mirza
scriptVersion = 1.0..0
"""
import os

STATIC_DIR                  = "static"
ASSETS_DIR                  = "assets"

#get the path to the current script:
#This will facilitate in geting the rest of the path programatically.
SCRIPT_PATH         = os.path.dirname(__file__)
STATIC_PATH         = os.path.join(SCRIPT_PATH,STATIC_DIR)
ASSETS_PATH         = os.path.join(STATIC_PATH,ASSETS_DIR)

#HTTP_CODES.
HTTP_OK                     = 200
HTTP_CREATED                = 201
HTTP_ACCEPTED               = 202
HTTP_MOVED_PERMANENTLY      = 301
HTTP_BAD_REQUEST            = 400
HTTP_UNAUTHORIZED           = 401
HTTP_PAYMENT_REQUIRED       = 402
HTTP_FORBIDDEN              = 403
HTTP_NOT_FOUND              = 404
HTTP_PAYLOAD_TOO_LARGE      = 413
HTTP_IM_A_TEAPOT            = 418
HTTP_TOO_MANY_REQUESTS      = 429 #Rate limiting
HTTP_SERVER_ERROR           = 500
HTTP_NOT_IMPLEMENTED        = 501
HTTP_SERVICE_UNAVAILABLE    = 503
