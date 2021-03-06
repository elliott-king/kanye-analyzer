from flask import Flask
from flask import request
from flask_apscheduler import APScheduler

import nlp
import nltk
import constants
import mongo_handler

import ast
import json

'''
set FLASK_APP=server.py (on windows)
export FLASK_APP=server.py
py -m flask run
'''

app = Flask(__name__)
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

positivity_test, positivity_train = nlp.get_test_train_sets_positivity()
category_test, category_train = nlp.get_test_train_sets_category()

positivity_classifier = nltk.NaiveBayesClassifier.train(positivity_train)
category_classifier = nltk.NaiveBayesClassifier.train(category_train)

n_retrained = 0

@app.route('/')
def hello_world():
    return 'Hello world!'

@app.route('/classify', methods=['GET', 'POST'])
def classify():
    if request.method == 'POST':
        comment = request.json
        print("Getting comment classification:", comment['name'])

        comment_features = nlp.get_features(comment)
        cat = category_classifier.classify(comment_features)
        pos = positivity_classifier.classify(comment_features)

        print('Comment', comment['name'], 'is referring to', cat, 'and', pos)
        
        return json.dumps({
                'category': constants.CATEGORIES_TEXT[cat], 
                'is_wavy': constants.POSITIVITY_TEXT[pos]})

    return "Invalid request."

# According to SO, python's json module should be safe enough for untrusted input. 
# We should not, however, allow user-crafted JSON as a full query.
# https://stackoverflow.com/questions/7278238/sanitizing-inputs-to-mongodb
@app.route('/user_classification', methods=['POST'])
def user_classification():
    if request.method == 'POST':
        comment_name, ipaddr = request.json['comment_name'], request.json['ipaddr']
        classification = request.json['classification']

        print("Applying user classification", classification, "to comment", comment_name)
        mongo_handler.update_user_classification(comment_name, classification)
        return("Applying user classification to comment " + comment_name)


    return "Invalid request - expecting POST."

@app.route('/statistics')
def generate_statistics():
    print("Generating statistics for all comments")

    positivity_counts = mongo_handler.positivity_counts()
    category_counts = mongo_handler.categories_counts()
    return json.dumps({
        "positivity_statistics": positivity_counts,
        "category_statistics": category_counts
    })

@app.route('/n_retrained')
def count_ntrained():
    return(f'Classifier retrained {n_retrained} times\n')
   
@scheduler.task('interval', id='reset_classifiers', 
        seconds=86400, misfire_grace_time=300)
def reset_classifier():
    global positivity_classifier
    global category_classifier 

    positivity_test, positivity_train = nlp.get_test_train_sets_positivity()
    category_test, category_train = nlp.get_test_train_sets_category()

    positivity_classifier = nltk.NaiveBayesClassifier.train(positivity_train)
    category_classifier = nltk.NaiveBayesClassifier.train(category_train)

    global n_retrained
    n_retrained += 1
