# -*- coding: utf-8 -*-
"""
Created on Wed, April 01 10:10:10 2020
@author: Ahmad H. Mirza
scriptVersion = 1.0..0
"""

from flask_wtf import FlaskForm, RecaptchaField
# Field types can be imported from wtforms
# Field validators from wtforms.validators
from wtforms import validators
from wtforms.fields.html5 import EmailField
from wtforms import StringField,TextField,SubmitField,PasswordField,FileField
try:
    from wtforms.validators import DataRequired, Length, Optional,AnyOf
    print("imported validators.")
except:
    print("ROROEIJR")

class SignupForm(FlaskForm):
    
    """ Form for new user registration"""
    lName = StringField("Last Name: ",validators=[DataRequired()])
    fName = StringField("First Name: ")
    company = StringField("Company: ")
    department = StringField("Department: ")
    emailAddr = EmailField("Email Address: ", 
                [validators.DataRequired(), validators.Email()])
    userName = StringField("User-Name: ")
    password = StringField("Password: ",validators=[DataRequired()])
    
    #recaptcha = RecaptchaField()
    submit = SubmitField("Submit")