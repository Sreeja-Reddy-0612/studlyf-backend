from mongoengine import Document, ObjectIdField, StringField

class ConnectionRequest(Document):
    from_ = ObjectIdField(required=True)
    to = ObjectIdField(required=True)
    status = StringField(required=True, choices=['pending', 'accepted', 'rejected'])