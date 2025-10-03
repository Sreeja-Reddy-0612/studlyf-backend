from mongoengine import Document, ObjectIdField

# class ConnectionRequest(Document):
#     from_ = ObjectIdField(required=True)
#     to = ObjectIdField(required=True)
#     status = StringField(required=True, choices=['pending', 'accepted', 'rejected'])

class Connection(Document):
    user1 = ObjectIdField(required=True)
    user2 = ObjectIdField(required=True)