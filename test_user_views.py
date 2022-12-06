"""User View tests."""

import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes, Follows
from bs4 import BeautifulSoup

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


class UserViewTestCase(TestCase):
    """Test views for users."""
    
    def setUp(self):
        """Create test client, add sample data."""

        with app.app_context():
            
            db.drop_all()
            db.create_all()          
            
            u = User.signup("testuser", "test@test.com", "HASHED_PASSWORD", None)
            uid = 1
            u.id = uid
            
            u1 = User.signup("test1", "email1@email.com", "password", None)
            uid1 = 5
            u1.id = uid1
            
            u2 = User.signup("test2", "email2@email.com", "password", None)
            uid2 = 22
            u2.id = uid2         
            
            u3 = User.signup("test3", "email3@email.com", "password", None)
            uid3 = 7
            u3.id = uid3
            
            db.session.add_all([u, u1, u2, u3])
            db.session.commit()

            u = User.query.get(uid)
            u1 = User.query.get(uid1)
            u2 = User.query.get(uid2)
            u3 = User.query.get(uid3)
            
            self.u = u 
            self.uid = uid
            self.u1 = u1
            self.uid1 = uid1
            self.u2 = u2
            self.uid2 = uid2
            self.u3 = u3 
            self.uid3 = uid3 

            #setup follows and commit to test DB
            f1 = Follows(user_being_followed_id=self.uid1, user_following_id=self.uid)
            f2 = Follows(user_being_followed_id=self.uid2, user_following_id=self.uid)
            f3 = Follows(user_being_followed_id=self.uid, user_following_id=self.uid1)
            db.session.add_all([f1, f2, f3])
            db.session.commit()
            
            #setup likes and messages and commit to test DB
            m1 = Message(text="trending warble", user_id=self.uid)
            m2 = Message(id=522, text="Eating some lunch", user_id=self.uid)
            m3 = Message(id=9876, text="likable warble", user_id=self.uid1)
            db.session.add_all([m1, m2, m3])
            db.session.commit()
            like = Likes(user_id=self.uid, message_id=9876)
            db.session.add(like)
            db.session.commit()
        
            self.client = app.test_client()
        
    def tearDown(self):
        
        with app.app_context():
            res = super().tearDown()
            db.session.rollback()
            db.drop_all()
            return res
    
    def test_homepage(self):
        """homepage or landing page test"""
        with self.client as client:
            resp = client.get("/")
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("New to Warbler?", str(resp.data))
            
        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.uid
            resp = client.get("/users")
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            
        
    def test_users_index(self):
        """main users page index and load"""
    
        with self.client as client:
            resp = client.get("/users")
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("@testuser", str(resp.data))
            self.assertIn("@test1", str(resp.data))
            self.assertIn("@test2", str(resp.data))
            self.assertIn("@test3", str(resp.data))
    
    def test_users_search(self):
        """testing if searching for user works correctly"""
        
        with self.client as client:
            resp = client.get("/users?q=test")
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("@testuser", str(resp.data))
            self.assertIn("@test1", str(resp.data))
            self.assertIn("@test2", str(resp.data))
            self.assertIn("@test3", str(resp.data))
    
    def test_user_show(self):
        """test showing a single user"""
        with self.client as client:
            resp = client.get(f"/users/{self.uid}")
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("@testuser", str(resp.data))
        
    def test_user_view(self):
        """test if user page has right counts"""
        with self.client as client:
            resp = client.get(f"/users/{self.uid}")
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("@testuser", str(resp.data))
            soup = BeautifulSoup(str(resp.data), 'html.parser')
            found = soup.find_all("li", {"class": "stat"})
            self.assertEqual(len(found), 4)

            # test for a count of 2 messages
            self.assertIn("2", found[0].text)

            # Test for a count of 2 followers
            self.assertIn("2", found[1].text)

            # Test for a count of 1 following
            self.assertIn("1", found[2].text)

            # Test for a count of 1 like
            self.assertIn("1", found[3].text)
    
    def test_unauthorized_likes_page_access(self):
        """testing if properly throws unauthorized error"""
        with self.client as client:
            resp = client.get(f"/users/{self.uid}/likes", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))
        
    def test_toggle_like(self):
        """testing toggle a like"""
        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.uid1
            
            resp = client.post("/users/toggle_like/522")
            likes = Likes.query.filter(Likes.message_id==522).all()
            self.assertEqual(len(likes), 1)
            self.assertEqual(likes[0].user_id, self.uid1)
            
            resp = client.post("/users/toggle_like/522")
            likes = Likes.query.filter(Likes.message_id==522).all()
            self.assertEqual(len(likes), 0)
    
    def test_show_following(self):
        """test showing following users page"""    
        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.uid
            resp = client.get(f"/users/{self.uid}/following")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("@test1", str(resp.data))
            self.assertIn("@test2", str(resp.data))
        
    def test_show_followers(self):
        """test showing followers users page"""
        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.uid
            resp = client.get(f"/users/{self.uid}/followers")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("@test1", str(resp.data))
                
    def test_unauthorized_following_page_access(self):
        """testing if properly throws unauthorized error"""
        with self.client as client:
            resp = client.get(f"/users/{self.uid}/following", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))
            
    def test_unauthorized_followers_page_access(self):
        """testing if properly throws unauthorized error"""
        with self.client as client:
            resp = client.get(f"/users/{self.uid}/followers", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))
