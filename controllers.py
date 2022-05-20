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

url_signer = URLSigner(session)


# Main webapge End points  ##############################
@action('index')
@action.uses('index.html', db, auth, url_signer)
def index():
    return dict(
        # COMPLETE: return here any signed URLs you need.
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
    form = Form(db.food_truck, csrf_session=session, formstyle=FormStyleBootstrap4)
    if form.accepted:
        redirect(URL('manage-listings'))
    # Either this is a GET request, or this is a POST but not accepted = with errors.
    return dict(form=form)


# End point to see all of your listings/food trucks
@action('manage-listings')
@action.uses('manage-listings.html', db, session, auth.user, url_signer)
def manage_listing():
    trucks = db(db.food_truck.created_by == get_user_email()).select()
    print(trucks)
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


# The endpoint for the customer to add a review
@action('add-review/<food_truck_id:int>', method=["GET", "POST"])
@action.uses('add-review.html', db, session, auth.user, url_signer.verify())
def add_review(food_truck_id=None):
    assert food_truck_id is not None

    # Check if food_truck_id is valid in db
    truck = db.food_truck[food_truck_id]
    assert truck is not None

    form = Form([
        Field('stars'),
        Field('text')
    ], csrf_session=session, formstyle=FormStyleBootstrap4)

    if form.accepted:
        db.review.insert(
            food_truck_id=food_truck_id,
            created_by=get_user(),
            stars=form.vars["stars"],
            text=form.vars["text"]
        )
        redirect(URL('index'))

    # Either this is a GET request, or this is a POST but not accepted = with errors.
    return dict(form=form, url_signer=url_signer)

# The endpoint for a customer to edit their review
@action('edit-review/<review_id:int>', method=["GET", "POST"])
@action.uses('edit-review.html', db, session, auth.user, url_signer.verify())
def edit_review(review_id=None):
    assert review_id is not None

    curr = db.review[review_id]
    if curr is None:
        redirect(URL('index'))

    form = Form(db.review, record=curr, deletable=False, csrf_session=session, formstyle=FormStyleBootstrap4)
    if form.accepted:
        redirect(URL('index'))

    return dict(form=form,
                url_signer=url_signer)


@action('delete-review/<review_id:int>')
@action.uses(db, session, auth.user, url_signer)
def delete_review(review_id=None):
    assert review_id is not None
    pass
