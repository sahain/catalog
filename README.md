## Catalog Application

`pip install -r requirements.txt`

<b>to begin</b>, from terminal, enter the following commands:
* `python models.py` - initialize db
* `python seeds.py` - to populate db with some data
* `python catalog.py` - to start app

application should be running on http://localhost:5000

To observe JSON endpoints in action:
* For catalog index: http://localhost:5000/catalog.json
* example of category list: http://localhost:5000/catalog/Billiards/items.json
* example of item: http://localhost:5000/catalog/Billiards/item/Cue.json
