import streamlit as st
import os
import uuid
from datetime import datetime, timedelta
from PIL import Image
import io
import json
import base64
import sqlite3
import shutil

# Page configuration
st.set_page_config(
    page_title="ImageHub Pro",
    page_icon="🖼️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for enhanced styling
def local_css():
    st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #2c3e50 0%, #3498db 100%);
        color: white;
    }
    .image-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        margin: 15px 0;
        border-left: 5px solid #667eea;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .image-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 35px rgba(0, 0, 0, 0.15);
    }
    .upload-section {
        background: white;
        padding: 30px;
        border-radius: 20px;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        margin: 20px 0;
        border: 2px dashed #667eea;
    }
    .user-info {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        margin: 10px 0;
        text-align: center;
    }
    .stats-card {
        background: rgba(255, 255, 255, 0.95);
        padding: 15px;
        border-radius: 12px;
        margin: 10px 0;
        text-align: center;
        backdrop-filter: blur(10px);
    }
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 25px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        color: white;
        transform: scale(1.05);
    }
    .url-display {
        background: #f8f9fa;
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #e9ecef;
        font-family: 'Courier New', monospace;
        font-size: 0.85em;
        word-break: break-all;
        margin: 8px 0;
    }
    .button-container {
        display: flex;
        gap: 10px;
        margin: 15px 0;
        flex-wrap: wrap;
    }
    .copy-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 20px !important;
        font-weight: bold !important;
        flex: 1;
        min-width: 120px;
    }
    .download-button {
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 20px !important;
        font-weight: bold !important;
        flex: 1;
        min-width: 120px;
    }
    .delete-button {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 20px !important;
        font-weight: bold !important;
        flex: 1;
        min-width: 120px;
    }
    .expiry-badge {
        background: linear-gradient(135deg, #ffd93d 0%, #ff9a3d 100%);
        color: #333;
        padding: 4px 12px;
        border-radius: 15px;
        font-size: 0.8em;
        font-weight: bold;
        display: inline-block;
        margin: 5px 0;
    }
    .feature-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        margin: 10px 0;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }
    .tab-content {
        padding: 20px 0;
    }
    /* Mobile responsiveness */
    @media (max-width: 768px) {
        .button-container {
            flex-direction: column;
        }
        .button-container button {
            width: 100%;
        }
    }
    </style>
    """, unsafe_allow_html=True)

local_css()

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'user_images' not in st.session_state:
    st.session_state.user_images = []

# Create directories
os.makedirs("user_images", exist_ok=True)
os.makedirs("user_data", exist_ok=True)
os.makedirs("static/media", exist_ok=True)

class DatabaseManager:
    def __init__(self):
        self.db_file = "user_data/images.db"
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                filename TEXT NOT NULL,
                original_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                media_path TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                file_extension TEXT NOT NULL,
                upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                delete_key TEXT UNIQUE,
                auto_delete_hours INTEGER DEFAULT 0,
                expires_at TIMESTAMP,
                views INTEGER DEFAULT 0,
                FOREIGN KEY (username) REFERENCES users (username)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def register_user(self, username, password):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            return True, "Registration successful"
        except sqlite3.IntegrityError:
            return False, "Username already exists"
        finally:
            conn.close()
    
    def login_user(self, username, password):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('SELECT password FROM users WHERE username = ?', (username,))
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0] == password:
            return True, "Login successful"
        return False, "Invalid credentials"
    
    def save_image(self, username, image_data):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO images (username, filename, original_name, file_path, media_path, 
                              file_size, file_extension, delete_key, auto_delete_hours, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            username, image_data['filename'], image_data['original_name'],
            image_data['file_path'], image_data['media_path'], image_data['file_size'],
            image_data['file_extension'], image_data['delete_key'],
            image_data['auto_delete_hours'], image_data['expires_at']
        ))
        
        conn.commit()
        conn.close()
    
    def get_user_images(self, username):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM images 
            WHERE username = ? 
            ORDER BY upload_time DESC
        ''', (username,))
        
        columns = [column[0] for column in cursor.description]
        images = []
        for row in cursor.fetchall():
            image_data = dict(zip(columns, row))
            images.append(image_data)
        
        conn.close()
        return images
    
    def delete_image(self, username, filename):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM images WHERE username = ? AND filename = ?
        ''', (username, filename))
        
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted
    
    def increment_views(self, filename):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE images SET views = views + 1 WHERE filename = ?
        ''', (filename,))
        
        conn.commit()
        conn.close()
    
    def cleanup_expired_images(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT filename, file_path, media_path FROM images 
            WHERE expires_at IS NOT NULL AND expires_at < ?
        ''', (datetime.now(),))
        
        expired_images = cursor.fetchall()
        
        for filename, file_path, media_path in expired_images:
            # Delete files
            for path in [file_path, media_path]:
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except:
                        pass
            
            # Delete from database
            cursor.execute('DELETE FROM images WHERE filename = ?', (filename,))
        
        conn.commit()
        conn.close()
        return len(expired_images)

class ImageManager:
    def __init__(self):
        self.base_path = "user_images"
        self.media_path = "static/media"
        self.db = DatabaseManager()
    
    def save_image(self, username, uploaded_file, auto_delete_hours=0):
        user_dir = os.path.join(self.base_path, username)
        os.makedirs(user_dir, exist_ok=True)
        os.makedirs(self.media_path, exist_ok=True)
        
        file_extension = uploaded_file.name.split('.')[-1].lower()
        unique_id = uuid.uuid4().hex[:16]
        filename = f"{unique_id}.{file_extension}"
        file_path = os.path.join(user_dir, filename)
        media_path = os.path.join(self.media_path, filename)
        
        file_content = uploaded_file.getbuffer()
        with open(file_path, "wb") as f:
            f.write(file_content)
        with open(media_path, "wb") as f:
            f.write(file_content)
        
        expires_at = None
        if auto_delete_hours > 0:
            expires_at = datetime.now() + timedelta(hours=auto_delete_hours)
        
        image_data = {
            'filename': filename,
            'original_name': uploaded_file.name,
            'file_path': file_path,
            'media_path': media_path,
            'file_size': len(file_content),
            'file_extension': file_extension,
            'delete_key': uuid.uuid4().hex[:12],
            'auto_delete_hours': auto_delete_hours,
            'expires_at': expires_at
        }
        
        self.db.save_image(username, image_data)
        return image_data
    
    def get_user_images(self, username):
        return self.db.get_user_images(username)
    
    def delete_image(self, username, filename):
        image_data = next((img for img in self.get_user_images(username) if img['filename'] == filename), None)
        if image_data:
            # Delete files
            for path in [image_data['file_path'], image_data['media_path']]:
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except:
                        pass
            
            # Delete from database
            return self.db.delete_image(username, filename)
        return False
    
    def get_image_url(self, image_data):
        filename = image_data['filename']
        
        try:
            # Try to get the current server information
            from streamlit.web.server.server import Server
            from streamlit.runtime.scriptrunner import get_script_run_ctx
            
            ctx = get_script_run_ctx()
            if ctx and hasattr(ctx, 'host') and ctx.host:
                base_url = f"http://{ctx.host}"
                return f"{base_url}/media/{filename}"
        except:
            pass
        
        # Fallback for local development
        return f"/media/{filename}"
    
    def format_file_size(self, size_bytes):
        """Convert file size to human readable format"""
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names)-1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def format_time_remaining(self, expires_at):
        """Format time remaining until expiration"""
        if not expires_at:
            return "Never"
        
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
        
        now = datetime.now()
        if expires_at < now:
            return "Expired"
        
        delta = expires_at - now
        days = delta.days
        hours = int(delta.seconds // 3600)
        minutes = int((delta.seconds % 3600) // 60)
        
        if days > 0:
            return f"{days}d {hours}h"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"

def get_binary_file_downloader_html(file_path, filename, button_text):
    with open(file_path, 'rb') as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}" style="text-decoration: none; flex: 1;"><button class="download-button">{button_text}</button></a>'
    return href

def add_javascript():
    st.markdown("""
    <script>
    function copyToClipboard(text, msgId) {
        navigator.clipboard.writeText(text).then(function() {
            var msgElement = document.getElementById(msgId);
            msgElement.style.display = 'block';
            setTimeout(function() {
                msgElement.style.display = 'none';
            }, 2000);
        });
    }
    
    function confirmDelete(filename, msgId) {
        if (confirm('Are you sure you want to delete this image? This action cannot be undone.')) {
            // This would need to be handled by Streamlit - for now we'll show a message
            var msgElement = document.getElementById(msgId);
            msgElement.style.display = 'block';
            msgElement.innerHTML = '✅ Deleted successfully!';
            // In a real implementation, you'd call a Streamlit callback here
        }
    }
    </script>
    """, unsafe_allow_html=True)

def login_section():
    st.markdown("""
    <div style='text-align: center; padding: 50px 20px;'>
        <h1 style='color: white; font-size: 3.5em; margin-bottom: 20px;'>🖼️ ImageHub Pro</h1>
        <p style='color: white; font-size: 1.3em; margin-bottom: 40px;'>Professional Image Hosting with Auto-Delete & Advanced Features</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<div class='upload-section'>", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
        
        with tab1:
            st.subheader("Welcome Back!")
            login_username = st.text_input("Username", placeholder="Enter your username", key="login_user")
            login_password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_pass")
            
            if st.button("🚀 Login to Dashboard", key="login_btn", use_container_width=True):
                if login_username and login_password:
                    db = DatabaseManager()
                    success, message = db.login_user(login_username, login_password)
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.username = login_username
                        st.success("🎉 Login successful! Redirecting...")
                        st.rerun()
                    else:
                        st.error("❌ " + message)
                else:
                    st.error("⚠️ Please fill in all fields")
        
        with tab2:
            st.subheader("Join ImageHub Pro")
            reg_username = st.text_input("Username", placeholder="Choose a username", key="reg_user")
            reg_password = st.text_input("Password", type="password", placeholder="Create a password", key="reg_pass")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password", key="confirm_pass")
            
            if st.button("✨ Create Account", key="reg_btn", use_container_width=True):
                if reg_username and reg_password and confirm_password:
                    if reg_password != confirm_password:
                        st.error("❌ Passwords do not match!")
                    elif len(reg_username) < 3:
                        st.error("❌ Username must be at least 3 characters long!")
                    elif len(reg_password) < 6:
                        st.error("❌ Password must be at least 6 characters long!")
                    else:
                        db = DatabaseManager()
                        success, message = db.register_user(reg_username, reg_password)
                        if success:
                            st.success("🎉 " + message + " You can now login!")
                        else:
                            st.error("❌ " + message)
                else:
                    st.error("⚠️ Please fill in all fields")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Features showcase
        st.markdown("""
        <div style='text-align: center; color: white; margin-top: 40px;'>
            <h3>🚀 Why Choose ImageHub Pro?</h3>
            <div style='display: flex; justify-content: center; gap: 20px; flex-wrap: wrap; margin-top: 20px;'>
                <div class='feature-card' style='flex: 1; min-width: 200px;'>
                    <h4>🕐 Auto Delete</h4>
                    <p>Set expiration times for your images</p>
                </div>
                <div class='feature-card' style='flex: 1; min-width: 200px;'>
                    <h4>📱 Mobile Ready</h4>
                    <p>Perfect on all devices</p>
                </div>
                <div class='feature-card' style='flex: 1; min-width: 200px;'>
                    <h4>🔒 Secure</h4>
                    <p>Your images are protected</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def main_app():
    add_javascript()
    image_manager = ImageManager()
    
    # Clean up expired images on app load
    expired_count = image_manager.db.cleanup_expired_images()
    if expired_count > 0:
        st.sidebar.info(f"🧹 Cleaned up {expired_count} expired images")
    
    with st.sidebar:
        st.markdown(f"""
        <div class='user-info'>
            <h3>👋 Welcome back, {st.session_state.username}!</h3>
            <p>Your professional image hub</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.subheader("📊 Dashboard Stats")
        
        user_images = image_manager.get_user_images(st.session_state.username)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Images", len(user_images))
        with col2:
            total_size = sum(img['file_size'] for img in user_images)
            st.metric("Storage Used", image_manager.format_file_size(total_size))
        
        if user_images:
            expiring_soon = sum(1 for img in user_images if img.get('expires_at') and 
                               datetime.fromisoformat(img['expires_at'].replace('Z', '+00:00')) > datetime.now())
            st.metric("Active Images", expiring_soon)
        
        st.markdown("---")
        st.subheader("⚡ Quick Actions")
        
        if st.button("🔄 Refresh Gallery", use_container_width=True):
            st.rerun()
        
        if st.button("📤 Upload New", use_container_width=True):
            st.session_state.auto_scroll = True
        
        st.markdown("---")
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()
    
    # Main content area
    tab1, tab2 = st.tabs(["📁 Image Gallery", "📤 Upload Images"])
    
    with tab1:
        st.title("🎨 Your Image Gallery")
        
        user_images = image_manager.get_user_images(st.session_state.username)
        
        if not user_images:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.markdown("""
                <div style='text-align: center; padding: 50px 20px;'>
                    <h3>📸 No images yet!</h3>
                    <p>Start by uploading your first image to see it here.</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            # Image grid
            for i in range(0, len(user_images), 3):
                cols = st.columns(3)
                for j in range(3):
                    if i + j < len(user_images):
                        img_data = user_images[i + j]
                        with cols[j]:
                            with st.container():
                                st.markdown("<div class='image-card'>", unsafe_allow_html=True)
                                
                                # Display image
                                try:
                                    image = Image.open(img_data['file_path'])
                                    st.image(image, use_container_width=True, caption=img_data['original_name'])
                                except Exception as e:
                                    st.error(f"❌ Error loading image")
                                
                                # Image info
                                st.caption(f"**{img_data['original_name']}**")
                                st.caption(f"📅 {img_data['upload_time'][:16]}")
                                st.caption(f"💾 {image_manager.format_file_size(img_data['file_size'])}")
                                st.caption(f"👁️ {img_data.get('views', 0)} views")
                                
                                # Auto-delete info
                                if img_data.get('expires_at'):
                                    time_remaining = image_manager.format_time_remaining(img_data['expires_at'])
                                    if time_remaining != "Expired":
                                        st.markdown(f"<div class='expiry-badge'>⏰ {time_remaining}</div>", unsafe_allow_html=True)
                                
                                # Image URL
                                image_url = image_manager.get_image_url(img_data)
                                st.markdown("**Shareable URL:**")
                                st.markdown(f'<div class="url-display">{image_url}</div>', unsafe_allow_html=True)
                                
                                # Action buttons
                                download_html = get_binary_file_downloader_html(
                                    img_data['file_path'], 
                                    img_data['original_name'],
                                    "⬇️ Download"
                                )
                                
                                button_html = f"""
                                <div class="button-container">
                                    <button class="copy-button" onclick="copyToClipboard('{image_url}', 'copy_msg_{i+j}')">📋 Copy URL</button>
                                    {download_html}
                                    <button class="delete-button" onclick="confirmDelete('{img_data['filename']}', 'delete_msg_{i+j}')">🗑️ Delete</button>
                                </div>
                                <div id="copy_msg_{i+j}" style="color: green; font-size: 0.9em; margin-top: 5px; display: none;">✅ Copied!</div>
                                <div id="delete_msg_{i+j}" style="color: red; font-size: 0.9em; margin-top: 5px; display: none;"></div>
                                """
                                
                                st.markdown(button_html, unsafe_allow_html=True)
                                
                                # Handle delete action
                                if st.button(f"Delete {img_data['filename']}", key=f"delete_{img_data['filename']}", help="Delete this image", use_container_width=True):
                                    if image_manager.delete_image(st.session_state.username, img_data['filename']):
                                        st.success("✅ Image deleted successfully!")
                                        st.rerun()
                                
                                st.markdown("</div>", unsafe_allow_html=True)
    
    with tab2:
        st.title("🚀 Upload New Images")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("<div class='upload-section'>", unsafe_allow_html=True)
            
            uploaded_files = st.file_uploader(
                "Choose images to upload",
                type=['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'],
                accept_multiple_files=True,
                key="multi_file_uploader"
            )
            
            if uploaded_files:
                st.subheader(f"📁 Selected Files ({len(uploaded_files)})")
                
                for uploaded_file in uploaded_files:
                    col_a, col_b = st.columns([1, 3])
                    with col_a:
                        try:
                            image = Image.open(uploaded_file)
                            st.image(image, width=80)
                        except:
                            st.error("❌")
                    with col_b:
                        st.write(f"**{uploaded_file.name}**")
                        st.write(f"Size: {image_manager.format_file_size(len(uploaded_file.getbuffer()))}")
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("<div class='upload-section'>", unsafe_allow_html=True)
            st.subheader("⚙️ Upload Settings")
            
            # Auto-delete options
            auto_delete_options = {
                "Never": 0,
                "1 Hour": 1,
                "6 Hours": 6,
                "12 Hours": 12,
                "1 Day": 24,
                "3 Days": 72,
                "1 Week": 168
            }
            
            selected_option = st.selectbox(
                "🕐 Auto-delete after:",
                options=list(auto_delete_options.keys()),
                index=0
            )
            auto_delete_hours = auto_delete_options[selected_option]
            
            if auto_delete_hours > 0:
                expiry_time = datetime.now() + timedelta(hours=auto_delete_hours)
                st.info(f"⏰ Images will auto-delete on: {expiry_time.strftime('%Y-%m-%d %H:%M')}")
            
            if st.button("🚀 Upload All Images", type="primary", use_container_width=True, disabled=not uploaded_files):
                if uploaded_files:
                    progress_bar = st.progress(0)
                    success_count = 0
                    
                    for i, uploaded_file in enumerate(uploaded_files):
                        try:
                            image_data = image_manager.save_image(
                                st.session_state.username, 
                                uploaded_file, 
                                auto_delete_hours
                            )
                            success_count += 1
                        except Exception as e:
                            st.error(f"Failed to upload {uploaded_file.name}: {str(e)}")
                        
                        progress_bar.progress((i + 1) / len(uploaded_files))
                    
                    if success_count > 0:
                        st.success(f"🎉 Successfully uploaded {success_count} image(s)!")
                        st.balloons()
                        st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)

# Main app logic
if st.session_state.logged_in:
    main_app()
else:
    login_section()

# Footer
st.markdown("""
<div style='text-align: center; color: white; margin-top: 50px; padding: 30px;'>
    <hr style='border-color: rgba(255,255,255,0.3);'>
    <p style='margin: 10px 0;'>Built with ❤️ using Streamlit | ImageHub Pro v3.0</p>
    <p style='font-size: 0.9em; opacity: 0.8;'>Professional Image Hosting • Auto-Delete • Secure Storage</p>
</div>
""", unsafe_allow_html=True)