# -*- coding: utf-8 -*-

import urllib2
import json

import redis

from flask import Flask, render_template, request, jsonify


app = Flask(__name__)
r = redis.StrictRedis(host='localhost', port='6379', db=0)

# users id-counter
if not r.get('counter'):
    r.set('counter', 1)


@app.route('/')
def hello_flask_redis():
    repos_list = (
        [{'name': x, 'id': int(y)} for (x,y) in
         r.zrange("user_list", 0, -1, withscores=True)]
        if r.exists('user_list') else []
    )

    return render_template('index.html', repos_list=repos_list)


@app.route('/get-repo', methods=['POST', ])
def get_repo():

    user = request.json['inputUser']
    repo = request.json['inputRepo']
    url = u'https://api.github.com/repos/{0}/{1}/commits'.format(user, repo)
    result = []
    final = {}
    try:
        response = urllib2.urlopen(url)
    except urllib2.HTTPError:
        final = {'commits': []}
    # if russian symbols
    except Exception:
        final = {'commits': []}
    else:
        data = json.loads(response.read())

        user_repo = '{0}:{1}'.format(user, repo)
        user_id = r.get(user_repo)
        is_new_repo = False

        if user_repo not in r.zrange("user_list", 0, -1):
            is_new_repo = True

            # set user_id
            user_id = r.get('counter')

            # increase users id-counter
            r.incr('counter')

            r.zadd('user_list', user_id, user_repo)

        else:
            # delete old commits
            for old_commit_id in r.lrange("commits:{0}".format(user_id), 0, -1):
                r.delete(old_commit_id)
            r.delete("commits:{0}".format(user_id))
        # add commits
        for ind, commit in enumerate(data, start=1):
            sha = commit["sha"]
            r.rpush("commits:{0}".format(user_id), sha)

            info = {
                'author': commit['commit']['committer']['name'],
                'message': commit['commit']['message'],
                'date': commit['commit']['committer']['date'],
                'user_id': user_id
            }
            r.hmset(sha, info)

            info['id'] = sha
            info['index'] = ind

            result.append(info)

        final = {'commits': result[:20]}

        # for left nav bar
        if is_new_repo:
            final["new_repo"] = user_repo

        # for pagination
        final["user_repo_id"] = user_id
        len_res = len(result)
        final["pag_count"] = (
            len_res / 20 if len_res % 20 == 0 else len_res/20 + 1)
    return jsonify(**final)


@app.route('/get-commits', methods=['POST', ])
def get_commits(user_id=None, count=0):
    if not user_id:
        user_id = request.json['userRepoId']
        count = int(request.json['count'])

    result = []

    for ind, commit_id in enumerate(
            r.lrange("commits:{0}".format(user_id), 0, -1), start=1):

        result.append(
            dict(
                zip(
                    ['index', 'id', 'user_id', 'date', 'author', 'message'],
                    [ind, commit_id, user_id] + r.hmget(
                        commit_id, 'date', 'author', 'message')
                ))
        )

    final = dict()
    final['commits'] = result[count*20:(count+1)*20]
    final["user_repo_id"] = user_id
    len_res = len(result)
    final["pag_count"] = (
        len_res / 20 if len_res % 20 == 0 else len_res/20 + 1)

    return jsonify(**final)


@app.route('/delete-commits', methods=['POST', ])
def delete_commits():
    user_id = None
    ids = request.json['commit_ids']

    for id_ in ids:
        if not user_id:
            [user_id, ] = r.hmget(id_, 'user_id')

        r.delete(id_)
        r.lrem('commits:{0}'.format(user_id), 1, id_)

    return get_commits(user_id)


if __name__ == '__main__':
    app.run()
