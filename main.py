from flask import Flask, render_template, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os
from dotenv import load_dotenv

load_dotenv()

TMDB_API_KEY = os.getenv('TMDB_API_KEY')

app = Flask(__name__)
app.app_context().push()
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
Bootstrap(app)

# CREATE DATABASE
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///my_favorite_movies.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# CREATE TABLE
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(1000), nullable=False)
    rating = db.Column(db.String(4), nullable=False)
    ranking = db.Column(db.String(4), nullable=False)
    review = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String(1000), nullable=False)

    # Optional: this will allow each book object to be identified by its title when printed.
    def __repr__(self):
        return f'<Movie {self.title}>'


db.create_all()


# CREATE EDIT FORM
class RateMovieForm(FlaskForm):
    rating = StringField('Your Rating Out of 10 e.g. 7.5', validators=[DataRequired()])
    review = StringField('Your Review', validators=[DataRequired()])
    submit = SubmitField('Done')


# CREATE ADD NEW MOVIE FORM
class AddMovieForm(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField('Done')


@app.route("/")
def home():
    # READ ALL RECORDS
    all_movies = Movie.query.order_by(Movie.rating).all()
    for i in range(len(all_movies)):
        # This line gives each movie a new ranking reversed from their order in all_movies
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route("/edit/<id>", methods=["GET", "POST"])
def edit(id):
    form = RateMovieForm()
    movie_selected = Movie.query.get(id)
    if form.validate_on_submit():
        movie_selected.rating = form.rating.data
        movie_selected.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", form=form, movie=movie_selected)


@app.route("/delete/<id>", methods=["GET", "POST"])
def delete(id):
    movie_to_delete = Movie.query.get(id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for("home"))


def tmdb_select(new_movie):
    movie_list = []
    tmdb_endpoint = "https://api.themoviedb.org/3/search/movie"
    tmdb_params = {
        "query": new_movie,
        "api_key": TMDB_API_KEY,
    }
    response = requests.get(tmdb_endpoint, params=tmdb_params)
    response.raise_for_status()
    movie_data = response.json()
    for result in movie_data["results"]:
        movie_list.append([result["id"], result["title"], result["release_date"]])
    return movie_list


def tmdb_detail(movie_id):
    tmdb_endpoint_id_search = f"https://api.themoviedb.org/3/movie/{movie_id}"
    tmdb_params_id_search = {
        "api_key": TMDB_API_KEY,
    }
    response = requests.get(tmdb_endpoint_id_search, params=tmdb_params_id_search)
    response.raise_for_status()
    movie_detail = response.json()
    new_movie = Movie(
        title=movie_detail["title"],
        year=movie_detail["release_date"],
        description=movie_detail["overview"],
        img_url=f"https://image.tmdb.org/t/p/w500/{movie_detail['poster_path']}",
        rating="None",
        ranking="None",
        review="None",
    )
    db.session.add(new_movie)
    db.session.commit()
    new_entry = Movie.query.filter_by(title=movie_detail["title"]).first()
    return new_entry.id


@app.route("/add", methods=["GET", "POST"])
def add():
    form = AddMovieForm()
    if form.validate_on_submit():
        new_movie = form.title.data
        movie_data = tmdb_select(new_movie)
        return render_template("select.html", movie_data=movie_data)
    return render_template("add.html", form=form)


@app.route("/select/<movie>", methods=["GET", "POST"])
def select(movie):
    movie_id = int((movie[1:]).split(",")[0])
    new_db_id = tmdb_detail(movie_id)
    return redirect(url_for('edit', id=new_db_id))


if __name__ == '__main__':
    app.run(debug=True)
