from tkinter import *
from tkinter import filedialog, messagebox
import sqlite3
from datetime import datetime, timedelta
from PIL import Image, ImageTk , ImageDraw , ImageFont
from tkinter import Canvas, Scrollbar
from tkinter import ttk
import re , os , qrcode #การตรวจสอบข้อมูลหรือค้นหาข้อมูลด้วยรูปแบบเฉพาะ

conn = sqlite3.connect(r"D:\c.db")
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT,
                    email TEXT UNIQUE,
                    first_name TEXT,
                    last_name TEXT,
                    gender TEXT,
                    birth_date TEXT,
                    phone_number TEXT,
                    profile_image TEXT);''')

c.execute('''CREATE TABLE IF NOT EXISTS movies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    poster_path TEXT NOT NULL,
                    second_poster_path TEXT NOT NULL,
                    genre TEXT NOT NULL,
                    age_rating TEXT NOT NULL,
                    runtime INTEGER NOT NULL)''')

c.execute('''CREATE TABLE IF NOT EXISTS booking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    movie_title TEXT,
                    show_date TEXT,
                    show_time TEXT,
                    seats TEXT,
                    total_price INTEGER ,
                    payment_date TEXT,
                    payment_status TEXT,
                    ticket_number TEXT)''')

conn.commit()

selected_date_text = "None"
selected_time_text = "None"
selected_seats = []
current_user = ""
open_windows = [] #เก็บข้อมูลการใช้งานหน้าต่าง แล้วสั่งปิดพร้อมกัน ในหน้าสรุปผล 

def create_admin_user():
    admin_users = [("PSXz", "0990248137"),("Nu", "123456"),("A","123")]
    
    for username, password in admin_users:
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        admin_exists = c.fetchone() #ลูปการดึงข้อมูล ผู้ดูแลมาตรวจสอบ
        
        if not admin_exists:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            print(f"Admin user {username} created.")

    conn.commit()

create_admin_user()

def register_user(username, password, first_name, last_name, phone_number, gender, birth_date , email):
    while True:
        # ตรวจสอบชื่อผู้ใช้
        if not username or len(username) < 4 :
            messagebox.showerror("Error", "Username must be at least 4 characters long.")
            return

        # ตรวจสอบรหัสผ่าน
        if not (re.search(r'[A-Za-z]', password) and len(re.findall(r'\d', password)) >= 4):
            messagebox.showerror("Error", "Password must contain at least 1 letter and at least 4 numbers.")
            return

        # ตรวจสอบชื่อจริง (first_name)
        if not first_name.strip():
            messagebox.showerror("Error", "First name cannot be empty.")
            return

        # ตรวจสอบนามสกุล (last_name)
        if not last_name.strip():
            messagebox.showerror("Error", "Last name cannot be empty.")
            return

        if not (phone_number.isdigit() and len(phone_number) == 10 and phone_number.startswith("0")):
            messagebox.showerror("Error", "Phone number must be 10 digits and start with '0'.")
            return
        
        valid_genders = ["Male", "Female", "Other"] 
        if gender.strip() not in valid_genders:
            messagebox.showerror("Error", "Gender must be one of the following: Male, Female, Other.")
            return

        # ตรวจสอบเพศ (gender)
        if not gender.strip():
            messagebox.showerror("Error", "Gender cannot be empty.")
            return

        # ตรวจสอบวันเดือนปีเกิด (birth_date)
        if not re.match(r'^\d{2}/\d{2}/\d{4}$', birth_date):
            messagebox.showerror("Error", "Birth date must be in the format DD/MM/YYYY.")
            return
        
        # ตรวจสอบอีเมล (email)
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            messagebox.showerror("Error", "Please enter a valid email address using only English characters.")
            return

        try:
            c.execute(''' 
                INSERT INTO users 
                (username, password, first_name, last_name, phone_number, gender, birth_date, email) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?) 
            ''', (username, password, first_name, last_name, phone_number, gender, birth_date, email))
            
            conn.commit()
            messagebox.showinfo("Success", "User registration is complete. Please Sign In.")
            break  
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Registration unsuccessful because the username is already in use.")
            return
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

def login_user():
    global current_user
    username = username_entry.get().strip()
    password = password_entry.get().strip() 
    if username and password:  
        with conn: 
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username=?", (username,))
            user = cursor.fetchone()  
            
            if user: 
                stored_password = user[2] 
                if password == stored_password:  
                    current_user = username  
                    
                    # ตรวจสอบว่าเป็นผู้ดูแลระบบ
                    if username in ["PSXz", "Nu"]:  
                        messagebox.showinfo("Success", f"{username} Login Successful! (Admin)")
                        open_admin_window()  
                    else:
                        messagebox.showinfo("Success", "Login Successful!")
                        open_movie_select()  
                else:
                    messagebox.showerror("Error", "Invalid password.")  
            else:
                messagebox.showerror("Error", "Username not found.")  
    else:
        messagebox.showerror("Error", "Please fill in all fields.")

def format_date(event, entry):
    date_value = entry.get()

    date_value = ''.join(filter(str.isdigit, date_value))

    # เพิ่ม / ตามลำดับ วัน/เดือน/ปี
    if len(date_value) >= 2:
        date_value = date_value[:2] + '/' + date_value[2:]
    if len(date_value) >= 5:
        date_value = date_value[:5] + '/' + date_value[5:]

    # ทำให้ผู้ใช้กรอกแบบถูกต้องโดยไม่มี / มากเกินไป
    if len(date_value) > 10:
        date_value = date_value[:10]
        
    entry.delete(0, 'end')  
    entry.insert(0, date_value)  

    if len(date_value) == 10:
        try:
            # แปลงเป็นวันที่เพื่อทำการตรวจสอบ
            day, month, year = map(int, date_value.split('/'))
            if not is_valid_date(day, month, year):
                raise ValueError("Invalid date. Please enter a valid date.")

            # ตรวจสอบว่าไม่เกินวันปัจจุบัน 
            today = datetime.today()
            if year > today.year or (year == today.year and month > today.month) or (year == today.year and month == today.month and day > today.day):
                raise ValueError("Date cannot be in the future.")

        except ValueError as e:
            messagebox.showerror("Invalid Date", str(e))
            entry.delete(0, 'end')

def is_valid_date(day, month, year):
    try:
        # ใช้ datetime เพื่อตรวจสอบวันเดือนปี
        new_date = datetime(year, month, day)
        return True
    except ValueError:
        return False

def open_register_window():
    register_window = Toplevel(root)
    register_window.title("Register")
    register_window.state("zoomed")
    root.withdraw()

    bg_image = Image.open(r"D:\GUI\Sign up.png")
    canvas = Canvas(register_window)
    canvas.pack(fill="both", expand=True)

    def set_placeholder(entry, placeholder):
        entry.insert(0, placeholder)
        entry.config(fg="grey")
        def on_focus_in(event):
            if entry.get() == placeholder:
                entry.delete(0, "end")
                entry.config(fg="black")
        def on_focus_out(event):
            if entry.get() == "":
                entry.insert(0, placeholder)
                entry.config(fg="grey")
        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)

    def update_bg_image(event):
        screen_width = register_window.winfo_width()
        screen_height = register_window.winfo_height()
        resized_image = bg_image.resize((screen_width, screen_height), Image.LANCZOS)
        bg_resized = ImageTk.PhotoImage(resized_image)
        canvas.delete("all")
        canvas.create_image(0, 0, image=bg_resized, anchor="nw")
        canvas.image = bg_resized

    register_window.bind("<Configure>", update_bg_image)

    Label(canvas, text="Sign Up", bg="white", fg="#3399FF", font=("Microsoft YaHei UI Bold", 50)).place(x=650, y=95)

    y_positions = {"username": 250, "password": 320, "first_name": 390,"last_name": 390, "phone_number": 460, "gender": 460,"birth_date": 530 , "email": 530 }

    # User Entry
    reg_username_entry = Entry(canvas, width=25, bg="white", font=("Microsoft YaHei UI Regular", 20), relief="ridge", borderwidth=3, highlightthickness=0)
    reg_username_entry.place(x=400, y=250)
    set_placeholder(reg_username_entry, "Username")
    
    # Password Entry
    reg_password_entry = Entry(canvas, width=25, bg="white", font=("Microsoft YaHei UI Regular", 20), relief="ridge", borderwidth=3, highlightthickness=0, show="")
    reg_password_entry.place(x=400, y=y_positions["password"])
    set_placeholder(reg_password_entry, "Password")
    
    # First Name Entry
    reg_first_name_entry = Entry(canvas, width=25, bg="white", font=("Microsoft YaHei UI Regular", 20), relief="ridge", borderwidth=3, highlightthickness=0)
    reg_first_name_entry.place(x=400, y=y_positions["first_name"])
    set_placeholder(reg_first_name_entry, "First Name")
    
    # Last Name Entry
    reg_last_name_entry = Entry(canvas, width=25, bg="white", font=("Microsoft YaHei UI Regular", 20), relief="ridge", borderwidth=3, highlightthickness=0)
    reg_last_name_entry.place(x=850, y=y_positions["last_name"])
    set_placeholder(reg_last_name_entry, "Last Name")
    
    # Phone Number Entry
    reg_phone_entry = Entry(canvas, width=25, bg="white", font=("Microsoft YaHei UI Regular", 20), relief="ridge", borderwidth=3, highlightthickness=0)
    reg_phone_entry.place(x=400, y=y_positions["phone_number"])
    set_placeholder(reg_phone_entry, "Phone Number")
    
    # Gender Entry
    reg_gender_entry = Entry(canvas, width=25, bg="white", font=("Microsoft YaHei UI Regular", 20), relief="ridge", borderwidth=3, highlightthickness=0)
    reg_gender_entry.place(x=850, y=y_positions["gender"])
    set_placeholder(reg_gender_entry, "Gender")
    
    # Birth Date Entry
    reg_birth_date_entry = Entry(canvas, width=25, bg="white", font=("Microsoft YaHei UI Regular", 20), relief="ridge", borderwidth=3, highlightthickness=0)
    reg_birth_date_entry.place(x=400, y=y_positions["birth_date"])
    set_placeholder(reg_birth_date_entry, "Birth Date (DD/MM/YYYY)")
    
    reg_birth_date_entry.bind("<KeyRelease>", lambda event: format_date(event, reg_birth_date_entry))

    reg_email_entry = Entry(canvas, width=25, bg="white", font=("Microsoft YaHei UI Regular", 20), relief="ridge", borderwidth=3, highlightthickness=0)
    reg_email_entry.place(x=850, y=y_positions["email"])  # Add email field position
    set_placeholder(reg_email_entry, "Email")


    Sign_Up_button = Button(canvas, text="Sign Up", relief="flat", bg="#38b6ff", borderwidth=3, highlightthickness=3, command=lambda: register_user(reg_username_entry.get(),reg_password_entry.get(),reg_first_name_entry.get(),reg_last_name_entry.get(),reg_phone_entry.get(),reg_gender_entry.get(),reg_birth_date_entry.get(),reg_email_entry.get()),font=("Microsoft YaHei UI Bold", 20 ), fg="white")
    Sign_Up_button.place(x=590, y=630)

    back_button = Button(canvas, text="Back", relief="flat", bg="#38b6ff", borderwidth=2, highlightthickness=3, command=lambda: (register_window.withdraw(), root.deiconify(), root.state("zoomed")),font=("Microsoft YaHei UI Bold", 20 ) ,fg="white")
    back_button.place(x=830, y=630)

def load_user_details():
    if not current_user:
        print("Debug: current_user is None or empty.") 
        messagebox.showerror("Error", "No user is logged in.")
        return None

    try:
        c.execute("SELECT * FROM users WHERE username=?", (current_user,))
        user = c.fetchone()
        print("Debug: SQL query executed.")  # Debugging
        print("Fetched user:", user)  # Debugging
        
        if user:
            return user
        else:
            messagebox.showerror("Error", "User not found in the database.")
            return None
    except sqlite3.Error as e:
        print("Debug: Database error occurred:", e)  # Debugging
        messagebox.showerror("Database Error", f"An error occurred: {e}")
        return None

def open_user_profile():
    user = load_user_details()
    if user:
        profile_window = Toplevel(root)
        profile_window.title("User Profile")
        profile_window.state("zoomed")  # ทำให้หน้าต่างขยายเต็มหน้าจอ
        
        # โหลดภาพพื้นหลัง
        bg_image = Image.open(r"D:\GUI\p.png")
        canvas = Canvas(profile_window)
        canvas.pack(fill="both", expand=True)

        def update_bg_image(event):
            screen_width = profile_window.winfo_width()
            screen_height = profile_window.winfo_height()
            
            resized_image = bg_image.resize((screen_width, screen_height), Image.LANCZOS)
            bg_resized = ImageTk.PhotoImage(resized_image)
            canvas.delete("all")  # ลบภาพพื้นหลังเก่า
            canvas.create_image(0, 0, image=bg_resized, anchor="nw")
            canvas.image = bg_resized  # เก็บ reference เพื่อป้องกันการถูก garbage collected

        profile_window.bind("<Configure>", update_bg_image)

        # แสดงข้อมูลผู้ใช้
        details = [
            f"Username : {user[1]}",
            f"Email : {user[3]}",
            f"First Name: {user[4]}",
            f"Last Name: {user[5]}",
            f"Gender: {user[6]}",
            f"Birth Date: {user[7]}",
            f"Phone Number: {user[8]}"
        ]
        
        # ตั้งค่าตำแหน่งเริ่มต้นของข้อมูล
        x_position = 725
        y_position = 180
        for detail in details:
            Label(profile_window, text=detail, font=("Microsoft YaHei UI Bold ", 27), bg="white").place(x=x_position, y=y_position)
            y_position += 50  # ปรับระยะห่างระหว่างข้อมูล

        # ตรวจสอบและดึงรูปโปรไฟล์
        profile_image_path = user[9] if len(user) > 9 and user[9] else 'default_profile_pic.png'  # ถ้าไม่มีรูปให้ใช้รูปเริ่มต้น
        try:
            profile_image = Image.open(profile_image_path)
            profile_image = profile_image.resize((156, 158))
            profile_photo = ImageTk.PhotoImage(profile_image)
            profile_label = Label(profile_window, image=profile_photo)
            profile_label.image = profile_photo
            profile_label.place(x=520, y=180)  # ปรับตำแหน่งรูปโปรไฟล์
        except:
            # ถ้าไม่สามารถเปิดภาพได้ แสดงเป็นภาพเริ่มต้น
            profile_image = Image.open(r"D:\GUI\256.png")
            profile_image = profile_image.resize((156, 158))
            profile_photo = ImageTk.PhotoImage(profile_image)
            profile_label = Label(profile_window, image=profile_photo)
            profile_label.image = profile_photo
            profile_label.place(x=520, y=180)  # ปรับตำแหน่งรูปโปรไฟล์

        y_position += 170  # ปรับระยะห่างหลังจากแสดงรูปโปรไฟล์

        # ปุ่มแก้ไขข้อมูล
        edit_button = Button(profile_window, text="Edit Profile", command=lambda: (profile_window.destroy(), open_edit_profile(user)),font=("Microsorft YaHei UI Bold",20))
        edit_button.place(x = 550 , y = 600)

        # ปุ่มปิด
        close_button = Button(profile_window, text="Close", command=profile_window.destroy,font=("Microsorft YaHei UI Bold",20))
        close_button.place(x=900, y = 600)

def open_edit_profile(user):
    edit_window = Toplevel(root)
    edit_window.title("Edit Profile")
    edit_window.state("zoomed")  # ทำให้หน้าต่างขยายเต็มหน้าจอ

    # โหลดภาพพื้นหลัง
    bg_image = Image.open(r"D:\GUI\p.png")
    canvas = Canvas(edit_window)
    canvas.pack(fill="both", expand=True)

    def update_bg_image(event):
        screen_width = edit_window.winfo_width()
        screen_height = edit_window.winfo_height()

        resized_image = bg_image.resize((screen_width, screen_height), Image.LANCZOS)
        bg_resized = ImageTk.PhotoImage(resized_image)
        canvas.delete("all")  # ลบภาพพื้นหลังเก่า
        canvas.create_image(0, 0, image=bg_resized, anchor="nw")
        canvas.image = bg_resized  # เก็บ reference เพื่อป้องกันการถูก garbage collected

    edit_window.bind("<Configure>", update_bg_image)

    y_position = 180
    Label(edit_window, text="First Name", font=("Microsoft YaHei UI", 16)).place(x=550, y=y_position)
    first_name_entry = Entry(edit_window, font=("Microsoft YaHei UI", 16),width=20)
    first_name_entry.insert(0, user[4]) 
    first_name_entry.place(x=800, y=y_position)
    y_position += 50

    Label(edit_window, text="Last Name", font=("Microsoft YaHei UI", 16)).place(x=550, y=y_position)
    last_name_entry = Entry(edit_window, font=("Microsoft YaHei UI", 16))
    last_name_entry.insert(0, user[5]) 
    last_name_entry.place(x=800, y=y_position)
    y_position += 50

    Label(edit_window, text="Phone Number", font=("Microsoft YaHei UI", 16)).place(x=550, y=y_position)
    phone_number_entry = Entry(edit_window, font=("Microsoft YaHei UI", 16))
    phone_number_entry.insert(0, user[8]) 
    phone_number_entry.place(x=800, y=y_position)
    y_position += 50

    Label(edit_window, text="Email", font=("Microsoft YaHei UI", 16)).place(x=550, y=y_position)
    email_entry = Entry(edit_window, font=("Microsoft YaHei UI", 16))
    email_entry.insert(0, user[3])
    email_entry.place(x=800, y=y_position)
    y_position += 50

    Label(edit_window, text="Gender", font=("Microsoft YaHei UI", 16)).place(x=550, y=y_position)
    gender_var = StringVar(value=user[6])
    gender_combobox = ttk.Combobox(edit_window, textvariable=gender_var, values=["Male", "Female", "Other"], state="readonly", font=("Microsoft YaHei UI", 12))
    gender_combobox.place(x=800, y=y_position)
    y_position += 50

    Label(edit_window, text="DD/MM/YYYY", font=("Microsoft YaHei UI", 16)).place(x=550, y=y_position)
    birth_date_entry = Entry(edit_window, font=("Microsoft YaHei UI", 16))
    birth_date_entry.insert(0, user[7]) 
    birth_date_entry.place(x=800, y=y_position)
    y_position += 50

    birth_date_entry.bind("<KeyRelease>", lambda event, entry=birth_date_entry: format_date(event, entry))

    # ปุ่มอัพโหลดภาพโปรไฟล์ใหม่
    def upload_image():
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")])
        if file_path:
            new_profile_image_path.set(file_path)  # เก็บ path ของไฟล์ที่เลือก
            profile_image = Image.open(file_path)
            profile_image = profile_image.resize((156, 158))
            profile_photo = ImageTk.PhotoImage(profile_image)
            profile_label.config(image=profile_photo)
            profile_label.image = profile_photo

    new_profile_image_path = StringVar()
    profile_image_path = user[9] if len(user) > 9 and user[9] else 'default_profile_pic.png'
    try:
        profile_image = Image.open(profile_image_path)
        profile_image = profile_image.resize((156, 158))
        profile_photo = ImageTk.PhotoImage(profile_image)
    except:
        profile_image = Image.open(r"D:\GUI\256.png") #เซ็ตภาพเริ่มต้นกรณีไม่อัพโหลดรูป
        profile_image = profile_image.resize((156, 158))
        profile_photo = ImageTk.PhotoImage(profile_image)

    profile_label = Label(edit_window, image=profile_photo)
    profile_label.image = profile_photo
    profile_label.place(x=200, y=180)

    upload_button = Button(edit_window, text="Upload Profile Image", command=upload_image)
    upload_button.place(x=215, y=350)

    save_button = Button(edit_window, text="Save Changes", command=lambda: save_profile_changes(user, first_name_entry, last_name_entry, phone_number_entry, email_entry, gender_var, new_profile_image_path.get(), birth_date_entry.get(),edit_window), font=("Microsoft YaHei UI", 14), bg="#38b6ff", fg="white")
    save_button.place(x=680, y=600)

def save_profile_changes(user, first_name_entry, last_name_entry, phone_number_entry, email_entry, gender_var, new_profile_image_path, birth_date, edit_window):
    new_first_name = first_name_entry.get()
    new_last_name = last_name_entry.get()
    new_phone_number = phone_number_entry.get()
    new_email = email_entry.get()
    new_gender = gender_var.get()
    
    profile_image_path = new_profile_image_path if new_profile_image_path else user[9]
    
    new_birth_date = birth_date 

    c.execute('''UPDATE users SET first_name=?, last_name=?, phone_number=?, email=?, gender=?, profile_image=?, birth_date=? WHERE username=?''',
              (new_first_name, new_last_name, new_phone_number, new_email, new_gender, profile_image_path, new_birth_date, user[1]))
    conn.commit()

    messagebox.showinfo("Success", "Profile updated successfully!")
    edit_window.destroy()
    open_user_profile()

def open_about():
    about_window = Toplevel()
    about_window.title("ข้อมูลผู้จัดทำ")
    about_window.state("zoomed")

    # โหลดภาพพื้นหลัง
    bg_image = Image.open(r"D:\GUI\ab.png")
    canvas = Canvas(about_window)
    canvas.pack(fill="both", expand=True)

    def update_bg_image(event):
        screen_width = root.winfo_width()
        screen_height = root.winfo_height()
    
        resized_image = bg_image.resize((screen_width, screen_height), Image.LANCZOS)
        bg_resized = ImageTk.PhotoImage(resized_image)
        canvas.delete("all") 
        canvas.create_image(0, 0, image=bg_resized, anchor="nw")
        canvas.image = bg_resized  # เก็บ reference เพื่อป้องกันการถูก garbage collected

    about_window.bind("<Configure>", update_bg_image)

    back_button = Button(canvas, text="ย้อนกลับ", relief="flat", bg="#38b6ff", borderwidth=2, highlightthickness=3, command=lambda: (about_window.withdraw()),font=("Microsoft YaHei UI Bold", 20 ) ,fg="white")
    back_button.place(x=1400, y=720)

def open_admin_window():
    global admin_window
    admin_window = Toplevel()
    admin_window.title("จัดการหนัง")
    admin_window.state("zoomed")
    root.withdraw()

    bg_image = Image.open(r"D:\GUI\movie_select.png")
    canvas = Canvas(admin_window)
    canvas.pack(fill="both", expand=True)

    def update_bg_image(event=None):
        screen_width = admin_window.winfo_width()  
        screen_height = admin_window.winfo_height()  
        resized_image = bg_image.resize((screen_width, screen_height), Image.LANCZOS)
        bg_resized = ImageTk.PhotoImage(resized_image)
        canvas.delete("all")
        canvas.create_image(0, 0, image=bg_resized, anchor="nw")
        canvas.image = bg_resized  

    admin_window.bind("<Configure>", update_bg_image)  

    btn_add_movie = Button(admin_window, text="เพิ่มรายการภาพยนต์", bg="#0097b2", font=("Microsoft YaHei UI Bold", 20), fg="white", width="20", height="1", command=open_add_movie_window)
    btn_add_movie.place(x=800, y=720)

    btn_logout = Button(admin_window, text="ออกจากระบบ", bg="red", font=("Microsoft YaHei UI Bold", 16), fg="white", width="10", height="1", command=lambda: (admin_window.destroy(), root.deiconify(), root.state("zoomed")))
    btn_logout.place(x=1370, y=10)

    btn_sales_summary = Button(admin_window, text="สรุปการขาย", bg="#0097b2", font=("Microsoft YaHei UI Bold", 20), fg="white", width="20", height="1", command= open_all_summary)
    btn_sales_summary.place(x=400, y=720)

    show_movies(admin_window)
    
def open_add_movie_window():
    add_movie_window = Toplevel()
    add_movie_window.title("เพิ่มหนัง")
    add_movie_window.state("zoomed")
    admin_window.withdraw()
    
    bg_image = Image.open(r"D:\GUI\add_movie.png")
    canvas = Canvas(add_movie_window)
    canvas.place(x=0, y=0, relwidth=1, relheight=1) 

    def update_bg_image(event=None):
        screen_width = add_movie_window.winfo_width()
        screen_height = add_movie_window.winfo_height()

        resized_image = bg_image.resize((screen_width, screen_height), Image.LANCZOS)
        bg_resized = ImageTk.PhotoImage(resized_image)
        canvas.delete("all")  # ลบภาพพื้นหลังเก่า
        canvas.create_image(0, 0, image=bg_resized, anchor="nw")
        canvas.image = bg_resized  

    add_movie_window.bind("<Configure>", update_bg_image)

    def create_entry_with_bottom_border(parent, x, y):
        entry_frame = Frame(parent, bg="white")
        entry_frame.place(x=x, y=y)

        entry = Entry(entry_frame, bd=0, width=20, font=("Microsoft YaHei UI Thin", 20))
        entry.pack(side=TOP)

        border = Frame(entry_frame, height=3, bg='#0097b2')
        border.pack(side=TOP, fill=X)

        return entry

    def create_label(parent, text, x, y):
        label_font = ("Microsoft YaHei UI bold", 16, )
        label = Label(parent, text=text, bg="white", font=label_font, fg="#0097b2")
        label.place(x=x, y=y)
        return label

    # ตั้งค่าตำแหน่งของ Label และ Entry แต่ละตัว
    create_label(canvas, "Movie Name : ", 185, 205)
    entry_title = create_entry_with_bottom_border(canvas, 350, 200)
    
    create_label(canvas, "Genre : ", 260, 305)
    genre_combobox = ttk.Combobox(add_movie_window, values=["Action", "Comedy", "Drama", "Horror", "Romance", "Sci-Fi", "Thriller","Animation"], state="readonly", font=("Microsoft YaHei UI", 20))
    genre_combobox.place(x=350, y=300)
    
    create_label(canvas, "Rate : ", 270 , 405)
    age_rating_combobox = ttk.Combobox(add_movie_window, values=["G", "PG", "PG-13", "R", "NC-17"], state="readonly" , font=("Microsoft YaHei UI", 20))
    age_rating_combobox.place(x=350 , y=405)

    create_label(canvas, "Runtime (minis) : ", 180 , 500)
    entry_runtime = create_entry_with_bottom_border(canvas, 370 , 500)
    
    create_label(canvas, "First Poster : ", 790 , 205)
    entry_first_poster = create_entry_with_bottom_border(canvas, 940 , 200)
    
    btn_import_first = Button(add_movie_window, text="Upload File", font=("Microsoft YaHei UI", 12), command=lambda: import_image(entry_first_poster))
    btn_import_first.place(x=1300, y=200)

    create_label(canvas, " Second : ", 827 , 305)
    entry_second_poster = create_entry_with_bottom_border(canvas, 940 , 300)
    
    btn_import_second = Button(add_movie_window, text="Upload File", font=("Microsoft YaHei UI", 12), command=lambda: import_image(entry_second_poster))
    btn_import_second.place(x=1300, y=300)

    def import_image(entry):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
        if file_path:
            entry.delete(0, END)
            entry.insert(0, file_path)

    def add_movie():
        title = entry_title.get()
        genre = genre_combobox.get()  
        age_rating = age_rating_combobox.get()  
        runtime = entry_runtime.get()
        first_poster_path = entry_first_poster.get()
        second_poster_path = entry_second_poster.get()

        if title and genre and age_rating and runtime and first_poster_path and second_poster_path:
            try:
                c.execute("INSERT INTO movies (title, poster_path, second_poster_path, genre, age_rating, runtime) VALUES (?, ?, ?, ?, ?, ?)", 
                          (title, first_poster_path, second_poster_path, genre, age_rating, runtime))
                conn.commit()
                messagebox.showinfo("Success", "Movie added successfully!")

                entry_title.delete(0, END)
                genre_combobox.set('')  
                age_rating_combobox.set('')  
                entry_runtime.delete(0, END)
                entry_first_poster.delete(0, END)
                entry_second_poster.delete(0, END)
                show_movies(admin_window)

            except Exception as e:
                messagebox.showerror("Error", "Failed to add movie: " + str(e))
        else:
            messagebox.showwarning("Warning", "Please fill in all fields.")

    btn_add = Button(add_movie_window, text="เพิ่มรายการภาพยนต์ใหม่", bg="#0097b2", font=("Microsoft YaHei UI Bold", 20), width = 20 , height = 1 ,fg = "white",  command=add_movie)
    btn_add.place(x=810, y=650)
    
    btn_logout = Button(add_movie_window, text="ย้อนกลับ", bg="#0097b2", font=("Microsoft YaHei UI Bold", 20), width = 20 ,height = 1 ,fg = "white",command=lambda: (add_movie_window.destroy(), admin_window.deiconify(), admin_window.state("zoomed")))
    btn_logout.place(x=420, y=650)

def show_movies(admin_window):
    # ลบกรอบที่มีข้อมูลหนังเก่าทั้งหมด
    for widget in admin_window.winfo_children():
        if isinstance(widget, Frame) and widget.winfo_name() == 'movie_frame':
            widget.destroy()

    movie_frame = Frame(admin_window, bg="white", name='movie_frame')
    movie_frame.place(x=300, y=100)

    c.execute("SELECT id, title, poster_path FROM movies ORDER BY id DESC LIMIT 12") 
    movies = c.fetchall()

    if not movies:
        Label(movie_frame, text="No movies available.", bg="white").grid(row=0, column=0)
        return

    for index, (movie_id, title, poster_path) in enumerate(movies):
        movie_sub_frame = Frame(movie_frame, bg="white") 

        row = 1 if index < 6 else 2 
        column = index if index < 6 else index - 6 
        movie_sub_frame.grid(row=row, column=column, padx=10, pady=(20, 20))  

        try:
            img = PhotoImage(file=poster_path)
            btn_movie = Button(movie_sub_frame, image=img, command=lambda movie_id=movie_id: open_movie_details(movie_id), bg="white", activebackground="white", borderwidth=0, highlightthickness=0)
            btn_movie.grid(row=0, column=0)  
            movie_sub_frame.image = img 
        except Exception as e:
            btn_movie = Button(movie_sub_frame, text="Image not found", command=lambda movie_id=movie_id: open_movie_details(movie_id), bg="white", activebackground="white", borderwidth=0, highlightthickness=0)
            btn_movie.grid(row=0, column=0) 

        # ตรวจสอบว่าอยู่ในหน้า admin หรือไม่
        is_admin = admin_window.title() == "จัดการหนัง" 

        if is_admin:

            btn_edit = Button(movie_sub_frame, text="แก้ไข", command=lambda movie_id=movie_id: edit_movie_details(movie_id), bg="orange", fg="white", font=("Helvetica", 10, "bold"))
            btn_edit.grid(row=1, column=0)  

            btn_delete = Button(movie_sub_frame, text="ลบหนัง", command=lambda m_id=movie_id: delete_movie(m_id, admin_window), font=("Helvetica", 10, "bold"), bg="red", fg="white", highlightbackground="black", highlightthickness=2)
            btn_delete.grid(row=2, column=0)  

def delete_movie(movie_id, admin_window):
    c.execute("DELETE FROM movies WHERE id=?", (movie_id,))
    conn.commit()
    messagebox.showinfo("Delete", "Movie deleted successfully!")
    show_movies(admin_window)

def edit_movie_details(movie_id):
    edit_window = Toplevel()
    edit_window.title("แก้ไขข้อมูลหนัง")
    edit_window.state("zoomed")

    # โหลดภาพพื้นหลัง
    bg_image = Image.open(r"D:\GUI\add_movie.png") 
    canvas = Canvas(edit_window)
    canvas.pack(fill="both", expand=True) 

    def update_bg_image(event=None):
        screen_width = edit_window.winfo_width()
        screen_height = edit_window.winfo_height()
        resized_image = bg_image.resize((screen_width, screen_height), Image.LANCZOS)
        bg_resized = ImageTk.PhotoImage(resized_image)
        canvas.delete("all")  
        canvas.create_image(0, 0, image=bg_resized, anchor="nw")
        canvas.image = bg_resized 

    edit_window.bind("<Configure>", update_bg_image)

    c.execute("SELECT title, genre, age_rating, runtime, poster_path, second_poster_path FROM movies WHERE id=?", (movie_id,))
    movie_data = c.fetchone()

    if movie_data:
        title, genre, age_rating, runtime, poster_path, second_poster_path = movie_data
    else:
        messagebox.showerror("Error", "ไม่พบข้อมูลหนัง")
        return

    # ชื่อหนัง
    label_x = 650
    label_y = 150  
    entry_width = 325
    title_label = Label(edit_window, text="ชื่อหนัง", bg="white", anchor="w",font=("Microsoft YaHei UI Bold", 20))
    title_label.place(x=470, y=145)
    title_entry = Entry(edit_window,font=("Microsoft YaHei UI Bold", 20),width=20)
    title_entry.insert(0, title)
    title_entry.place(x=label_x, y=label_y , width=entry_width)  

    label_y += 60
    genre_label = Label(edit_window, text="ประเภทหนัง", bg="white", anchor="w",font=("Microsoft YaHei UI Bold", 20))
    genre_label.place(x=470, y=215)  
    genre_combobox = ttk.Combobox(edit_window, values=["Action", "Comedy", "Drama", "Horror", "Romance", "Sci-Fi", "Thriller", "Animation"], state="readonly",font=("Microsoft YaHei UI Bold", 20))
    genre_combobox.set(genre)  
    genre_combobox.place(x=label_x, y=label_y +10 , width=225)  

    # เรทอายุ (Combobox)
    label_y += 60
    age_rating_label = Label(edit_window, text="เรทอายุ", bg="white", anchor="w",font=("Microsoft YaHei UI Bold", 20))
    age_rating_label.place(x=470, y=285)  
    age_rating_combobox = ttk.Combobox(edit_window, values=["G", "PG", "PG-13", "R", "NC-17"], state="readonly",font=("Microsoft YaHei UI Bold", 20),width=80)
    age_rating_combobox.set(age_rating)  
    age_rating_combobox.place(x=label_x, y=label_y + 20, width=125)  

    # เวลา (นาที)
    label_y += 70
    runtime_label = Label(edit_window, text="เวลา (นาที)", bg="white", anchor="w",font=("Microsoft YaHei UI Bold", 20))
    runtime_label.place(x=470, y=355)  
    runtime_entry = Entry(edit_window,font=("Microsoft YaHei UI Bold", 20))
    runtime_entry.insert(0, runtime)
    runtime_entry.place(x=label_x, y=label_y + 20, width=125)  

    # โปสเตอร์แรก
    label_y += 70
    poster_label = Label(edit_window, text="โปสเตอร์แรก", bg="white", anchor="w",font=("Microsoft YaHei UI Bold", 20))
    poster_label.place(x=470, y=425)  
    poster_path_entry = Entry(edit_window,font=("Microsoft YaHei UI Bold", 20))
    poster_path_entry.insert(0, poster_path)
    poster_path_entry.place(x=label_x, y=label_y + 20, width=375)  

    # โปสเตอร์ที่สอง
    label_y += 70
    second_poster_label = Label(edit_window, text="โปสเตอร์ที่สอง", bg="white", anchor="w",font=("Microsoft YaHei UI Bold", 20))
    second_poster_label.place(x=470, y=495)  
    second_poster_path_entry = Entry(edit_window,font=("Microsoft YaHei UI Bold", 20))
    second_poster_path_entry.insert(0, second_poster_path)
    second_poster_path_entry.place(x=label_x, y=label_y + 20, width=375)

    def import_image(entry):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
        if file_path:
            entry.delete(0, END)
            entry.insert(0, file_path)

    Button(edit_window, text="เลือกไฟล์โปสเตอร์แรก", command=lambda: import_image(poster_path_entry),font=("Microsoft YaHei UI Bold", 14)).place(x=1100, y=425)
    Button(edit_window, text="เลือกไฟล์โปสเตอร์ที่สอง", command=lambda: import_image(second_poster_path_entry),font=("Microsoft YaHei UI Bold", 14)).place(x=1100, y=500)

    # ฟังก์ชันบันทึกข้อมูล
    def save_changes():
        new_title = title_entry.get()
        new_genre = genre_combobox.get()
        new_age_rating = age_rating_combobox.get()  # รับค่าจาก Combobox
        new_runtime = runtime_entry.get()
        new_poster_path = poster_path_entry.get()
        new_second_poster_path = second_poster_path_entry.get()

        c.execute('''UPDATE movies SET title=?, genre=?, age_rating=?, runtime=?, poster_path=?, second_poster_path=? WHERE id=?''',
                  (new_title, new_genre, new_age_rating, new_runtime, new_poster_path, new_second_poster_path, movie_id))
        conn.commit()

        messagebox.showinfo("Success", "ข้อมูลหนังถูกอัปเดตเรียบร้อยแล้ว")
        edit_window.destroy()

        show_movies(admin_window)  # รีเฟรชหน้าต่าง admin_window

    save_button = Button(edit_window, text="บันทึกการแก้ไข", command=save_changes, bg="green", fg="white",font=("Microsoft YaHei UI Bold", 14))
    save_button.place(x=750, y=650)  

def open_movie_select():
    movie_select = Toplevel()
    movie_select.title("เลือกหนัง")
    movie_select.state("zoomed")
    root.withdraw()  
    open_windows.append(movie_select)

    bg_image = Image.open(r"D:\GUI\จองตั๋ว2.png")
    canvas = Canvas(movie_select)
    canvas.pack(fill="both", expand=True)

    def update_bg_image(event=None):
        screen_width = movie_select.winfo_width()  
        screen_height = movie_select.winfo_height() 

        resized_image = bg_image.resize((screen_width, screen_height), Image.LANCZOS)
        bg_resized = ImageTk.PhotoImage(resized_image)
        canvas.delete("all")  
        canvas.create_image(0, 0, image=bg_resized, anchor="nw")
        canvas.image = bg_resized 

    movie_select.bind("<Configure>", update_bg_image)

    button_image = Image.open(r"D:\GUI\2.png")
    button_image = button_image.resize((75,75), Image.LANCZOS)
    button_image_tk = ImageTk.PhotoImage(button_image)

    image_button = Button(movie_select, image=button_image_tk, command=open_user_profile, borderwidth=0)
    image_button.image = button_image_tk  
    image_button.place(x=630, y=720)

    about_image = Image.open(r"D:\GUI\1.png")
    about_image = about_image.resize((75,75), Image.LANCZOS)
    about_image_tk = ImageTk.PhotoImage(about_image)

    about_button = Button(movie_select, image=about_image_tk, command=open_about, borderwidth=0)
    about_button.image = about_image_tk  
    about_button.place(x=830, y=720)

    ticket_image = Image.open(r"D:\GUI\3.png")
    ticket_image = ticket_image.resize((75,75), Image.LANCZOS)
    ticket_image_tk = ImageTk.PhotoImage(ticket_image)

    ticket_button = Button(movie_select, image=ticket_image_tk, command=view_booking_history, borderwidth=0)
    ticket_button.image = ticket_image_tk  
    ticket_button.place(x=730, y=720)

    btn_logout = Button(movie_select, text="ออกจากระบบ", bg="red", font=("Microsoft YaHei UI Bold", 20), fg="white", width=10, height=1, command=lambda: (movie_select.withdraw(), root.deiconify(), root.state("zoomed")))
    btn_logout.place(x=1350, y=10)

    show_movies(movie_select)

def open_movie_details(movie_id):
    global selected_date_text, selected_time_text
    movie_detail_window = Toplevel()
    movie_detail_window.title("รายละเอียดภาพยนต์")
    movie_detail_window.state("zoomed")
    open_windows.append(movie_detail_window)

    bg_image = Image.open(r"D:\GUI\movie_select.png")
    canvas = Canvas(movie_detail_window)
    canvas.pack(fill="both", expand=True)

    def update_bg_image(event=None):
        screen_width = movie_detail_window.winfo_width()
        screen_height = movie_detail_window.winfo_height()
        resized_image = bg_image.resize((screen_width, screen_height), Image.LANCZOS)
        bg_resized = ImageTk.PhotoImage(resized_image)
        canvas.delete("all")
        canvas.create_image(0, 0, image=bg_resized, anchor="nw")
        canvas.image = bg_resized
    movie_detail_window.bind("<Configure>", update_bg_image)

    c.execute("SELECT title, second_poster_path, genre, age_rating, runtime FROM movies WHERE id=?", (movie_id,))
    movie = c.fetchone()

    if movie:
        title, second_poster_path, genre, age_rating, runtime = movie

        # สร้างเฟรมจัดระเบียบ
        frame = Frame(movie_detail_window, bg="white", bd=5)
        frame.place(relx=0.5, rely=0.5, anchor="center", width=800, height=600)

        # แสดงข้อมูลภาพยนต์
        Label(frame, text=title, bg="white", font=("Microsoft YaHei UI Bold", 25)).place(x=220, y=3)
        Label(frame, text="Genre : " + genre, bg="white", font=("Microsoft YaHei UI Bold", 20)).place(x=220, y=60)
        Label(frame, text="Rate : " + age_rating, bg="white", font=("Microsoft YaHei UI Bold", 20)).place(x=220, y=105)
        Label(frame, text=str(runtime) + " mins", bg="white", font=("Microsoft YaHei UI Bold", 20)).place(x=220, y=155)

        try:
            img = PhotoImage(file=second_poster_path)
            label_img = Label(frame, image=img)
            label_img.image = img
            label_img.place(x=30, y=2)
        except Exception as e:
            Label(frame, text="ภาพไม่พบ", bg="white", font=("Microsoft YaHei UI Bold", 15), fg="red").place(x=150, y=10)

        create_date_time_selection(frame)

        Label(frame, text="Theater 1", bg="white", font=("Microsoft YaHei UI Regular", 20)).place(x=0, y=400)
        Label(frame, text="เลือกวันที่รับชม", bg="white", font=("Microsoft YaHei UI Regular", 20)).place(x=0, y=280)

        def open_seat_if_selected():
            if selected_date_text.strip() == "" or selected_time_text.strip() == "":
                messagebox.showwarning("คำเตือน", "กรุณาเลือกวันที่และรอบเวลาให้ครบถ้วนก่อนทำการจองที่นั่ง")
            else:
                open_seat_booking(title)

        Button(movie_detail_window, text="เลือกที่นั่งในการรับชม", bg="#0097b2", font=("Microsoft YaHei UI Bold", 20),width=20, height=1, fg="white", command=open_seat_if_selected).place(x=810, y=650)

        Button(movie_detail_window, text="ย้อนกลับ", bg="#0097b2", font=("Microsoft YaHei UI Bold", 20),width=20, height=1, fg="white", command=lambda: movie_detail_window.withdraw()).place(x=380, y=650)

def create_date_time_selection(parent_frame):
    global selected_date_text, selected_time_text, time_frame
    selected_date_text = " "
    selected_time_text = " "

    selected_date_label = Label(parent_frame, text="วันที่รับชม: " + selected_date_text + "  รอบในการรับชม: " + selected_time_text,font=("Microsoft YaHei UI Bold", 20), bg="white")
    selected_date_label.place(x=0, y=230)

    date_frame = Frame(parent_frame, bg="white", bd=2)
    date_frame.place(x=50, y=330, width=800, height=80)

    today = datetime.now()
    thai_months = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]

    # สร้างปุ่มวันที่
    for i in range(5):
        date = today + timedelta(days=i)
        button_text = "{:02d} {} {}".format(date.day, thai_months[date.month - 1], date.year + 543)
        Button(date_frame, text=button_text, font=("Microsoft YaHei UI Bold", 12), bg="#0097b2", fg="white",
               command=lambda d=date: select_date(d, selected_date_label)).place(x=i * 130, y=10)

    # เฟรมสำหรับเลือกเวลา
    time_frame = Frame(parent_frame, bg="white", bd=2)
    time_frame.place(x=50, y=450, width=800, height=60)

    create_time_buttons(selected_date_label)

def create_time_buttons(selected_date_label):
    global time_frame, selected_date_text

    start_hour = 10
    interval_hours = 2
    interval_minutes = 30
    num_buttons = 6

    current_time = datetime.now()

    for i in range(num_buttons):
        total_minutes = (start_hour * 60) + (i * (interval_hours * 60 + interval_minutes))
        hour = total_minutes // 60
        minute = total_minutes % 60
        button_text = "{:02d}:{:02d}".format(hour, minute)

        # สร้างเวลาในวันที่ที่เลือก
        selected_date_is_today = selected_date_text == current_time.strftime("%d-%m-%Y")
        button_time = current_time.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # ตรวจสอบเวลาและสถานะปุ่ม
        if selected_date_is_today and button_time < current_time:
            Button(time_frame, text=button_text, font=("Microsoft YaHei UI Bold", 12), width=6, height=1,
                   bg="gray", fg="white", state="disabled").place(x=i * 80, y=10)
        else:
            Button(time_frame, text=button_text, font=("Microsoft YaHei UI Bold", 12), width=6, height=1,
                   bg="#0097b2", fg="white", command=lambda t=button_text: select_time(t, selected_date_label)).place(x=i * 80, y=10)

def select_date(date, label):
    global selected_date_text
    selected_date_text = date.strftime("%d-%m-%Y")
    label.config(text="วันที่รับชม: " + selected_date_text + "  รอบในการรับชม: " + selected_time_text)

    # ลบปุ่มเวลาทั้งหมดและสร้างใหม่
    for widget in time_frame.winfo_children():
        widget.destroy()
    create_time_buttons(label)

def select_time(time, label):
    global selected_time_text
    selected_time_text = time
    label.config(text="วันที่รับชม: " + selected_date_text + "  รอบในการรับชม: " + selected_time_text)
    
def open_seat_booking(title):
    global reserved_seats  
    global selected_seats   
    selected_seats = []  
    reserved_seats = []

    seat_booking_window = Toplevel()
    seat_booking_window.title("เลือกที่นั่งสำหรับ " + title)
    seat_booking_window.state("zoomed")
    open_windows.append(seat_booking_window)

    # โหลดและตั้งภาพพื้นหลัง
    bg_image = Image.open(r"D:\GUI\select_seat.png")
    resized_bg_image = bg_image.resize((seat_booking_window.winfo_screenwidth(), seat_booking_window.winfo_screenheight()), Image.LANCZOS)
    bg_resized = ImageTk.PhotoImage(resized_bg_image)

    # ใช้ Label เป็นภาพพื้นหลัง
    bg_label = Label(seat_booking_window, image=bg_resized)
    bg_label.image = bg_resized  # เก็บอ้างอิงภาพ
    bg_label.place(x=0, y=0, relwidth=1, relheight=1)  # ขยายภาพเต็มหน้าต่าง

    # กำหนด Label สำหรับแสดงที่นั่งที่เลือก
    selection_label = Label(seat_booking_window, text="ที่นั่ง : ", font=("Microsoft YaHei UI Bold", 20), bg="#0097b2", fg="white")
    selection_label.place(x=300, y=567)

    cost_label = Label(seat_booking_window, text=" 0 ฿", font=("Microsoft YaHei UI Bold", 20), bg="#0097b2", fg="white")
    cost_label.place(x=1150, y=567)

    # ตรวจสอบสถานะ admin
    is_admin = current_user in ["PSXz", "Nu"]  # เปลี่ยนรายการ admin ตามที่กำหนด

    update_seat_availability(title, selected_date_text, selected_time_text)

    seat_frame = Frame(seat_booking_window, bg="white")
    seat_frame.place(x=280, y=180)

    rows_2 = ['H', 'G', 'F', 'E']
    for row_index, row_label in enumerate(rows_2):
        for col in range(16):
            seat_label = f"{row_label}{col + 1}"
            seat_btn = Button(seat_frame, text=seat_label, width=6, height=1, font=("Microsoft YaHei UI Bold", 10), bg="white", fg="#0097b2")

            if seat_label in reserved_seats:
                seat_btn.config(state=DISABLED, bg="gray")
            else:
                seat_btn.config(command=lambda btn=seat_btn, r=row_index, c=col: book_seat(btn, r, c, selection_label, cost_label))
            seat_btn.grid(row=row_index, column=col, padx=2, pady=6)

    gap_row_index = len(rows_2)  
    seat_frame.grid_rowconfigure(gap_row_index, minsize=20) 

    rows_1 = ['D', 'C', 'B', 'A']
    for row_index, row_label in enumerate(rows_1, start=gap_row_index + 0):
        for col in range(16):
            seat_label = f"{row_label}{col + 1}"
            seat_btn = Button(seat_frame, text=seat_label, width=6, height=1, font=("Microsoft YaHei UI Bold", 10), bg="white", fg="#0097b2")
            if seat_label in reserved_seats:
                seat_btn.config(state=DISABLED, bg="gray")
            else:
                seat_btn.config(command=lambda btn=seat_btn, r=row_index, c=col: book_seat(btn, r, c, selection_label, cost_label))
            seat_btn.grid(row=row_index, column=col, padx=2, pady=6) 

    # วางปุ่มยืนยันการจอง
    confirm_button = Button(seat_booking_window,text="ยืนยันการจอง",bg="#0097b2",
        font=("Microsoft YaHei UI Bold", 20),
        width=20,
        height=1,
        fg="white",
        state=DISABLED if is_admin else NORMAL,  # ปิดปุ่มถ้าเป็น admin
        command=lambda: confirm_booking(title)
    )
    confirm_button.place(x=810, y=650)

    btn_back = Button(seat_booking_window, text="ย้อนกลับ", bg="#0097b2", font=("Microsoft YaHei UI Bold", 20), width=20, height=1, fg="white", command=lambda: (seat_booking_window.withdraw(), open_movie_details))
    btn_back.place(x=380, y=650)

def update_seat_availability(movie_title, show_date, show_time):
    global reserved_seats
    reserved_seats = []  # ล้างข้อมูลเดิมออก
    try:
        c.execute("SELECT seats FROM booking WHERE movie_title=? AND show_date=? AND show_time=?", (movie_title, show_date, show_time))
        bookings = c.fetchall()
        for booking in bookings:
            reserved_seats.extend(booking[0].split(','))  # แยกที่นั่งและบันทึกใน reserved_seats
    except Exception as e:
        messagebox.showerror("Error", f"ไม่สามารถดึงข้อมูลการจองได้: {str(e)}")

def book_seat(button, row, col, selection_label, cost_label):
    if row < 4:  
        seat_label = f"{chr(72 - row)}{col + 1}"
    else:  
        seat_label = f"{chr(68 - (row - 4))}{col + 1}"

    if seat_label in reserved_seats:
        messagebox.showwarning("Warning", "ที่นั่งนี้ถูกจองไปแล้ว")
        return
    
    price_per_seat = 100

    if button.cget("bg") == "white":  # ถ้าปุ่มมีพื้นหลังเป็นสีขาวยังไม่ได้เลือก
        button.config(bg="#0097b2", fg="white")  # เปลี่ยนพื้นหลังเป็นสีฟ้า และตัวหนังสือเป็นสีขาว
        selected_seats.append(seat_label)  # เพิ่มที่นั่งที่เลือก
    else:  # ถ้าปุ่มมีพื้นหลังเป็นสีฟ้า (ถูกเลือกอยู่แล้ว)
        button.config(bg="white", fg="#0097b2")  # เปลี่ยนพื้นหลังกลับ
        selected_seats.remove(seat_label)  

    # อัพเดตข้อความแสดงที่นั่งที่เลือก
    if len(selected_seats) > 10:
        display_text = ", ".join(selected_seats[:10]) + " ..."
    else:
        display_text = ", ".join(selected_seats)

    selection_label.config(text="ที่นั่ง : " + display_text)
    total_cost = len(selected_seats) * price_per_seat
    cost_label.config(text="{:,}".format(total_cost) + " ฿")
    
def confirm_booking(title):
    if not selected_seats:
        messagebox.showwarning("Warning", "กรุณาเลือกที่นั่งก่อน")
        return
    if selected_date_text == "None" or selected_time_text == "None":
        messagebox.showwarning("Warning", "กรุณาเลือกวันที่และเวลา")
        return

    # คำนวณราคารวม
    seat_count = len(selected_seats)
    price_per_seat = 100
    total_price = seat_count * price_per_seat

    # เปิดหน้าต่างชำระเงินพร้อมกับข้อมูลทั้งหมด
    open_payment_window(title, selected_date_text, selected_time_text, selected_seats, total_price)

def open_payment_window(movie_title, show_date, show_time, seats, total_price):
    payment_window = Toplevel()
    payment_window.title("ยืนยันการดำเนินการ")
    payment_window.state("zoomed")

    bg_image_summary = Image.open(r"D:\GUI\movie_select.png")
    canvas_summary = Canvas(payment_window)
    canvas_summary.pack(fill="both", expand=True)
    open_windows.append(payment_window)

    def update_bg_image_summary(event=None):
        screen_width = payment_window.winfo_width()
        screen_height = payment_window.winfo_height()
        resized_image = bg_image_summary.resize((screen_width, screen_height), Image.LANCZOS)
        bg_resized = ImageTk.PhotoImage(resized_image)
        canvas_summary.delete("bg_image")  # ลบภาพพื้นหลังเก่า
        canvas_summary.create_image(0, 0, image=bg_resized, anchor="nw", tags="bg_image")
        canvas_summary.image = bg_resized  # เก็บอ้างอิงภาพเพื่อไม่ให้ถูกเก็บออก

    payment_window.bind("<Configure>", update_bg_image_summary)
    img = Image.open(r"D:\GUI\pays.png")  
    #img = img.resize((400,300), Image.LANCZOS)  # ปรับขนาดรูปภาพ
    img = ImageTk.PhotoImage(img)
    img_label = Label(canvas_summary, image=img)
    img_label.image = img  # เก็บ reference เพื่อป้องกันการลบภาพ
    canvas_summary.create_window(770, 300, window=img_label) 

    num_seats = len(seats)
    num_seats_label = Label(canvas_summary, text=f"จำนวนที่นั่งที่ถูกจอง : {num_seats} ที่นั่ง", font=("Microsoft YaHei UI Bold", 20), bg='white')
    canvas_summary.create_window(550, 580, window=num_seats_label)  

    total_price_label = Label(canvas_summary, text=f"ราคารวมที่ต้องจ่าย : {total_price:,} บาท", font=("Microsoft YaHei UI Bold", 20), bg='white')
    canvas_summary.create_window(1000, 580, window=total_price_label)  

    pay_button = Button(canvas_summary, text="ยืนยันการชำระ",bg="#0097b2", font=("Microsoft YaHei UI Bold", 20), width = 20 , height = 1 ,fg = "white",command=lambda: save_payment_and_show_summary(movie_title, show_date, show_time, seats, total_price))
    canvas_summary.create_window(1000, 682, window=pay_button)

    btn_logout = Button(payment_window, text="ย้อนกลับ",  bg="#0097b2", font=("Microsoft YaHei UI Bold", 20), width = 20 , height = 1 ,fg = "white", command=lambda: (payment_window.withdraw(),open_seat_booking))
    btn_logout.place(x=380, y=650)

def save_payment_and_show_summary(movie_title, show_date, show_time, seats, total_price):

    if not seats:
        messagebox.showwarning("Warning", "กรุณาเลือกที่นั่งก่อน")
        return

    try:
        payment_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        payment_status = "ชำระแล้ว"

        for seat in seats:
            ticket_number = f"{current_user}-{show_date.replace('/', '')}-{seat}"
            ticket_path = generate_ticket_from_template(movie_title, show_date, show_time, seat, 100, ticket_number)

            # บันทึกข้อมูลตั๋วในฐานข้อมูล
            c.execute('''INSERT INTO booking 
                          (username, movie_title, show_date, show_time, seats, total_price, payment_date, payment_status, ticket_number) 
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                      (current_user, movie_title, show_date, show_time, seat, 100, payment_date, payment_status, ticket_number))
            conn.commit()

        messagebox.showinfo("Success", "การจองและสร้างตั๋วเสร็จสมบูรณ์!")
        show_booking_summary(movie_title, show_date, show_time, seats, total_price)
    except Exception as e:
        messagebox.showerror("Error", f"ไม่สามารถบันทึกข้อมูลการชำระเงินได้: {e}")

