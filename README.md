# CTC-Image-Uploader
This python script gets collection information from a LightRoom database, uploads all the images to flickr, generates bitly short url, and output a pdf 

## Workflow
### Install
1. Install python 2.x
2. Install virtualenv
3. Install requirements from requirements.txt
4. Start the venv by running source venv/bin/activate
(elaborate more)

### To add new photos
1. Copy the new Lightroom Catalog.lcat to data folder. Make a backup of the old one is highly recommended.
2. Copy the new photos to data/images. Note that they should be in folders of their respecitve sets. e.g. Block_01-01_red_Snake, Concept_01-01_Programming, References_01_Breadboard_Noneslideshow. Notice the cases, underscore and noneslideshow surfix.
3. Make a copy of the old db file, mainDB.db, and run `python flickr_uploader.py --fetchDB`. If nothing has been rearranged, also use `--dont_reorder_sets` flag(?)
3. Run `python flickr_uploader.py --process`, and wait for finish. The result is in `testExtra.txt`(extras) and `testRes.txt`(photos)

### To replace existing photos
1. Find out the photo_id of the targets, and the set_id of the photo set with SQLite Browser
2. Run `python flickr_uploader.py --deletePhoto (photoID)` on individual photo_ids
3. Run `python flickr_uploader.py --reorderSet (setID)` on the photo set
4. Run `python flickr_uploader.py --process` 
