from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Category, Item
import random

engine = create_engine('sqlite:///catalog.db')
Base.metadata.create_all(engine)

DBSession = sessionmaker(bind=engine)
session = DBSession()

first_names = ["Abner", "Bob", "Chrysanthos", "Carlos", "D", "Hagit",
               "Jericho", "Naliaka", "Sandeep", "Rosalyn"]
last_names = ["Adkins", "Fonda", "Mercer", "Poornima", "Epaphras", "Hildegard",
              "Allard", "Sharrow", "Paul", "Popovski", "Sherazi", "Wong"]

fname = random.choice(first_names)
lname = random.choice(last_names)
name = fname + " " + lname
email = fname[0].lower() + lname.lower() + "@example.com"

user1 = User(username=name, email=email, picture="https://randomuser.me/api/portraits/lego/1.jpg")
session.add(user1)
session.commit()

cat1 = Category(name="Billiards", user=user1)
session.add(cat1)
session.commit()

cat2 = Category(name="Chariot Racing", user=user1)
session.add(cat2)
session.commit()

cat3 = Category(name="Hoop Trundling", user=user1)
session.add(cat3)
session.commit()

item6 = Item(title="Metal Hoop", user=user1,
             description="Something something...", category=cat3)
session.add(item6)
session.commit()

item7 = Item(title="Wooden Hoop", user=user1,
             description="Something something...", category=cat3)
session.add(item7)
session.commit()
