from dotenv import load_dotenv
from os import environ
from datetime import datetime, timedelta
from jwt import encode, decode
from bcrypt import hashpw, gensalt, checkpw
from json import dump
load_dotenv()

# token = jwt.sign_jwt_token(request.headers.get('x-jwt'))    
def sign_jwt_token(payload):
  try:
      if(payload == None):
        return False
      payload['exp'] = datetime.utcnow() + timedelta(seconds=60*60*24*5)
      token = encode(dump(payload),environ.get('JWT_PRIVATE_TOKEN'),algorithm="HS256")
      return token
  except:
      return None

# verified, payload = jwt.verify_jwt_token(token)
def verify_jwt_token(token):
  try:
      if(token == None):
        return False
      payload = decode(token, environ.get('JWT_PRIVATE_TOKEN'),algorithms=["HS256"])
      return True, payload
  except:
    return False

def get_verified_id(params):
  jwt = params['x-jwt']
  if(jwt == None):
    return "jwt token not found"
  status, payload = verify_jwt_token(jwt)
  if(status and payload['id'] is not None):
    return int(payload['int'])
  return "Wrong token"

def hash_password(password):
  try:
    hashed_pw = hashpw(password.encode('utf-8'), gensalt())
    return hashed_pw.decode('utf-8')
  except:
    Exception("Can not hash password")

def check_password(password, db_password):
  try:
    checked = checkpw(password.encode('utf-8'), db_password.encode('utf-8'))
    return checked
  except:
    Exception("Can not check password")
