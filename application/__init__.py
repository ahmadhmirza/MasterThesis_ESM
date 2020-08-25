#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 27 08:46:51 2020

@author: ahmad

__init__.py file is considered a package, and can be imported. When you import 
a package, the __init__.py executes and defines what symbols the package 
exposes to the outside world.
"""


"""
command to run :
    flask run --host=0.0.0.0  # runs on internal network
    flask run  # runs on localhost
"""

"""initialize app"""
from flask import Flask
try:
    import tensorflow as tf
    print("TF IMPORT SUCCESSFUL")
except Exception as e:
    print("INIT: " + str(e))
def create_app():
    import os
    app = Flask(__name__)
    app.config['SECRET_KEY'] = "SECRET_KEY_STRING_HERE"
    
    with app.app_context():
        from .FileUpload import FileUpload_routes
        app.register_blueprint(FileUpload_routes.fileUpload_bp)

        from .FileDownload import FileDownload_routes
        app.register_blueprint(FileDownload_routes.fileDownload_bp)

        from .PlantUmlService import GenerateUML_routes
        app.register_blueprint(GenerateUML_routes.plantUml_bp)

        from .CanTestService import CanTest_routes
        app.register_blueprint(CanTest_routes.canTest_bp)

        from .Signup import Signup_routes
        app.register_blueprint(Signup_routes.signup_bp)

        from .ML_ClassificationService import ML_Routes
        app.register_blueprint(ML_Routes.machineLearning_bp)

        from .ML_App import ML_GUI_Routes
        app.register_blueprint(ML_GUI_Routes.mlGUI_bp)

        #For each new added service, it blueprint should be registered
        # in this function.
        #[Reference] https://hackersandslackers.com/flask-blueprints
        return app
