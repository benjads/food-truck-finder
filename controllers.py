"""
This file defines actions, i.e. functions the URLs are mapped into
The @action(path) decorator exposed the function at URL:

    http://127.0.0.1:8000/{app_name}/{path}

If app_name == '_default' then simply

    http://127.0.0.1:8000/{path}

If path == 'index' it can be omitted:

    http://127.0.0.1:8000/

The path follows the bottlepy syntax.

@action.uses('generic.html')  indicates that the action uses the generic.html template
@action.uses(session)         indicates that the action uses the session
@action.uses(db)              indicates that the action uses the db
@action.uses(T)               indicates that the action uses the i18n & pluralization
@action.uses(auth.user)       indicates that the action requires a logged in user
@action.uses(auth)            indicates that the action requires the auth object

session, db, T, auth, and tempates are examples of Fixtures.
Warning: Fixtures MUST be declared with @action.uses({fixtures}) else your app will result in undefined behavior
"""

from py4web import action, request, abort, redirect, URL, Field
from yatl.helpers import A

from py4web.utils.form import Form, FormStyleBootstrap4
from .common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash
from py4web.utils.url_signer import URLSigner
from .models import get_user_email, get_user
from pydal.validators import *

# For search bar functionality
import uuid
import random

url_signer = URLSigner(session)


# Main webpage End points  ##############################
@action('index')
@action.uses('index.html', db, auth, url_signer)
def index():
    return dict(
        # COMPLETE: return here any signed URLs you need.
        load_trucks_url=URL('load-trucks', signer=url_signer),
        add_review_url=URL('add_review', signer=url_signer),
        delete_review_url=URL('delete_review', signer=url_signer),
        load_reviews_url=URL('load_reviews', signer=url_signer),
        search_url=URL('search', signer=url_signer),
        my_callback_url=URL('my_callback', signer=url_signer),
    )


@action('about-us')
@action.uses('about-us.html', db, auth, url_signer)
def index():
    return dict()


# Food Truck Listing End Points #########################################
# Create food truck listing form
@action('add-listing', method=["GET", "POST"])
@action.uses('add-listing.html', db, session, auth.user, url_signer)
def add_listing():
    dotws = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
    fields = [
        Field('name', requires=IS_NOT_EMPTY()),
        Field('address', requires=IS_NOT_EMPTY()),
        Field('cuisine_type', requires=IS_NOT_EMPTY()),
        Field('phone_number', requires=IS_NOT_EMPTY()),
        Field('email', requires=IS_EMAIL()),
        Field('website', requires=IS_URL())
    ]
    for dotw in dotws:
        fields.append(Field('hours_' + dotw + '_open'))
        fields.append(Field('hours_' + dotw + '_close'))

    form = Form(fields, csrf_session=session, formstyle=FormStyleBootstrap4)
    if form.accepted:
        print(form.vars)
        food_truck_id = db.food_truck.insert(
            name=form.vars['name'],
            address=form.vars['address'],
            cuisine_type=form.vars['cuisine_type'],
            phone_number=form.vars['phone_number'],
            email=form.vars['email'],
            website=form.vars['website']
        )

        for dotw in dotws:
            open_time = form.vars['hours_' + dotw + '_open']
            close_time = form.vars['hours_' + dotw + '_close']

            if open_time == '' or close_time == '':
                continue

            db.food_truck_hours.insert(
                food_truck_id=food_truck_id,
                dotw=dotw,
                open_time=open_time,
                close_time=close_time
            )

        redirect(URL('manage-listings'))
    # Either this is a GET request, or this is a POST but not accepted = with errors.
    return dict(form=form)


# End point to see all of your listings/food trucks
@action('manage-listings')
@action.uses('manage-listings.html', db, session, auth.user, url_signer)
def manage_listing():
    trucks = db(db.food_truck.created_by == get_user_email()).select()

    return dict(trucks=trucks, url_signer=url_signer)


# End point to edit 1 specific listing/food truck
@action('edit-listing/<food_truck_id:int>', method=["GET", "POST"])
@action.uses('edit-listing.html', db, session, auth.user, url_signer)
def edit_listing(food_truck_id=None):
    assert food_truck_id is not None

    curr = db.food_truck[food_truck_id]
    if curr is None:
        redirect(URL('index'))

    form = Form(db.food_truck, record=curr, deletable=False, csrf_session=session, formstyle=FormStyleBootstrap4)
    if form.accepted:
        redirect(URL('manage-listings'))
    return dict(form=form,
                url_signer=url_signer,
                food_truck_id=food_truck_id)


# The endpoint for the customer to delete a food truck listing
@action('delete-listing/<food_truck_id:int>')
@action.uses(db, session, auth.user, url_signer.verify())
def delete_listing(food_truck_id=None):
    assert food_truck_id is not None
    db(db.food_truck.id == food_truck_id).delete()
    # How do we get the POST body?
    redirect(URL('manage-listings'))


@action('load-trucks')
@action.uses(db, url_signer.verify())
def load_trucks():
    trucks = db(db.food_truck).select().as_list()
    return dict(trucks=trucks)


# This is our very first API function.
@action('load_reviews')
@action.uses(url_signer.verify(), db, auth)
def load_reviews():
    reviews = db(db.review).select().as_list()
    return dict(reviews=reviews)


# The endpoint for the customer to add a review
@action('add-review/<food_truck_id:int>', method=["POST"])
@action.uses('add-review.html', db, auth.user, url_signer.verify())
def add_review(food_truck_id=None):
    assert food_truck_id is not None
    id = db.review.insert(
        food_truck_id=request.json.get('food_truck_id'),
        text=request.json.get('text'),
        stars=request.json.get('rating'),
        created_by=get_user()
    )
    return dict(id=id)

    # Either this is a GET request, or this is a POST but not accepted = with errors.
    # return dict(form=form, url_signer=url_signer)


@action('delete-review/<review_id:int>')
@action.uses(db, auth.user, url_signer.verify())
def delete_review(review_id=None):
    assert review_id is not None
    db(db.review.id == review_id).delete()
    return


# Vue End Point : Returns the reviews Database Table
@action('vue_get_reviews')
@action.uses(db, session, auth.user, url_signer.verify())
def vue_get_reviews():
    # Returns the reviews db table as a list
    reviews = db(db.reviews).select().as_list()
    return dict(reviews=reviews)


# Vue End Point : returns a list of food truck names if they match the user's search term
@action('search')
@action.uses(db)
def search():
    # Get the user's search word, and db
    q = request.params.get("q")
    food_trucks = db(db.food_truck).select().as_list()

    results = []
    for truck in food_trucks:
        # If search term is a substring in the name, then append it to the return list
        if q.lower() in truck['name'].lower():
            results.append(truck['name'])

    return dict(results=results)
