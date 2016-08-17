from bin.flickr_uploader.exelProcessing import getShortURLForExtras,getOrderInSet,processAllSheets,outputXML

if __name__=="__main__":
	#print getOrderInSet("b2-p-1")
	#print getOrderInSet("b1-p-1-6")
	processAllSheets()
	getShortURLForExtras()
	outputXML()