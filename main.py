from flask import jsonify, request
from database.db import send_query, initialized_database_app
from util import check_required_params
import auth
import json


app, connection = initialized_database_app(__name__)


@app.post("/auth/login")
def login():
  try:
    params = json.loads(request.get_data())
    [email, password], err = check_required_params(params, ['email', 'password'])
    if(err):
      return jsonify({"data":None, "err": err})

    result = send_query(f'SELECT id, name, age, email, balance, budget, password FROM userTbl WHERE email="{email}";', connection)
    if(result == None):
      return jsonify({"data": None, "err":"User not found" })
    hashPw = result['password']
    if(auth.check_password(password, hashPw)):
      token = auth.sign_jwt_token({"id":result['id']})
      return jsonify({'data':{"token":token}})
    return jsonify({'data':None, "err":"Wrong password"})
  except:
    return jsonify({'data':None, "err":"Unexpected error from login"})


@app.post("/auth/createAccount")
def createAccount():
  try:
    [email, password, name], err = check_required_params(json.loads(request.get_data()), ['email', 'password', 'name'])
    if(err):
      return jsonify({"data":None, "err": err})

    hashPw = auth.hash_password(password)
    result = send_query(f'INSERT INTO userTbl (id,createAt,updateAt,name,email,password,balance) values(null,sysdate(),sysdate(),"{name}","{email}","{hashPw}",0)', connection)
    token = auth.sign_jwt_token({"id":result['id']})
    return jsonify({'data':{"token":token}})
  except:
    return jsonify({'data':None, "err":"이미 존재하는 이메일"})


@app.get("/auth/jwt/token")
def get_jwt_token():
  try:
    id = auth.get_verified_id(json.loads(request.get_data()))
    if(type(id) is int):
      return jsonify({'data':{"id":id}, "err":None})
    return jsonify({"data":None, "err": id})
  except:
    return jsonify({'data':None, "err":"Wrong jwtToken"})


@app.route("/auth/user")
def getUser():
  try:
    id = auth.get_verified_id(json.loads(request.get_data()))
    if(type(id) is not int):
      return jsonify({"data":None, "err": id})
    result = send_query(f"SELECT id, name, age, email, balance, budget FROM userTbl WHERE id={id};")
    if(result == None):
      return jsonify({"data": None, "err":"User not found" })
    return jsonify({"data": result, "err":None})
  except:
    return jsonify({'data':None, "err":"Wrong jwtToken"})


@app.get("/spend/<limit>")
def get_spend(limit):
  try:
    id = auth.get_verified_id(json.loads(request.get_data()))
    if(type(id) is not int):
      return jsonify({"data":None, "err": id})
      
    limit_str = '' if limit == None or limit == -1 else ' LIMIT ' + str(limit)
    result = send_query(f'SELECT buyTbl.id, DATE_FORMAT(createAt, "%m/%d %h:%m") AS nDate, categoryTbl.name AS categoryName, categoryTbl.icon AS icon, categoryTbl.id AS categoryId, store, price FROM buyTbl LEFT JOIN categoryTbl ON categoryTbl_id=categoryTbl.id WHERE userTbl_id=1 ORDER BY nDate DESC{limit_str};')
    return jsonify({"data": result, "err":None})
  except:
    return jsonify({'data':None, "err":"Unexpected error from get_spend"})


@app.post('/insert/new')
def insert_new():
  try:
    params = json.loads(request.get_data())
    [jwt, store, price, categoryId], err = check_required_params(params, ['x-jwt', 'store', 'price', 'categoryId'])
    if(err):
      return jsonify({"data":None, "err": err})
    id = auth.get_verified_id({'x-jwt':jwt})
    if(type(id) is not int):
      return jsonify({"data":None, "err": id})
    
    store_str = '' if params['store'] == None else '"' + params['store'] + '",'
    result = send_query(f'insert into buytbl(id,createAt,updateAt,store,price,userTbl_id,categoryTbl_id) values(null,SYSDATE(),SYSDATE(),{store_str}{price},{id},{categoryId});')
    return jsonify({"data": result, "err":None})
  except:
    return jsonify({'data':None, "err":"Unexpected error from insert_new"})


