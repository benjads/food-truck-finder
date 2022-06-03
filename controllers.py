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

from py4web.utils.form import *
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
        add_review_url=URL('add-review', signer=url_signer),
        delete_review_url=URL('delete-review', signer=url_signer),
        load_reviews_url=URL('load-reviews', signer=url_signer),
        search_url=URL('search', signer=url_signer),
        my_callback_url=URL('my-callback', signer=url_signer),
    )


@action('about-us')
@action.uses('about-us.html', db, auth, url_signer)
def about_us():
    return dict()


# Food Truck Listing End Points #########################################
# Create food truck listing form
@action('add-listing', method=["GET", "POST"])
@action.uses('edit-listing.html', db, session, auth.user, url_signer)
def add_listing():
    dotws = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
    cuisines = ['Vegetarian', 'Vegan', 'Pescatarian', 'Gluten-free', 'Kosher', 'Halal',
                'Italian', 'Mediterranean', 'Chinese', 'German', 'Indian', 'Japanese', 'Korean', 'American']
    fields = [
        Field('name', requires=IS_NOT_EMPTY()),
        Field('address', requires=IS_NOT_EMPTY()),
        Field('cuisine_type', requires=IS_IN_SET(cuisines)),
        Field('phone_number', requires=IS_NOT_EMPTY()),
        Field('email', requires=IS_EMAIL()),
        Field('website', requires=IS_URL())
    ]
    for dotw in dotws:
        fields.append(Field('hours_' + dotw + '_open'))
        fields.append(Field('hours_' + dotw + '_close'))
    FormStyleBootstrap4.widgets['cuisine_type'] = SelectWidget()
    form = Form(fields, csrf_session=session, formstyle=FormStyleBootstrap4)
    if form.accepted:
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
    return dict(action_name='Add', form=form)


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

    dotws = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
    # list of cuisine types here
    cuisines = ['Vegetarian', 'Vegan', 'Pescatarian', 'Gluten-free', 'Kosher', 'Halal',
                'Italian', 'Mediterranean', 'Chinese', 'German', 'Indian', 'Japanese', 'Korean', 'American']

    fields = [
        Field('name', requires=IS_NOT_EMPTY()),
        Field('address', requires=IS_NOT_EMPTY()),
        Field('cuisine_type', requires=IS_IN_SET(cuisines)),
        Field('phone_number', requires=IS_NOT_EMPTY()),
        Field('email', requires=IS_EMAIL()),
        Field('website', requires=IS_URL())
    ]
    for dotw in dotws:
        fields.append(Field('hours_' + dotw + '_open'))
        fields.append(Field('hours_' + dotw + '_close'))
    # iterate over our cuisine list, append
    # for cuisine in cuisines:
    #     fields.append(Field(cuisine))

    record = curr
    hours_records = db(db.food_truck_hours.food_truck_id == curr.id).select()
    for hours_record in hours_records:
        record['hours_' + hours_record.dotw + '_open'] = hours_record.open_time
        record['hours_' + hours_record.dotw + '_close'] = hours_record.close_time
    FormStyleBootstrap4.widgets['cuisine_type'] = SelectWidget()
    form = Form(fields, record=curr, deletable=False, csrf_session=session, formstyle=FormStyleBootstrap4)
    if form.accepted:
        food_truck_id = db.food_truck.update_or_insert(
            curr.id,
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

            db.food_truck_hours.update_or_insert(
                ((db.food_truck_hours.food_truck_id == curr.id) & (db.food_truck_hours.dotw == dotw)),
                food_truck_id=curr.id,
                dotw=dotw,
                open_time=open_time,
                close_time=close_time
            )

        redirect(URL('manage-listings'))
    # Either this is a GET request, or this is a POST but not accepted = with errors.
    return dict(action_name='Edit', form=form)


# The endpoint for the customer to delete a food truck listing
@action('delete-listing/<food_truck_id:int>')
@action.uses(db, session, auth.user, url_signer.verify())
def delete_listing(food_truck_id=None):
    assert food_truck_id is not None
    db(db.food_truck.id == food_truck_id).delete()
    # How do we get the POST body?
    redirect(URL('manage-listings'))

@action('load-trucks')
@action.uses(db)
def load_trucks():
    trucks = db(db.food_truck).select().as_list()
    return dict(trucks=trucks)

# This is our very first API function.
@action('load-reviews')
@action.uses(url_signer.verify(), db, auth)
def load_reviews():
    truck_id = request.params.get('food_truck_id')
    reviews = db(db.review.food_truck_id == truck_id).select().as_list()
    return dict(reviews=reviews, current_user=get_user())


# The endpoint for the customer to add a review
@action('add-review', method=["POST"])
@action.uses(db, auth.user, url_signer.verify())
def add_review():
    r = db(db.auth_user.id == get_user()).select().first()
    name = r.first_name + " " + r.last_name if r is not None else "Unknown"

    id = db.review.insert(
        food_truck_id=request.json.get('food_truck_id'),
        text=request.json.get('text'),
        created_by=get_user(),
        name=name,
    )
    return dict(id=id, name=name, created_by=get_user())

    # Either this is a GET request, or this is a POST but not accepted = with errors.
    # return dict(form=form, url_signer=url_signer)


@action('delete-review')
@action.uses(db, auth.user, url_signer.verify())
def delete_review():
    db(db.review.id == request.params.get('id')).delete()
    return "ok"



# Vue End Point : returns a list of food truck names if they match the user's search term
@action('search')
@action.uses(db)
def search():
    # Get the user's search word, and db
    q = request.params.get("q")
    food_trucks = db(db.food_truck).select().as_list()
    # cuisine_trucks = db(db.food_truck).select().as_list()

    truck_results = []  # List for food truck names if the truck name matches
    cuisine_results = []  # List for food truck names if the cuisine type matches
    for truck in food_trucks:
        # If search term is a substring in the name, then append it to the return list
        if q.lower() in truck['name'].lower():
            truck_results.append(truck['name'])
        # If the search term matches with the cuisine type, then append it to the list
        if q.lower() in truck['cuisine_type'].lower():
            cuisine_results.append(truck['name'])

    return dict(truck_results=truck_results, cuisine_results=cuisine_results)
    
