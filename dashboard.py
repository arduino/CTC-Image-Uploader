from flask import Flask, render_template
from jinja2 import Environment

from mainDB import CTCPhotoDB
from flickr_procedure import getFilenameFromRec

app = Flask(__name__,static_folder='data')
app.debug=True

@app.template_filter("imgPath")
def getImgPath(rec):
	global db
	return getFilenameFromRec(rec,db)

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


if __name__ == '__main__':
	app.run()