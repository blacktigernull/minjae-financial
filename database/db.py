from dotenv import load_dotenv
from os import environ
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from flask import Flask
from flask_cors import CORS
import json

load_dotenv()

db_config = {
    'user'     : environ.get('user'),
    'password' : environ.get('password'),
    'host'     : environ.get('host'),
    'port'     : environ.get('port'),
    'database' : environ.get('database'),
}

DB_URL = f"mysql+mysqlconnector://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}?charset=utf8" 

def initialized_database_app(name):
    app = Flask(name)
    CORS(app)
    engine = create_engine(DB_URL, encoding = 'utf-8')
    return app, engine.connect

def send_query(query, connection):
    try:
        with connection() as conn:
            res = conn.execute(text(query))
            result = json.loads(json.dumps([dict(r) for r in res]))
            if(type(result) is list):
                if(len(result) == 0):
                    return None
                elif(len(result) == 1):
                    return result[0]
            return result
    except:
        Exception("Unexpected error from sending query") 
