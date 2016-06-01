import flickrapi

from configs import flickr_api_key, flickr_api_secret

from UploadPhotos import uploadPictures
from CreateAndFillSets import CreateAndFillSets
from fetchURLAndGenShortLink import fetchURLAndGenShortLink


f = flickrapi.FlickrAPI(flickr_api_key, flickr_api_secret)

if __name__=="__main__":
	f.authenticate_via_browser(perms='delete')

	uploadPictures()
	print("all pictures Uploaded")

	CreateAndFillSets()
	print("All Sets created and filled")

	fetchURLAndGenShortLink()
	print("All hosted URLs saved, short links created")

