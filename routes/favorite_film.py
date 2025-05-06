from flask import Blueprint, render_template, redirect, url_for, session,request
from pymongo import MongoClient
import os
import requests
from bson import ObjectId

favorite_bp = Blueprint('favorite', __name__)

# MongoDB connection settings
uri = os.environ.get('MONGO_URI', "mongodb+srv://kiwi:trang%402005@film-users.10h2w59.mongodb.net/?retryWrites=true&w=majority")
dbname = os.environ.get('MONGO_DBNAME', "film-users")

def get_db():
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    db = client[dbname]
    return client, db

@favorite_bp.route('/films/favorites')
def view_favorites():
    client, db = get_db()
    if db is None:
        return redirect(url_for('login'))
    
    try:
        user_id = session.get('user_id')  # Lấy user_id từ session
        if not user_id:
            return redirect(url_for('login'))  # Nếu không có user_id, chuyển hướng tới login
        
        # Tìm tất cả các bộ phim yêu thích của người dùng
        favorites = db.favorites.find({"user_id": ObjectId(user_id)})
        
        films = []
        for favorite in favorites:
            film = db.films.find_one({"id": favorite["film_id"]})
            if film:
                films.append(film)  # Thêm thông tin phim vào mảng films
        # top phimphim
        top_films = list(db.films.find().sort("rating", -1).limit(5))
        # Tính tổng số trang (Ví dụ: giả sử mỗi trang hiển thị 8 phim)
        items_per_page = 12
        total_films = len(films)  # Số lượng phim yêu thích
        total_pages = (total_films // items_per_page) + (1 if total_films % items_per_page != 0 else 0)
        
        # Lấy phim cho trang hiện tại (có thể thêm phân trang nếu cần)
        page = request.args.get('page', 1, type=int)  # Lấy trang hiện tại từ query string, mặc định là trang 1
        start = (page - 1) * items_per_page
        end = start + items_per_page
        films_on_page = films[start:end]  # Lấy các phim trên trang hiện tại
        
        return render_template('favorites.html', 
                               films=films_on_page,  # Truyền các phim của trang hiện tại
                               total_pages=total_pages,  # Truyền tổng số trang
                               current_page=page,   # Truyền trang hiện tại
                               top_films=top_films) #top_phim
    finally:
        client.close()
