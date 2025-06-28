# app.py

from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.wrappers import Response as WerkzeugResponse # <-- Thêm dòng này

from models import (
    load_posts, save_posts, add_post, get_post_by_id, update_post, delete_post, add_comment,
    save_users, add_user, find_user, verify_password, USERS_FILE, POSTS_FILE,
    Post, User 
)
import os
from werkzeug.utils import secure_filename 
from typing import List, Optional, Dict, Union, Any

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'default_secret_key_for_development')

# Cấu hình tải lên file
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp3', 'mp4', 'mov'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # Giới hạn kích thước file tải lên là 16MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Hàm kiểm tra đuôi file có hợp lệ hay không
def allowed_file(filename: str) -> bool:
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Hàm xử lý tải lên file
def upload_files(files: List[Any]) -> List[str]:
    uploaded_urls: List[str] = []
    for file in files:
        if file and allowed_file(file.filename):
            filename: str = secure_filename(file.filename)
            file_path: str = os.path.join(app.config['UPLOAD_FOLDER'], filename) # type: ignore
            file.save(file_path)
            uploaded_urls.append(url_for('static', filename=f'uploads/{filename}'))
        else:
            # Bạn có thể thêm xử lý lỗi ở đây, ví dụ: flash message
            flash(f'File "{file.filename}" không được phép hoặc không hợp lệ.', 'error')
    return uploaded_urls

# Kiểm tra và tạo file dữ liệu nếu chưa tồn tại
if not os.path.exists(USERS_FILE):
    save_users([])
if not os.path.exists(POSTS_FILE):
    save_posts([])

# --- Context Processor cho người dùng hiện tại ---
@app.context_processor
def inject_user() -> Dict[str, Optional[str]]:
    return dict(current_user=session.get('username'))

# --- Routes chung ---
@app.route('/')
def index() -> str: # render_template trả về str là hợp lệ
    posts: List[Post] = load_posts()
    return render_template('index.html', posts=posts)

# --- Routes Bài viết ---
@app.route('/post/<post_id>')
def post_detail(post_id: str) -> Union[str, WerkzeugResponse]: # Sử dụng WerkzeugResponse
    post: Optional[Post] = get_post_by_id(post_id)
    if not post:
        flash('Bài viết không tồn tại.', 'error')
        return redirect(url_for('index'))
    return render_template('post_detail.html', post=post)

@app.route('/new_post', methods=['GET', 'POST'])
def new_post() -> Union[str, WerkzeugResponse]:
    if 'username' not in session:
        flash('Bạn cần đăng nhập để tạo bài viết.', 'warning')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title: str = request.form['title']
        content: str = request.form['content']
        author: str = session['username']
        
        # Xử lý tải lên file
        media_urls: List[str] = []
        if 'media_files' in request.files: # Kiểm tra xem có trường input với name='media_files' không
            files_to_upload = request.files.getlist('media_files') # Lấy tất cả các file từ trường này
            media_urls = upload_files(files_to_upload)

        if title and content:
            # Cập nhật hàm add_post để nhận media_urls
            # Chúng ta sẽ sửa hàm add_post trong models.py ở bước tiếp theo
            add_post(title, content, author, media_urls)  #type: ignore
            flash('Bài viết của bạn đã được đăng!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Tiêu đề và nội dung không được để trống.', 'error')
    return render_template('create_post.html')

