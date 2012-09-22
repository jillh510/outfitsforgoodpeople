import webapp2

class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['ContentType'] = 'text/plain'
        self.response.out.write('Hello, webapp World!')

app - webapp2.WSGIApplication([('/', MainPage)],
                              debug=True)
