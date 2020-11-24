import datetime
import hashlib


from mongoengine import *


connect("mytoutiao")

#必须使用try except，否则报停止迭代异常
class CustomQuerySet(QuerySet):
    def to_public_json(self):
        result = []
        try:
            for doc in self:
                json = doc.to_public_json()
                result.append(json)
        except:
            print('error')

        return result


class User(Document):
    email = EmailField(required=True, unique=True)
    username = StringField(max_length=50, required=True, unique=True)
    password = StringField(required=True)
    created = DateTimeField(required=True, default=datetime.datetime.now())
    head_img = StringField(required=True)
    gender = IntField(required=True)
    # user_followed = ListField(ReferenceField("User", reverse_delete_rule=CASCADE))#关注别人

    # meta = {'queryset_class': CustomQuerySet}


    def to_public_json(self):
        data = {
            "id": str(self.id),
            "username": self.username,
            "hashedEmail": hashlib.md5(self.email.encode("utf-8")).hexdigest(),
            "created": self.created.strftime("%Y-%m-%d %H:%M:%S"),
            "head_img": self.head_img,
            "gender": self.gender,
        }

        return data