"""
Get images from a folder and

- push them to Flickr one by one
- get a bitly url short address for each image
- add the combined duo to a CSV file for later handling in a spreadsheet editor
- add the outcome to a PDF with a scaled version of the image for visual reference of the operation

This is meant to help the process of pushing large sets of images from the
production set to an online platform that will take care of re-scaling and
serving the pictures. In the long run we should consider an alternative to Flickr.

 The CSV file will allow syncing captions in different languages for a certain
 set of pictures. It should be possible -with a later script to be designed- to
 export the CSV file as a series of ASCIIDOC files separated in folders by
 language. Those files will later be included inside the corresponding ASCIIDOC
 version of a tutorial by invoking a certain TAG.

Reference links:

- https://pypi.python.org/pypi/pyshorteners (not used)
- https://github.com/jasminegao/bitlyAPI_tutorials (note, bundles are no more operative)
- https://github.com/bitly/bitly-api-python (official API for python)
- http://dev.bitly.com/my_apps.html (bitly apps)
- https://www.flickr.com/services/api/misc.urls.html (flickr urls demistified)
- https://stuvel.eu/flickrapi-doc/1-intro.html#installation (installing flickr API)
- https://www.flickr.com/services/api/replace.api.html (flickr can replace pictures)
- https://www.flickr.com/services/api/flickr.photos.getInfo.html (xml format for the flickr API response)
-

(c) 2016 D. Cuartielles for Arduino LLC
Code under GPLv3
"""
import sqlite3
import string
import os
import sys
import flickrapi
import webbrowser
import requests
import json
import pprint
from itertools import groupby, chain

