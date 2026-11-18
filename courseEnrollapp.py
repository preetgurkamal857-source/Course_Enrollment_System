import os
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import mysql.connector


# MySQL connection settings
DB_CONFIG = {
    "host": "localhost",
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": "enrollment_db",
    "use_pure": True
}


def setup_database():
    # Connect to MySQL without selecting a database first
    conn = mysql.connector.connect(
        host=DB_CONFIG["host"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        use_pure=True
    )

    cursor = conn.cursor()

    try:
        cursor.execute("CREATE DATABASE IF NOT EXISTS enrollment_db")
        cursor.execute("USE enrollment_db")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR(50) DEFAULT not NULL PRIMARY KEY,
                password VARCHAR(50)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS enrollments (
                student_id INT AUTO_INCREMENT PRIMARY KEY,
                student_name VARCHAR(100),
                course_name VARCHAR(100)
            )
        """)

        cursor.execute("SHOW COLUMNS FROM enrollments")
        columns = {column[0]: column for column in cursor.fetchall()}

        if "student_id" not in columns and "id" in columns:
            cursor.execute("""
                ALTER TABLE enrollments
                CHANGE COLUMN `id` `student_id` INT NOT NULL
            """)
            cursor.execute("SHOW COLUMNS FROM enrollments")
            columns = {column[0]: column for column in cursor.fetchall()}

        if "student_id" in columns and "id" in columns:
            cursor.execute("""
                UPDATE enrollments
                SET student_id = id
                WHERE (student_id IS NULL OR student_id = 0)
                  AND id IS NOT NULL
            """)

            if columns["id"][3] == "PRI":
                cursor.execute("ALTER TABLE enrollments DROP PRIMARY KEY")
            cursor.execute("ALTER TABLE enrollments DROP COLUMN `id`")
            cursor.execute("SHOW COLUMNS FROM enrollments")
            columns = {column[0]: column for column in cursor.fetchall()}

        if "student_id" not in columns:
            cursor.execute("""
                ALTER TABLE enrollments
                ADD COLUMN student_id INT NOT NULL DEFAULT 0
            """)
            cursor.execute("SHOW COLUMNS FROM enrollments")
            columns = {column[0]: column for column in cursor.fetchall()}

        for column_name, column in columns.items():
            if column_name != "student_id" and "auto_increment" in column[5].lower():
                nullable = "NULL" if column[2] == "YES" else "NOT NULL"
                cursor.execute(
                    f"ALTER TABLE enrollments MODIFY COLUMN `{column_name}` "
                    f"{column[1]} {nullable}"
                )

        if columns["student_id"][3] == "":
            cursor.execute("""
                ALTER TABLE enrollments
                ADD INDEX idx_enrollments_student_id (student_id)
            """)

        cursor.execute("SET @next_student_id = (SELECT COALESCE(MAX(student_id), 0) FROM enrollments)")
        cursor.execute("""
            UPDATE enrollments
            SET student_id = (@next_student_id := @next_student_id + 1)
            WHERE student_id IS NULL OR student_id = 0
        """)

        cursor.execute("""
            ALTER TABLE enrollments
            MODIFY COLUMN student_id INT NOT NULL AUTO_INCREMENT
        """)

        # Create the starter portal login if it does not already exist
        cursor.execute(
            "INSERT IGNORE INTO users (id, password) VALUES (%s, %s)",
            ("admin", "admin123")
        )

        conn.commit()

    finally:
        cursor.close()
        conn.close()


class EnrollmentSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Course Enrollment System")
        self.root.configure(bg="#eaf2f8")

        # Start in full-screen mode
        self.root.attributes("-fullscreen", True)

        # Press Esc or F11 to toggle full-screen mode
        self.root.bind("<Escape>", self.toggle_fullscreen)
        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<Control-q>", self.exit_app)
        self.root.protocol("WM_DELETE_WINDOW", self.exit_app)

        # Colors used for the animated dashboard header
        self.header_colors = ["#173f5f", "#20639b", "#3caea3", "#20639b"]
        self.color_index = 0

        self.show_login()

    def toggle_fullscreen(self, event=None):
        current_state = self.root.attributes("-fullscreen")
        self.root.attributes("-fullscreen", not current_state)

    def exit_app(self, event=None):
        if messagebox.askyesno("Exit", "Are you sure you want to close the app?"):
            self.root.destroy()

    def add_button_hover(self, button, normal_color, hover_color):
        button.configure(bg=normal_color)
        button.bind(
            "<Enter>",
            lambda event: button.configure(bg=hover_color)
        )
        button.bind(
            "<Leave>",
            lambda event: button.configure(bg=normal_color)
        )

    def show_login(self):
        self.clear_screen()
        self.root.configure(bg="#eaf2f8")

        login_frame = tk.Frame(
            self.root,
            bg="white",
            highlightbackground="#20639b",
            highlightthickness=3
        )
        login_frame.place(
            relx=0.5,
            rely=0.5,
            anchor="center",
            width=380,
            height=480
        )

        tk.Label(
            login_frame,
            text="🎓",
            font=("Arial", 35),
            bg="white"
        ).pack(pady=(25, 0))

        tk.Label(
            login_frame,
            text="Course Enrollment",
            font=("Arial", 22, "bold"),
            bg="white",
            fg="#173f5f"
        ).pack(pady=(5, 20))

        tk.Label(
            login_frame,
            text="User ID",
            font=("Arial", 12),
            bg="white",
            fg="#34495e"
        ).pack(anchor="w", padx=35)

        self.user_id = tk.Entry(
            login_frame,
            font=("Arial", 14),
            relief="solid",
            bd=1
        )
        self.user_id.pack(pady=(5, 15), padx=35, fill="x")

        tk.Label(
            login_frame,
            text="Password",
            font=("Arial", 12),
            bg="white",
            fg="#34495e"
        ).pack(anchor="w", padx=35)

        self.password = tk.Entry(
            login_frame,
            font=("Arial", 14),
            show="*",
            relief="solid",
            bd=1
        )
        self.password.pack(pady=(5, 20), padx=35, fill="x")

        login_button = tk.Button(
            login_frame,
            text="Login",
            font=("Arial", 13, "bold"),
            fg="white",
            command=self.validate_login,
            relief="flat",
            cursor="hand2"
        )
        login_button.pack(padx=35, fill="x", ipady=9)
        self.add_button_hover(login_button, "#20639b", "#173f5f")

        exit_button = tk.Button(
            login_frame,
            text="Exit",
            font=("Arial", 11, "bold"),
            fg="white",
            command=self.exit_app,
            relief="flat",
            cursor="hand2"
        )
        exit_button.pack(padx=35, pady=(10, 0), fill="x", ipady=6)
        self.add_button_hover(exit_button, "#e74c3c", "#c0392b")

        tk.Label(
            login_frame,
            text="Press Ctrl+Q to close the app",
            font=("Arial", 9),
            bg="white",
            fg="#7f8c8d"
        ).pack(pady=12)

        self.user_id.focus_set()

    def validate_login(self):
        user_id = self.user_id.get().strip()
        password = self.password.get()

        if not user_id or not password:
            messagebox.showwarning(
                "Missing Information",
                "Please enter your user ID and password."
            )
            return

        conn = None
        cursor = None

        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT id FROM users WHERE id = %s AND password = %s",
                (user_id, password)
            )
            user = cursor.fetchone()

            if user:
                messagebox.showinfo("Welcome", "Login successful!")
                self.show_dashboard()
            else:
                messagebox.showerror(
                    "Login Failed",
                    "Invalid user ID or password."
                )

        except mysql.connector.Error as error:
            messagebox.showerror("Database Error", str(error))

        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def show_dashboard(self):
        self.clear_screen()
        self.root.configure(bg="#f4f7fb")

        # Animated color-changing header
        self.header = tk.Frame(self.root, bg="#173f5f", height=75)
        self.header.pack(fill="x")

        self.header_title = tk.Label(
            self.header,
            text="🎓  Enrollment Dashboard",
            font=("Arial", 22, "bold"),
            fg="white",
            bg="#173f5f"
        )
        self.header_title.pack(pady=18)

        self.animate_header()

        # Enrollment form
        form_frame = tk.Frame(
            self.root,
            bg="white",
            padx=25,
            pady=20,
            highlightbackground="#d6e4f0",
            highlightthickness=1
        )
        form_frame.pack(pady=25)

        tk.Label(
            form_frame,
            text="Student Name:",
            font=("Arial", 12),
            bg="white",
            fg="#34495e"
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.name_entry = tk.Entry(
            form_frame,
            font=("Arial", 12),
            width=30,
            relief="solid",
            bd=1
        )
        self.name_entry.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(
            form_frame,
            text="Course:",
            font=("Arial", 12),
            bg="white",
            fg="#34495e"
        ).grid(row=1, column=0, padx=10, pady=10, sticky="w")

        self.course_box = ttk.Combobox(
            form_frame,
            values=[
                "Python Data Science",
                "Web Development",
                "AI Essentials"
            ],
            state="readonly",
            width=28,
            font=("Arial", 11)
        )
        self.course_box.grid(row=1, column=1, padx=10, pady=10)

        enroll_button = tk.Button(
            form_frame,
            text="Enroll Student",
            font=("Arial", 11, "bold"),
            fg="white",
            command=self.enroll_student,
            relief="flat",
            cursor="hand2"
        )
        enroll_button.grid(row=2, column=0, padx=10, pady=15, sticky="ew")
        self.add_button_hover(enroll_button, "#2ecc71", "#27ae60")

        clear_button = tk.Button(
            form_frame,
            text="Clear Form",
            font=("Arial", 11, "bold"),
            fg="white",
            command=self.clear_form,
            relief="flat",
            cursor="hand2"
        )
        clear_button.grid(row=2, column=1, padx=10, pady=15, sticky="ew")
        self.add_button_hover(clear_button, "#f39c12", "#d68910")

        tk.Label(
            self.root,
            text="Current Enrollments",
            font=("Arial", 16, "bold"),
            bg="#f4f7fb",
            fg="#173f5f"
        ).pack(pady=(5, 10))

        # Enrollment table
        table_frame = tk.Frame(self.root, bg="#f4f7fb")
        table_frame.pack(fill="both", expand=True, padx=35, pady=5)

        self.enrollment_list = ttk.Treeview(
            table_frame,
            columns=("Student ID", "Student Name", "Course"),
            show="headings",
            selectmode="extended",
            height=10
        )

        self.enrollment_list.heading("Student ID", text="Student ID")
        self.enrollment_list.heading("Student Name", text="Student Name")
        self.enrollment_list.heading("Course", text="Course")

        self.enrollment_list.column("Student ID", width=130, anchor="center")
        self.enrollment_list.column("Student Name", width=250, anchor="center")
        self.enrollment_list.column("Course", width=250, anchor="center")

        self.enrollment_list.pack(fill="both", expand=True)

        bottom_frame = tk.Frame(self.root, bg="#f4f7fb")
        bottom_frame.pack(pady=15)

        clear_table_button = tk.Button(
            bottom_frame,
            text="Clear Table",
            font=("Arial", 11, "bold"),
            fg="white",
            command=self.clear_enrollments,
            relief="flat",
            cursor="hand2"
        )
        clear_table_button.grid(row=0, column=0, padx=10, ipadx=20, ipady=7)
        self.add_button_hover(clear_table_button, "#e67e22", "#ca6f1b")

        delete_selected_button = tk.Button(
            bottom_frame,
            text="Delete Selected",
            font=("Arial", 11, "bold"),
            fg="white",
            command=self.delete_selected_enrollments,
            relief="flat",
            cursor="hand2"
        )
        delete_selected_button.grid(row=0, column=1, padx=10, ipadx=20, ipady=7)
        self.add_button_hover(delete_selected_button, "#3498db", "#2471a3")

        logout_button = tk.Button(
            bottom_frame,
            text="Logout",
            font=("Arial", 11, "bold"),
            fg="white",
            command=self.show_login,
            relief="flat",
            cursor="hand2"
        )
        logout_button.grid(row=0, column=2, padx=10, ipadx=25, ipady=7)
        self.add_button_hover(logout_button, "#e74c3c", "#c0392b")

        exit_button = tk.Button(
            bottom_frame,
            text="Exit",
            font=("Arial", 11, "bold"),
            fg="white",
            command=self.exit_app,
            relief="flat",
            cursor="hand2"
        )
        exit_button.grid(row=0, column=3, padx=10, ipadx=25, ipady=7)
        self.add_button_hover(exit_button, "#7f8c8d", "#626567")

        self.load_enrollments()

    def animate_header(self):
        if hasattr(self, "header") and self.header.winfo_exists():
            color = self.header_colors[self.color_index]

            self.header.configure(bg=color)
            self.header_title.configure(bg=color)

            self.color_index = (self.color_index + 1) % len(self.header_colors)

            # Change the header color every 700 milliseconds
            self.root.after(700, self.animate_header)

    def enroll_student(self):
        name = self.name_entry.get().strip()
        course = self.course_box.get()

        if not name:
            messagebox.showwarning(
                "Missing Information",
                "Please enter the student's name."
            )
            return

        if not course:
            messagebox.showwarning(
                "Missing Information",
                "Please select a course."
            )
            return

        conn = None
        cursor = None

        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO enrollments (student_name, course_name)
                VALUES (%s, %s)
                """,
                (name, course)
            )
            conn.commit()

            messagebox.showinfo(
                "Enrollment Complete",
                f"{name} has been enrolled in {course}."
            )

            self.clear_form()
            self.load_enrollments()

        except mysql.connector.Error as error:
            messagebox.showerror("Database Error", str(error))

        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def load_enrollments(self):
        for row in self.enrollment_list.get_children():
            self.enrollment_list.delete(row)

        conn = None
        cursor = None

        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT student_id, student_name, course_name
                FROM enrollments
                ORDER BY student_id
            """)

            for row in cursor.fetchall():
                self.enrollment_list.insert("", "end", values=row)

        except mysql.connector.Error as error:
            messagebox.showerror("Database Error", str(error))

        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def clear_form(self):
        self.name_entry.delete(0, tk.END)
        self.course_box.set("")

    def clear_enrollments(self):
        if not self.enrollment_list.get_children():
            messagebox.showinfo("Clear Table", "The enrollment table is already empty.")
            return

        confirmed = messagebox.askyesno(
            "Clear Table",
            "Delete all enrollment entries? This action cannot be undone."
        )
        if not confirmed:
            return

        conn = None
        cursor = None

        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM enrollments")
            conn.commit()

            for row in self.enrollment_list.get_children():
                self.enrollment_list.delete(row)

            messagebox.showinfo("Clear Table", "All enrollment entries were cleared.")

        except mysql.connector.Error as error:
            messagebox.showerror("Database Error", str(error))

        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def delete_selected_enrollments(self):
        selected_rows = self.enrollment_list.selection()
        if not selected_rows:
            messagebox.showwarning(
                "Delete Selected",
                "Please select one or more table rows to delete."
            )
            return

        student_ids = [
            int(self.enrollment_list.item(row)["values"][0])
            for row in selected_rows
        ]

        confirmed = messagebox.askyesno(
            "Delete Selected",
            f"Delete {len(student_ids)} selected enrollment "
            f"{'entry' if len(student_ids) == 1 else 'entries'}?"
        )
        if not confirmed:
            return

        conn = None
        cursor = None

        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            placeholders = ", ".join(["%s"] * len(student_ids))
            cursor.execute(
                f"DELETE FROM enrollments WHERE student_id IN ({placeholders})",
                student_ids
            )
            conn.commit()

            for row in selected_rows:
                self.enrollment_list.delete(row)

            messagebox.showinfo(
                "Delete Selected",
                f"{len(student_ids)} selected "
                f"{'entry was' if len(student_ids) == 1 else 'entries were'} deleted."
            )

        except mysql.connector.Error as error:
            messagebox.showerror("Database Error", str(error))

        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()

    # Ask for the MySQL password if it is not set in Windows
    if DB_CONFIG["password"] is None:
        DB_CONFIG["password"] = simpledialog.askstring(
            "MySQL Database Password",
            f"Enter the MySQL server password for database user "
            f"{DB_CONFIG['user']} (not the portal login password):",
            show="*",
            parent=root
        )

    # Cancel exits the program; an empty password is allowed
    if DB_CONFIG["password"] is None:
        root.destroy()
    else:
        try:
            setup_database()
            root.deiconify()

            app = EnrollmentSystem(root)
            root.mainloop()

        except mysql.connector.Error as error:
            if error.errno == 1045:
                details = (
                    f"MySQL rejected authentication for database user "
                    f"{DB_CONFIG['user']}.\n\n"
                    "Enter that MySQL account's password, not the app's "
                    "portal password (admin / admin123). If you have forgotten "
                    "the MySQL password, use MySQL Installer or your database "
                    "administrator to recover or reset the account."
                )
            else:
                details = str(error)
            messagebox.showerror(
                "Database Error",
                details,
                parent=root
            )
            root.destroy()