import os
import webapp2
import jinja2
from google.appengine.ext import db
from google.appengine.ext import blobstore
from google.appengine.api import images
from google.appengine.ext.webapp import blobstore_handlers
from urllib import quote
import sys
import traceback

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True, extensions=['jinja2.ext.autoescape'],)
jinja_env.filters['fixurl'] = quote

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)
    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)
    def render(self, template, **kw):   
        self.write(self.render_str(template, **kw))

class ImageHandler(webapp2.RequestHandler):
    def get (self):
        design = db.get(self.request.get("entity_id"))
        if design.image:
            self.response.headers['Content-Type'] = "image/png"
            self.response.out.write(design.image)

class ServeHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self):
        blob_info = blobstore.BlobInfo.get(self.request.get("blob_key"))
        self.send_blob(blob_info)


class Design(db.Model):
    created = db.DateTimeProperty(auto_now_add = True)
    designTitle = db.StringProperty(required = True)
    
    imageBlobCommon = blobstore.BlobReferenceProperty()
    imageBlobs = db.ListProperty(blobstore.BlobKey)
    
    designerName = db.StringProperty(required = True)
    designerPosition = db.StringProperty(required = True)
    designerDetails = db.TextProperty(required = True)
    desc = db.TextProperty(required = True)
    garmentDetails = db.TextProperty(required = True)
    videoUrl = db.StringProperty(required = True)
    videoShareUrl = db.StringProperty(required = False)

    voteCount1 = db.IntegerProperty(default = 0)
    voteCount2 = db.IntegerProperty(default = 0)
    voteCount3 = db.IntegerProperty(default = 0)

    ipaddress = db.StringListProperty(default = [])

 
class MainPage(Handler):
    def get(self):
        designs = db.GqlQuery("SELECT * FROM Design ORDER BY created DESC")
        #design_query = Design.all()
        #designs = design_query.fetch(10)

        imageUrls = {design.key(): [(images.get_serving_url(design.imageBlobs[0]) + '=s453'), (images.get_serving_url(design.imageBlobs[3]) + '=s453'), (images.get_serving_url(design.imageBlobs[6]) + '=s453'), images.get_serving_url(design.imageBlobCommon)] for design in designs}
        self.render("front.htm", designs = designs, imageUrls = imageUrls)

class PostHandler(Handler):
    def get(self):
        design = db.get(self.request.get("entity_id"))
        if design:
            commonImage = images.get_serving_url(design.imageBlobCommon)

            thumbnailUrls = [[], [], []]
            imageUrls = [[], [], []]
            bigImageUrls = [[], [], []]
            
            for i in range(0, 3):
              for imageBlob in design.imageBlobs[i*3 : i*3+3]:
                image_url = images.get_serving_url(imageBlob)
                thumbnailUrls[i].append(image_url + '=s80')
                imageUrls[i].append(image_url + '=s453')
                bigImageUrls[i].append(image_url + '=s1200')

            self.render("second_page.htm", design = design, imageUrls = imageUrls, bigImageUrls = bigImageUrls, commonImage = commonImage, thumbnailUrls = thumbnailUrls, pageType='post', url=self.request.url)


class ImageDetailsHandler(Handler):
  def get(self):
    design = db.get(self.request.get('entity_id'))
    imageIndex = int(self.request.get('image_index'))

    thumbnailUrls = []
    imageUrls = []
    bigImageUrls = []

    for imageBlob in design.imageBlobs[imageIndex*3 : imageIndex*3 + 3]:
      image_url = images.get_serving_url(imageBlob)
      thumbnailUrls.append(image_url + '=s80')
      imageUrls.append(image_url + '=s453')
      bigImageUrls.append(image_url + '=s800')

    self.render("popup_image_details.htm", imageUrls = imageUrls, bigImageUrls = bigImageUrls, thumbnailUrls = thumbnailUrls)


class AboutPageHandler(Handler):
    def get(self):
        self.render("about.htm")

class ContactPageHandler(Handler):
    def get(self):
        self.render("contact.htm")

