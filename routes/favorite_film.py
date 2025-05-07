from flask import Blueprint, render_template, redirect, url_for, session, request, jsonify
from models.favorite import Favorite

favorite_bp = Blueprint('favorite', __name__)

@favorite_bp.route('/films/favorites')
def view_favorites():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session.get('user_id')
    
    # Get favorite films using the Favorite model
    films = Favorite.get_user_favorite_films(user_id)
    
    # Only keep films that have valid data
    films = [film for film in films if film]
    
    # Get top films
    top_films = films[:5] if len(films) >= 5 else films
    
    # Pagination
    items_per_page = 12
    total_films = len(films)
    total_pages = (total_films // items_per_page) + (1 if total_films % items_per_page != 0 else 0)
    
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * items_per_page
    end = start + items_per_page
    films_on_page = films[start:end]
    
    return render_template('favorites.html', 
                          films=films_on_page,
                          total_pages=total_pages,
                          current_page=page,
                          top_films=top_films)
