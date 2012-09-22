import cgi
import datetime
import urllib
import webapp2
import logging

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api import images

import jinja2
import os

TEMP_BAND_UNDER_50 = 0
TEMP_BAND_50_59 = 5
TEMP_BAND_60_69 = 6
TEMP_BAND_70_79 = 7
TEMP_BAND_OVER_80 = 8

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

class ChildToDress(db.Model):
  """Models an individual ChildToDress entry with an author, kidName, and date."""
  author = db.StringProperty()
  kidName = db.StringProperty(multiline=True)
  date = db.DateTimeProperty(auto_now_add=True)

class ArticleOfClothing(db.Model):
  """Models an article of clothing with type, temperatureBands, image, and name"""
  name = db.StringProperty()
  clothingType = db.CategoryProperty()
  temperatureBands = db.ListProperty(long)
  nonDummyData = db.IntegerProperty()
  image = db.BlobProperty()
  imagePath = db.StringProperty()
  has_image = db.StringProperty()
  

def family_key(family_name=None):
  """Constructs a Datastore key for a Family entity with family_name."""
  return db.Key.from_path('Family', family_name or 'default_family')

class MainPage(webapp2.RequestHandler):
    def get(self):
        
        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
            
        family_name=self.request.get('family_name')

        childrenToDress = db.GqlQuery("SELECT * "
                                "FROM ChildToDress "
                                "WHERE ANCESTOR IS :1 "
                                "ORDER BY date DESC LIMIT 10",
                                family_key(family_name))
        
        childrenToDress = ChildToDress.all()
        childrenToDress.ancestor(family_key(family_name))
        
        """ Only get your own children"""
        user_nickname = 'default'
        if users.get_current_user():
            user_nickname = users.get_current_user().nickname()
        childrenToDress.filter("author = ", user_nickname)

        template_values = {
            'childrenToDress': childrenToDress,
            'url': url,
            'url_linktext': url_linktext,
        }

        template = jinja_environment.get_template('index.html')
        self.response.out.write(template.render(template_values))

class Family(webapp2.RequestHandler):
    def post(self):
      family_name = self.request.get('family_name')
      childToDress = ChildToDress(parent=family_key(family_name))

      if users.get_current_user():
        childToDress.author = users.get_current_user().nickname()

      childToDress.kidName = self.request.get('content')
      childToDress.put()
      
      self.redirect('/?' + urllib.urlencode({'family_name': family_name}))       

class ClothingChoices(webapp2.RequestHandler):
    def post(self):

        temperature = self.request.get('temperature')

        kidName = self.request.get('kid')

        logging.info("Clothing choices for %s at temperature %s",
                      kidName, temperature)
        
        temperatureBand = int(temperature) // 10
        
        if temperatureBand < 5:
            temperatureBand = TEMP_BAND_UNDER_50
        if temperatureBand > 8:
            temperatureBand = TEMP_BAND_OVER_80
        
        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        articlesOfClothing = ArticleOfClothing.all()
        articlesOfClothing.filter("temperatureBands = ", temperatureBand)
        articlesOfClothing.filter("nonDummyData = ", 3)
        
        """ Rewrite this stuff to generate the HTML by hand """
          
        template_values = {
            'temperature': temperature,
            'kidName': kidName,
            'articlesOfClothing': articlesOfClothing,
            'url': url,
            'url_linktext': url_linktext,
        }
        template = jinja_environment.get_template('clothingChoices.html')
        self.response.out.write(template.render(template_values))

class ImgServing(webapp2.RequestHandler):
    def get(self):
        image_key = self.request.get("img_id")
        logging.info("image_key %s", image_key)

        address_k = db.Key.from_path('ArticleOfClothing', image_key)
        articleOfClothing = db.get(address_k)
        logging.info("image name from AOC object %s", articleOfClothing.name)
   
        if articleOfClothing.image:
            logging.info("Drawing image")
            self.response.headers['Content-Type'] = "image/jpg"
            self.response.out.write(articleOfClothing.image)
        else:
            logging.info("No image found")
            self.error(404)
            
            
class ImageChooser(webapp2.RequestHandler):
    def get(self):

      if users.get_current_user():
         url = users.create_logout_url(self.request.uri)
         url_linktext = 'Logout'
      else:
          url = users.create_login_url(self.request.uri)
          url_linktext = 'Login'
            
      template_values = {
          'displayText': "Image chooser",
          'url': url,
          'url_linktext': url_linktext,
          }
      template = jinja_environment.get_template('imageChooser.html')
      self.response.out.write(template.render(template_values))

