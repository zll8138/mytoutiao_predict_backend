import os
import uuid
from datetime import datetime

import jwt

from flask import jsonify, request, send_from_directory

from mongoengine import Q

import config
from models import User, Channel, Img, Article, Cover, Comment
from werkzeug.security import generate_password_hash, check_password_hash

from app import app
from .common import login_required

@app.route("/app/v1_0/authorizations", methods=["POST"])
def app_login():
    # hashed_password = generate_password_hash('246810')
    # User(
    #     mobile='13911111111',
    #     code=hashed_password,
    #     photo='http://toutiao-img.itheima.net/FuyELvGh8jbise6dfoEr0W7luPLq',
    #     gender=1,
    #     name='zhangsan',
    #     intro='zhangsanfeng',
    #     email='zhangsan@qq.com'
    # ).save()

    if not request.json.get("mobile"):
        return jsonify({"error": "mobile not specified"}), 409
    if not request.json.get("code"):
        return jsonify({"error": "code not specified"}), 409

    try:
        mobile = request.json.get("mobile")
        print(mobile)
        users = User.objects(mobile=mobile)
    except:
        print('error')

    user = users.first()

    if user == None:
        return jsonify({"error": "User not found"}), 403


    if not check_password_hash(user.code, request.json.get("code")):
        return jsonify({"error": "Invalid password"}), 401

    token = jwt.encode({
        "userid": str(user.id),
        "name": user.name,
        "email": user.email,
        "created": str(user.created)
    }, app.config["SECRET_KEY"]).decode('utf-8')

    return jsonify({
        "message": 'OK',
        "data": {
            "user": user.name,
            "token": token,
        }
    })

# {
# 	"message": "OK",
# 	"data": {
# 		"name": "13911111116",
# 		"photo": "http://toutiao-img.itheima.net/Fkj6tQi3xJwVXi1u2swCElotfdCi",
# 		"is_media": false,
# 		"intro": "",
# 		"certi": "",
# 		"art_count": 0,
# 		"follow_count": 2,
# 		"fans_count": 0,
# 		"like_count": -4,
# 		"id": 1159803119077425152
# 	}
# }

@app.route("/app/v1_0/user", methods=["GET"])
@login_required
def get_user_info(userid):
    userinfo = User.objects(id=userid).first()
    if not userinfo:
        return jsonify({"message": "Invalid user."})
    else:
        return jsonify({
            "message": 'OK',
            "data": {
                "name": userinfo.name,
                "photo": userinfo.photo,
                "is_media": False,
                "intro": userinfo.intro,
                "certi": "",
                "art_count": 5,
                "follow_count": 5,
                "fans_count": 5,
                "like_count": 5,
                "id": str(userinfo.id)
            }
        })
@app.route("/app/v1_0/channels", methods=["GET"])
@login_required
def client_get_channels(userid):

    channels = Channel.objects()

    return jsonify({
        "message": 'OK',
        "data": {
            "channels": channels.to_public_json()
        }
    })

@app.route("/app/v1_0/user/channels", methods=["PATCH"])
@login_required
def user_add_channel(userid):
    user = User.objects(id=userid).first()
    body = request.json
    channels = body.get('channels')
    channel_id = channels[0]['id']
    channel_add = Channel.objects(id=channel_id).first()
    user.channels.append(channel_add)
    user.save()
    return jsonify({
        "message": 'OK',
        "data": {}
    })

@app.route("/app/v1_0/user/channels", methods=["GET"])
@login_required
def get_user_channels(userid):
    user = User.objects(id=userid).first()

    return jsonify({
        "message": 'OK',
        "data": {
            "channels":[channel.to_public_json() for channel in user.channels]
        }
    })

@app.route("/app/v1_0/user/channels/<string:channelid>", methods=["DELETE"])
@login_required
def delete_user_channel(userid,channelid):
    user = User.objects(id=userid).first()
    channel_del = Channel.objects(id=channelid).first()
    user.channels.remove(channel_del)
    user.save()

    return jsonify({
        "message": 'OK',
        "data": {}
    })