def show_booking_summary(movie_title, show_date, show_time, seats, total_price ):
    summary_window = Toplevel()
    summary_window.title("สรุปการจอง")
    summary_window.state("zoomed")
    open_windows.append(summary_window)

    c.execute('''SELECT first_name, last_name, email, profile_image FROM users WHERE username=?''', (current_user,))
    user_data = c.fetchone()

    if user_data:
        first_name, last_name, email , profile_picture_path = user_data
    else:
        first_name, last_name, email, profile_picture_path = "ไม่พบข้อมูล", "ไม่พบข้อมูล", "ไม่พบอีเมล", None

    c.execute('''SELECT payment_date, payment_status FROM booking WHERE username=? AND movie_title=? AND show_date=? AND show_time=? LIMIT 1''',
              (current_user, movie_title, show_date, show_time))
    payment_data = c.fetchone()

    if payment_data:
        payment_date, payment_status = payment_data
    else:
        payment_date, payment_status = "ไม่พบข้อมูล", "ไม่พบข้อมูล"

    bg_image_summary = Image.open(r"D:\GUI\จองตั๋ว4.png")
    canvas_summary = Canvas(summary_window)
    canvas_summary.pack(fill="both", expand=True)

    def update_bg_image_summary(event=None):
        screen_width = summary_window.winfo_width()
        screen_height = summary_window.winfo_height()

        resized_image = bg_image_summary.resize((screen_width, screen_height), Image.LANCZOS)
        bg_resized = ImageTk.PhotoImage(resized_image)
        canvas_summary.delete("all")  # ลบภาพพื้นหลังเก่า
        canvas_summary.create_image(0, 0, image=bg_resized, anchor="nw")
        canvas_summary.image = bg_resized  # เก็บอ้างอิงภาพเพื่อไม่ให้ถูกเก็บออก

    summary_window.bind("<Configure>", update_bg_image_summary)

    # แสดงข้อมูลการจอง
    Label(canvas_summary, text="Customer", fg="#0097b2", font=("Microsoft YaHei UI Bold", 24), bg='white').place(x=180, y=140)
    Label(canvas_summary, text="Username : " + current_user, fg="black", font=("Microsoft YaHei UI Bold", 18), bg='white').place(x=290, y=240)
    Label(canvas_summary, text= movie_title, fg="black", font=("Microsoft YaHei UI Bold", 20), bg='white').place(x=290, y=430)
    Label(canvas_summary, text="วันที่รับชม : " + show_date, fg="black", font=("Microsoft YaHei UI Bold", 18), bg='white').place(x=800, y=200)
    Label(canvas_summary, text="เวลา : " + show_time, fg="black", font=("Microsoft YaHei UI Bold", 18), bg='white').place(x=1000, y=200)
    Label(canvas_summary, text="ราคา : " + "{:,}".format(total_price) + " บาท", fg="black", font=("Microsoft YaHei UI Bold", 18), bg='white').place(x=800, y=240)
    Label(canvas_summary, text="ที่นั่ง : " , fg="black", font=("Microsoft YaHei UI Bold", 18), bg='white').place(x=800, y=360)

    # แสดงชื่อจริง, นามสกุล, และอีเมล
    Label(canvas_summary, text= first_name + " " + last_name, fg="black", font=("Microsoft YaHei UI Bold", 20), bg='white').place(x=290, y=200)
    Label(canvas_summary, text="E-mail : " + email, fg="black", font=("Microsoft YaHei UI Bold", 18), bg='white').place(x=290, y=280)
    Label(canvas_summary, text="Movie Details", fg="#0097b2", font=("Microsoft YaHei UI Bold", 24), bg='white').place(x=180, y=380)
    Label(canvas_summary, text="Booking Details", fg="#0097b2", font=("Microsoft YaHei UI Bold", 24), bg='white').place(x=800, y=140)

    # แสดงเวลาในการชำระและสถานะการชำระ
    Label(canvas_summary, text="ชำระเมื่อ: " + payment_date, fg="black", font=("Microsoft YaHei UI Bold", 18), bg='white').place(x=800, y=280)
    Label(canvas_summary, text="สถานะ: " + payment_status, fg="black", font=("Microsoft YaHei UI Bold", 18), bg='white').place(x=800, y=320)

    # แสดงรูปโปรไฟล์
    if profile_picture_path:
        try:
            profile_image = Image.open(profile_picture_path)
            profile_image = profile_image.resize((100,100), Image.Resampling.LANCZOS)  # ปรับขนาดรูปโปรไฟล์
            profile_photo = ImageTk.PhotoImage(profile_image)

            profile_label = Label(canvas_summary, image=profile_photo, bg='white')
            profile_label.image = profile_photo  # เก็บ reference ของภาพ
            profile_label.place(x=180, y=200)  # ตำแหน่งของรูปโปรไฟล์

        except Exception as e:
            print(f"ไม่สามารถโหลดรูปโปรไฟล์ได้: {e}")

    # ค้นหาโปสเตอร์ที่สอง, เรทอายุ และประเภท
    c.execute("SELECT second_poster_path, age_rating, genre FROM movies WHERE title=?", (movie_title,))
    movie_data = c.fetchone()
    
    if movie_data:
        second_poster_path, age_rating, genre = movie_data
        
        # แสดงโปสเตอร์ที่สอง
        if second_poster_path:
            try:
                img2 = Image.open(second_poster_path)
                img2 = img2.resize((90, 130), Image.Resampling.LANCZOS)  # ปรับขนาดโปสเตอร์ที่สอง
                img2 = ImageTk.PhotoImage(img2)
                poster_label2 = Label(canvas_summary, image=img2, bg='white')
                poster_label2.image = img2  # เก็บอ้างอิงภาพ
                poster_label2.place(x=180, y=435)  # ตำแหน่งของโปสเตอร์ที่สอง
            except Exception as e:
                Label(canvas_summary, text="ไม่สามารถโหลดภาพโปสเตอร์ที่สองได้", bg='white').place(x=50, y=330)
        
        # แสดงเรทอายุและประเภท
        Label(canvas_summary, text="Rate : " + age_rating, font=("Microsoft YaHei UI Bold", 18), bg='white').place(x=290, y=510)
        Label(canvas_summary, text=genre, font=("Microsoft YaHei UI Bold", 18), bg='white').place(x=290, y=470)
    else:
        Label(canvas_summary, text="ไม่มีข้อมูลหนัง", bg='white').place(x=750, y=330)

    # แสดงที่นั่งที่เลือกในแถวละ 16
    max_seats_per_row = 16
    seat_rows = [seats[i:i + max_seats_per_row] for i in range(0, len(seats), max_seats_per_row)]
    
    y_position = 367
    for row in seat_rows:
        seat_row_text = ', '.join(row)
        Label(canvas_summary, text= seat_row_text, fg="black", font=("Microsoft YaHei UI Bold", 12 ), bg='white').place(x=870, y=y_position)
        y_position += 35  

    btn_close_all = Button(canvas_summary, text=" เสร็จสิ้น ", bg="white", font=("Microsoft YaHei UI Bold", 20), width=40, height=1, fg="#0097b2", command=close_open_windows)
    btn_close_all.place(x=425, y=725) 
    update_bg_image_summary()