class ImageUploader(webapp2.RequestHandler):
    def post(self):

        articlesOfClothing = ArticleOfClothing.all()
        articlesOfClothing.filter("nonDummyData = ", 3)
        
        articlesOfClothing.filter("name = ", 'sandals')
        cur_image = self.request.get("sandals_img")
        cur_entities = articlesOfClothing.fetch(5)
        for cur_ent in cur_entities:
            logging.info("Putting sandals image")
            cur_ent.image = db.Blob(cur_image)
            cur_ent.has_image = 'yes'
            cur_ent.put()
            """ self.response.headers['Content-Type'] = "image/jpeg"
            self.response.out.write(cur_image) """

        articlesOfClothing = ArticleOfClothing.all()
        articlesOfClothing.filter("nonDummyData = ", 3)            
        articlesOfClothing.filter("name = ", 'shoes')        
        cur_image = self.request.get("shoes_img")
        cur_entities = articlesOfClothing.fetch(5)
        for cur_ent in cur_entities:
            logging.info("Putting shoes image")
            cur_ent.image = db.Blob(cur_image)
            cur_ent.has_image = 'yes'
            cur_ent.put()
            
        articlesOfClothing = ArticleOfClothing.all()
        articlesOfClothing.filter("nonDummyData = ", 3)
        articlesOfClothing.filter("name = ", 'shorts')        
        cur_image = self.request.get("shorts_img")
        cur_entities = articlesOfClothing.fetch(5)
        for cur_ent in cur_entities:
            logging.info("Putting shorts image")
            cur_ent.image = cur_image
            cur_ent.has_image = 'yes'
            cur_ent.put()

        articlesOfClothing = ArticleOfClothing.all()
        articlesOfClothing.filter("nonDummyData = ", 3)
        articlesOfClothing.filter("name = ", 'long pants')        
        cur_image = self.request.get("pants_img")
        cur_entities = articlesOfClothing.fetch(5)
        for cur_ent in cur_entities:
            logging.info("Putting long pants image")
            cur_ent.image = cur_image
            cur_ent.has_image = 'yes'
            cur_ent.put()

        articlesOfClothing = ArticleOfClothing.all()
        articlesOfClothing.filter("nonDummyData = ", 3)
        articlesOfClothing.filter("name = ", 'long-sleeved shirt')        
        cur_image = self.request.get("ls_shirt_img")
        cur_entities = articlesOfClothing.fetch(5)
        for cur_ent in cur_entities:
            logging.info("Putting long-sleeved shirt image")
            cur_ent.image = cur_image
            cur_ent.has_image = 'yes'
            cur_ent.put()

        articlesOfClothing = ArticleOfClothing.all()
        articlesOfClothing.filter("nonDummyData = ", 3)            
        articlesOfClothing.filter("name = ", 'short-sleeved shirt')        
        cur_image = self.request.get("ss_shirt_img")
        cur_entities = articlesOfClothing.fetch(5)
        for cur_ent in cur_entities:
            logging.info("Putting short-sleeved shirt image")
            cur_ent.image = cur_image
            cur_ent.has_image = 'yes'
            cur_ent.put()
            
        articlesOfClothing = ArticleOfClothing.all()
        articlesOfClothing.fetch(20)
        
        if users.get_current_user():
           url = users.create_logout_url(self.request.uri)
           url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
          
        template_values = {
            'displayText': "hello image uploader",
            'articlesOfClothing': articlesOfClothing,
            'url': url,
            'url_linktext': url_linktext,
        }
        template = jinja_environment.get_template('imageUploader.html')
        self.response.out.write(template.render(template_values))
    

""" Initialize the clothing choices here, no images yet """
"""Do the shirts"""
ls_shirt = ArticleOfClothing(key_name='long-sleeved shirt')
ls_shirt.name = 'long-sleeved shirt'
ls_shirt.clothingType = 'Shirt'
""" yeah yeah yeah. TODO put in the constants."""
ls_shirt.temperatureBands = [0, 5, 6]
ls_shirt.nonDummyData = 3
ls_shirt.put()

articleOfClothing2 = ArticleOfClothing(key_name='short-sleeved shirt')
articleOfClothing2.name = 'short-sleeved shirt'
articleOfClothing2.clothingType = 'Shirt'
""" yeah yeah yeah. TODO put in the constants."""
articleOfClothing2.temperatureBands = [6, 7, 8]
articleOfClothing2.nonDummyData = 3
articleOfClothing2.put()

"""Do the pants"""
articleOfClothing3 = ArticleOfClothing(key_name='long pants')
articleOfClothing3.name = 'long pants'
articleOfClothing3.clothingType = 'Pants'
""" yeah yeah yeah. TODO put in the constants."""
articleOfClothing3.temperatureBands = [0, 5, 6, 7]
articleOfClothing3.nonDummyData = 3
articleOfClothing3.put()

articleOfClothing4 = ArticleOfClothing(key_name='shorts')
articleOfClothing4.name = 'shorts'
articleOfClothing4.clothingType = 'Pants'
""" yeah yeah yeah. TODO put in the constants."""
articleOfClothing4.temperatureBands = [7, 8]
articleOfClothing4.nonDummyData = 3
articleOfClothing4.put()

"""Do the footwear"""
articleOfClothing5 = ArticleOfClothing(key_name='shoes')
articleOfClothing5.name = 'shoes'
articleOfClothing5.clothingType = 'Shoes'
""" yeah yeah yeah. TODO put in the constants."""
articleOfClothing5.temperatureBands = [0, 5, 6, 7, 8]
articleOfClothing5.nonDummyData = 3
articleOfClothing5.put()

articleOfClothing6 = ArticleOfClothing(key_name='sandals')
articleOfClothing6.name = 'sandals'
articleOfClothing6.clothingType = 'Shoes'
""" yeah yeah yeah. TODO put in the constants."""
articleOfClothing6.temperatureBands = [8]
articleOfClothing6.nonDummyData = 3
articleOfClothing6.put()

app = webapp2.WSGIApplication([('/', MainPage),
                              ('/sign', Family),
                              ('/clothingChoices', ClothingChoices),
                               ('/imageChooser', ImageChooser),
                               ('/imageUploader', ImageUploader),
                               ('/imgServing', ImgServing)],
                              debug=True)
