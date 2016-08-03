#import bin.flickr_uploader
import sys
from bin.flickr_uploader.fetchDBData import fetchDBData
from bin.flickr_uploader.MainProcedure import processAll
from bin.flickr_uploader.tools import deletePhoto

if __name__=="__main__":
	args=sys.argv

	if "--process" in args:
		processAll()
	elif "--fetchDB" in args:
		if "--dont_reorder_sets" in args:
			keepSetsOrder=True
		else:
			print "Some data will be lost with this operation. Press y to continue, other keys to quit."
			cfm=raw_input("")
			if cfm!="y":
				quit()
			keepSetsOrder=False
		fetchDBData(keepSetsOrder)
	elif "--deletePhoto" in args:
		photoID=args[args.index("--deletePhoto")+1]
		deletePhoto(photoID)
	else:
		print """
	Please specify an operation.
	--fetchDB
		Update the database with new lightroom category

		--dont_reorder_sets
			Keep the "ordered" flag for all photosets. 
			If nothing has been rearranged use this flag.
			
	--process
		Upload, create flickr sets, generate shortLinks
		"""