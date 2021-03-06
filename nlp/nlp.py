import emoji
import nltk
import mongo_handler
import constants
import pprint
import random

# Taken from nltk book:
# http://www.nltk.org/book/ch05.html

'''
Usage:

Call from command line to classify 100 comments.

python3 cli:
    import nlp
    import nltk

    test, train = nlp.get_test_train_sets_positivity()
    classifier = nltk.NaiveBayesClassifier.train(train)
    nltk.classify.accuracy(classifier, test)
    classifier.show_most_informative_features()

    import mongo_handler
    comment = mongo_handler.get_comment(name)
    comment_features = nlp.get_features(comment)
    classifier.classify(comment_features)

    original_tags, classified_tags = [], []
    for features, tag in test:
        original_tags.append(tag)
        classified_tags.append(classifier.classify(features))
    cm = nltk.ConfusionMatrix(original_tags, classified_tags)
    print(cm.pretty_format(sort_by_count=True, show_percents=True, truncate=9))
'''

# tokenize string:           nltk.word_tokenize(s)
# show part of speech (pos): nltk.pos_tag(tokenized_string)
# view documentation of tag: nltk.help.upenn_tagset('TOKEN_NAME')

# TODO: identify dialogue act types: section 6.2.2
# TODO: how does pos_tag work? Is it a dict, or does it refer to the order of the tokens?

# Comment useful values:
# author, body, created, created_utc, parent_id, is_submitter
# name, id (identifier, identifier with t1_ prefix)
# permalink (does not include reddit.com)
# link_id, link_permalink (overall thread id & permalink, includes reddit.com)
# consider also using neighbor words around 'wavy'

def get_features(comment):
    if not comment:
        raise ValueError('Cannot extract features for empty comment.')

    body = comment['body']
    body_lowercase = body.lower()

    # NOTE: does not break up multiple emojis without space between them
    tokens = nltk.word_tokenize(body)
    tagged = nltk.pos_tag(tokens) # list of tuples
    # https://stackoverflow.com/questions/48660547
    entities = nltk.chunk.ne_chunk(tagged) 

    features = {}
    # NaiveBayes cannot take non-binary values. Must be binned. Ch6 5.3
    l = len(tokens)
    if l < 3:
        features['short'] = True
    elif l < 15:
        features['mid-length'] = True
    else:
        features['long'] = True

    features['top level comment'] = comment['link_id'] == comment['parent_id']
    features['is OP'] = comment['is_submitter']
    features['mentions user'] = 'u/' in body

    for e in constants.USEFUL_EMOJI:
        features['emoji ({})'.format(emoji.emojize(e, use_aliases=True))] \
            = emoji.emojize(e, use_aliases=True) in comment['body']

    for w in constants.USEFUL_WORDS:
        features['contains \'{}\''.format(w)] = w in body_lowercase

    named_entities = 0
    for chunk in entities:
        if hasattr(chunk, 'label'):
            named_entities += 1
    if named_entities <= 0:
        features['no ne'] = True
    elif named_entities < 2:
        features['one ne'] = True
    else:
        features['multiple ne'] = True

    return features

def featureset(categorized_comments):
    return [(get_features(comment), category) 
            for (comment, category) in categorized_comments]

def get_test_train_sets_positivity():
    labeled_set = mongo_handler.classified_comments_with_positivity()
    random.shuffle(labeled_set)
    train_set = nltk.classify.apply_features(get_features, labeled_set[:500])
    test_set = nltk.classify.apply_features(get_features, labeled_set[500:])
    return test_set, train_set

def get_test_train_sets_category():
    labeled_set = mongo_handler.classified_comments_with_category()
    random.shuffle(labeled_set)
    train_set = nltk.classify.apply_features(get_features, labeled_set[:500])
    test_set = nltk.classify.apply_features(get_features, labeled_set[500:])
    return test_set, train_set

def category_metrics_display():
    metrics = mongo_handler.categories_counts()
    total = 0
    s = ""
    for category in metrics:
        count, pct = metrics[category]
        total += count
        count, pct = str(count), str(pct)

        category = category + ' ' * (15 - len(category))
        # Make 'count' three characters. TODO: does not scale
        count = ' ' * (3 - len(count)) + count
        if len(pct) < 2:
            pct = ' ' + pct
        
        s += 'CATEGORY: {}    COUNT: {}    PCT: {}\n'.format(
                category, count, pct)
    s += 'TOTAL: {}'.format(total)
    return s

def generate_confusion_matrix(classifier=None, test=None):
    '''Generate confusion matrix for categories. 

        See explanation of confusion matrix: 
        http://www.nltk.org/book/ch06.html (section 3.4)
    '''   
    if not test:
        test, train = get_test_train_sets_category()

    if not classifier:
        classifier = nltk.NaiveBayesClassifier.train(train)

    original_tags, classified_tags = [], []
    for features, tag in test:
        original_tags.append(tag)
        classified_tags.append(classifier.classify(features))
    cm = nltk.ConfusionMatrix(original_tags, classified_tags)
    print(cm.pretty_format(sort_by_count=True, show_percents=True, truncate=9))

def request_input_on_cursor(comment):
    categories = constants.CATEGORIES_TEXT
    positivity_options = constants.POSITIVITY_TEXT
    
    POSITIVITY_VECTORIZATION = list(constants.POSITIVITY_TEXT.keys())

    CATEGORY_VECTORIZATION = list(constants.CATEGORIES_TEXT.keys())
 
    s = '\nThe categories are:\n' + '\n'.join(
            ['{}: {}'.format(i, v) for i, v in enumerate(categories)])
    print(s + '\n')
    features = get_features(comment)
    print('==============================================================')
    print(comment['body'])
    print('Created (utc): ', comment['created_utc'])
    print('Fullname:', comment['name'])
    print('link: ' +  'reddit.com' + comment ['permalink'])
    pprint.pprint(features)
    category = input('Category? ')
    while not category or int(category) >= len(categories) or int(category) < 0:
        print(
                'Invalid category selection.', 
                'Please use a number between 0 and', 
                len(categories) - 1)
        category = input('Category? ')

    print('Category chosen:', categories[CATEGORY_VECTORIZATION[int(category)]])
    name = comment['name']
    category = CATEGORY_VECTORIZATION[int(category)]

    p = '\nThe positivity options are:\n' + '\n'.join(
            ['{}: {}'.format(i, v) for i, v in enumerate(positivity_options)])
    print(p)
    positivity = input('Positivity? ')
    while (not positivity 
           or int(positivity) >= len(positivity_options) 
           or int(positivity) < 0):
        print(
                'Invalid category selection.', 
                'Please use a number between 0 and', 
                len(positivity_options) - 1)
        positivity = input('Positivity?')
    print('This comment is:', positivity_options[POSITIVITY_VECTORIZATION[int(positivity)]])
    positivity = POSITIVITY_VECTORIZATION[int(positivity)]

    mongo_handler.update_comment_category(
            name, category=category, is_wavy=positivity)

# generate train data by hand
if __name__ == '__main__':
    
    command_cursor = mongo_handler.get_noncategorized_comments(limit=50)
    for comment in command_cursor:
        request_input_on_cursor(comment)
