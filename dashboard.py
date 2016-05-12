from flask import Flask, render_template, send_from_directory, jsonify
from jinja2 import Environment
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
import json


from mainDB import CTCPhotoDB
from flickr_procedure import getFilenameFromRec

app = Flask(__name__,static_url_path="", static_folder="frontend/app")
app.debug=True

def convertToJson(rows):
	return json.dumps([dict(one) for one in rows])

@app.route("/photosets/all",methods=["GET"])
def getAllPhotoSets():
	global db
	db=CTCPhotoDB()
	photoSets=db.getAllSets()
	#res=convertToJson(photoSets)
	res=[]
	for one in photoSets:
		res.append({	\
			"title":one["name"],	\
			"set_id":one["set_id"],	\
			"hosted_id":one["hosted_id"],	\
			"state":one["state"]
			})

	return jsonify({"photosets":res})

@app.route("/photosets/<int:set_id>",methods=["GET"])
def getPhotosInSet(set_id):
	global db
	db=CTCPhotoDB()
	photos=db.getPhotosBySetID(set_id)
	#res=convertToJson(photos)
	res=[]
	for one in photos:
		res.append({	\
			"title":one["file_name"],	\
			"order":one["order_in_set"], \
			"local_src":getFilenameFromRec(one,db),	\
			"hosted_src":one["hosted_url"],	\
			"synced":one["synced"]
			})

	return jsonify({"photos":res})


@app.template_filter("imgPath")
def getImgPath(rec):
	global db
	return getFilenameFromRec(rec,db)

'''
@app.route('/<path:filename>')
def base_static(filename):
    return send_from_directory(app.root_path + '/data/', filename)
'''

#@app.route('/')
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

@app.route('/')
def mainView():
	return render_template("index.html")


if __name__ == '__main__':
	app.run(host="0.0.0.0",threaded=True)
'''

if __name__ == '__main__':
  http_server = HTTPServer(WSGIContainer(app))
  http_server.listen(5000)
  IOLoop.instance().start()
'''
