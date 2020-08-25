#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 27 09:52:56 2020

@author: ahmad
"""

"""
Application's entry point
"""

from application import create_app

def main():
	app = create_app()
	app.run(host="192.168.0.192", debug = False)

if __name__ == "__main__":
	main()
    