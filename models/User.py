from mongoengine import Document, StringField, EmailField, ListField

class User(Document):
    name = StringField(required=True)
    email = EmailField(required=True)
    profile_picture = StringField()
    college = StringField()
    branch = StringField()
    year = StringField()
    skills = ListField(StringField())
    bio = StringField()
    gender = StringField()