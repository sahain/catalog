from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Category, Item
import random

engine = create_engine('postgresql://cat_user:catalog@localhost/cat_db')
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

user1 = User(
    username=name,
    email=email,
    picture="https://randomuser.me/api/portraits/lego/1.jpg")
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
             description="By Victorian times both wood and metal hoops were favorite playthings. The hoop can be trundled along, raced, used for skipping or twirling around the waist.",
             category=cat3)
session.add(item6)
session.commit()

item7 = Item(title="Wooden Hoop", user=user1,
             description="Our hoops are made of solid native hardwoods 28 in. in diameter x 1 1/2 in wide and 1/4 in thick. A dowel is included as a rolling stick, as well as a history card.",
             category=cat3)
session.add(item7)
session.commit()

item8 = Item(title="Cue", user=user1,
             description="If you enjoy playing pool with your own cue stick, this is the product for you. Made by McDermott, this is a pool cue stick that comes with its own carrying case and a host of extras. This will make the game that you love even more enjoyable. Weighing 19 ounces, this is the perfect fit for all levels of pool players. It is also easy to disassemble and store in the carrying case for transport from game to game.",
             category=cat1)
session.add(item8)
session.commit()

item9 = Item(title="Balls", user=user1,
             description="Experience a professional pool experience and perfect your plays with these Billiard Factory Premium Regulation Pool Balls! Never rush your shot and make a strong impression with this complete set of 16 balls that feature expert construction using the finest materials.",
             category=cat1)
session.add(item9)
session.commit()
