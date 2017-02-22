# CTC-Image-Uploader
This python script gets collection information from a LightRoom database, uploads all the images to flickr, generates bitly short url, and output a pdf.
It must be used together with a lightroom database file(lcat) and photos/files organized in the specific pattern.

It is recommanded to keep the current database file(main.db).

Extra configuration can be found in `bin/configs.py`


## Workflow
Most of the following procedures must be executed in commandline. SQLite browser(http://sqlitebrowser.org/) is also required for working with the data.

### Install
1. Clone the repository into a local directory. Make sure you stay in dev branch
2. Install python 2.7.13. Follow the instructions in https://www.cyberciti.biz/faq/install-python-linux/ to install 2.7.13
3. Install virtualenv. Follow the instructions in https://virtualenv.pypa.io/en/stable/installation/ Note: you may need to install pip before running the commands
4. Start the venv by running `source venv/bin/activate`
5. Install requirements from requirements.txt. Type `pip install requirements.txt`

### To add new photos
1. Make sure you're in the virtual environment by running `source venv/bin/activate`
1. Copy the new Lightroom Catalog.lcat to data folder. It is highly recommended to make a backup of the old one each time you do it.
2. Copy the new photos to data/images. Note that they should be in folders of their respecitve sets. e.g. Block_01-01_red_Snake, Concept_01-01_Programming, References_01_Breadboard_Noneslideshow. Notice the cases, underscore and noneslideshow surfix.
3. Make a copy of the old db file, mainDB.db, and run `python flickr_uploader.py --fetchDB`. If nothing has been rearranged, also use `--dont_reorder_sets` flag(?)
3. Run `python flickr_uploader.py --process`, and wait for finish. The result is in `testExtra.txt`(extras) and `testRes.txt`(photos)

### To replace existing photos
1. Make sure you're in the virtual environment by running `source venv/bin/activate`
1. Find out the photo_id of the targets, and the set_id of the photo set with SQLite Browser
2. Run `python flickr_uploader.py --deletePhoto (photoID)` on individual photo_ids
3. Run `python flickr_uploader.py --reorderSet (setID)` on the photo set
4. Run `python flickr_uploader.py --process` 

### To update extra files
1. Make sure you're in the virtual environment by running `source venv/bin/activate`
1. Make changes in the Exel sheets, please refer to the existing Exel files when making changes. If you want to change the structure, more information is available in `bin/configs.py`
2. Run `python ExelActions.py` 

### To change url shortening provider
1. With SQLite browser, open maindb.db
2. In Execute SQL tab, write the following commands: `UPDATE sets SET shortlinked = 0` and press run button
3. Modify `bin/configs.py`, and change the yourls_URL field.
3. Open commandline, go to the path of flickrUploader.
4. Make sure you're in the virtual environment by running `source venv/bin/activate`
5. Run `python flickr_uploader.py --process` 
