import unittest

from flask import current_app
from flask_testing import TestCase
from app import global_variable


class TestDevelopmentConfig(TestCase):
    def create_app(self):
        global_variable.app.config.from_object('app.config.DevelopmentConfig')
        return global_variable.app

    def test_app_is_development(self):
        self.assertTrue(global_variable.app.config['DEBUG'] is True)
        self.assertFalse(current_app is None)
        # self.assertTrue(
        #    app.config['SQLALCHEMY_DATABASE_URI'] ==
        #    'postgres://postgres:postgres@users-db:5432/users_dev'
        # )


class TestTestingConfig(TestCase):
    def create_app(self):
        global_variable.app.config.from_object('app.config.TestingConfig')
        return global_variable.app

    def test_app_is_testing(self):
        # self.assertTrue(app.config['SECRET_KEY'] == 'my_precious')
        self.assertTrue(global_variable.app.config['DEBUG'])
        # self.assertTrue(app.config['TESTING'])
        self.assertFalse(global_variable.app.config['PRESERVE_CONTEXT_ON_EXCEPTION'])
        # self.assertTrue(
        #    app.config['SQLALCHEMY_DATABASE_URI'] ==
        #    'postgres://postgres:postgres@users-db:5432/users_test'
        # )


class TestProductionConfig(TestCase):
    def create_app(self):
        global_variable.app.config.from_object('app.config.ProductionConfig')
        return global_variable.app

    def test_app_is_production(self):
        # self.assertTrue(app.config['SECRET_KEY'] == 'my_precious')
        self.assertFalse(global_variable.app.config['DEBUG'])
        self.assertFalse(global_variable.app.config['TESTING'])


if __name__ == '__main__':
    unittest.main()