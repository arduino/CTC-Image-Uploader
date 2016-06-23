import flickrapi

from configs import flickr_api_key, flickr_api_secret

from UploadPhotos import uploadPictures
from CreateAndFillSets import CreateAndFillSets
from fetchURL import fetchURL
from CreateShortLinks import createAndOutputShortLinks

f = flickrapi.FlickrAPI(flickr_api_key, flickr_api_secret)

if __name__=="__main__":
	f.authenticate_via_browser(perms='delete')

	uploadPictures()
	print "All pictures Uploaded"

	CreateAndFillSets()
	print "All Sets created and filled"

	fetchURL()
	print "All hosted URLs saved"

	createAndOutputShortLinks()
	print "All short links created"