def close_open_windows():
    for window in open_windows:
        window.destroy()  
    open_windows.clear()  
    open_movie_select()  

def generate_ticket_from_template(movie_title, show_date, show_time, seat, price, ticket_number):
    try:
        # โหลดภาพพื้นฐานที่ใช้เป็นตั๋ว
        ticket_template = Image.open(r"D:\GUI\X.png")
        draw = ImageDraw.Draw(ticket_template)

        # โหลดฟอนต์
        font = ImageFont.truetype("arial.ttf", 25)
        font_title = ImageFont.truetype("arial.ttf", 30)  

        # ข้อมูลสำหรับ QR Code
        qr_data = f"""Movie: {movie_title} Date: {show_date} Time: {show_time} Seat: {seat} Price: {price} ฿ Ticket No: {ticket_number} """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        # สร้างภาพ QR Code
        qr_image = qr.make_image(fill_color="black", back_color="white")
        qr_image = qr_image.resize((150, 150))  

        draw.text((70, 70), f"Movie : {movie_title}", fill="black", font=font_title)
        draw.text((70, 120), f"Date : {show_date}", fill="black", font=font)
        draw.text((70, 170), f"Time : {show_time}", fill="black", font=font)
        draw.text((70, 220), f"Seat : {seat}", fill="black", font=font)
        draw.text((70, 270), f"Price : {price} Baht ", fill="black", font=font)

        # แทรก QR Code ลงในภาพตั๋ว
        ticket_template.paste(qr_image, (650, 75))  

        # บันทึกภาพใหม่
        ticket_path = f"tickets/{ticket_number}.png"
        ticket_template.save(ticket_path)

        return ticket_path
    except Exception as e:
        print(f"Error generating ticket: {e}")
        return None

