# -*- coding: utf-8 -*-
"""
Created on Wed, April 01 10:10:10 2020
@author: Ahmad H. Mirza
scriptVersion = 1.0..0
"""

from flask_wtf import FlaskForm
# Field types can be imported from wtforms
# Field validators from wtforms.validators
from wtforms import StringField,TextField,SubmitField,PasswordField,FileField
from wtforms.widgets import PasswordInput
try:
    from wtforms.validators import DataRequired, Length, Optional,AnyOf
    print("imported validators.")
except:
    print("ROROEIJR")

class LoginForm(FlaskForm):
    
    """ Form for new user registration"""
    userName = StringField("UserName: ",validators=[DataRequired()])
    password = StringField("PassWord: ",validators=[DataRequired()], widget=PasswordInput(hide_value=False))
    #recaptcha = RecaptchaField()
    submit = SubmitField("Submit")


class newWorkflowForm(FlaskForm):
    
    """ Form for new user registration"""
    workflowName = StringField("Workflow Name: ",validators=[DataRequired()])
    baseModel    = StringField("BaseModel: ",validators=[DataRequired()] )
    #recaptcha = RecaptchaField()
    submit = SubmitField("Create Workflow")