@app.get('/dashBoard/overview')
def dashBoard_overview():
  try:
    id = auth.get_verified_id(json.loads(request.get_data()))
    if(type(id) is not int):
      return jsonify({"data":None, "err": id})
    
    monthOverview = send_query(f'SELECT DAYOFWEEK(createAt) AS nDate, SUM(price) AS price FROM buyTbl WHERE buyTbl.userTbl_id={id} AND createAt BETWEEN SUBDATE(SYSDATE(), INTERVAL 7 DAY) AND SYSDATE() GROUP BY nDate WITH ROLLUP ORDER BY nDate;')
    lastMonthOverview = send_query(f'SELECT DAYOFWEEK(createAt) AS nDate, SUM(price) AS price FROM buyTbl WHERE buyTbl.userTbl_id={id} AND createAt BETWEEN SUBDATE(SYSDATE(), INTERVAL 14 DAY) AND SUBDATE(SYSDATE(), INTERVAL 7 DAY) GROUP BY nDate WITH ROLLUP ORDER BY nDate;')
    return jsonify({"data": {'monthOverview':monthOverview, 'lastMonthOverview':lastMonthOverview}, "err":None})
  except:
    return jsonify({'data':None, "err":"Unexpected error from dashBoard_overview"})


@app.get('/category')
def get_category():
  try:
    categorys = send_query('SELECT * FROM categoryTbl;')
    return jsonify({"data": categorys, "err":None})
  except:
    return jsonify({'data':None, "err":"Unexpected error from get_category"})


@app.get('/category/overview')
def category_overview():
  try:
    id = auth.get_verified_id(json.loads(request.get_data()))
    if(type(id) is not int):
      return jsonify({"data":None, "err": id})
    
    monthOverview = send_query(f'SELECT SUM(price) AS price, COUNT(price) AS count, categoryTbl_id, categoryTbl.name as categoryName, categoryTbl.slug AS slug, categoryTbl.icon AS icon FROM buyTbl LEFT JOIN categoryTbl ON categoryTbl_id=categoryTbl.id WHERE buyTbl.userTbl_id={id} AND createAt BETWEEN SUBDATE(sysdate(), INTERVAL 1 MONTH) AND SYSDATE() GROUP BY categoryTbl_id ORDER BY price DESC;')
    lastMonthOverview = send_query(f'SELECT SUM(price) AS price, COUNT(price) AS count, categoryTbl_id AS categoryId, categoryTbl.name AS categoryName, categoryTbl.slug AS slug, categoryTbl.icon AS icon FROM buyTbl LEFT JOIN categoryTbl ON categoryTbl_id=categoryTbl.id WHERE buyTbl.userTbl_id={id} AND createAt BETWEEN SUBDATE(SYSDATE(), INTERVAL 2 MONTH) AND SUBDATE(SYSDATE(), INTERVAL 1 MONTH) GROUP BY categoryTbl_id ORDER BY price DESC LIMIT 1;')
    return jsonify({"data": {'monthOverview':monthOverview, 'lastMonthOverview':lastMonthOverview}, "err":None})
  except:
    return jsonify({'data':None, "err":"Unexpected error from category_overview"})