def view_booking_history():
    history_window = Toplevel()
    history_window.title("ประวัติการจอง")
    history_window.state("zoomed")

    header_frame = Frame(history_window, bg="#3399FF", height=80)
    header_frame.pack(fill=X)

    Label(header_frame, text="ประวัติการจอง", font=("Arial", 24, "bold"), bg="#3399FF", fg="white").pack(pady=20, side=LEFT, padx=10)

    # ปุ่มย้อนกลับ
    back_button = Button(header_frame, text="ย้อนกลับ", command=history_window.destroy, bg="#FF6666", fg="white", font=("Arial", 12), relief="flat")
    back_button.pack(side=RIGHT, padx=10, pady=10)

    # ดึงข้อมูลโปรไฟล์จากฐานข้อมูล
    c.execute('''SELECT username, profile_image, first_name, last_name, email FROM users WHERE username=?''', (current_user,))
    profile_data = c.fetchone()

    if profile_data:
        username = profile_data[0]
        profile_picture_path = profile_data[1]
        first_name = profile_data[2]
        last_name = profile_data[3]
        email = profile_data[4]
    else:
        username = "ไม่พบข้อมูล"
        profile_picture_path = None
        first_name = "ไม่พบชื่อ"
        last_name = "ไม่พบข้อมูล"
        email = "ไม่พบอีเมล"

    c.execute('''SELECT movie_title, show_date, show_time, GROUP_CONCAT(seats), total_price, payment_date 
        FROM booking 
        WHERE username=?
        GROUP BY movie_title, show_date, show_time, payment_date
        ORDER BY payment_date DESC
    ''', (current_user,))
    bookings = c.fetchall()

    if not bookings:
        Label(history_window, text="ยังไม่มีประวัติการจอง", font=("Arial", 20)).pack(pady=20)
        return

    # แสดงรูปโปรไฟล์และข้อมูลชื่อผู้ใช้งาน
    profile_frame = Frame(history_window)
    profile_frame.pack(pady=10)

    if profile_picture_path:
        try:
            profile_image = Image.open(profile_picture_path)
            profile_image = profile_image.resize((125, 125), Image.Resampling.LANCZOS)
            profile_photo = ImageTk.PhotoImage(profile_image)

            profile_label = Label(profile_frame, image=profile_photo)
            profile_label.image = profile_photo
            profile_label.grid(row=0, column=0, rowspan=3, padx=10)

        except Exception as e:
            print(f"ไม่สามารถโหลดรูปโปรไฟล์ได้: {e}")

    info_label = Label(profile_frame, text=f"Username: {username}", font=("Arial", 14))
    info_label.grid(row=0, column=1, sticky="w", padx=10)

    name_label = Label(profile_frame, text=f"Name: {first_name} {last_name}", font=("Arial", 14))
    name_label.grid(row=1, column=1, sticky="w", padx=10)

    email_label = Label(profile_frame, text=f"Email: {email}", font=("Arial", 14))
    email_label.grid(row=2, column=1, sticky="w", padx=10)

    # Scrollable frame
    canvas = Canvas(history_window)
    scrollbar = Scrollbar(history_window, orient=VERTICAL, command=canvas.yview)
    canvas.pack(side=LEFT, fill=BOTH, expand=True)
    scrollbar.pack(side=RIGHT, fill=Y)

    canvas.configure(yscrollcommand=scrollbar.set)

    scrollable_frame = Frame(canvas)
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    def update_scroll_region(event):
        canvas.configure(scrollregion=canvas.bbox("all"))

    scrollable_frame.bind("<Configure>", update_scroll_region)

    # แสดงข้อมูลการจอง
    for booking in bookings:
        movie_title, show_date, show_time, seats, total_price, payment_date = booking
        seats_list = seats.split(',')

        c.execute('''SELECT poster_path FROM movies WHERE title=?''', (movie_title,))
        movie_data = c.fetchone()

        if movie_data:
            poster_path = movie_data[0]
        else:
            poster_path = None

        group_frame = Frame(scrollable_frame, borderwidth=2, relief="solid", pady=10, padx=10)
        group_frame.pack(fill=X, padx=320, pady=5)

        if poster_path:
            try:
                poster_image = Image.open(poster_path)
                poster_image = poster_image.resize((83, 122), Image.Resampling.LANCZOS)
                poster_photo = ImageTk.PhotoImage(poster_image)

                poster_label = Label(group_frame, image=poster_photo)
                poster_label.image = poster_photo
                poster_label.pack(side=LEFT, padx=10)

            except Exception as e:
                print(f"ไม่สามารถโหลดโปสเตอร์ได้: {e}")

        movie_info_frame = Frame(group_frame)
        movie_info_frame.pack(side=LEFT, padx=10, anchor="n")

        Label(movie_info_frame, text=f"Movie: {movie_title}", font=("Arial", 16, "bold")).pack(anchor="w")
        Label(movie_info_frame, text=f"Date: {show_date} | Time: {show_time}", font=("Arial", 14)).pack(anchor="w")
        Label(movie_info_frame, text=f"Booking Time: {payment_date}", font=("Arial", 12)).pack(anchor="w")

        seats_text = ', '.join(seats_list)
        if len(seats_list) > 16:
            seats_text = ', '.join(seats_list[:16]) + ", ..."

        Label(movie_info_frame, text="Seats: " + seats_text, font=("Arial", 12)).pack(anchor="w")

        Button(group_frame, text="ดูตั๋วทั้งหมด", command=lambda ticket_paths=[f"tickets/{current_user}-{show_date.replace('/', '')}-{seat}.png" for seat in seats_list]: open_ticket_images_in_group(ticket_paths, movie_title, show_date, show_time), bg="#3399FF", fg="white", font=("Arial", 12), relief="flat").pack(side=RIGHT, padx=10) 