@app.route('/edit_post/<post_id>', methods=['GET', 'POST'])
def edit_post(post_id: str) -> Union[str, WerkzeugResponse]:
    if 'username' not in session:
        flash('Bạn cần đăng nhập để chỉnh sửa bài viết.', 'warning')
        return redirect(url_for('login'))
    
    post: Optional[Post] = get_post_by_id(post_id)
    if not post:
        flash('Bài viết không tồn tại.', 'error')
        return redirect(url_for('index'))
    
    if post['author'] != session['username']:
        flash('Bạn không có quyền chỉnh sửa bài viết này.', 'error')
        return redirect(url_for('post_detail', post_id=post_id))

    if request.method == 'POST':
        title: str = request.form['title']
        content: str = request.form['content']
        
        # Xử lý tải lên file mới (thêm vào các file cũ)
        new_media_urls: List[str] = []
        if 'media_files' in request.files:
            files_to_upload = request.files.getlist('media_files')
            new_media_urls = upload_files(files_to_upload)
        
        # Lấy các media_urls hiện có và thêm các file mới vào
        # Đảm bảo post['media_urls'] luôn tồn tại
        existing_media_urls = post.get('media_urls', [])
        all_media_urls = existing_media_urls + new_media_urls

        if title and content:
            # Cập nhật hàm update_post để nhận media_urls
            # Chúng ta sẽ sửa hàm update_post trong models.py ở bước tiếp theo
            update_post(post_id, title, content, all_media_urls) #type: ignore
            flash('Bài viết đã được cập nhật.', 'success')
            return redirect(url_for('post_detail', post_id=post_id))
        else:
            flash('Tiêu đề và nội dung không được để trống.', 'error')

    # Khi tải trang chỉnh sửa, đảm bảo gửi media_urls hiện có đến template
    # Bạn sẽ cần cập nhật render_template trong edit_post để gửi post object đầy đủ
    return render_template('post_detail.html', post=post) # Dòng này đã đúng, post đã có media_urls

@app.route('/delete_post/<post_id>', methods=['POST'])
def delete_post_route(post_id: str) -> WerkzeugResponse: # Sử dụng WerkzeugResponse
    if 'username' not in session:
        flash('Bạn cần đăng nhập để xóa bài viết.', 'warning')
        return redirect(url_for('login'))
    
    post: Optional[Post] = get_post_by_id(post_id)
    if not post:
        flash('Bài viết không tồn tại.', 'error')
        return redirect(url_for('index'))
    
    if post['author'] != session['username']:
        flash('Bạn không có quyền xóa bài viết này.', 'error')
        return redirect(url_for('post_detail', post_id=post_id))

    if delete_post(post_id):
        flash('Bài viết đã được xóa.', 'success')
    else:
        flash('Không thể xóa bài viết.', 'error')
    return redirect(url_for('index'))

@app.route('/add_comment/<post_id>', methods=['POST'])
def add_comment_route(post_id: str) -> WerkzeugResponse: # Sử dụng WerkzeugResponse
    if 'username' not in session:
        flash('Bạn cần đăng nhập để bình luận.', 'warning')
        return redirect(url_for('login'))
    
    comment_text: str = request.form['comment_text']
    author: str = session['username']
    if comment_text:
        if add_comment(post_id, author, comment_text):
            flash('Bình luận của bạn đã được thêm.', 'success')
        else:
            flash('Không thể thêm bình luận. Bài viết không tồn tại?', 'error')
    else:
        flash('Bình luận không được để trống.', 'error')
    
    return redirect(url_for('post_detail', post_id=post_id))


# --- Routes Đăng ký/Đăng nhập ---
@app.route('/register', methods=['GET', 'POST'])
def register() -> Union[str, WerkzeugResponse]: # Sử dụng WerkzeugResponse
    if 'username' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username: str = request.form['username']
        password: str = request.form['password']
        
        if not username or not password:
            flash('Tên người dùng và mật khẩu không được để trống.', 'error')
        elif add_user(username, password):
            flash('Đăng ký thành công! Vui lòng đăng nhập.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Tên người dùng đã tồn tại.', 'error')
    return render_template('auth.html', form_type='register')

@app.route('/login', methods=['GET', 'POST'])
def login() -> Union[str, WerkzeugResponse]: # Sử dụng WerkzeugResponse
    if 'username' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username: str = request.form['username']
        password: str = request.form['password']
        
        user: Optional[User] = find_user(username)
        if user and verify_password(user['password'], password):
            session['username'] = username
            flash(f'Chào mừng, {username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Tên người dùng hoặc mật khẩu không đúng.', 'error')
    return render_template('auth.html', form_type='login')

@app.route('/logout')
def logout() -> WerkzeugResponse: # Sử dụng WerkzeugResponse
    session.pop('username', None)
    flash('Bạn đã đăng xuất.', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Đảm bảo debug=False khi triển khai lên production
    # Render sẽ tự động đặt môi trường là 'production' hoặc bạn có thể dùng biến env
    app.run(debug=os.environ.get('FLASK_ENV') == 'development')