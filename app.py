# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import re
from datetime import datetime

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app, db)


# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#


class City(db.Model):
    __tablename__ = 'City'

    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String, nullable=False)
    state = db.Column(db.String(2), nullable=False)
    venues = db.relationship('Venue', backref='city', lazy=False)
    artists = db.relationship('Artist', backref='city', lazy=False)


venue_genres = db.Table(
    'venue_genres',
    db.Column('venue_id', db.Integer, db.ForeignKey('Venue.id'), primary_key=True),
    db.Column('genre_id', db.Integer, db.ForeignKey('Genre.id'), primary_key=True),
)

artist_genres = db.Table(
    'artist_genres',
    db.Column('artist_id', db.Integer, db.ForeignKey('Artist.id'), primary_key=True),
    db.Column('genre_id', db.Integer, db.ForeignKey('Genre.id'), primary_key=True),
)


class Genre(db.Model):
    __tablename__ = 'Genre'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False, unique=True)
    venues = db.relationship('Venue', secondary=venue_genres, backref=db.backref('genres', lazy=False))
    artists = db.relationship('Artist', secondary=artist_genres, backref=db.backref('genres', lazy=False))


class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    address = db.Column(db.Text)
    phone = db.Column(db.String(20))
    image_link = db.Column(db.Text)
    facebook_link = db.Column(db.Text)
    website_link = db.Column(db.Text)
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.Text, default="")
    city_id = db.Column(db.Integer, db.ForeignKey('City.id'), nullable=True)
    shows = db.relationship('Show', backref='venues', lazy=True)

    @db.validates('facebook_url')
    @db.validates('image_link')
    @db.validates('website_link')
    def validate_link(self, key, value):
        if (re.match(
                "https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)",
                value)):
            return value
        else:
            raise ValueError("link not valid!")


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    phone = db.Column(db.String(20))
    image_link = db.Column(db.Text)
    facebook_link = db.Column(db.Text)
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.Text, default="")
    website_link = db.Column(db.Text)
    city_id = db.Column(db.Integer, db.ForeignKey('City.id'), nullable=False)
    shows = db.relationship('Show', backref='artists', lazy=True)

    @db.validates('facebook_url')
    @db.validates('image_link')
    @db.validates('website_link')
    def validate_link(self, key, value):
        if (re.match(
                "https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)",
                value)):
            return value
        else:
            raise ValueError("link not valid!")


class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<Show id={self.id} start={self.start_time}>'


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    venues = City.query.order_by('id').all()
    return render_template('pages/venues.html', areas=venues);