def open_ticket_images_in_group(ticket_paths, movie_title, show_date, show_time):
    ticket_window = Toplevel()
    ticket_window.title(f"ตั๋วที่เลือกสำหรับ {movie_title} - {show_date} {show_time}")
    ticket_window.state("zoomed")

    header_frame = Frame(ticket_window, bg="#3399FF", height=80)
    header_frame.pack(fill=X)

    Label(header_frame, text="My Ticket", font=("Arial", 24, "bold"), bg="#3399FF", fg="white").pack(pady=20)

    # Frame สำหรับปุ่มปิดหน้าต่าง
    button_frame = Frame(ticket_window, bg="#3399FF", height=50)
    button_frame.pack(fill=X)

    Button(button_frame,text="ปิดหน้าต่าง",font=("Arial", 14),bg="red",fg="white",command=ticket_window.destroy,relief="flat",width=15).pack(pady=10)

    # Canvas และ Scrollbar สำหรับภาพ
    canvas = Canvas(ticket_window)
    canvas.pack(side=LEFT, fill=BOTH, expand=True)

    scrollbar = Scrollbar(ticket_window, orient=VERTICAL, command=canvas.yview)
    scrollbar.pack(side=RIGHT, fill=Y)

    scrollable_frame = Frame(canvas)
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    # ฟังก์ชันปรับปรุงขอบเขตการเลื่อน
    def update_scroll_region():
        canvas.update_idletasks()  
        canvas.configure(scrollregion=canvas.bbox("all"))

    # แสดงภาพตั๋วทั้งหมด
    for ticket_path in ticket_paths:
        if os.path.exists(ticket_path):
            try:
                ticket_image = Image.open(ticket_path)

                max_width, max_height = 450, 225
                ticket_image.thumbnail((max_width, max_height))

                ticket_photo = ImageTk.PhotoImage(ticket_image)

                label_image = Label(scrollable_frame, image=ticket_photo)
                label_image.image = ticket_photo  
                label_image.pack(fill=X, padx=550, pady=5)

            except Exception as e:
                print(f"Error displaying ticket image: {e}")
        else:
            Label(scrollable_frame, text=f"Ticket not found: {ticket_path}", font=("Arial", 12), fg="red").pack(padx=10, pady=10)

    update_scroll_region()

    scrollable_frame.bind("<Configure>", lambda event: update_scroll_region())

