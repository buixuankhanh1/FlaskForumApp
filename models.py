# models.py

import json
import os
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
# Loại bỏ Generic, thêm Any
from typing import List, Optional, TypedDict, TypeVar, Any, cast

# Định nghĩa kiểu dữ liệu cho Bình luận
class Comment(TypedDict):
    id: str
    author: str
    text: str

# Định nghĩa kiểu dữ liệu cho Bài viết
class Post(TypedDict):
    id: str
    title: str
    content: str
    author: str
    comments: List[Comment]
    # <-- THÊM DÒNG NÀY: Một danh sách các URL của file đa phương tiện
    media_urls: List[str]

# Định nghĩa kiểu dữ liệu cho Người dùng
class User(TypedDict):
    username: str
    password: str # Mật khẩu đã được băm

# Tạo một biến TypeVar để biểu diễn bất kỳ kiểu dữ liệu nào cho danh sách
# Chúng ta vẫn cần T để các hàm load_users/load_posts có thể trả về kiểu cụ thể
T = TypeVar('T')

# Đường dẫn tới các file dữ liệu
USERS_FILE = 'users.json'
POSTS_FILE = 'posts.json'

# Cập nhật hàm load_data và save_data
# load_data: sẽ trả về List[Any] vì nội dung JSON có thể đa dạng
# và chúng ta sẽ ép kiểu nó ở các hàm gọi cụ thể (load_users, load_posts)
def load_data(filename: str) -> List[Any]: 
    """Tải dữ liệu từ một file JSON."""
    if not os.path.exists(filename):
        return []
    with open(filename, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_data(data: List[Any], filename: str) -> None: # data có thể là List[Any]
    """Lưu dữ liệu vào một file JSON."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- Quản lý Người dùng ---
def load_users() -> List[User]:
    """Tải danh sách người dùng từ file JSON."""
    # Ép kiểu rõ ràng sau khi tải dữ liệu
    return cast(List[User], load_data(USERS_FILE))

def save_users(users: List[User]) -> None:
    """Lưu danh sách người dùng vào file JSON."""
    save_data(users, USERS_FILE)

def add_user(username: str, password: str) -> bool:
    """Thêm người dùng mới."""
    users: List[User] = load_users()
    if any(user['username'] == username for user in users):
        return False
    
    hashed_password: str = generate_password_hash(password)
    users.append({'username': username, 'password': hashed_password})
    save_users(users)
    return True

def find_user(username: str) -> Optional[User]:
    """Tìm người dùng theo tên."""
    users: List[User] = load_users()
    for user in users:
        if user['username'] == username:
            return user
    return None

def verify_password(hashed_password: str, password: str) -> bool:
    """Kiểm tra mật khẩu."""
    return check_password_hash(hashed_password, password)

# --- Quản lý Bài viết ---
def load_posts() -> List[Post]:
    """Tải danh sách bài viết từ file JSON."""
    # Ép kiểu rõ ràng sau khi tải dữ liệu
    return cast(List[Post], load_data(POSTS_FILE))

def save_posts(posts: List[Post]) -> None:
    """Lưu danh sách bài viết vào file JSON."""
    save_data(posts, POSTS_FILE)

def get_post_by_id(post_id: str) -> Optional[Post]:
    """Tìm bài viết theo ID."""
    posts: List[Post] = load_posts()
    for post in posts:
        if post['id'] == post_id:
            return post
    return None

def add_post(title: str, content: str, author: str, media_urls: List[str]) -> str:
    """Thêm bài viết mới."""
    posts: List[Post] = load_posts()
    new_post: Post = {
        'id': str(uuid.uuid4()),
        'title': title,
        'content': content,
        'author': author,
        'comments': [],
        'media_urls': media_urls # <-- THÊM DÒNG NÀY
    }
    posts.append(new_post)
    save_posts(posts)
    return new_post['id']

def update_post(post_id: str, title: str, content: str, media_urls: List[str]) -> bool:
    """Cập nhật bài viết."""
    posts: List[Post] = load_posts()
    for post in posts:
        if post['id'] == post_id:
            post['title'] = title
            post['content'] = content
            post['media_urls'] = media_urls # <-- THÊM DÒNG NÀY (sẽ ghi đè nếu muốn thay thế hoàn toàn)
            # Hoặc nếu bạn muốn thêm vào (như trong app.py đã làm):
            # post.setdefault('media_urls', []).extend(media_urls)
            # Tuy nhiên, trong app.py chúng ta đã xử lý việc gộp danh sách trước khi gọi update_post
            save_posts(posts)
            return True
    return False

def delete_post(post_id: str) -> bool:
    """Xóa bài viết."""
    posts: List[Post] = load_posts()
    original_len = len(posts)
    posts = [post for post in posts if post['id'] != post_id]
    if len(posts) < original_len:
        save_posts(posts)
        return True
    return False

def add_comment(post_id: str, author: str, comment_text: str) -> bool:
    """Thêm bình luận vào bài viết."""
    posts: List[Post] = load_posts()
    for post in posts:
        if post['id'] == post_id:
            new_comment: Comment = {
                'id': str(uuid.uuid4()),
                'author': author,
                'text': comment_text
            }
            post['comments'].append(new_comment)
            save_posts(posts)
            return True
    return False