from xml.etree import ElementTree
from reportlab.platypus.tables import Table
from reportlab.lib.units import cm, inch
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import utils
from reportlab.platypus import (
    BaseDocTemplate,
    PageTemplate,
    NextPageTemplate,
    PageBreak,
    Frame,
    Image,
    Paragraph
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.colors import (
    black,
    purple,
    white,
    grey,
    yellow
)

##################################
# parameters you need to configure
##################################
# title to the report to be performed
documentTitle = "Flickr Uploadr + BitLy Shortenr Report"
# path for the images to include
thePath = "/home/blushingboy/Dropbox/development/sketchbooks/python/flickr-bitly/block_2-3_fencing"
# name of the report without extension
reportName = "flickr_uploadr-bitly_shortenr"
# logo
filepathLogo = "images/ctc_logo.png"
# Flickr information
flickr_api_key = u'c1b9a319a2e25dbcd49ca1eea44a5990'
flickr_api_secret = u'f4b371ff599357ed'
# BitLy information, generated at: https://bitly.com/a/oauth_apps
bitly_token = u'4555ea0b8d63a11269e82c733d5d1d2158d61d02'

##################################
# parameters you shouldn't touch too often
##################################
# insert the database name
filename = "data/LightroomCatalog.lrcat"
# database tables were we will perform the search
dbTableCaptions = "AgLibraryIPTC"
dbTableImages = "AgLibraryCollectionImage"
dbTableFiles = "AgLibraryFile"
dbTableCollections = "AgLibraryCollection"
dbTableAdobeImages = "Adobe_Images"
# collection we are working with
idCollection = "683635"  # this is the current collection for the Fencing example
idParentCollection = "683583"  # this is the collection that contains the whole system
# collection to exclude
idExclude = "671489"
# list of collections
listCollections = []
# sortable list
listCTCpictures = []
# verbose level
ver = 0

##################################

def stylesheet():
    styles= {
        'default': ParagraphStyle(
            'default',
            fontName='Helvetica',
            fontSize=14,
            leading=12,
            leftIndent=0,
            rightIndent=0,
            firstLineIndent=0,
            alignment=TA_LEFT,
            spaceBefore=0,
            spaceAfter=0,
            bulletFontName='Helvetica',
            bulletFontSize=10,
            bulletIndent=0,
            textColor= black,
            backColor=None,
            wordWrap=None,
            borderWidth= 0,
            borderPadding= 0,
            borderColor= None,
            borderRadius= None,
            allowWidows= 1,
            allowOrphans= 0,
            textTransform=None,  # 'uppercase' | 'lowercase' | None
            endDots=None,
            splitLongWords=1,
        ),
    }
    styles['title'] = ParagraphStyle(
        'title',
        parent=styles['default'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=42,
        alignment=TA_CENTER,
    )
    styles['alert'] = ParagraphStyle(
        'alert',
        parent=styles['default'],
        leading=14,
        backColor=yellow,
        borderColor=black,
        borderWidth=1,
        borderPadding=5,
        borderRadius=2,
        spaceBefore=10,
        spaceAfter=10,
    )
    styles['fillIn'] = ParagraphStyle(
        'fillIn',
        parent=styles['default'],
        leading=14,
        borderPadding=5,
        borderRadius=2,
        spaceBefore=10,
        spaceAfter=10,
    )
    styles['paragraph'] = ParagraphStyle(
        'paragraph',
        parent=styles['default'],
        leading=14,
        borderPadding=5,
        borderRadius=2,
        spaceBefore=10,
        spaceAfter=10,
    )
    return styles

def foot1(canvas,doc):
    canvas.saveState()
    canvas.setFont('Helvetica',12)
    canvas.drawString(inch, 0.75 * inch, "Page %d" % doc.page)
    canvas.restoreState()

def foot2(canvas,doc):
    canvas.saveState()
    canvas.setFont('Helvetica',12)
    canvas.drawString(inch, 0.75 * inch, "Page %d - these images are property of Arduino Verkstad AB - CONFIDENTIAL" % doc.page)
    canvas.restoreState()

def get_image(path, width=1*cm):
    img = utils.ImageReader(path)
    iw, ih = img.getSize()
    aspect = ih / float(iw)
    return Image(path, width=width, height=(width * aspect))

##################################

# class to do the sorting in a pretty way
class CTCpicture:
    def __init__(self, idImage, collection, idFile, filename, caption, posImage):
        self.idImage = idImage
        self.collection = collection
        self.idFile = idFile
        self.filename = filename
        self.caption = caption
        self.posImage = posImage

##################################

## funciton to authenticate any operations to be made on flickr
def flickrAuthenticate():
    # instantiate the flickr API into the flickr object
    flickr = flickrapi.FlickrAPI(flickr_api_key, flickr_api_secret)
    
    print('Flickr: authentication phase')
    
    # Only do this if we don't have a valid token already
    if not flickr.token_valid(perms='read'):
    
        # Get a request token
        flickr.get_request_token(oauth_callback='oob')
        
        # Open a browser at the authentication URL. Do this however
        # you want, as long as the user visits that URL.
        authorize_url = flickr.auth_url(perms=u'read')
        webbrowser.open_new_tab(authorize_url)
    
        # Get the verifier code from the user. Do this however you
        # want, as long as the user gives the application the code.
        verifier = unicode(raw_input('Verifier code: '))
    
        # Trade the request token for an access token
        flickr.get_access_token(verifier)
        
        # Return success
        print('Flickr: auth succeeded')
        return true
        
    # Return failure
    print('Flickr: auth failed')
    return false

## function to get information about a picture straigth from flickr
## XXX: for PNGS you need to use the original picture and not the reduced size one
def flickrGetPictureData(photo_id='26242764326'):    
    print('Flickr: get information from image' + photo_id)
    resp = flickr.photos.getInfo(photo_id)
    
    # Parse the data out of the returned string
    farmid = '1';
    photo = resp.findall('photo')[0]
    serverid = photo.attrib['server']
    id = photo.attrib['id']
    secret = photo.attrib['secret']
    originalsecret = photo.attrib['originalsecret']
    originalformat = photo.attrib['originalformat']
    
    title = (photo.findall('title')[0]).text
    description = (photo.findall('description')[0]).text
    
    # Make your own url according to https://www.flickr.com/services/api/misc.urls.html
    photourl = "https://farm" + farmid + ".staticflickr.com/" + serverid + "/" + id + "_" + secret + "_z.jpg"
    webbrowser.open_new_tab(photourl)
    
    # Report some data to STDOUT before returning
    print('Flickr: image title\t' + title)
    print('Flickr: image desc\t' + description)
    print('Flickr: image format\t' + originalformat)
    print('Flickr: image url\t' + photourl)
    
    #print(repr(resp))
    
    # Return the photourl, the only part we actually need
    return photourl

## This is the bitly shorten function that will be used to do what it says
def bitlyShorten(photourl):
    # Prepare the query given the token
    query_params = {
        'access_token': bitly_token,
        'longUrl': photourl}
    
    # Prepare the endpoint, and request the url shortener
    endpoint = "https://api-ssl.bitly.com/v3/shorten"
    response = requests.get(endpoint, params = query_params)
    
    # The data comes back as a json string
    data = json.loads(response.content)
    
    # Print out the result
    print('BitLy: shorten url\t' + data['data']['url'])
    
    # Return the result
    return data['data']['url']

# end early
#XXXquit()

##################################

## generate the array listCollections carrying all of the collections
## that belong to our general export action. This operation is done taking
## the id of the parent collection as a reference
def getCollections(cursor):
    # get the information from the table with the collections
    command = "SELECT id_local,name FROM " + dbTableCollections + " WHERE parent LIKE '" + idParentCollection + "'"
    cursor.execute(command)
    res=[]
    for row in cursor:
        # if it is in the collection, then get the id and print it
        res.append(row)
        '''
        for field in row.keys():
            if type(row[field]) is int:
                str2 = str(row[field])
            elif type(row[field]) is unicode:
                str2 = (row[field]).encode('utf8')
            else:
                str2 = str(row[field])
            if str(field) == "id_local" and str2 != idExclude:
                listCollections.append(str2)
                if ver == 1:
                    print str2
        '''
    return res

## 
def getCollectionName(cursor):
    # get the information about the collection name
    command = "SELECT * FROM " + dbTableCollections + " WHERE id_local LIKE '" + idCollection + "'"
    cursor.execute(command)
    collectionName = ""
    for row in cursor:
        # if it is in the collection, then get the id and print it
        '''
        for field in row.keys():
            if type(row[field]) is int:
                str2 = str(row[field])
            elif type(row[field]) is unicode:
                str2 = (row[field]).encode('utf8')
            else:
                str2 = str(row[field])
            if str(field) == "name":
                collectionName = str2
                if ver == 1:
                    print str2
        '''
    # Return the name of the collection
    return collectionName

##
def getSetName(cursor):
    # get the information about the set name
    command = "SELECT * FROM " + dbTableCollections + " WHERE id_local LIKE '" + collection + "'"
    cursor.execute(command)
    setName = ""
    for row in cursor:
        # if it is in the collection, then get the id and print it
        for field in row.keys():
            if type(row[field]) is int:
                str2 = str(row[field])
            elif type(row[field]) is unicode:
                str2 = (row[field]).encode('utf8')
            else:
                str2 = str(row[field])
            if str(field) == "name":
                setName = str2
                if ver == 1:
                    print str2

    # Return the name of the set
    return setName

##
def getImagesInSet(cursor, collection):
    command = "SELECT image, positionInCollection FROM " + dbTableImages + " WHERE collection LIKE '" + str(collection) + "'"
    cursor.execute(command)
    listImages=[]
    for row in cursor:
        # if it is in the collection, then get the id and print it
        listImages.append(row)
        #idImage = row["image"]
        #posImage = row["positionInCollection"]
        '''
        for field in row.keys():
            if type(row[field]) is int:
                str2 = str(row[field])
            elif type(row[field]) is unicode:
                str2 = (row[field]).encode('utf8')
            else:
                str2 = str(row[field])
            if str(field) == "image":
                idImage = str2
        for field in row.keys():
            if type(row[field]) is int:
                str2 = str(row[field])
            elif type(row[field]) is unicode:
                str2 = (row[field]).encode('utf8')
            else:
                str2 = str(row[field])
            if str(field) == "positionInCollection":
                posImage = str2
        if idImage != "":
            # print collection + ":" + idImage + ":" + posImage
            #listImages.append(collection + ":" + str(idImage) + ":" + str(posImage))
        '''
    return listImages

##
def getImgFiles(cursor, idImages):
    command = '''SELECT {0}.id_local, {1}.baseName, {2}.caption
    FROM {0}
    INNER JOIN {1}
    ON {0}.rootFile={1}.id_local
    INNER JOIN {2}
    ON {0}.id_local={2}.image
    WHERE {0}.id_local in ({3});
    '''.format(dbTableAdobeImages,dbTableFiles,dbTableCaptions,",".join(str(i) for i in idImages))
    cursor.execute(command)
    listFiles=[]
    for row in cursor:
        listFiles.append(row)
    return listFiles

    #"SELECT "+dbTableFiles+".baseName FROM " + dbTableAdobeImages + "INNHER JOIN "+dbTableFiles+" ON  WHERE id_local LIKE '" + idImage + "'"
def getRootFiles(cursor,collection,idImage,posImage,rootFile,listRootFiles):
    # make the search
    command = "SELECT * FROM " + dbTableAdobeImages + " WHERE id_local LIKE '" + idImage + "'"
    cursor.execute(command)
    for row in cursor:
        for field in row.keys():
            if type(row[field]) is int:
                str2 = str(row[field])
            elif type(row[field]) is unicode:
                str2 = (row[field]).encode('utf8')
            else:
                str2 = str(row[field])
            if str(field) == "rootFile":
                rootFile = str2
        if rootFile != "":
            #print collection + ":" + idImage + ":" + posImage + ":" + rootFile
            listRootFiles.append(collection + ":" + idImage + ":" + posImage + ":" + rootFile)
            #countImages = countImages + 1

##
def getBaseName(cursor,collection,idImage,posImage,rootFile,listFiles):
    # make the search
    command = "SELECT * FROM " + dbTableFiles + " WHERE id_local LIKE '" + rootFile + "'"
    cursor.execute(command)
    for row in cursor:
        baseName=""
        for field in row.keys():
            if type(row[field]) is int:
                str2 = str(row[field])
            elif type(row[field]) is unicode:
                str2 = (row[field]).encode('utf8')
            else:
                str2 = str(row[field])
            if str(field) == "baseName":
                baseName = str2
        if baseName != "":
            #print collection + ":" + idImage + ":" + posImage + ":" + rootFile + ":" + baseName
            listFiles.append(collection + ":" + idImage + ":" + posImage + ":" + rootFile + ":" + baseName)

##
def getCaption(cursor,collection,idImage,posImage,rootFile,baseName,listCTCpicturesLocal):
    # make the search
    command = "SELECT * FROM " + dbTableCaptions + " WHERE image LIKE '" + idImage + "'"
    cursor.execute(command)
    for row in cursor:
        for field in row.keys():
            if type(row[field]) is int:
                str2 = str(row[field])
            elif type(row[field]) is unicode:
                str2 = (row[field]).encode('utf8')
            else:
                str2 = str(row[field])
            if str(field) == "caption":
                caption = str2
        if baseName != "":
            #print collection + ":" + idImage + ":" + posImage + ":" + rootFile + ":" + baseName + ":" + caption
            listCaptions.append(collection + ":" + idImage + ":" + posImage + ":" + rootFile + ":" + baseName + ":" + caption)
            if posImage != "None":
                posImage = "{:.2f}".format(float(posImage))
                listCTCpicturesLocal.append(CTCpicture(idImage, collection, rootFile, baseName, caption, posImage))
            else:
                listCTCpicturesLocal.append(CTCpicture(idImage, collection, rootFile, baseName, caption, -1))


## This is the function to render the PDF for one collection given the CSS defined earler
def renderCollectionPDF(filepathLogo,reportName,setName,collectionName,listCTCpicturesLocal,countImages):
    #and here we render MF PDFs!!
    #styles=getSampleStyleSheet()
    Elements=[]
    #doc = BaseDocTemplate(reportName + listCTCpicturesLocal[0].collection + ".pdf",showBoundary=0,leftMargin=0, rightMargin=0, topMargin=0, bottomMargin=0, pagesize=A4)
    doc = BaseDocTemplate(reportName + "-" + setName + ".pdf",showBoundary=0,leftMargin=0, rightMargin=0, topMargin=0, bottomMargin=0, pagesize=A4)
    styles=stylesheet();

    #normal frame as for SimpleFlowDocument
    frameT = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')

    #Two Columns
    frame1 = Frame(doc.leftMargin, doc.bottomMargin, doc.width/2-6, doc.height/2-6, id='row1col1')
    frame2 = Frame(doc.leftMargin+doc.width/2+6, doc.bottomMargin, doc.width/2-6, doc.height/2-6, id='row1col2')
    frame3 = Frame(doc.leftMargin, doc.bottomMargin+doc.height/2-6, doc.width/2-6, doc.height/2-6, id='row2col1')
    frame4 = Frame(doc.leftMargin+doc.width/2+6, doc.bottomMargin+doc.height/2-6, doc.width/2-6, doc.height/2-6, id='row2col2')

    ##################################

    # title page
    # XXX add any extra information here
    try:
        Elements.append(get_image(filepathLogo, width=15*cm))
    except:
        Elements.append(Paragraph("problems reading image: " + filepathLogo,styles['alert']))
    Elements.append(Paragraph("Report for: <br />" + collectionName,styles['title']))
    Elements.append(Paragraph("Set: <br />" + setName,styles['title']))
    Elements.append(Paragraph("Please fill in this data for further reference:",styles['paragraph']))
    data=[("Date:","____________________","Room:","____________________"),("Photographer:","____________________","Signature:","____________________"),("Hand Model:","____________________","Signature:","____________________"),("Tech Support:","____________________","Signature:","____________________")]
    table = Table(data, colWidths=135, rowHeights=40)
    Elements.append(table)
    Elements.append(Paragraph("Other notes (please elaborate):",styles['paragraph']))
    Elements.append(NextPageTemplate('TwoCol'))
    Elements.append(PageBreak())

    index = 1
    for p in listCTCpicturesLocal:
        #print p.collection + ":" + p.idImage + ":" + str(p.posImage) + ":" + p.idFile + ":" + p.filename + ":" + p.caption

        # get the existing files
        filepath = thePath + p.filename + ".jpg"
        #Elements.append(Paragraph(filepath,styles['Normal']))
        try:
            Elements.append(get_image(filepath, width=10*cm))
        except:
            Elements.append(Paragraph("problems reading image: " + filepath,styles['alert']))
        Elements.append(Paragraph("<b>Set:</b> " + setName +"<br /><b>Filename:</b> " + p.filename + "<br /><b>Notes:</b> " + p.caption,styles['paragraph']))
        Elements.append(Paragraph("<b>Image:</b> " + str(index) + " of " + str(countImages) + "<br /><br /><br />",styles['paragraph']))
        index = index + 1

    #Elements.append(Paragraph("Frame two columns,  "*500,styles['Normal']))
    Elements.append(NextPageTemplate('OneCol'))
    Elements.append(PageBreak())

    # closing page
    Elements.append(Paragraph("Disclaimer: ",styles['title']))
    Elements.append(Paragraph("This document is property of Arduino Verkstad AB and it is confidential. If you found this document please send it to: <br /><b>Arduino Verkstad AB</b><br />Anckargripsgatan 3<br />21119 Malmo<br />Sweden",styles['paragraph']))
    Elements.append(Paragraph("The contents of this document cannot be shared under no circumstances. If you are working under a contract for Arduino Verkstad AB, you are NOT entitled to share this information with anyone.",styles['paragraph']))
    doc.addPageTemplates([PageTemplate(id='OneCol',frames=frameT,onPage=foot1), PageTemplate(id='TwoCol',frames=[frame3,frame4,frame1,frame2],onPage=foot2), ])

    #start the construction of the pdf
    doc.build(Elements)

############################################################################
##
## MODE OF OPERATION
## 
## 1) you need to look into the DB for the collections which parent is the
##    one corresponding to the one defined
##
## 2) you need to gather all of the information you need about the different
##    files, like their root folder, the actual file name, etc
##
## 3) you need to navigate the array of images one by one and push them to 
##    Flickr
##
## 4) for the recently uploaded image, get it's flickr information
##
## 5) with the flickr information, mainly the photourl, generate the short url
##
## 6) store the photourl, shorturl and other relevant information into a single
##    array that can be used later to generate reports
##
## 7) given the array of final information, render a PDF with views of the images
##    but also a CSV file with the URLs to make easier the automation of the process
##
## NOTE: remember that you need the PNGs in original size, while the JPGs gotta be 640 wide
##
############################################################################

## The Loop that will look into the DB
with sqlite3.connect(filename) as conn:
    # Create a DB handler
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get the list of collections under a certain parent
    listCollections=getCollections(cursor)
    
    print "Begin!"
    # Get the information from the table with the images in the collections
    for collection in listCollections:
        print collection
        # Init the arrays to be used when navigating a collection
        # List of images
        listImages = []
        
        # List of rootFiles
        listRootFiles = []
        
        # List of files
        listFiles = []
        
        # List of files with captions
        listCaptions = []
        
        # Clean up the results list
        listCTCpicturesLocal = []

        # Get the name of the set we are working with
        setName = collection[1]
        
        # Get the images in the set (populates listImages[])
        listImages=getImagesInSet(cursor, collection[0])
        print len(listImages)
        listImages=listImages[:10]
        imgFiles=getImgFiles(cursor, [i[0] for i in listImages])

        lst=sorted(chain(listImages,imgFiles),key=lambda x:x[0])
        resultList=[]
        for k,g in groupby(lst,key=lambda x:x[0]):
            d={}
            for dct in g:
                d.update(dct)
            d=dict((key,value) for key,value in d.iteritems() if key in ("id_local","baseName","caption","positionInCollection"))
            resultList.append(d)

        resultList=sorted(resultList, key=lambda x: x["positionInCollection"])

        #renderCollectionPDF(filepathLogo,reportName,setName,setName,resultList,len(listImages))
        '''
        # Get the information from the table with the rootFiles in the collections
        countImages = 0
        for image in listImages:
            imgFiles=getImgFiles(cursor, collection[0])
            print imgFiles
            quit()


        for image in listImages:
            # Extract the image information
            collection = (image.split(":"))[0]
            idImage = (image.split(":"))[1]
            posImage = (image.split(":"))[2]
            rootFile = ""

            # Get the list of root files (populates listRootFiles[])
            getRootFiles(cursor,collection,idImage,posImage,rootFile,listRootFiles)

        #print listRootFiles
            
        # Get the information from the table with the files in the collections
        for rootFileRow in listRootFiles:
            # Extract the image information
            collection = (rootFileRow.split(":"))[0]
            idImage = (rootFileRow.split(":"))[1]
            posImage = (rootFileRow.split(":"))[2]
            rootFile = (rootFileRow.split(":"))[3]
            baseName = ""

            # Get the list of basenames (populates listFiles[])
            getBaseName(cursor,collection,idImage,posImage,rootFile,listFiles)

        #print listFiles

        # get the information from the table with the captions in the collections
        for fileRow in listFiles:
            # extract the image information
            collection = (fileRow.split(":"))[0]
            idImage = (fileRow.split(":"))[1]
            posImage = (fileRow.split(":"))[2]
            rootFile = (fileRow.split(":"))[3]
            baseName = (fileRow.split(":"))[4]
            caption = ""

            # Get the caption for a certain image (populates listCaptions[] and listCTCpicturesLocal[])
            getCaption(cursor,collection,idImage,posImage,rootFile,baseName,listCTCpicturesLocal)
        
        print len(listCTCpicturesLocal)
        '''

        # Sort the list and add it to the global list
        #listCTCpicturesLocal = sorted(listCTCpicturesLocal, key=lambda pic: pic.posImage)
        #print listCTCpicturesLocal
        ### HERE IS WHERE WE NEED TO UPLOAD AND GENERATE SHORTURL

        # Render the PDF for this collection
        #renderCollectionPDF()