def show_sales_summary():
    summary_window = Toplevel()
    summary_window.title("สรุปการขาย")
    summary_window.state("zoomed")

    summary_window.configure(bg="#f0f0f0")

    # แถบสีฟ้าด้านบน
    top_bar = Frame(summary_window, bg="#87CEEB", height=80)
    top_bar.pack(fill=X, side=TOP)

    # ข้อความที่แถบสีฟ้าด้านบน
    title_label = Label(top_bar, text="สรุปยอดขายในภาพรวม", font=("Arial", 22, "bold"), bg="#87CEEB", fg="white")
    title_label.pack(pady=10)

    # แถบสีฟ้าด้านล่าง
    bottom_bar = Frame(summary_window, bg="#87CEEB", height=80)
    bottom_bar.pack(fill=X, side=BOTTOM)

    # สร้างเฟรมหลักสำหรับการจัดวางตาราง
    main_frame = Frame(summary_window, bg="#f0f0f0")
    main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

    today = datetime.today()
    week_start = today - timedelta(days=today.weekday())  # วันจันทร์ของสัปดาห์นี้
    month_start = today.replace(day=1)  # วันที่ 1 ของเดือนนี้

    # สรุปยอดขายตามกลุ่มอายุ
    age_summary = {
        "Child": {"sales": 0, "seats": 0},
        "Teen": {"sales": 0, "seats": 0},
        "Adult": {"sales": 0, "seats": 0},
        "Senior": {"sales": 0, "seats": 0},
    }

    # สรุปยอดขายตามประเภทหนัง
    genre_sales = {
        "Action": {"sales": 0, "seats": 0},
        "Comedy": {"sales": 0, "seats": 0},
        "Drama": {"sales": 0, "seats": 0},
        "Horror": {"sales": 0, "seats": 0},
        "Romance": {"sales": 0, "seats": 0},
        "Sci-Fi": {"sales": 0, "seats": 0},
        "Thriller": {"sales": 0, "seats": 0},
        "Animation": {"sales": 0, "seats": 0}
    }

    daily_sales = 0
    weekly_sales = 0
    monthly_sales = 0
    total_sales = 0  # ยอดขายรวมทั้งหมด

    # ดึงข้อมูลการจอง
    c.execute('''SELECT username, movie_title, total_price, seats, show_time, payment_date FROM booking''')
    bookings = c.fetchall()

    for booking in bookings:
        username, movie_title, total_price, seats, show_time, payment_date = booking
        seats_list = seats.split(',')

        # คำนวณยอดขายและจำนวนที่นั่งตามประเภทหนัง
        c.execute('''SELECT genre FROM movies WHERE title=?''', (movie_title,))
        movie_data = c.fetchone()

        if movie_data:
            genre = movie_data[0]
            if genre in genre_sales:
                genre_sales[genre]["sales"] += total_price
                genre_sales[genre]["seats"] += len(seats_list)

        # คำนวณกลุ่มอายุจากวันเกิด
        c.execute('''SELECT birth_date FROM users WHERE username=?''', (username,))
        user_data = c.fetchone()

        if user_data:
            birthdate = user_data[0]
            try:
                birth_date_obj = datetime.strptime(birthdate, '%d/%m/%Y')
                age = today.year - birth_date_obj.year - ((today.month, today.day) < (birth_date_obj.month, birth_date_obj.day))

                if age < 12:
                    age_group = "Child"
                elif 13 <= age < 19:
                    age_group = "Teen"
                elif 20 <= age < 60:
                    age_group = "Adult"
                else:
                    age_group = "Senior"

                if age_group in age_summary:
                    age_summary[age_group]["sales"] += total_price
                    age_summary[age_group]["seats"] += len(seats_list)

            except Exception as e:
                continue

        # คำนวณยอดขายวันนี้, สัปดาห์นี้, เดือนนี้, และรวมทั้งหมด
        payment_date_obj = datetime.strptime(payment_date, '%Y-%m-%d %H:%M:%S')

        if payment_date_obj.date() == today.date():
            daily_sales += total_price

        if week_start.date() <= payment_date_obj.date() <= today.date():
            weekly_sales += total_price

        if month_start.date() <= payment_date_obj.date() <= today.date():
            monthly_sales += total_price

        total_sales += total_price

    # สรุปยอดขายรวม
    summary_label = Label(main_frame, text="สรุปยอดขายรวม", font=("Arial", 16, "bold"))
    summary_label.place(x=320 , y =20)

    sales_tree = ttk.Treeview(main_frame, columns=("label", "amount"), show="headings")
    sales_tree.heading("label", text="ประเภท")
    sales_tree.heading("amount", text="จำนวนเงิน")
    sales_tree.column("label", width=200)
    sales_tree.column("amount", width=150)

    sales_tree.insert("", "end", values=("ยอดขายวันนี้", f"{daily_sales:,.2f} บาท"))
    sales_tree.insert("", "end", values=("ยอดขายสัปดาห์นี้", f"{weekly_sales:,.2f} บาท"))
    sales_tree.insert("", "end", values=("ยอดขายเดือนนี้", f"{monthly_sales:,.2f} บาท"))
    sales_tree.insert("", "end", values=("ยอดขายรวม", f"{total_sales:,.2f} บาท"))

    sales_tree.place(x=320 , y =60)

    # ตารางข้อมูลยอดขายตามกลุ่มอายุ
    age_label = Label(main_frame, text="ข้อมูลยอดขายตามกลุ่มอายุ", font=("Arial", 16, "bold"))
    age_label.place(x=780 , y = 20)

    age_tree = ttk.Treeview(main_frame, columns=("age_group", "sales", "seats"), show="headings")
    age_tree.heading("age_group", text="กลุ่มอายุ")
    age_tree.heading("sales", text="ยอดขาย")
    age_tree.heading("seats", text="จำนวนที่นั่ง")
    age_tree.column("age_group", width=200)
    age_tree.column("sales", width=150)
    age_tree.column("seats", width=150)

    for age_group in age_summary:
        age_tree.insert("", "end", values=(age_group, f"{age_summary[age_group]['sales']:,.2f}", f"{age_summary[age_group]['seats']:,} ที่นั่ง"))

    age_tree.place(x=780 , y =60)

    # ตารางข้อมูลยอดขายตามประเภทหนัง
    genre_label = Label(main_frame, text="ข้อมูลยอดขายตามประเภทหนัง", font=("Arial", 16, "bold"))
    genre_label.place(x=320 , y =330)

    genre_tree = ttk.Treeview(main_frame, columns=("genre", "sales", "seats"), show="headings")
    genre_tree.heading("genre", text="ประเภทหนัง")
    genre_tree.heading("sales", text="ยอดขาย")
    genre_tree.heading("seats", text="จำนวนที่นั่ง")
    genre_tree.column("genre", width=200)
    genre_tree.column("sales", width=150)
    genre_tree.column("seats", width=150)

    for genre in genre_sales:
        genre_tree.insert("", "end", values=(genre, f"{genre_sales[genre]['sales']:,.2f}", f"{genre_sales[genre]['seats']:,} ที่นั่ง"))

    genre_tree.place(x=320 , y =380)

    close_button = Button(bottom_bar, text="ปิด", font=("Arial", 16, "bold"), command=summary_window.destroy, bg="red", fg="white" ,width=20 ,height=2)
    close_button.pack(side=RIGHT, padx=10, pady=10)
    
def report_sales_by_movie(conn):
    c = conn.cursor()
    c.execute('''
    SELECT movie_title, SUM(total_price) AS total_sales
    FROM booking
    GROUP BY movie_title;
    ''')
    report = c.fetchall()
    return report

# ฟังก์ชันแสดงยอดขายแยกตามรอบเวลา
def report_sales_by_show_time(conn):
    c = conn.cursor()
    c.execute('''
    SELECT show_time, SUM(total_price) AS total_sales
    FROM booking
    GROUP BY show_time
    ORDER BY total_sales DESC;
    ''')
    report = c.fetchall()
    return report

