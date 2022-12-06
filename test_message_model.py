"""Message model tests."""

import os
from unittest import TestCase
from sqlalchemy import exc
from models import db, User, Message, Follows, Likes

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app
from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data


with app.app_context():
    db.create_all()
    

class UserModelTestCase(TestCase):
    """Test models for messages."""
    
    def setUp(self):
        """Create test client, add sample data."""

        with app.app_context():
            
            db.drop_all()
            db.create_all()          
            
            u = User.signup("testuser", "test@test.com", "HASHED_PASSWORD", None)
            uid = 1
            u.id = uid
            
            u2 = User.signup("testuser2", "test2@test.com", "HASHED_PASSWORD", None)
            uid2 = 2
            u2.id = uid2
            
            db.session.add_all([u,u2])
            db.session.commit()

            u = User.query.get(uid)
            u2 = User.query.get(uid2)
            
            self.u = u 
            self.uid = uid
            
            self.u2 = u2 
            self.uid2 = uid2
            
            self.client = app.test_client()

    def tearDown(self):
        
        with app.app_context():
            res = super().tearDown()
            db.session.rollback()
            db.drop_all()
            return res
        
    def test_message_model(self):
        """Does basic model work?"""
        
        with app.app_context():
            m = Message(text="message test", user_id=self.uid)
            db.session.add(m)
            db.session.commit()
            
            user = User.query.get(self.uid)
            
            # User should have 1 message
            self.assertEqual(len(user.messages), 1)
            self.assertEqual(user.messages[0].text, "message test")
            
        
    def test_message_likes(self):
        """testing liking message"""
        
        with app.app_context():
            m = Message(text="message test", user_id=self.uid)
            db.session.add(m)
            #db.session.commit()
            
            user1 = User.query.get(self.uid)
            user2 = User.query.get(self.uid2)
            
            user2.likes.append(m)
            db.session.commit()
            
            likes = Likes.query.filter(Likes.user_id == user2.id).all()
            self.assertEqual(len(likes), 1)
            self.assertEqual(likes[0].message_id, m.id)