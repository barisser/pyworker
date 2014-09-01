import os
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask import request
from flask import make_response
import requests
import json
import ast
import time
import node
import bitsource
import transactions
import addresses
import workertasks
import unicodedata

app = Flask(__name__)
app.config['PROPAGATE_EXCEPTIONS']=True
dbname='chainscribe'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']  #"postgresql://localhost/"+dbname