# ฟังก์ชันแสดงยอดขายแยกตามรอบเวลาและหนัง
def report_sales_by_movie_and_time(conn):
    c = conn.cursor()
    c.execute('''
    SELECT movie_title, show_time, SUM(total_price) AS total_sales
    FROM booking
    GROUP BY movie_title, show_time
    ORDER BY total_sales DESC;
    ''')
    report = c.fetchall()
    return report

# ฟังก์ชันสร้างรายงานทั้งหมด
def generate_report():
    conn = sqlite3.connect(r"D:\c.db")
    movie_report = report_sales_by_movie(conn)
    show_time_report = report_sales_by_show_time(conn)
    movie_time_report = report_sales_by_movie_and_time(conn)
    conn.close()

    return movie_report, show_time_report, movie_time_report

def format_number(value):
    try:
        return "{:,.2f}".format(float(value))  # คั่นหลักพันและแสดงทศนิยม 2 ตำแหน่ง
    except (ValueError, TypeError):
        return value

def show_report():
    movie_report, show_time_report, movie_time_report = generate_report()

    # สร้างหน้าต่างรายงาน
    report_window = Toplevel(root)
    report_window.title("รายงานยอดขาย")
    report_window.state("zoomed")

    # โหลดภาพพื้นหลัง
    bg_image = Image.open(r"D:\GUI\xs.png")

    # สร้าง Canvas สำหรับพื้นหลัง
    canvas = Canvas(report_window)
    canvas.pack(fill="both", expand=True)

    # ฟังก์ชันสำหรับอัพเดตภาพพื้นหลังเมื่อขนาดหน้าต่างเปลี่ยน
    def update_bg_image(event):
        screen_width = report_window.winfo_width()
        screen_height = report_window.winfo_height()

        resized_image = bg_image.resize((screen_width, screen_height), Image.LANCZOS)
        bg_resized = ImageTk.PhotoImage(resized_image)
        canvas.delete("all")  # ลบภาพพื้นหลังเก่า
        canvas.create_image(0, 0, image=bg_resized, anchor="nw")
        canvas.image = bg_resized  # เก็บ reference เพื่อป้องกันการถูก garbage collected

    report_window.bind("<Configure>", update_bg_image)

    # การตั้งค่ารายการ Treeview 
    label_movie_report = Label(report_window, text="รายงานยอดขายแยกตามหนัง", font=("Microsoft YaHei UI Bold", 14),bg="white")
    label_movie_report.place(x=340, y=110)

    tree_movie = ttk.Treeview(report_window, columns=("Movie", "Total Sales"), show="headings", height=10)
    tree_movie.heading("Movie", text="Movie Title")
    tree_movie.heading("Total Sales", text="Total Sales")
    tree_movie.place(x=340, y=150)

    # เรียงข้อมูลยอดขายแยกตามหนัง จากมากไปน้อย
    sorted_movie_report = sorted(movie_report, key=lambda x: x[1], reverse=True)
    for row in sorted_movie_report:
        movie_title, total_sales = row
        tree_movie.insert("", "end", values=(movie_title, format_number(total_sales)))

    # ตารางรายงานยอดขายแยกรอบเวลา 
    label_show_time_report = Label(report_window, text="รายงานยอดขายแยกรอบเวลา", font=("Microsoft YaHei UI Bold", 14),bg="white")
    label_show_time_report.place(x=820, y=110)

    tree_show_time = ttk.Treeview(report_window, columns=("Show Time", "Total Sales"), show="headings", height=10)
    tree_show_time.heading("Show Time", text="Show Time")
    tree_show_time.heading("Total Sales", text="Total Sales")
    tree_show_time.place(x=820, y=150)

    # เรียงข้อมูลยอดขายแยกรอบเวลา
    sorted_show_time_report = sorted(show_time_report, key=lambda x: x[0])
    for row in sorted_show_time_report:
        show_time, total_sales = row
        tree_show_time.insert("", "end", values=(show_time, format_number(total_sales)))

    # ตารางรายงานยอดขายแยกหนังและรอบเวลา 
    label_movie_time_report = Label(report_window, text="รายงานยอดขายแยกหนังและรอบเวลา", font=("Microsoft YaHei UI Bold", 14),bg="white")
    label_movie_time_report.place(x=340, y=400)

    tree_movie_time = ttk.Treeview(report_window, columns=[], show="headings", height=10)
    tree_movie_time.place(x=340, y=440)

    # สร้างคอลัมน์สำหรับแต่ละรอบเวลา
    all_show_times = set(row[1] for row in movie_time_report)
    sorted_show_times = sorted(all_show_times)
    columns = ["Movie"] + [f"{time}" for time in sorted_show_times]
    tree_movie_time["columns"] = columns

    tree_movie_time.heading("Movie", text="Movie Title")
    tree_movie_time.column("Movie", width=200)

    for time in sorted_show_times:
        tree_movie_time.heading(f"{time}", text=f"{time}")
        tree_movie_time.column(f"{time}", width=100)

    movie_data = {}
    for row in movie_time_report:
        movie_title, show_time, total_sales = row
        if movie_title not in movie_data:
            movie_data[movie_title] = {}
        movie_data[movie_title][show_time] = format_number(total_sales)

    for movie, times in movie_data.items():
        row_data = [movie] + [times.get(time, "-") for time in sorted_show_times]
        tree_movie_time.insert("", "end", values=row_data)

    report_window.grid_rowconfigure(0, weight=0)
    report_window.grid_columnconfigure(0, weight=1) 
    report_window.grid_columnconfigure(1, weight=1)  

    back_button = Button(canvas, text="ปิด", relief="flat", bg="red", borderwidth=2, highlightthickness=3, command=report_window.destroy,font=("Microsoft YaHei UI ", 16 ),width=20)
    back_button.place(x=630, y=720)

