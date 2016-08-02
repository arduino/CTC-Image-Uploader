import xml.etree.ElementTree as ET
import flickrapi
from bin.flickr_uploader.configs import flickr_api_key, flickr_api_secret

f = flickrapi.FlickrAPI(flickr_api_key, flickr_api_secret)


def deletePhotosInAlbum(set_hosted_ID):
	try:
		res=f.photosets.getPhotos(photoset_id=set_hosted_ID)
	except Exception as e:
		print e
	else:
		photos=res.find("photoset").findall("photo")
		for one in photos:
			photo_id=one.attrib["id"]
			print photo_id
			f.photos.delete(photo_id=photo_id)

	try:
		f.photosets.delete(photoset_id=set_hosted_ID)
	except Exception as e:
		print e
	print "photoset {} deleted".format(set_hosted_ID)

def parseAllSetsDoc():
	tree=ET.parse("data/allPhotoSets.xml")
	root=tree.getroot()
	ids=[]
	for one in root.iter("photoset"):
		#print one.attrib["id"]
		#ids.append(one.attrib["id"])
		deletePhotosInAlbum(one.attrib["id"])
	

if __name__=="__main__":
	parseAllSetsDoc()
	#deletePhotosInAlbum("72157670600289116")
	#deletePhotosInAlbum("72157670028548592")
	#deletePhotosInAlbum("72157669655549430")
	#deletePhotosInAlbum("72157670060291001")