class SignupPageHandler(Handler):
    def get(self):
        self.render("signup.htm")
    
    def post(self):
        email = self.request.get("email")
        first_name = self.request.get("first_name")
        last_name = self.request.get("last_name")
        postal_code = self.request.get("postal_code")
        country = self.request.get("country")
        emails = Email(email=email, first_name=first_name, last_name=last_name, postal_code=postal_code, country=country)
        emails.put()
        #self.render("signup.htm", email = "")

class Email(db.Model):
    email=db.StringProperty()
    first_name=db.StringProperty()
    last_name=db.StringProperty()
    postal_code=db.StringProperty()
    country=db.StringProperty()
    

class ControlPanel(blobstore_handlers.BlobstoreUploadHandler, Handler):
  def get(self):
    upload_url = blobstore.create_upload_url('/ControlPanel')
    self.render_front(uploadUrl = upload_url)

  def post(self):
    upload_file_common = self.get_uploads('common_picture')
    imageBlobInfoCommon = upload_file_common[0]

    imageBlobInfo = [[], [], []]
    imageBlobs = []

    for i in range(0, 3):
      imageBlobs.append(self.get_uploads('picture%s_main' % str(i+1))[0].key())
      imageBlobs.append(self.get_uploads('picture%s_second' % str(i+1))[0].key())
      imageBlobs.append(self.get_uploads('picture%s_third' % str(i+1))[0].key())

      imageBlobInfo[i].append(self.get_uploads('picture%s_main' % str(i+1))[0])
      imageBlobInfo[i].append(self.get_uploads('picture%s_second' % str(i+1))[0])
      imageBlobInfo[i].append(self.get_uploads('picture%s_third' % str(i+1))[0])

    designTitle = self.request.get("design_title")
    designerName = self.request.get("designer_name")
    designerPosition = self.request.get("designer_position")
    designerDetails = self.request.get("designer_details")
    desc = self.request.get("description")
    garmentDetails = self.request.get("garment_details")
    videoUrl = self.request.get("video_url")
    videoShareUrl = self.request.get("video_share_url")

    if designTitle and designerName and desc and garmentDetails:
       design = Design(designTitle = designTitle, imageBlobCommon = imageBlobInfoCommon.key(), imageBlobs = imageBlobs, designerName = designerName, designerPosition = designerPosition, designerDetails = designerDetails, desc = desc, garmentDetails = garmentDetails, videoUrl = videoUrl, videoShareUrl = videoShareUrl)
       design.put()
       self.redirect("/ControlPanel")
    else:
      error = "One or more mandarory fields missing."# + ' '.join (['test', designTitle, designerName, desc, garmentDetails])
      for imageBlobList in imageBlobInfo:
        for imageBlob in imageBlobList:
          imageBlog.delete()
      upload_url = blobstore.create_upload_url('/ControlPanel')
      self.render_front(designTitle, designerName, designerPosition, designerDetails, desc, garmentDetails, videoUrl, videoShareUrl, error, uploadUrl)
  
  def render_front(self, designTitle = "", designerName = "", designerPosition = "", designerDetails = "", desc = "", garmentDetails = "", videoUrl = "", videoShareUrl = "", error="", uploadUrl=""):
    self.render("control_panel.htm", designTitle = designTitle, designerName = designerName, designerPosition = designerPosition, designerDetails = designerDetails, desc = desc, garmentDetails = garmentDetails, videoUrl = videoUrl, videoShareUrl = videoShareUrl, error = error, uploadUrl = uploadUrl)