def show_top_spenders():
    top_spenders_window = Toplevel()
    top_spenders_window.title("สรุป Top Spender")
    top_spenders_window.state("zoomed")

    today = datetime.today()
    week_start = today - timedelta(days=today.weekday()) 
    month_start = today.replace(day=1) 

    # ดึงข้อมูลการจอง
    c.execute('''SELECT username, total_price, payment_date FROM booking''')
    bookings = c.fetchall()

    spender_data = {}

    for booking in bookings:
        username, total_price, payment_date = booking
        try:
            payment_date_obj = datetime.strptime(payment_date, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            continue  

        if username not in spender_data:
            spender_data[username] = {
                "daily_sales": 0,
                "weekly_sales": 0,
                "monthly_sales": 0,
                "total_sales": 0,
            }

        # คำนวณยอดขายตามช่วงเวลา
        if payment_date_obj.date() == today.date():
            spender_data[username]["daily_sales"] += float(total_price)

        if week_start.date() <= payment_date_obj.date() <= today.date():
            spender_data[username]["weekly_sales"] += float(total_price)

        if month_start.date() <= payment_date_obj.date() <= today.date():
            spender_data[username]["monthly_sales"] += float(total_price)

        spender_data[username]["total_sales"] += float(total_price)

    # คัดเลือก 3 อันดับ Top Spender ของแต่ละช่วงเวลา
    top_daily_spenders = sorted(spender_data.items(), key=lambda x: x[1]["daily_sales"], reverse=True)[:3]
    top_weekly_spenders = sorted(spender_data.items(), key=lambda x: x[1]["weekly_sales"], reverse=True)[:3]
    top_monthly_spenders = sorted(spender_data.items(), key=lambda x: x[1]["monthly_sales"], reverse=True)[:3]
    top_all_time_spenders = sorted(spender_data.items(), key=lambda x: x[1]["total_sales"], reverse=True)[:10]

    def display_spenders(tree, spenders, key):
        for row in tree.get_children():
            tree.delete(row) 

        for idx, (username, sales_data) in enumerate(spenders, 1):
            tree.insert("", "end", values=(idx, username, f"{sales_data[key]:,.2f} บาท"))

    # ขอบบนและขอบล่างสีฟ้า
    top_frame = Frame(top_spenders_window, bg="#66ccff", height=80)
    top_frame.pack(fill="x")
    label_top = Label(top_frame, text="สรุปผล Top Spender", font=("Arial", 20, "bold"), bg="#66ccff", fg="white")
    label_top.pack(pady=10)

    bottom_frame = Frame(top_spenders_window, bg="#66ccff", height=80)
    bottom_frame.pack(fill="x", side="bottom")
    close_button = Button(bottom_frame, text="ปิด", command=top_spenders_window.destroy, bg="#ff6666", font=("Arial", 14))
    close_button.pack(side="right", padx=10, pady=10)
    row_counter = 0 

    # แถวที่ 1 ตารางรายวันและรายสัปดาห์
    frame_row_1 = Frame(top_spenders_window)
    frame_row_1.pack(pady=20)

    label_daily = Label(frame_row_1, text="Top Spenders - รายวัน", font=("Arial", 16, "bold"), anchor="w")
    label_daily.grid(row=0, column=0, columnspan=2, padx=100 , pady=10, sticky="w")

    tree_daily = ttk.Treeview(frame_row_1, columns=("อันดับ", "ผู้ใช้", "ยอดใช้จ่ายรายวัน"), show="headings")
    tree_daily.heading("อันดับ", text="อันดับ")
    tree_daily.heading("ผู้ใช้", text="ผู้ใช้")
    tree_daily.heading("ยอดใช้จ่ายรายวัน", text="ยอดใช้จ่ายรายวัน")
    tree_daily.grid(row=1, column=0, padx=100, pady=10)

    display_spenders(tree_daily, top_daily_spenders, "daily_sales")

    label_weekly = Label(frame_row_1, text="Top Spenders - รายสัปดาห์", font=("Arial", 16, "bold"), anchor="w")
    label_weekly.grid(row=0, column=1, padx=10, pady=10, sticky="w")

    tree_weekly = ttk.Treeview(frame_row_1, columns=("อันดับ", "ผู้ใช้", "ยอดใช้จ่ายรายสัปดาห์"), show="headings")
    tree_weekly.heading("อันดับ", text="อันดับ")
    tree_weekly.heading("ผู้ใช้", text="ผู้ใช้")
    tree_weekly.heading("ยอดใช้จ่ายรายสัปดาห์", text="ยอดใช้จ่ายรายสัปดาห์")
    tree_weekly.grid(row=1, column=1, padx=10, pady=10)

    display_spenders(tree_weekly, top_weekly_spenders, "weekly_sales")

    row_counter += 1

    # แถวที่ 2 ตารางรายเดือนและตลอดกาล
    frame_row_2 = Frame(top_spenders_window)
    frame_row_2.pack(pady=20)

    label_monthly = Label(frame_row_2, text="Top Spenders - รายเดือน", font=("Arial", 16, "bold"), anchor="w")
    label_monthly.grid(row=0, column=0, columnspan=2, padx=100, pady=10, sticky="w")

    tree_monthly = ttk.Treeview(frame_row_2, columns=("อันดับ", "ผู้ใช้", "ยอดใช้จ่ายรายเดือน"), show="headings")
    tree_monthly.heading("อันดับ", text="อันดับ")
    tree_monthly.heading("ผู้ใช้", text="ผู้ใช้")
    tree_monthly.heading("ยอดใช้จ่ายรายเดือน", text="ยอดใช้จ่ายรายเดือน")
    tree_monthly.grid(row=1, column=0, padx=100, pady=10)

    display_spenders(tree_monthly, top_monthly_spenders, "monthly_sales")

    label_all_time = Label(frame_row_2, text="Top Spenders - ตลอดกาล", font=("Arial", 16, "bold"), anchor="w")
    label_all_time.grid(row=0, column=1, padx=10, pady=10, sticky="w")

    tree_all_time = ttk.Treeview(frame_row_2, columns=("อันดับ", "ผู้ใช้", "ยอดใช้จ่ายตลอดกาล"), show="headings")
    tree_all_time.heading("อันดับ", text="อันดับ")
    tree_all_time.heading("ผู้ใช้", text="ผู้ใช้")
    tree_all_time.heading("ยอดใช้จ่ายตลอดกาล", text="ยอดใช้จ่ายตลอดกาล")
    tree_all_time.grid(row=1, column=1, padx=10, pady=10)

    display_spenders(tree_all_time, top_all_time_spenders, "total_sales")

def connect_to_db():
    conn = sqlite3.connect(r"D:\c.db") 
    return conn

def calculate_age(birth_date):
    if not birth_date:
        return None  # ถ้า birth_date เป็น None หรือค่าว่างให้คืนค่า None

    try:
        birth_date_obj = datetime.strptime(birth_date, "%d/%m/%Y")
        today = datetime.today()
        age = today.year - birth_date_obj.year
        if today.month < birth_date_obj.month or (today.month == birth_date_obj.month and today.day < birth_date_obj.day):
            age -= 1
        return age
    except ValueError:
        return None

# ฟังก์ชันคำนวณกลุ่มวัยตามอายุ
def get_age_group(age):
    if 0 <= age <= 12:
        return "เด็ก"
    elif 13 <= age <= 19:
        return "วัยรุ่น"
    elif 20 <= age <= 60:
        return "วัยทำงาน"
    else:
        return "ผู้สูงอายุ"

# ฟังก์ชันดึงข้อมูลจากตาราง booking และ users
def get_booking_data():
    conn = connect_to_db()
    cursor = conn.cursor()
    try:
        query = """
        SELECT b.username, b.total_price, b.show_time, m.genre, m.age_rating, u.birth_date
        FROM booking b
        JOIN movies m ON b.movie_title = m.title
        JOIN users u ON b.username = u.username
        """
        cursor.execute(query)
        bookings = cursor.fetchall()
    except sqlite3.OperationalError as e:
        print("Error:", e)
        bookings = []
    finally:
        conn.close()
    
    return bookings

def get_time_slot(show_time):
    # ลิสต์รอบเวลาที่กำหนด
    time_slots = ["10:00", "12:30", "15:00", "17:30", "20:00", "22:30"]
    
    # ตรวจสอบว่าเวลาอยู่ในลิสต์ที่กำหนดหรือไม่
    if show_time in time_slots:
        return show_time
    else:
        return "ไม่ระบุ"

# ฟังก์ชันสร้าง Treeview สำหรับการแสดงข้อมูล
def create_treeview(parent_frame, title, data):
    treeview = ttk.Treeview(parent_frame, columns=("กลุ่มวัย", "ประเภทหนัง", "ยอดใช้จ่าย", "รอบเวลา"), show="headings")
    treeview.heading("กลุ่มวัย", text="กลุ่มวัย")
    treeview.heading("ประเภทหนัง", text="ประเภทหนัง")
    treeview.heading("ยอดใช้จ่าย", text="ยอดใช้จ่าย")
    treeview.heading("รอบเวลา", text="รอบเวลา")

    treeview.column("กลุ่มวัย", width=150)
    treeview.column("ประเภทหนัง", width=150)
    treeview.column("ยอดใช้จ่าย", width=100)
    treeview.column("รอบเวลา", width=100)

    # แสดงข้อมูลใน Treeview
    treeview.insert("", "end", text=title, values=("", "", "", ""))
    treeview.insert("", "end", values=("กลุ่มวัย", "ประเภทหนัง", "ยอดใช้จ่าย", "รอบเวลา"))

    for row in data:
        treeview.insert("", "end", values=row)
    
    treeview.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
    
    return treeview

def show_movie_data_by_age_group():
    # สร้างหน้าต่างใหม่
    movie_data_window = Toplevel()
    movie_data_window.title("ข้อมูลการรับชมภาพยนต์ตามกลุ่มวัย")
    movie_data_window.state("zoomed")

        # โหลดภาพพื้นหลัง
    bg_image = Image.open(r"D:\GUI\xp.png")

    # สร้าง Canvas สำหรับพื้นหลัง
    canvas = Canvas(movie_data_window)
    canvas.pack(fill="both", expand=True)

    # ฟังก์ชันสำหรับอัพเดตภาพพื้นหลังเมื่อขนาดหน้าต่างเปลี่ยน
    def update_bg_image(event):
        screen_width = movie_data_window.winfo_width()
        screen_height = movie_data_window.winfo_height()

        resized_image = bg_image.resize((screen_width, screen_height), Image.LANCZOS)
        bg_resized = ImageTk.PhotoImage(resized_image)
        canvas.delete("all")  # ลบภาพพื้นหลังเก่า
        canvas.create_image(0, 0, image=bg_resized, anchor="nw")
        canvas.image = bg_resized  # เก็บ reference เพื่อป้องกันการถูก garbage collected

    movie_data_window.bind("<Configure>", update_bg_image)

    # ฟังก์ชันอัปเดตข้อมูลตามกลุ่มวัยที่เลือก
    def update_data_by_age_group(selected_group=None):
        # ดึงข้อมูลการจองจากฐานข้อมูล
        bookings = get_booking_data()

        # เก็บยอดใช้จ่ายตามกลุ่มวัยและประเภทหนัง
        age_group_data = {}

        for booking in bookings:
            username, total_price, time, genre, age_rating, birth_date = booking

            # คำนวณอายุจากวันเกิด
            age = calculate_age(birth_date)
            if age is None:
                continue  # ถ้าไม่มีข้อมูลวันเกิด

            age_group = get_age_group(age)

            if selected_group and age_group != selected_group:
                continue  # ข้ามกลุ่มวัยที่ไม่ตรงกับที่เลือก

            if age_group not in age_group_data:
                age_group_data[age_group] = {}

            if genre not in age_group_data[age_group]:
                age_group_data[age_group][genre] = {"total_sales": 0, "times": {}}

            age_group_data[age_group][genre]["total_sales"] += total_price

            time_slot = get_time_slot(time)

            # ตรวจสอบว่า time_slot อยู่ใน dictionary หรือไม่ ถ้าไม่ให้เพิ่มเข้าไป
            if time_slot not in age_group_data[age_group][genre]["times"]:
                age_group_data[age_group][genre]["times"][time_slot] = 0

            age_group_data[age_group][genre]["times"][time_slot] += total_price

        # เตรียมข้อมูลแสดงผล
        result_data = []

        for age_group, genres in age_group_data.items():
            for genre, data in genres.items():
                row = [age_group, genre, f"{data['total_sales']:,.2f} บาท"]

                for time_slot in ["10:00", "12:30", "15:00", "17:30", "20:00", "22:30"]:
                    sales = data["times"].get(time_slot, 0)
                    row.append(f"{sales:,.2f} บาท")

                result_data.append(row)

        # แสดงข้อมูลใน Treeview
        columns = ["กลุ่มวัย", "ประเภทหนัง", "ยอดใช้จ่ายรวม", "10:00", "12:30", "15:00", "17:30", "20:00", "22:30"]
        if hasattr(update_data_by_age_group, "treeview"):
            # ลบข้อมูลเก่าออกก่อน
            update_data_by_age_group.treeview.delete(*update_data_by_age_group.treeview.get_children())

        treeview = ttk.Treeview(movie_data_window, columns=columns, show="headings")

        for col in columns:
            treeview.heading(col, text=col)

        treeview.column("กลุ่มวัย", width=150)
        treeview.column("ประเภทหนัง", width=150)
        treeview.column("ยอดใช้จ่ายรวม", width=150)
        for time_slot in ["10:00", "12:30", "15:00", "17:30", "20:00", "22:30"]:
            treeview.column(time_slot, width=120)

        for row in result_data:
            treeview.insert("", "end", values=row)

        treeview.place(x=17, y=180, width=1500, height=500)

        # เก็บ Treeview ไว้ในฟังก์ชันเพื่ออัปเดตครั้งถัดไป
        update_data_by_age_group.treeview = treeview

    # เรียกแสดงข้อมูลทั้งหมดเริ่มต้น
    update_data_by_age_group()

    # สร้างปุ่มเลือกกลุ่มวัย (เรียงในแนวนอน)
    age_group_buttons = [
        ("เด็ก", "เด็ก"),
        ("วัยรุ่น", "วัยรุ่น"),
        ("วัยทำงาน", "วัยทำงาน"),
        ("ผู้สูงอายุ", "ผู้สูงอายุ")
    ]


    button_frame = Frame(movie_data_window,bg="white")
    button_frame.place(x=250, y=120)  # ตั้งตำแหน่งของ frame ที่นี่

    for idx, (text, group) in enumerate(age_group_buttons):
        button = Button(button_frame, text=text, command=lambda group=group: update_data_by_age_group(group), bg="#4CAF50", font=("Arial", 14),width=20)
        button.grid(row=0, column=idx, padx=10)

    # ปุ่มแสดงข้อมูลทั้งหมด
    show_all_button = Button(movie_data_window, text="แสดงข้อมูลทั้งหมด", command=lambda: update_data_by_age_group(None), bg="#4CAF50", font=("Arial", 14),width=20)
    show_all_button.place(x=10, y=120)  # ตั้งตำแหน่งของปุ่มแสดงข้อมูลทั้งหมด

    # ปุ่มปิดหน้าต่าง
    close_button = Button(movie_data_window, text="ปิด", command=movie_data_window.destroy, bg="red", font=("Arial", 14),width=20)
    close_button.place(x=650, y=720)  # ตั้งตำแหน่งของปุ่มปิด

def open_all_summary():
    sum = Toplevel()
    sum.title("สรุปผล")
    sum.state("zoomed")

    # โหลดภาพพื้นหลัง
    bg_image = Image.open(r"D:\GUI\H.png")
    canvas = Canvas(sum)
    canvas.pack(fill="both", expand=True)

    def update_bg_image(event):
        screen_width = sum.winfo_width()
        screen_height = sum.winfo_height()
    
        resized_image = bg_image.resize((screen_width, screen_height), Image.LANCZOS)
        bg_resized = ImageTk.PhotoImage(resized_image)
        canvas.delete("all")  # ลบภาพพื้นหลังเก่า
        canvas.create_image(0, 0, image=bg_resized, anchor="nw")
        canvas.image = bg_resized  # เก็บ reference เพื่อป้องกันการถูก garbage collected

    sum.bind("<Configure>", update_bg_image)

    btn_sales_summary = Button(sum, text="ภาพรวม", bg="#0097b2", font=("Microsoft YaHei UI Bold", 16), fg="white", width="16", height="1", command= show_sales_summary)
    btn_sales_summary.place(x=220, y=520)

    btn_sales_summary = Button(sum, text="Top Spender", bg="#0097b2", font=("Microsoft YaHei UI Bold", 16), fg="white", width="16", height="1", command= show_top_spenders)
    btn_sales_summary.place(x=500, y=525)

    btn_sales_summary = Button(sum, text="จำแนกตามผุ้ชม", bg="#0097b2", font=("Microsoft YaHei UI Bold", 16), fg="white", width="16", height="1", command= show_movie_data_by_age_group)
    btn_sales_summary.place(x=770, y=525)

    btn_sales_summary = Button(sum, text="จำแนกตามหนังแต่ละเรื่อง", bg="#0097b2", font=("Microsoft YaHei UI Bold", 16), fg="white", width="16", height="1", command= show_report)
    btn_sales_summary.place(x=1050, y=525)

    close_button = Button(sum, text="ปิด", command=sum.destroy, bg="red", font=("Arial", 14),width=20)
    close_button.place(x=650, y=720) 

# สร้างหน้าต่างหลัก
root = Tk()
root.title("Login")
root.state("zoomed")  

# โหลดภาพพื้นหลัง
bg_image = Image.open(r"D:\GUI\Sign up.png")
canvas = Canvas(root)
canvas.pack(fill="both", expand=True)

def update_bg_image(event):
    screen_width = root.winfo_width()
    screen_height = root.winfo_height()
    
    resized_image = bg_image.resize((screen_width, screen_height), Image.LANCZOS)
    bg_resized = ImageTk.PhotoImage(resized_image)
    canvas.delete("all")  # ลบภาพพื้นหลังเก่า
    canvas.create_image(0, 0, image=bg_resized, anchor="nw")
    canvas.image = bg_resized  # เก็บ reference เพื่อป้องกันการถูก garbage collected

root.bind("<Configure>", update_bg_image)

def create_entry_with_underline(parent, x_position, y_position, placeholder, width=400, height=45, is_password=False):
    entry = Entry(parent, fg="#757575", border=0, bg="white", font=("Microsoft YaHei UI", 25))
    entry.place(x=x_position, y=y_position, width=width, height=height)
    
    # แสดง placeholder
    entry.insert(0, placeholder)
    entry.bind("<FocusIn>", lambda event: clear_placeholder(event, placeholder, is_password))
    entry.bind("<FocusOut>", lambda event: add_placeholder(event, placeholder, is_password))
    
    underline = Canvas(parent, width=width, height=2, bg="#3399FF", highlightthickness=0)  # เปลี่ยนสีเส้นใต้เป็นสีฟ้า
    underline.place(x=x_position, y=y_position + height, anchor="nw")

    return entry

def clear_placeholder(event, placeholder, is_password):
    if event.widget.get() == placeholder:
        event.widget.delete(0, END)
        if is_password:
            event.widget.config(show="*")  # ซ่อนรหัสผ่านเป็น ***
        else:
            event.widget.config(fg="black")  # ตั้งสีข้อความเป็นดำ

def add_placeholder(event, placeholder, is_password):
    if event.widget.get() == "":
        event.widget.insert(0, placeholder)  # แสดง placeholder ถ้าช่องว่าง
        if is_password:
            event.widget.config(show="")  # แสดง placeholder เมื่อไม่กรอก

label_username = Label(canvas, text="Login", bg="white", font=("Microsoft YaHei UI Bold", 50), fg="#3399FF").place(x=950, y=130)
username_entry = create_entry_with_underline(canvas, x_position=800, y_position=280, placeholder="Username", width=500, height=45)
password_entry = create_entry_with_underline(canvas, x_position=800, y_position=380, placeholder="Password", width=500, height=45, is_password=True)

user_image = Image.open(r"D:\GUI\user_icon-removebg-preview.png")
user_image = ImageTk.PhotoImage(user_image)
image_label = Label(canvas, image=user_image, bg="white")  
image_label.place(x=740, y=278)

pass_image = Image.open(r"D:\GUI\pass_icon.png")
pass_image = ImageTk.PhotoImage(pass_image)
image_label = Label(canvas, image=pass_image, bg="white")  
image_label.place(x=740, y=378)

logo_image = Image.open(r"D:\GUI\EDJOR (1).png")
logo_image = ImageTk.PhotoImage(logo_image)
image_label = Label(canvas, image=logo_image, bg="white")  
image_label.place(x=160, y=120)

# สร้างปุ่มด้วยฟอนต์ Microsoft YaHei UI Bold
sign_up = Button(canvas, text="Sign Up", command=lambda: (root.withdraw(), open_register_window()), relief="flat", fg="white" , bg="#38b6ff" , font=("Microsoft YaHei UI Bold", 20 )).place(x=890, y=500)
sign_in = Button(canvas, text="Sign In", command=login_user , relief="flat", bg="#38b6ff" , fg="white" , font=("Microsoft YaHei UI Bold", 20 )).place(x=1070, y=500)

root.mainloop()
conn.close()