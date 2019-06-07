import unittest
import mongo_handler
import constants

from pymongo import MongoClient

long_comment = {
    "subreddit_id" : "t5_2r78l", 
    "created_utc": 34,
    "approved_at_utc" : None, 
    "edited" : False, 
    "link_id" : "t3_9j0m3i",
    "name" : "t1_e6oq65l", 
    "author" : "Dr_Wombo_Combo", 
    "parent_id" : "t1_e6o655y", 
    "score" : 1, 
    "body" : "Wavy baby 🌊", 
    "link_title" : "So, there's this girl and..", 
}

basic_comment =  {
    'author': 'HangTheDJHoldTheMayo',
    'body': 'Shits so wavy he can read the sound waves homie ',
    'created_utc': 1541259203,
    'name': 't1_e8z9okx'}

not_wavy = {
    'author': 'test_author_for_node',
    'name': 'not_wavy_comment',
    'body': 'does not contain the \'w\' word',
    'created_utc': 3020
}

exists_in_db = {
    'author': 'test_author_for_node',
    'name': 'exists_in_db_wavy_comment',
    'body': 'does contain \'wavy\'',
    'created_utc': 4455
}

is_wavy = {
    'author': 'test_author_for_node',
    'name': 'test_comment_new_in_db',
    'body': 'does contain wavy',
    'created_utc': 10
}

# User classifications.
user_classifications = [
    {
        'name': 'has_many_user_classifications',
        'ip': 'testip1',
        'is_wavy': 'wavy',
        'category': 'poster' 
    },{
        'name': 'has_many_user_classifications',
        'ip': 'testip2',
        'is_wavy': 'not_wavy',
        'category': 'poster' 
    },{
        'name': 'has_many_user_classifications',
        'ip': 'testip3',
        'is_wavy': 'wavy',
        'category': 'kanye' 
    },{
        'name': 'has_one_classification',
        'ip': 'testip4',
        'is_wavy': 'wavy',
        'category': 'poster'
    },{
        'name': 'only_classified_category',
        'ip': 'testip5',
        'category': 'link'
    }
]

db = mongo_handler.DB_TEST

class CommentsDBTest(unittest.TestCase):
    def setUp(self):
        client = MongoClient()
        comments_collection = client.test[constants.COMMENTS]
        comments_collection.insert_many([ long_comment, basic_comment, not_wavy, exists_in_db, is_wavy ])
    
    def tearDown(self):
        client = MongoClient()
        comments_collection = client.test[constants.COMMENTS]
        comments_collection.delete_many({})

    def testSimple(self):
        comment = mongo_handler.get_comment('t1_e8z9okx', pretty=False, db=db)
        self.assertEqual(comment['author'], 'HangTheDJHoldTheMayo')

        with self.assertRaises(ValueError):
            mongo_handler.get_comment('comment_dne', db=db)

    def testShortener(self):
        comment = mongo_handler.get_comment('t1_e6oq65l', db=db)
        self.assertEqual(len(comment), 4)

    def testBodyOnly(self):
        comment = mongo_handler.body_only(mongo_handler.get_comment('t1_e8z9okx', db=db))
        self.assertEqual(comment, basic_comment['body'])

    def testGetRecent(self):
        comments = mongo_handler.get_recent_comments(limit=2, db=db)
        self.assertEqual(comments[0]['author'], basic_comment['author'])
        self.assertEqual(comments[1]['author'], exists_in_db['author'])

class CategoriesDBTest(unittest.TestCase):

    def setUp(self):
        self.client = MongoClient()
        categories_collection = self.client.test[constants.TRAIN_CATEGORIES]
        categories_collection.insert_many([
            {'name': 'in_db', 'category': 'poster'},
            {'name': 'also_in_db', 'category': 'kanye', 'is_wavy': 'wavy'}
        ])

        comments_collection = self.client.test[constants.COMMENTS]
        comments_collection.insert_many([ long_comment, basic_comment, not_wavy, exists_in_db, is_wavy ])

        user_categorized_collection = self.client.test[constants.USER_CLASSIFIED]
        user_categorized_collection.insert_many(user_classifications)

    def tearDown(self):
        categories_collection = self.client.test[constants.TRAIN_CATEGORIES]
        categories_collection.delete_many({})

        comments_collection = self.client.test[constants.COMMENTS]
        comments_collection.delete_many({})

        user_categorized_collection = self.client.test[constants.USER_CLASSIFIED]
        user_categorized_collection.delete_many({})
    
    def testIn(self):
        # TODO: include comment existing in database
        self.assertFalse(mongo_handler.is_updated('zarglbargl', db=db))
        self.assertTrue(mongo_handler.is_updated('in_db', db=db))

    def testGetNoncategorized(self):
        command_cursor = mongo_handler.get_noncategorized_comments(db=db)
        self.assertEqual(sum(1 for _ in command_cursor), 5)

    def testGetCategorized(self):
        command_cursor = mongo_handler.get_categorized_comments(db=db)
        self.assertEqual(sum(1 for _ in command_cursor), 2)

        command_cursor = mongo_handler.get_positivity_categorized_comments(db=db)
        self.assertEqual(sum(1 for _ in command_cursor), 1)

    # TODO: test statistics

    def testGetUserCategorized(self):
        categorized_list = mongo_handler.get_user_categorized_comments(db=db)
        self.assertEqual(len(categorized_list), 3)

        for comment in categorized_list:
            if comment['name'] == 'has_many_user_classifications':
                self.assertEqual(comment['is_wavy'], 'wavy')
                self.assertEqual(comment['category'], 'poster')
            if comment['name'] == 'has_one_classification':
                self.assertEqual(comment['is_wavy'], 'wavy')
                self.assertEqual(comment['category'], 'poster')
            if comment['name'] == 'only_classified_category':
                self.assertEqual(comment['category'], 'link')
                self.assertFalse('is_wavy' in comment)
    
    def testUserPositivityClassified(self):
        categorized_list = mongo_handler.get_user_positivity_categorized_comments(db=db)
        self.assertEqual(len(categorized_list), 2)

if __name__ == '__main__':
    unittest.main()