@app.get('/category/report/<categoryId>')
def category_report(categoryId):
  try:
    id = auth.get_verified_id(json.loads(request.get_data()))
    if(type(id) is not int):
      return jsonify({"data":None, "err": id})
    if(categoryId == None):
      return jsonify({"data":None, "err": "categoryId is required"})
    
    overview = send_query(f'SELECT DATE_FORMAT(createAt, "%d") AS nDate, SUM(price) AS price, COUNT(price) AS count FROM buyTbl WHERE buyTbl.userTbl_id={id} AND createAt BETWEEN SUBDATE(SYSDATE(), INTERVAL 1 MONTH) AND SYSDATE() AND categoryTbl_id={categoryId} GROUP BY nDate WITH ROLLUP ORDER BY nDate;')
    table = send_query(f'SELECT buyTbl.id, DATE_FORMAT(createAt, "%m/%d  %h:%m") AS nDate, store, price, categoryTbl.id AS categoryId, categoryTbl.name AS categoryName, categoryTbl.icon AS icon FROM buyTbl LEFT JOIN categoryTbl ON categoryTbl_id=categoryTbl.id WHERE buyTbl.userTbl_id={id} AND categoryTbl_id={categoryId} ORDER BY nDate DESC;')
    return jsonify({"data": {'overview':overview, 'table':table}, "err":None})
  except:
    return jsonify({'data':None, "err":"Unexpected error from category_report"})


@app.get('/timeReport/<monthInfo>')
def timeReport(monthInfo):
  try:
    id = auth.get_verified_id(json.loads(request.get_data()))
    if(type(id) is not int):
      return jsonify({"data":None, "err": id})
    if(monthInfo == None):
      return jsonify({"data":None, "err": "monthInfo is required"})
    
    line_graph = send_query(f"SELECT DATE_FORMAT(createAt, '%d') AS nDate, SUM(price) AS price, COUNT(price) AS count FROM buyTbl WHERE buyTbl.userTbl_id={id} AND createAt BETWEEN DATE({monthInfo}01) AND LAST_DAY(DATE({monthInfo}01)) GROUP BY nDate WITH ROLLUP ORDER BY nDate;")
    top_spend = send_query(f"SELECT store, categoryTbl.name AS categoryName, price FROM buyTbl LEFT JOIN categoryTbl ON categoryTbl_id=categoryTbl.id WHERE buyTbl.userTbl_id={id} AND createAt BETWEEN DATE({monthInfo}01) AND LAST_DAY(DATE({monthInfo}01)) ORDER BY price DESC LIMIT 3;")
    top_freq = send_query(f"SELECT store, COUNT(store) AS count, SUM(price) AS price FROM buyTbl WHERE buyTbl.userTbl_id={id} AND createAt BETWEEN DATE({monthInfo}01) AND LAST_DAY(DATE({monthInfo}01)) GROUP BY store ORDER BY count DESC LIMIT 3;")
    category = send_query(f"SELECT SUM(price) AS price, COUNT(price) AS count, categoryTbl_id, categoryTbl.name as categoryName, categoryTbl.slug AS slug, categoryTbl.icon AS icon FROM buyTbl LEFT JOIN categoryTbl ON categoryTbl_id=categoryTbl.id WHERE buyTbl.userTbl_id={id} AND createAt BETWEEN DATE({monthInfo}01) AND LAST_DAY(DATE({monthInfo}01)) GROUP BY categoryTbl_id ORDER BY price DESC;")
    return jsonify({"data": {'lineGraph':line_graph, 'topSpend':top_spend, 'topFreq':top_freq, 'category':category}, "err":None})
  except:
    return jsonify({'data':None, "err":"Unexpected error from time_report"})


@app.post('/profile/update')
def user_profile():
  try:
    params = json.loads(request.get_data())
    id = auth.get_verified_id({'x-jwt':params['x-jwt']})
    if(type(id) is not int):
      return jsonify({"data":None, "err": id})
    query = "UPDATE userTbl SET updateAt=SYSDATE()"
    query += "" if params['name'] == None else ',name="' + params['name'] + '"'
    query += "" if params['email'] == None else ',email="' + params['email'] + '"'
    query += "" if params['age'] == None else ',age="' + params['age'] + '"'
    query += "" if params['password'] == None else ',password="' + auth.hash_password(params['password']) + '"'
    query += "" if params['balance'] == None else ',balance="' + params['balance'] + '"'
    query += "" if params['budget'] == None else ',budget="' + params['budget'] + '"'
    query += f"WHERE id={id}"
    result = send_query(query)
    return jsonify({"data": result, "err":None})
  except:
    return jsonify({'data':None, "err":"이미 존재하는 이메일입니다"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port="4000")


