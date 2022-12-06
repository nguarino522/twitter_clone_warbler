"""Message View tests."""

import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

# Now we can import app

from app import app, CURR_USER_KEY


# Make Flask errors be real errors, rather than HTML pages with error info
app.config['TESTING'] = True


# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

with app.app_context():
    db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        with app.app_context():
            
            db.drop_all()
            db.create_all()          
            
            u = User.signup("testuser", "test@test.com", "HASHED_PASSWORD", None)
            uid = 1
            u.id = uid
            
            db.session.add(u)
            db.session.commit()

            u = User.query.get(uid)
            
            self.u = u 
            self.uid = uid

            m1 = Message(id=7, text="trending warble", user_id=self.uid)
            m2 = Message(id=522, text="Eating some lunch", user_id=self.uid)
            db.session.add_all([m1, m2])
            db.session.commit()
            
            self.client = app.test_client()
        
    def tearDown(self):
        
        with app.app_context():
            res = super().tearDown()
            db.session.rollback()
            db.drop_all()
            return res

    def test_add_message(self):
        """Can a user add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.uid

            test_uid = self.uid
            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = client.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.filter_by(text="Hello")           
            self.assertIsNotNone(msg)
    
    
    def test_message_delete(self):
        """Can a user delete a message?"""
        
        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.uid
            
            resp = client.post("/messages/522/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            m = Message.query.get(522)
            self.assertIsNone(m)
    
    
    def test_uathorized_message_delete(self):
        """test if unauthorized user attempts to delete other user's message"""
        
        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = 5
            resp = client.post("/messages/522/delete", follow_redirects=True)
            self.assertIn("Access unauthorized", str(resp.data))
            m = Message.query.get(522)
            self.assertIsNotNone(m)

        
    def test_message_delete_no_authentication(self):
        """test if not logged in attempt to delete message"""
        
        with self.client as client:
            resp = client.post("/messages/522/delete", follow_redirects=True)
            self.assertIn("Access unauthorized", str(resp.data))
            m = Message.query.get(522)
            self.assertIsNotNone(m)

    def test_invalid_message_show(self):
        """test that 404 comes up when invalid message id"""
        
        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.uid
            
            resp = client.get('/messages/99999999', follow_redirects=True)
            self.assertEqual(resp.status_code, 404)