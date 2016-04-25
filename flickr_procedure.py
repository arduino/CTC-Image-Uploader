import flickrapi
import threading, Queue

from mainDB import CTCPhotoDB

flickr_api_key = u'c1b9a319a2e25dbcd49ca1eea44a5990'
flickr_api_secret = u'f4b371ff599357ed'

upload_queue=Queue.Queue()
db=CTCPhotoDB()

'''

def getFilenameFromRec(rec):
	baseName=rec["file_name"]
	setName=db.getSetByID(photoInfo['set_id'])["name"]
	try:
		filename=getFilename(baseName,setName)
	except e:
		print e
	return filename

def getFilename(baseName,setName):
	filename_woExt="./data/images/"+setName+"/"+baseName
	if os.path.exists(filename_woExt+".jpg"):
		filename=filename_woExt+".jpg"
	elif os.path.exists(filename_woExt+".png"):
		filename=filename_woExt+".png"
	else:
		raise Exception(filename_woExt+"does not exist")
	return filename

def uploadPicture(pic_id):
	photoInfo=db.getPhotoByID(pic_id)
	baseName=photoInfo['file_name']
	setName=db.getSetByID(photoInfo['set_id'])["name"]
	try:
		filename=getFilename(baseName,setName)
		res=f.upload(filename=filename,caption=baseName,callback=xxxx)
	except e:
		print e
'''

'''
def main():
	createPhotoSets()
	uploadPictures()
	addPicsToSets()
	orderPics()
'''

def createPhotoSet(set_id,setName):
	#res=f.photosets.create(title=setName)
	#db.modifySetByID(id=set_id, hosted_url=res.attrib["id"])
	db.modifySetByID(set_id=set_id, hosted_url="bla")

def createPhotoSets():
	#create photosets in flickr
	photoSets=db.getAllSets()
	print photoSets
	for one in photoSets:
		#print type(one)
		createPhotoSet(one["set_id"],one["name"])
	#db.commit()

'''
def uploadPictures():
	createWorkers(5)

	pics=db.getAllPhotos()
	for one in pics:
		if one["synced"]:
			continue

		filename=getFilenameFromRec(one)
		#wait while upload_queue is processed
		while upload_queue.qsize()>100:
			pass
		upload_queue.put(filename)

def createWorkers(num):
	for i in range(num):
		worker=threading.Thread(target=uploadPhoto, args=(i,upload_queue))
		worker.setDaemon(True)
		worker.start()

def uploadPhoto(index, queue):
	global f
	#res=f.upload(filename="data/images/block_2-3_fencing/block_2-3_fencing_step-1.png")
	#print res.find("photoid").text
	while True:
		filename=q.get()
		print "worker {} uploading {}".format(index,queue)
		res=f.upload(filename)
		q.task_done()
'''


if __name__=="__main__":
	global f
	f = flickrapi.FlickrAPI(flickr_api_key, flickr_api_secret)
	f.authenticate_via_browser(perms='delete')

	createPhotoSets()

	#res=f.photos.getInfo(photo_id="26506697451")
	#for one in res.find("photo"):
	#	print one
	#print res.find("photo").find("title").text
	#f.photos.delete(photo_id=res.find("photoid").text)

