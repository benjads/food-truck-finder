"""
This file defines the database models
"""

import datetime
from .common import db, Field, auth
from pydal.validators import *


def get_user_email():
    return auth.current_user.get('email') if auth.current_user else None


def get_user():
    return auth.current_user.get('id') if auth.current_user else None


def get_time():
    return datetime.datetime.utcnow()


# Table for a single food truck
db.define_table(
    'food_truck',
    # food truck ID
    Field('name', requires=IS_NOT_EMPTY()),
    Field('address', requires=IS_NOT_EMPTY()),
    Field('cuisine_type', requires=IS_NOT_EMPTY()),
    Field('phone_number', requires=IS_NOT_EMPTY()),
    Field('email', requires=IS_EMAIL()),
    Field('website', requires=IS_URL()),
    Field('created_by', default=get_user_email),  # links the foodtruck to email it is created by
)
db.food_truck.id.readable = db.food_truck.id.writable = False
db.food_truck.created_by.readable = db.food_truck.created_by.writable = False
# db.food_truck.availability.readable = db.food_truck.availability.writable = False
# db.food_truck.address.readable = db.food_truck.address.writable = False
# db.food_truck.cuisine_type.readable = db.food_truck.cuisine_type.writable = False

# Food truck hours for that single food truck
db.define_table(
    'food_truck_hours',
    Field('food_truck_id', 'reference food_truck', ondelete='CASCADE'),
    Field('dotw', requires=IS_NOT_EMPTY()),  # day of the week
    Field('open_time', requires=IS_NOT_EMPTY()),
    Field('close_time')
)
db.food_truck_hours.id.readable = db.food_truck_hours.id.writable = False
# db.food_truck_hours.food_truck_id.readable = db.food_truck_hours.food_truck_id.writable = False

# Database table
db.define_table(
    'review',
    Field('food_truck_id', 'reference food_truck', ondelete='CASCADE'),
    Field('stars', 'integer', IS_INT_IN_RANGE(0, 5), requires=IS_NOT_EMPTY()),  # The star rating 0-5
    Field('text', requires=IS_NOT_EMPTY()),  # The review
    Field('name'),   #The name
    Field('created_by', 'reference auth_user', requires=IS_NOT_EMPTY(), ondelete='CASCADE', default=get_user)
)
db.review.id.readable = db.review.id.writable = False
db.review.food_truck_id.readable = db.review.food_truck_id.writable = False
db.review.created_by.readable = db.review.created_by.writable = False

db.commit()
