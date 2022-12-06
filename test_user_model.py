"""User model tests."""

import os
from unittest import TestCase
from sqlalchemy import exc
from models import db, User, Message, Follows

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
    """Test models for users."""

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
            
            self.client = app.test_client()

    def tearDown(self):
        
        with app.app_context():
            res = super().tearDown()
            db.session.rollback()
            db.drop_all()
            return res
    
    def test_user_model(self):
        """Does basic model work?"""

        with app.app_context():
            # User should have no messages & no followers
            user_test = User.query.get(self.uid)
            self.assertEqual(len(user_test.messages), 0)
            self.assertEqual(len(user_test.followers), 0)
    
    def test_repr_method(self):
        """Does the repr method work as expected?"""

        self.assertEqual(repr(self.u), f"<User #{self.u.id}: testuser, test@test.com>")
    
    
    #############################
    ## AUTHENTICATION TESTS #####
    #############################
    def test_valid_authentication(self):
        """Does User.authenticate successfully return a user when given a valid username and password?"""
        
        with app.app_context():
            u = User.authenticate(self.u1.username, "password")
            self.assertIsNotNone(u)
            self.assertEqual(u.id, self.uid1)
    
    def test_invalid_username(self):
        """Does User.authenticate fail to return a user when the username is invalid?"""

        with app.app_context():
            self.assertFalse(User.authenticate("badusername", "password"))

    def test_wrong_password(self):
        """Does User.authenticate fail to return a user when the password is invalid?"""

        with app.app_context():
            self.assertFalse(User.authenticate(self.u1.username, "badpassword"))
            
    
    
    #############################
    ###### SIGNUP TESTS #########
    #############################
    
    def test_valid_signup(self):
        """test valid signup"""
        with app.app_context():
            u_signup_test = User.signup("test_signup_user", "test22@test.com", "HASHED_PASSWORD", None)
            uid = 999
            u_signup_test.id = uid
            db.session.commit()
        
            u_test = User.query.get(uid)
            self.assertIsNotNone(u_test)
            self.assertEqual(u_test.username, "test_signup_user")
            self.assertEqual(u_test.email, "test22@test.com")
            self.assertNotEqual(u_test.password, "HASHED_PASSWORD")
            # Bcrypt strings should start with $2b$
            self.assertTrue(u_test.password.startswith("$2b$"))
        
    def test_invalid_username_signup(self):
        """testing invalid username criteria for signup"""
        with app.app_context():
            u_signup_test = User.signup(None, "test22@test.com", "HASHED_PASSWORD", None)
            uid = 999
            u_signup_test.id = uid
            
            with self.assertRaises(exc.IntegrityError) as context:
                db.session.commit()
            
    
    def test_invalid_email_signup(self):
        """testing invalid email criteria for signup"""
        with app.app_context():
            u_signup_test = User.signup("test_signup_user", None, "HASHED_PASSWORD", None)
            uid = 999
            u_signup_test.id = uid
            
            with self.assertRaises(exc.IntegrityError) as context:
                db.session.commit()
        
    def test_invalid_password_signup(self):
        """testing invalid password criteria for signup"""
        with app.app_context():           
            with self.assertRaises(ValueError) as context:
                u_signup_test = User.signup("test_signup_user", "test22test.com", None, None)
        
    
    #############################
    ### FOLLOWING TEST #########
    #############################
    
    
    def test_user_follows(self):
        """test for following user"""
        with app.app_context():
            ut1 = User.query.get(self.uid1)
            ut2 = User.query.get(self.uid2)
        
            ut1.following.append(ut2)
            db.session.commit()

            self.assertEqual(len(ut2.following), 0)
            self.assertEqual(len(ut2.followers), 1)
            self.assertEqual(len(ut1.followers), 0)
            self.assertEqual(len(ut1.following), 1)

            self.assertEqual(ut2.followers[0].id, ut1.id)
            self.assertEqual(ut1.following[0].id, ut2.id)

            self.assertTrue(ut1.is_following(ut2))
            self.assertFalse(ut2.is_following(ut1))
            
            self.assertTrue(ut2.is_followed_by(ut1))
            self.assertFalse(ut1.is_followed_by(ut2))
        
        
        
    
    