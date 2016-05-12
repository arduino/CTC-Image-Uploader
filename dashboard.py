from flask import Flask, render_template, send_from_directory
from jinja2 import Environment
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop



from mainDB import CTCPhotoDB
from flickr_procedure import getFilenameFromRec

app = Flask(__name__,static_folder="frontend")
app.debug=True

@app.template_filter("imgPath")
def getImgPath(rec):
	global db
	return getFilenameFromRec(rec,db)

'''
@app.route('/<path:filename>')
def base_static(filename):
    return send_from_directory(app.root_path + '/data/', filename)
'''
@app.route('/')
def hello_world():
	global db
	db=CTCPhotoDB()
	records=[]
	photoSets=db.getAllSets()
	for one in photoSets:
		photos=filter(lambda i:i["synced"]!=0,db.getPhotosBySetID(one["set_id"]))
		record={"set":one,"photos":photos}
		records.append(record)
	return render_template("testMainTemplate.html",records=records)

'''
if __name__ == '__main__':
	app.run(host="0.0.0.0",threaded=True)
'''

if __name__ == '__main__':
  http_server = HTTPServer(WSGIContainer(app))
  http_server.listen(5000)
  IOLoop.instance().start()