@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_term = request.form.get('search_term', '')
    venues = Venue.query.filter(Venue.name.like('%' + search_term + '%')).order_by('id').all()
    response = {
        "count": len(venues),
        "data": venues
    }
    return render_template('pages/search_venues.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue = Venue.query.get(venue_id)
    past_shows = Show.query.filter(Show.venue_id == venue_id).filter(Show.start_time < datetime.now()).join(Venue).join(
        Artist).all()
    upcomming_shows = Show.query.filter(Show.venue_id == venue_id).filter(Show.start_time >= datetime.now()).join(
        Venue).join(Artist).all()

    return render_template('pages/show_venue.html', venue=venue, past_shows=past_shows, upcoming_shows=upcomming_shows,
                           past_shows_count=len(past_shows),
                           upcoming_shows_count=len(upcomming_shows))


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    try:
        selected_genres = request.form.getlist('genres')
        formdata = request.form
        venue = Venue(name=formdata['name'], address=formdata['address'], phone=formdata['phone'],
                      image_link=formdata['image_link'],
                      facebook_link=formdata['facebook_link'], website_link=formdata['website_link'])
        if 'looking_for_artist' in formdata.keys():
            if formdata['looking_for_artist'] == 'y' and 'looking_description' not in formdata.keys():
                raise Exception()
            else:
                venue.seeking_talent = formdata['looking_for_artist'] == 'y'
                if venue.seeking_talent:
                    venue.seeking_description = formdata['looking_description']

        city_name = formdata['city']
        state = formdata['state']
        c_tmp = City.query.filter(City.city == city_name).filter(City.state == state).first()
        if c_tmp is None:
            city = City(city=city_name, state=state)
            city.venues.append(venue)
        else:
            c_tmp.venues.append(venue)

        for genre in selected_genres:
            genre_tmp = Genre.query.filter(Genre.title == genre).first()
            if genre_tmp is None:
                g = Genre(title=genre)
                g.venues.append(venue)
            else:
                genre_tmp.venues.append(venue)

        db.session.add(venue)
        db.session.commit()
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except:
        db.session.rollback()
        flash('An error has occurred!', 'error')
    finally:
        db.session.close()
    return redirect(url_for('index'))


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    venue = Venue.query.get(venue_id)
    if venue is None:
        flash('Venue not found!', 'error')
    else:
        try:
            db.session.delete(venue)
            db.session.commit()
            flash(f'Venue {venue.name} has been deleted!')
        except:
            db.session.rollback()
            flash('Venue not found!', 'error')
        finally:
            db.session.close()
    return jsonify({
        'success': 'true'
    })


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    data = Artist.query.all()
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_term = request.form.get('search_term', '')
    artists = Artist.query.filter(Artist.name.like('%' + search_term + '%')).order_by('id').all()
    response = {
        "count": len(artists),
        "data": artists
    }
    return render_template('pages/search_artists.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist = Artist.query.get(artist_id)
    past_shows = Show.query.filter(Show.artist_id == artist_id).filter(Show.start_time < datetime.now()).join(
        Venue).join(Artist).all()
    upcomming_shows = Show.query.filter(Show.artist_id == artist_id).filter(Show.start_time >= datetime.now()).join(
        Venue).join(Artist).all()

    return render_template('pages/show_artist.html', artist=artist, past_shows=past_shows,
                           upcoming_shows=upcomming_shows,
                           past_shows_count=len(past_shows),
                           upcoming_shows_count=len(upcomming_shows))


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id)
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    try:
        selected_genres = request.form.getlist('genres')
        form_data = request.form
        artist = Artist.query.get(artist_id)
        artist.name = form_data.get('name', '')
        artist.phone = form_data.get('phone', '')
        artist.image_link = form_data.get('image_link', '')
        artist.facebook_link = form_data.get('facebook_link', '')
        artist.website_link = form_data.get('website_link', '')
        if 'looking_for_venue' in form_data.keys():
            if form_data['looking_for_venue'] == 'y' and 'looking_description' not in form_data.keys():
                raise Exception()
            else:
                artist.seeking_venue = form_data['looking_for_venue'] == 'y'
                if artist.seeking_venue:
                    artist.seeking_description = form_data['looking_description']

        city_name = form_data['city']
        state = form_data['state']
        c_tmp = City.query.filter(City.city == city_name).filter(City.state == state).first()
        if c_tmp is None:
            city = City(city=city_name, state=state)
            city.artists.append(artist)
        else:
            c_tmp.artists.append(artist)

        for genre in selected_genres:
            genre_tmp = Genre.query.filter(Genre.title == genre).first()
            if genre_tmp is None:
                g = Genre(title=genre)
                g.artists.append(artist)
            else:
                genre_tmp.artists.append(artist)

        db.session.commit()
        flash('Artist ' + request.form['name'] + ' was successfully Edited!')
    except:
        db.session.rollback()
        flash('An error has occurred!', 'error')
    finally:
        db.session.close()
    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id)
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    try:
        selected_genres = request.form.getlist('genres')
        form_data = request.form
        venue = Venue.query.get(venue_id)
        venue.name = form_data.get('name', '')
        venue.phone = form_data.get('phone', '')
        venue.address = form_data.get('address', '')
        venue.image_link = form_data.get('image_link', '')
        venue.facebook_link = form_data.get('facebook_link', '')
        venue.website_link = form_data.get('website_link', '')
        if 'looking_for_artist' in form_data.keys():
            if form_data['looking_for_artist'] == 'y' and 'looking_description' not in form_data.keys():
                raise Exception()
            else:
                venue.seeking_talent = form_data['looking_for_artist'] == 'y'
                if venue.seeking_talent:
                    venue.seeking_description = form_data['looking_description']

        city_name = form_data['city']
        state = form_data['state']
        c_tmp = City.query.filter(City.city == city_name).filter(City.state == state).first()
        if c_tmp is None:
            city = City(city=city_name, state=state)
            city.venues.append(venue)
        else:
            c_tmp.venues.append(venue)

        for genre in selected_genres:
            genre_tmp = Genre.query.filter(Genre.title == genre).first()
            if genre_tmp is None:
                g = Genre(title=genre)
                g.venues.append(venue)
            else:
                genre_tmp.venues.append(venue)

        db.session.commit()
        flash('Artist ' + request.form['name'] + ' was successfully Edited!')
    except:
        db.session.rollback()
        flash('An error has occurred!', 'error')
    finally:
        db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    try:
        selected_genres = request.form.getlist('genres')
        formdata = request.form
        artist = Artist(name=formdata['name'], phone=formdata['phone'],
                        image_link=formdata['image_link'],
                        facebook_link=formdata.get('facebook_link', ''), website_link=formdata.get('website_link', ''))
        if 'looking_for_venue' in formdata.keys():
            if formdata['looking_for_venue'] == 'y' and 'looking_description' not in formdata.keys():
                raise Exception()
            else:
                artist.seeking_venue = formdata['looking_for_venue'] == 'y'
                if artist.seeking_venue:
                    artist.seeking_description = formdata['looking_description']

        city_name = formdata['city']
        state = formdata['state']
        c_tmp = City.query.filter(City.city == city_name).filter(City.state == state).first()
        if c_tmp is None:
            city = City(city=city_name, state=state)
            city.artists.append(artist)
        else:
            c_tmp.artists.append(artist)

        for genre in selected_genres:
            genre_tmp = Genre.query.filter(Genre.title == genre).first()
            if genre_tmp is None:
                g = Genre(title=genre)
                g.artists.append(artist)
            else:
                genre_tmp.artists.append(artist)

        db.session.add(artist)
        db.session.commit()
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except:
        db.session.rollback()
        flash('An error has occurred!', 'error')
    finally:
        db.session.close()
    return redirect(url_for('index'))


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    shows = Show.query.join(Venue).join(Artist).all()
    return render_template('pages/shows.html', shows=shows)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    try:
        artist_id = int(request.form['artist_id'])
        venue_id = int(request.form['venue_id'])
        start_date = datetime.strptime(request.form['start_time'], '%Y-%m-%d %H:%M:%S')
        show = Show(venue_id=venue_id, artist_id=artist_id, start_time=start_date)
        db.session.add(show)
        db.session.commit()
        flash('Show was successfully listed!')
    except:
        db.session.rollback()
        flash('An error occurred!', 'error')
    finally:
        db.session.close()
        return render_template('pages/home.html')
    # on successful db insert, flash success


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
