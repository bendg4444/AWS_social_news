
from urllib.request import urlopen
from datetime import datetime
from bs4 import BeautifulSoup
import psycopg2
import psycopg2.extras  # We'll need this to convert SQL responses into dictionaries

def get_db_connection():
  try:
    conn = psycopg2.connect("user=postgres password=password1! host=database-daniela.cca9ozjnaqxx.eu-west-2.rds.amazonaws.com")
    return conn
  except:
    print("Error connecting to database.")
conn = get_db_connection()

def get_html(url):
    page = urlopen(url)
    html_bytes = page.read()
    html = html_bytes.decode("utf_8")
    return html

def parse_tags_bs(html, url):
   
    soup = BeautifulSoup(html, "html.parser")
    html_div_tags = soup.select(".ssrcss-1yh0utg-PromoContent")
    article_info = []

    #loops through each instance of html class retrieved above
    for div in html_div_tags:
        
        #header responsible for getting URL and title
        header = div.select('.e1f5wbog0')
        href = header[0].get('href')
        title = header[0].get_text()
        
        try:
            tag_name = div.select('.ecn1o5v1')[0]
            tag = tag_name.get_text()

        except:
            print("found error")

        if 'Live' in title:
            pass

        if "http" not in href:
            href = url + href
        
        article_info.append({'title': title, 'url':href, 'tag':tag})

    return article_info

def insert_into_database(query, params = ()):
    
    if conn != None:
        with conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor) as cur:
            try:
                cur.execute(query, params)
                returned_data = cur.fetchall()
                conn.commit()
                return returned_data
            except:
                return "Error executing query."
    else:
        return "No connection"

if __name__ == "__main__":
    bbc_url = "http://bbc.co.uk"
    bbc_html_doc = get_html(bbc_url)
    articles = parse_tags_bs(bbc_html_doc, bbc_url)
    
    #If I need to update the database with fresh articles
    stories_query = "INSERT INTO stories (title, url, created_at, updated_at) VALUES (%s, %s, %s, %s);"
    insert_tags_query = "INSERT INTO tags (description) VALUES (%s) ON CONFLICT DO NOTHING;"

    #fills database with fresh articles
    for article in articles:
        title = article['title']
        url = article['url']
        tags_param = [article['tag']]
        stories_params = [title, url, datetime.now(), datetime.now()]
        insert_into_database(stories_query, stories_params)
        insert_into_database(insert_tags_query, tags_param)

    #creates a list of titles, id
    titles_query = "SELECT title, id FROM stories"
    titles = insert_into_database(titles_query)
    
    #list of titles with their id
    title_info = []
    for info in titles:
        title = info['title']
        id = info['id']
        title_info.append({'title': title, 'id': id})

    #list of tags with their id
    tags_query = "SELECT description, id FROM tags"
    tags = insert_into_database(tags_query)

    #fill the metadata table with the relation between title and tag
    for article in articles:

        #Gets id from database for story
        title_param =[article['title']]
        story = insert_into_database("SELECT id FROM stories WHERE title = %s;", title_param)
        story_id = story[0]['id']

        #gets id for tag
        tag_param = [article['tag']]
        tag = insert_into_database("SELECT id FROM tags WHERE description = %s", tag_param)
        tag_id = tag[0]['id']

        meta_param = [story_id, tag_id]
        insert_into_database("INSERT INTO metadata (story_id, tag_id) VALUES (%s, %s);", meta_param)