class ControlPanelEdit(blobstore_handlers.BlobstoreUploadHandler, Handler):
  def get(self):
    self.design = db.get(self.request.get("entity_id"))
    self.upload_url = blobstore.create_upload_url('/ControlPanelEdit')
    self.render_front()

  def render_front(self):
    self.render("control_panel_edit.htm", design = self.design, uploadUrl = self.upload_url)

  def post(self):
    design = db.get(self.request.get("entity_id"))

    if(len(self.get_uploads('common_picture')) != 0):
      blobstore.delete([design.imageBlobCommon])
      design.imageBlobCommon = self.get_uploads('common_picture')[0].key()

    for i in range(0,3):
      image1 = self.get_uploads('picture%s_main' % str(i+1))
      image2 = self.get_uploads('picture%s_second' % str(i+1))
      image3 = self.get_uploads('picture%s_third' % str(i+1))
      
      if(len(image1) != 0):
        blobstore.delete([design.imageBlobs[i*3]])
        design.imageBlobs[i*3] = image1[0].key()
      
      if(len(image2) != 0):
        blobstore.delete([design.imageBlobs[i*3 + 1]])
        design.imageBlobs[i*3 + 1] = image2[0].key()
      
      if(len(image3) != 0):
        blobstore.delete([design.imageBlobs[i*3 + 2]])
        design.imageBlobs[i*3 + 2] = image3[0].key()

    design.designTitle = self.request.get("design_title")
    design.designerName = self.request.get("designer_name")
    design.designerPosition = self.request.get("designer_position")
    design.designerDetails = self.request.get("designer_details")
    design.desc = self.request.get("description")
    design.garmentDetails = self.request.get("garment_details")
    design.videoUrl = self.request.get("video_url")
    design.videoShareUrl = self.request.get("video_share_url")

    design.put()
    self.redirect("/PostHistory")


class PostHistory(Handler):
  def get(self):
    self.render_front()

  def render_front(self):
    designs = db.GqlQuery("SELECT * FROM Design ORDER BY created DESC")
    self.render("post_history.htm", designs = designs)

class EmailPostHandler(Handler):
  def get(self):
    self.render_front()

  def invalidreg(self, emailkey):
        import re
        emailregex ="^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3\})(\\]?)$"
        if len(emailkey) > 7:
            if re.match(emailregex, emailkey) != None:
                return False
            return True
        else:
            return True

  def render_front(self):
    emails = db.GqlQuery("SELECT email FROM Email")
    emailids = []
    for email in emails:
      if not self.invalidreg(email.email):
        if email.email not in emailids:
          emailids.append(email.email)
    self.render("email_post.htm", emailids = emailids)

class VoteHandler(blobstore_handlers.BlobstoreUploadHandler, Handler):
   def get(self):
       pass

   def post(self):
    self.response.headers = {'Content-Type': 'application/json;charset=UTF-8'}
    voteCount = -1
    designKey = self.request.get('designId')
    voteClass = self.request.get('class')
    ip = os.environ["REMOTE_ADDR"]
    try:
      design = db.get(designKey)
      if voteClass == 'vote1':       
        if ip not in design.ipaddress:
          voteCount = design.voteCount1 + 1
          design.voteCount1 = voteCount;
          design.ipaddress.append(ip);
          del ip;
        else:
          voteCount = design.voteCount1
      elif voteClass == 'vote2':
        if ip not in design.ipaddress:
          voteCount = design.voteCount2 + 1
          design.voteCount2 = voteCount;
          design.ipaddress.append(ip);
          del ip;
        else:
          voteCount = design.voteCount2
      elif voteClass == 'vote3':
        if ip not in design.ipaddress:
          voteCount = design.voteCount3 + 1
          design.voteCount3 = voteCount;
          design.ipaddress.append(ip);
          del ip;
        else:
          voteCount = design.voteCount3
      design.put()
    except:
      self.response.out.write('error: ' + traceback.format_exc())
      return
    self.response.out.write(str(voteCount))
    #{"id"="' + self.request.get('val') + '"}a')
    #self.render("control_panel.htm")
    #self.redirect("www.google.com")

applications = []
applications.append(('/', MainPage))
applications.append(('/ControlPanel', ControlPanel))
applications.append(('/ControlPanelEdit', ControlPanelEdit))
applications.append(('/PostHistory', PostHistory))
applications.append(('/vote', VoteHandler))
applications.append(('/ServeBlob', ServeHandler))
applications.append(('/img', ImageHandler))
applications.append(('/item', PostHandler))
applications.append(('/popupImageDetails', ImageDetailsHandler))
applications.append(('/about', AboutPageHandler))
applications.append(('/contact', ContactPageHandler))
applications.append(('/signup', SignupPageHandler))
applications.append(('/email_post', EmailPostHandler))

app = webapp2.WSGIApplication(applications, debug=True)