#  I own the FixTrail screens and connect the user interface here.

import sqlite3
from datetime import datetime
import tkinter.messagebox as messagebox

import customtkinter as ctk

import database
import troubleshooting

# I follow the operating system's light or dark appearance setting.
ctk.set_appearance_mode("System")
# I use the standard blue theme for the controls.
ctk.set_default_color_theme("blue")

# I use one helper to make buttons look and behave consistently.
def add_button(parent, text, command, width=220, color=None, pady=8):
    options = {"text": text, "command": command, "width": width}
    if color:
        options["fg_color"] = color
    ctk.CTkButton(parent, **options).pack(pady=pady)

# I keep the screens and signed-in user details in one main window.
class TroubleshootingApp(ctk.CTk):

    # I set up the window and begin with the login screen.
    def __init__(self):
        super().__init__()
        self.title("Smart IT Troubleshooting Assistant")
        self.geometry("720x620")
        self.minsize(620, 520)
        self.current_username = None
        self.current_role = None
        self.show_login()

    # I remove the old screen before drawing the next one.
    def clear_screen(self):
        for widget in self.winfo_children():
            widget.destroy()

    # I create a shared frame and heading for each screen.
    def make_screen(self, title):
        self.clear_screen()
        frame = ctk.CTkFrame(self, corner_radius=12)
        frame.pack(fill="both", expand=True, padx=28, pady=28)
        heading = ctk.CTkLabel(
            frame, text=title, font=ctk.CTkFont(size=24, weight="bold")
        )
        heading.pack(padx=24, pady=(24, 18))
        return frame

    #  I build the login screen and connect it to account checking.

    def show_login(self):
        frame = self.make_screen("Smart IT Troubleshooting Assistant")
        ctk.CTkLabel(frame, text="Username").pack(pady=(8, 4))
        username_entry = ctk.CTkEntry(frame, width=300, placeholder_text="Username")
        username_entry.pack(pady=4)
        ctk.CTkLabel(frame, text="Password").pack(pady=(12, 4))
        password_entry = ctk.CTkEntry(frame, width=300, placeholder_text="Password", show="*")
        password_entry.pack(pady=4)
        status = ctk.CTkLabel(frame, text="")
        status.pack(pady=8)

        # I check the entered details and open the dashboard when they match.
        def login():
            username = username_entry.get().strip()
            password = password_entry.get()
            if not username or not password:
                status.configure(text="Enter both username and password.", text_color="red")
                return
            try:
                account = database.authenticate_user(username, password)
            except sqlite3.Error as error:
                messagebox.showerror("Database error", f"Could not log in: {error}")
                return
            if account is None:
                status.configure(text="Incorrect username or password.", text_color="red")
                return
            self.current_username, self.current_role = account
            self.show_dashboard()

        add_button(frame, "Login", login)
        add_button(frame, "Create Account", self.show_registration, color="gray", pady=6)

    #  I collect account details and pass them to the database module.

    def show_registration(self):
        frame = self.make_screen("Create Account")
        ctk.CTkLabel(frame, text="Username").pack(pady=(8, 4))
        username_entry = ctk.CTkEntry(frame, width=300, placeholder_text="Username")
        username_entry.pack(pady=4)
        ctk.CTkLabel(frame, text="Password").pack(pady=(12, 4))
        password_entry = ctk.CTkEntry(
            frame, width=300, placeholder_text="Password", show="*"
        )
        password_entry.pack(pady=4)

        # I ask the database to validate and save this new account.
        def register():
            try:
                success, result = database.register_user(
                    username_entry.get(), password_entry.get()
                )
            except sqlite3.Error as error:
                messagebox.showerror("Database error", f"Could not create account: {error}")
                return
            if success:
                messagebox.showinfo("Account created", result)
                self.show_login()
            else:
                messagebox.showerror("Registration error", result)

        add_button(frame, "Create Account", register, pady=14)
        add_button(frame, "Back to Login", self.show_login, color="gray", pady=6)

    #  I connect the screens and show admin actions only to admins.

    def show_dashboard(self):
        frame = self.make_screen(f"Welcome, {self.current_username}")
        add_button(frame, "Start Troubleshooting", self.show_troubleshooting, 280, pady=9)
        add_button(frame, "View History", self.show_history, 280, pady=9)
        if self.current_role == "admin":
            add_button(frame, "Add Questions and Problems", self.show_add_rule, 280, pady=9)
            add_button(frame, "Admin Statistics", self.show_statistics, 280, pady=9)
        add_button(frame, "Logout", self.logout, 280, "gray", 9)

    #  I collect answers and pass them to the troubleshooting rules.

    def show_troubleshooting(self):
        frame = self.make_screen("Start Troubleshooting")
        content = ctk.CTkScrollableFrame(frame)
        content.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        category_menu = ctk.CTkOptionMenu(content, values=list(troubleshooting.CATEGORIES),
                                          command=lambda _value: update_questions(), width=300)
        category_menu.pack(pady=(8, 12))
        question_container = ctk.CTkFrame(content, fg_color="transparent")
        question_container.pack(fill="x", expand=True)

        question_labels = []
        answer_menus = []
        custom_rules = []
        # I redraw the questions when the selected category changes.
        def draw_questions():
            for label, answer in zip(question_labels, answer_menus):
                label.destroy()
                answer.destroy()
            question_labels.clear()
            answer_menus.clear()
            category = category_menu.get()
            try:
                custom_rules.clear()
                custom_rules.extend(database.get_custom_rules(category))
            except sqlite3.Error as error:
                messagebox.showerror("Database error", f"Could not load added questions: {error}")
            questions = list(troubleshooting.CATEGORIES[category]["questions"])
            questions += [rule["question"] for rule in custom_rules]
            for question in questions:
                label = ctk.CTkLabel(question_container, text=question, wraplength=560)
                label.pack(padx=20, pady=(8, 3))
                answer = ctk.CTkOptionMenu(
                    question_container,
                    values=["Select an answer", "Yes", "No"],
                    width=220,
                )
                answer.set("Select an answer")
                answer.pack(pady=(0, 5))
                question_labels.append(label)
                answer_menus.append(answer)

        # I refresh the form using the current category.
        def update_questions():
            draw_questions()

        update_questions()

        # I check the answers, run the rules and open the result screen.
        def analyse():
            answers = [answer.get() for answer in answer_menus]
            if any(answer not in ("Yes", "No") for answer in answers):
                messagebox.showerror("Missing answers", "Please answer every question.")
                return
            category = category_menu.get()
            try:
                diagnosis, score, solution = troubleshooting.analyze_answers(
                    category, answers, custom_rules
                )
            except ValueError as error:
                messagebox.showerror("Could not analyse problem", str(error))
                return
            self.show_result(category, answers, diagnosis, score, solution)

        add_button(content, "Analyse Problem", analyse, pady=10)
        add_button(content, "Back to Dashboard", self.show_dashboard, color="gray", pady=(2, 14))

    #  I give admins a simple form for adding a question and its matching fix.
    def show_add_rule(self):
        # I check the role again in case this screen is opened outside the dashboard.
        if self.current_role != "admin":
            messagebox.showerror("Access denied", "Administrator access is required.")
            return

        frame = self.make_screen("Add a Question and Problem")
        content = ctk.CTkScrollableFrame(frame)
        content.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        # I let the admin choose which existing category will show the new question.
        ctk.CTkLabel(content, text="Category").pack(pady=(6, 2))
        category_menu = ctk.CTkOptionMenu(content, values=list(troubleshooting.CATEGORIES))
        category_menu.pack(pady=4)

        # I collect the question, the answer that activates the rule, and its fix.
        fields = []
        for label_text, placeholder in [
            ("Question", "Enter a Yes/No question"),
            ("Likely problem", "Enter the problem name"),
            ("Weight", "Enter a whole number, for example 50"),
            ("Recommended solution", "Enter a simple fix"),
        ]:
            ctk.CTkLabel(content, text=label_text).pack(pady=(7, 2))
            entry = ctk.CTkEntry(content, width=400, placeholder_text=placeholder)
            entry.pack(pady=3)
            fields.append(entry)

        ctk.CTkLabel(content, text="This rule matches when the answer is").pack(pady=(7, 2))
        expected_answer = ctk.CTkOptionMenu(content, values=["Yes", "No"])
        expected_answer.pack(pady=3)

        # I validate the form before saving it to the local database.
        def save_rule():
            question, diagnosis, weight_text, solution = [field.get().strip() for field in fields]
            if not all((question, diagnosis, weight_text, solution)):
                messagebox.showerror("Missing details", "Please complete every field.")
                return
            try:
                weight = int(weight_text)
                if weight < 1 or weight > database.MAX_SQLITE_INTEGER:
                    raise ValueError
            except ValueError:
                messagebox.showerror(
                    "Invalid weight",
                    "Enter a whole number within SQLite's supported integer range.",
                )
                return
            try:
                database.add_custom_rule(
                    category_menu.get(), question, expected_answer.get(),
                    diagnosis, weight, solution,
                )
            except sqlite3.Error as error:
                messagebox.showerror("Database error", f"Could not save the question: {error}")
                return
            messagebox.showinfo("Question added", "The new question and problem were saved.")
            self.show_dashboard()

        add_button(content, "Save Question", save_rule, pady=10)
        add_button(content, "Back to Dashboard", self.show_dashboard, color="gray", pady=(2, 12))

    #  I show the result and ask whether the suggested fix worked.

    def show_result(self, category, answers, diagnosis, score, solution):
        frame = self.make_screen("Troubleshooting Result")
        result_items = [
            ("Category", category),
            ("Likely Problem", diagnosis),
            ("Decision Score", f"{score:.2f}%"),
            ("Recommended Solution", solution),
        ]
        for title, value in result_items:
            ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(weight="bold")).pack(pady=(7, 1))
            ctk.CTkLabel(frame, text=value, wraplength=560, justify="center").pack(pady=(0, 5))
        ctk.CTkLabel(frame, text="Did this solution fix the problem?").pack(pady=(8, 3))
        add_button(frame, "Yes, it is fixed", lambda: self.record_outcome(
            "Resolved", category, answers, diagnosis, score, solution), pady=4)
        add_button(frame, "No, it did not fix it", lambda: self.record_outcome(
            "Unresolved", category, answers, diagnosis, score, solution), pady=4)

    #  I save the user's outcome and choose the next screen.

    def record_outcome(self, outcome, category, answers, diagnosis, score, solution):
        try:
            database.save_history(
                self.current_username, category, diagnosis, score, solution, outcome
            )
        except sqlite3.Error as error:
            messagebox.showerror("Database error", f"Could not save the result: {error}")
            return
        if outcome == "Unresolved":
            self.show_passport(category, answers, diagnosis, score, solution)
        else:
            self.show_completion("Issue resolved", "The successful fix was saved to your history.")

    #  I prepare a summary the user can share with IT support.

    def show_passport(self, category, answers, diagnosis, score, solution):
        frame = self.make_screen("FixTrail Escalation Passport")
        questions = troubleshooting.CATEGORIES[category]["questions"]
        try:
            custom_rules = database.get_custom_rules(category)
        except sqlite3.Error:
            custom_rules = []
        questions = questions + [rule["question"] for rule in custom_rules]
        lines = ["IT SUPPORT HANDOVER", f"Date: {datetime.now():%Y-%m-%d %H:%M}",
                 f"User: {self.current_username}", f"Category: {category}",
                 f"Likely problem: {diagnosis}", f"Decision Score: {score:.2f}%",
                 f"Fix attempted: {solution}", "Outcome: Still unresolved", "", "Answers:"]
        lines.extend(f"- {question} {answer}" for question, answer in zip(questions, answers))
        report = ctk.CTkTextbox(frame, wrap="word")
        report.pack(fill="both", expand=True, padx=18, pady=10)
        report.insert("end", "\n".join(lines))
        report.configure(state="disabled")
        ctk.CTkLabel(frame, text="Show this summary when contacting IT support.").pack(pady=3)
        add_button(frame, "Dashboard", self.show_dashboard, pady=(3, 10))

    #  I confirm the session and offer the next navigation choices.

    def show_completion(self, title, message):
        frame = self.make_screen(title)
        ctk.CTkLabel(frame, text=message, wraplength=520).pack(pady=18)
        add_button(frame, "Try Another Problem", self.show_troubleshooting, pady=5)
        add_button(frame, "Dashboard", self.show_dashboard, pady=5)

    #  I show the signed-in user's saved sessions.

    def show_history(self):
        frame = self.make_screen("Troubleshooting History")
        try:
            records = database.get_user_history(self.current_username)
        except sqlite3.Error as error:
            messagebox.showerror("Database error", f"Could not load history: {error}")
            return
        history_text = ctk.CTkTextbox(frame, width=600, height=360, wrap="word")
        history_text.pack(fill="both", expand=True, padx=20, pady=8)
        if not records:
            history_text.insert("end", "No troubleshooting history yet.")
        for created_at, category, diagnosis, score, solution, outcome in records:
            history_text.insert(
                "end",
                f"Date: {created_at}\n"
                f"Category: {category}\n"
                f"Likely Problem: {diagnosis}\n"
                f"Decision Score: {score:.2f}%\n"
                f"Recommended Solution: {solution}\n"
                f"Outcome: {outcome}\n"
                f"{'-' * 48}\n",
            )
        history_text.configure(state="disabled")
        add_button(frame, "Back to Dashboard", self.show_dashboard, 240, pady=10)

    #  I show the two totals available to an administrator.

    def show_statistics(self):
        # I check the administrator role before reading these totals.
        if self.current_role != "admin":
            messagebox.showerror("Access denied", "Administrator access is required.")
            return
        frame = self.make_screen("Admin Statistics")
        try:
            users, sessions = database.get_admin_statistics()
        except sqlite3.Error as error:
            messagebox.showerror("Database error", f"Could not load statistics: {error}")
            return
        ctk.CTkLabel(frame, text=f"Total registered users: {users}").pack(pady=12)
        ctk.CTkLabel(frame, text=f"Total troubleshooting sessions: {sessions}").pack(pady=12)
        add_button(frame, "Back to Dashboard", self.show_dashboard, 240, pady=18)

    #I clear the saved account details when the user logs out.

    def logout(self):
        self.current_username = None
        self.current_role = None
        self.show_login()