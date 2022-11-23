import psycopg2
import psycopg2.extras
from flask import Flask, current_app, jsonify, request
from flask_cors import CORS
from datetime import datetime

def get_db_connection():
    conn = psycopg2.connect("user=postgres password=trainee_ben1! host=news-scraper-db-ben.c1i5dspnearp.eu-west-2.rds.amazonaws.com")
    return conn

#Set up
app = Flask(__name__)
conn = get_db_connection()
ERROR_400 = 400
ACCEPTED_200 = 200

if __name__=='__main__':
      app.run(debug=True,host='0.0.0.0', port=5000)

def execute_query(query, params = (), code={}):
    if conn != None:
      with  conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor) as curs:
        try:
          curs.execute(query, params)
          returned_data = curs.fetchall()
          return returned_data
        except:
          return "Error executing query."

@app.route("/", methods=["GET"])
def index():
  title = request.args.get('title')
  url = request.args.get('url')
  if title is not None:
      now = datetime.now()
      params = (title, url, now, now)
      query =  """INSERT INTO stories (title, url, created_at, updated_at) 
                    VALUES (%s, %s, %s, %s);"""
      execute_query(query, params)
  return current_app.send_static_file("index.html")

@app.route("/stories", methods=["GET"])
def stories():

    query = """SELECT stories.*, SUM(CASE direction WHEN 'up' THEN 1 WHEN 'down' THEN -1 ELSE 0 END)
               AS score FROM stories LEFT JOIN votes ON votes.story_id = stories.id GROUP BY stories.id 
               ORDER BY score DESC;"""

    responded_data = execute_query(query)
    num_of_stories = len(responded_data)

    if num_of_stories != 0:
      message = 'Successfully retrieved data'
      return jsonify(stories = responded_data, success = True, total_stories = num_of_stories, response_code = ACCEPTED_200)

    else:
      message = 'Could not find any stories on the server'
      return jsonify(stories = responded_data, success = False, total_stories = num_of_stories, response_code = ERROR_400, message = message)

@app.route("/stories/<id>/votes", methods=["POST"])
def user_vote(id):

    up_vote_query =  """INSERT INTO votes (direction, created_at, updated_at, story_id) 
                     VALUES ('up', current_timestamp, current_timestamp, %s)"""
    down_vote_query = """INSERT INTO votes (direction, created_at, updated_at, story_id) 
                      VALUES ('down', current_timestamp, current_timestamp, %s)"""
    params = [id]
    if request.method == 'POST':

      received_data = request.json

      if received_data["direction"] == 'up':
          success_json = {'code': 200, 'success': 'Up-Voted successfully'}
          execute_query(up_vote_query, params)
          return success_json

      elif received_data["direction"] == 'down':
          success_json = {'code': 200, 'success': 'Down-Vote successfully'}
          execute_query(down_vote_query, params)
          return success_json

@app.route("/search", methods=['GET'])
def get_by_tag():
  tag_param = request.args.get('tags').split(',')
  print(tag_param)
  response_data = []
  for tag in tag_param:
      response_data.append(execute_query("""SELECT title, url, tags.description FROM stories 
                                JOIN metadata ON metadata.story_id = stories.id 
                                JOIN tags ON metadata.tag_id =  tags.id WHERE tags.description = %s;""", [tag]))
  return jsonify(response_data)