def datatime2timestamp(_date):
    millisec = _date.timestamp() * 1000
    return int(millisec)

def timestamp2datatime(_timestamp):
        d = datetime.fromtimestamp(_timestamp / 1000)
        return d

@app.route("/app/v1_1/articles", methods=["GET"])
@login_required
def get_articles_by_channelid(userid):
    page = 1
    per_page = 10
    param = request.args
    query_timestamp = param.get('timestamp')
    channel_id = param.get('channel_id')
    print(query_timestamp)
    _date = timestamp2datatime(int(query_timestamp))
    articles = Article.objects(channel=channel_id,created__lt=_date).order_by("-created")

    paginated_articles = articles.skip((page - 1) * per_page).limit(per_page)
    if len(paginated_articles) <= 0:
        return jsonify({
            "message": 'OK',
            "data": {
                "pre_timestamp": 0,
                "total_count": articles.count(),
                "page": page,
                "per_page": per_page,
                "results": []
            }
        })
    else:
        pre_timestamp = datatime2timestamp(paginated_articles[len(paginated_articles) - 1].created)
        print(pre_timestamp)
        return jsonify({
                "message": 'OK',
                "data": {
                    "pre_timestamp": pre_timestamp,
                    "total_count": articles.count(),
                    "page": page,
                    "per_page": per_page,
                    "results": paginated_articles.to_public_json_client()
                }
            })

@app.route("/app/v1_0/search", methods=["GET"])
@login_required
def getArticlesBySearchWord(userid):
    page = int(request.args.get("page"))
    per_page = int(request.args.get("per_page"))
    keyword = request.args.get("q")

    articles = Article.objects(Q(title__contains=keyword) | Q(content__contains=keyword))

    paginated_articles = articles.skip((page - 1) * per_page).limit(per_page)

    return jsonify({
        "message": 'OK',
        "data": {
            "total_count": articles.count(),
            "page": page,
            "per_page": per_page,
            "results": paginated_articles.to_public_json_client()
        }
    })

@app.route("/app/v1_0/articles/<string:articleid>", methods=["GET"])
@login_required
def get_article_by_id(userid,articleid):
    # user = User.objects(id=userid).first()
    article = Article.objects(id=articleid).first()

    return jsonify({
        "message": 'OK',
        "data": article.to_public_json_client()
    })

@app.route("/app/v1_0/comments", methods=["POST"])
@login_required
def add_aritcle_comment(userid):
    user = User.objects(id=userid).first()
    body = request.json
    content = body.get('content')
    articleid = body.get('target')
    comment = Comment(
        content=content,
        user=user
    )
    article = Article.objects(id=articleid).first()
    article.comments.append(comment)
    article.save()

    return jsonify({
        "message": 'OK',
        "data": {
            "com_id": -1,
            "target": articleid,
            "art_id": articleid,
            "new_obj": {
                "com_id": -1,
                "aut_id": str(user.id),
                "pubdate": comment.created,
                "content": comment.content,
                "is_top": 0,
                "aut_name": user.name,
                "aut_photo": user.photo,
                "like_count": 0,
                "reply_count": 0
            }
        }
    })

@app.route("/app/v1_0/comments", methods=["GET"])
@login_required
def get_comments_by_articleid(userid):
    # user = User.objects(id=userid).first()
    param = request.args
    articleid = param.get('source')
    per_page = int(param.get('limit'))
    if param.get('offset'):
        page = int(param.get('offset'))
    else:
        page = 0

    article = Article.objects(id=articleid).first()
    comments = article.comments[(page+1) * per_page-1::-1]
    results = [comment.to_public_json() for comment in comments]
    return jsonify({
        "message": 'OK',
        "data": {
            "total_count": len(article.comments),
            "end_id": 1599394834,
            "last_id": 1599394834,
            "results": results
        }
    })