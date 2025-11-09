from flask import Flask, render_template, request, redirect, url_for, session, send_file, jsonify
from groq import Groq
import csv
import datetime
import os
import io
from dotenv import load_dotenv

# ✅ Load environment variables from .env (for local use)
load_dotenv()

# ✅ Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# ✅ Configure upload folder
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ✅ Define file paths
REPORT_FILE = 'reports.csv'
USERS_FILE = 'users.csv'
ADMIN_FILE = 'admin.csv'

# ✅ Load Groq API key
groq_key = os.getenv("GROQ_API_KEY")

# ✅ Debug print (visible in Render logs)
if not groq_key:
    print("❌ ERROR: GROQ_API_KEY not found in environment variables! Please set it on Render.")
else:
    print("✅ GROQ_API_KEY loaded successfully.")

# ✅ Initialize Groq client safely
client = Groq(api_key=groq_key)


# ------------------------- STATIC DISEASE DATA ------------------------- #
disease_data = {
    "cold": "Paracetamol, Cetirizine",
    "fever": "Dolo 650, Crocin",
    "headache": "Saridon, Disprin",
    "diabetes": "Metformin, Glimepiride",
    "asthma": "Inhaler, Montelukast",
    "cough": "Benadryl, Ascoril",
    "vomiting": "Ondansetron, Domperidone",
    "diarrhea": "ORS, Loperamide",
    "high bp": "Amlodipine, Telmisartan",
    "acidity": "Pantoprazole, Rantac",
    "back pain": "Diclofenac, Flexon",
    "joint pain": "Ibuprofen, Calcium Tablets",
    "skin allergy": "Cetirizine, Calamine Lotion",
    "eye irritation": "Ciplox Eye Drops, Refresh Tears",
    "ear pain": "Ciplox Ear Drops, Paracetamol",
    "toothache": "Combiflam, Clove Oil",
    "menstrual pain": "Meftal Spas, Drotin",
    "constipation": "Lactulose Syrup, Isabgol"
}

# ------------------------- GROQ CHATBOT ------------------------- #

load_dotenv()  # Loads variables from .env file

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """
You are E-ASHA, a friendly digital assistant for ASHA workers in rural India. 
Your purpose is to help ASHA workers navigate the E-ASHA web app and provide safe medical guidance.

You can help with these main areas:

1. **Website Navigation Help**
   - **Login Process**: Guide users to select role (ASHA Worker/Admin), enter username and password
   - **Adding Patients**: 
     * Go to Home page → Enter Patient Name, Age, Mobile Number → Click Next
     * Select disease from dropdown (18 diseases available including Cold, Fever, Headache, Diabetes, Asthma, etc.)
     * Get medicine suggestions automatically
   - **Patient History**: 
     * Access via navbar → Search by patient name or mobile number
     * View all previous patient records with dates
   - **Dashboard**: 
     * Check daily patient counts by selecting specific dates
     * View your performance statistics
   - **Sidebar Menu**: Profile, Help, Emergency Contact, Logout
   - **Admin Features** (for admins): Manage ASHA workers, view all reports, disease trends graphs

2. **Disease & Medicine Help**
   Available diseases and medicines in the system:
   - Cold (सर्दी) → Paracetamol, Cetirizine
   - Fever (ताप) → Dolo 650, Crocin
   - Headache (डोकेदुखी) → Saridon, Disprin
   - Diabetes (मधुमेह) → Metformin, Glimepiride
   - Asthma (दमा) → Inhaler, Montelukast
   - Cough (खोकला) → Benadryl, Ascoril
   - Vomiting (ओकाऱ्या) → Ondansetron, Domperidone
   - Diarrhea (जुलाब) → ORS, Loperamide
   - High BP (उच्च रक्तदाब) → Amlodipine, Telmisartan
   - Acidity (अम्लपित्त) → Pantoprazole, Rantac
   - Back Pain (पाठीचा त्रास) → Diclofenac, Flexon
   - Joint Pain (सांधेदुखी) → Ibuprofen, Calcium Tablets
   - Skin Allergy (त्वचेची अ‍ॅलर्जी) → Cetirizine, Calamine Lotion
   - Eye Irritation (डोळ्यांची जळजळ) → Ciplox Eye Drops, Refresh Tears
   - Ear Pain (कानदुखी) → Ciplox Ear Drops, Paracetamol
   - Toothache (दात दुखणे) → Combiflam, Clove Oil
   - Menstrual Pain (मासिक पाळीचा त्रास) → Meftal Spas, Drotin
   - Constipation (मळावष्टंभ) → Lactulose Syrup, Isabgol

   **Always remind**: "Consult a doctor for serious problems or if symptoms persist."

3. **Emergency Contacts**
   - Ambulance Service: 108
   - ASHA Helpline: 1800-180-1104
   - Nearest PHC: Village Health Center, +91 9876543210
   - Women Helpline: 1091
   - Child Helpline: 1098

4. **Common Questions & Quick Answers**
   - **Adding Patient**: Home → Enter details → Select disease → Get medicine
   - **Patient History**: Navbar → Patient History → Search by name/mobile
   - **Dashboard**: Navbar → Dashboard → Select date for patient count
   - **Emergency Help**: Available in sidebar or ask me directly

**Response Format Examples:**

For "How to add patient?":
"To add a new patient (रोगी जोड़ना):

1. Go to Home page
2. Enter Patient Name, Age, Mobile Number  
3. Click Next button
4. Select disease from dropdown (18 options available)
5. Get automatic medicine suggestions

⚠️ Always consult a doctor for serious problems."

For medicine queries:
"For [Disease Name]: [Medicine Names]
Available in E-ASHA system under disease selection.
⚠️ Consult a doctor if symptoms persist."

**Rules:**
- Keep answers simple, clear, and helpful for rural ASHA workers
- Use primarily English with Hindi terms in brackets for clarity
- Always prioritize patient safety - recommend doctor consultation for serious cases
- Guide users step-by-step through website features
- Be encouraging and supportive in your responses
- Use proper formatting with numbered steps and bullet points
- Keep responses concise but complete
- Always end medical advice with safety reminder
- IMPORTANT: Put each numbered step on a separate line with proper line breaks
- Format numbered lists with clear spacing between each point
"""


def chat_with_groq(prompt):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
    )
    return response.choices[0].message.content.strip()

@app.route("/chat")
def chat_home():
    return render_template("chat_widget.html")


@app.route("/ask", methods=["POST"])
def chat_ask():
    try:
        user_input = request.json.get("message")
        if not user_input:
            return jsonify({"reply": "Please type a message."})
        reply = chat_with_groq(user_input)
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"}), 500


# ------------------------- ROLE SELECTION PAGE ------------------------- #
@app.route('/')
@app.route('/role')
def role_select():
    return render_template('role_select.html')

# ------------------------- LOGIN ------------------------- #
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ''
    if request.method == 'POST':
        entered_username = request.form['username']
        entered_password = request.form['password']
        try:
            with open(USERS_FILE, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row['username'] == entered_username and row['password'] == entered_password:
                        session['logged_in'] = True
                        session['username'] = row['username']
                        session['user'] = {
                            'id': row['username'],
                            'name': row.get('name', ''),
                            'mobile': row.get('mobile', ''),
                            'location': row.get('location', ''),
                            'photo': row.get('photo', 'default.jpg')
                        }
                        return redirect(url_for('page1'))
                error = "Invalid username or password."
        except FileNotFoundError:
            error = "User database not found."
    return render_template('login.html', error=error)

# ------------------------- LOGOUT ------------------------- #
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('role_select'))

# ------------------------- PAGE 1 ------------------------- #
@app.route('/page1', methods=['GET', 'POST'])
def page1():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        session['name'] = request.form['name']
        session['age'] = request.form['age']
        session['mobile'] = request.form['mobile']
        return redirect(url_for('select'))
    return render_template('page1.html')

# ------------------------- SELECT DISEASE ------------------------- #
@app.route('/select', methods=['GET', 'POST'])
def select():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    name = session.get('name')
    age = session.get('age')
    mobile = session.get('mobile')
    username = session.get('username')
    medicine = ''
    error = ''

    if not name or not age or not mobile:
        return redirect(url_for('page1'))

    if request.method == 'POST':
        disease = request.form.get('disease')
        if not disease:
            error = "\u26a0\ufe0f Please select a disease."
        else:
            medicine = disease_data.get(disease.lower(), "No medicine found")
            date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            with open(REPORT_FILE, 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([username, name, age, mobile, disease, medicine, date])

    return render_template('select.html', name=name, age=age, mobile=mobile, medicine=medicine, error=error)

# ------------------------- PATIENT HISTORY ------------------------- #
@app.route('/history')
def history():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    query = request.args.get('query', '').lower()
    username = session.get('username')
    reports = []

    try:
        with open(REPORT_FILE, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                if row[0] == username:
                    if query:
                        if query in row[1].lower() or query in row[3]:
                            reports.append(row)
                    else:
                        reports.append(row)
    except FileNotFoundError:
        pass

    return render_template("history.html", reports=reports)

# ------------------------- DASHBOARD ------------------------- #
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    selected_date = datetime.datetime.now().strftime('%Y-%m-%d')
    if request.method == 'POST':
        selected_date = request.form.get('date', selected_date)

    total_today = 0
    username = session.get('username')

    try:
        with open(REPORT_FILE, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                if row[0] == username and row[-1].startswith(selected_date):
                    total_today += 1
    except FileNotFoundError:
        pass

    try:
        formatted_date = datetime.datetime.strptime(selected_date, '%Y-%m-%d').strftime('%-d %B %Y')
    except:
        formatted_date = selected_date

    return render_template('dashboard.html', total_today=total_today, formatted_date=formatted_date, selected_date=selected_date)

# ------------------------- PROFILE PAGE ------------------------- #
@app.route('/profile')
def profile():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('profile.html', user=session.get('user', {}))

# ------------------------- Emergency ------------------------- #
@app.route('/emergency')
def emergency_contact():
    return render_template('emergency_contact.html')


# ------------------------- ADMIN LOGIN ------------------------- #
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            with open(ADMIN_FILE, newline='') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row['username'] == username and row['password'] == password:
                        session['admin'] = username
                        return redirect(url_for('home_admin'))
            error = 'Invalid username or password'
        except FileNotFoundError:
            error = 'Admin database not found.'
    return render_template('admin_login.html', error=error)

# ------------------------- ADMIN HOME ------------------------- #
@app.route('/home_admin')
def home_admin():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    return render_template('home_admin.html')

# ------------------------- MANAGE ASHA WORKERS ------------------------- #
@app.route('/manage_asha')
def manage_asha():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    query = request.args.get('query', '').lower()
    users = []

    try:
        with open(USERS_FILE, newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if query:
                    if query in row['username'].lower() or query in row['name'].lower() or query in row['mobile'] or query in row['location'].lower():
                        users.append(row)
                else:
                    users.append(row)
    except FileNotFoundError:
        pass

    return render_template('manage_asha.html', users=users)
# ------------------------- ADD ASHA WORKER ------------------------- #
@app.route('/add_asha', methods=['GET', 'POST'])
def add_asha():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    error = None  # for error messages

    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        name = request.form['name'].strip()
        mobile = request.form['mobile'].strip()
        location = request.form['location'].strip()
        image = request.files.get('photo')

        # ✅ Check if username already exists
        if os.path.isfile(USERS_FILE):
            with open(USERS_FILE, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row['username'].lower() == username.lower():
                        error = f"⚠️ Username '{username}' is already taken. Please choose another."
                        return render_template(
                            'add_asha.html',
                            error=error,
                            username=username,
                            name=name,
                            mobile=mobile,
                            location=location
                        )

        # ✅ Save photo
        photo_filename = "default.jpg"
        if image and image.filename:
            photo_filename = f"{username}_{image.filename}"
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))

        # ✅ Save new user
        new_user = {
            'username': username,
            'password': password,
            'name': name,
            'mobile': mobile,
            'location': location,
            'photo': photo_filename
        }

        file_exists = os.path.isfile(USERS_FILE)
        with open(USERS_FILE, 'a', newline='') as file:
            fieldnames = ['username', 'password', 'name', 'mobile', 'location', 'photo']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(new_user)

        return redirect(url_for('manage_asha'))

    # Render page with error if any
    return render_template('add_asha.html', error=error)


# ------------------------- Delet ASHA WORKER ------------------------- #

@app.route('/delete_asha/<username>')
def delete_asha(username):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    users = []
    try:
        with open(USERS_FILE, 'r') as file:
            reader = csv.DictReader(file)
            users = list(reader)

        users = [user for user in users if user['username'] != username]

        with open(USERS_FILE, 'w', newline='') as file:
            fieldnames = ['username', 'password', 'name', 'mobile', 'location', 'photo']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(users)

    except FileNotFoundError:
        pass

    return redirect(url_for('manage_asha'))


# ------------------------- edit ASHA WORKER ------------------------- #

@app.route('/edit_asha/<username>', methods=['GET', 'POST'])
def edit_asha(username):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    users = []
    user_data = None

    try:
        with open(USERS_FILE, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['username'] == username:
                    user_data = row
                users.append(row)
    except FileNotFoundError:
        return "User data not found", 404

    if not user_data:
        return "User not found", 404

    if request.method == 'POST':
        password = request.form['password']
        name = request.form['name']
        mobile = request.form['mobile']
        location = request.form['location']
        new_photo = request.files.get('photo')

        photo_filename = user_data['photo']
        if new_photo and new_photo.filename:
            old_path = os.path.join(app.config['UPLOAD_FOLDER'], photo_filename)
            if os.path.exists(old_path) and photo_filename != 'default.jpg':
                os.remove(old_path)
            photo_filename = f"{username}_{new_photo.filename}"
            new_photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))

        for row in users:
            if row['username'] == username:
                row['password'] = password
                row['name'] = name
                row['mobile'] = mobile
                row['location'] = location
                row['photo'] = photo_filename

        with open(USERS_FILE, 'w', newline='') as file:
            fieldnames = ['username', 'password', 'name', 'mobile', 'location', 'photo']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(users)

        return redirect(url_for('manage_asha'))

    return render_template('edit_asha.html', user=user_data)

# ------------------------- allview ------------------------- #
@app.route('/allview')
def allview():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    query = request.args.get('query', '').lower()
    filter_user = request.args.get('user_id', '')

    # ✅ Date filters
    from_date = request.args.get("from_date", "")
    to_date = request.args.get("to_date", "")

    reports = []
    unique_users = set()
    unique_dates = set()

    try:
        with open(REPORT_FILE, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                username, name, age, mobile, disease, medicine, date = row
                unique_users.add(username)
                unique_dates.add(date.split()[0])

                        # ✅ Collect usernames from users.csv (so new ASHAs also appear)
        if os.path.isfile(USERS_FILE):
            with open(USERS_FILE, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    unique_users.add(row['username'])

        # Re-read for filtered reports
        with open(REPORT_FILE, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                username, name, age, mobile, disease, medicine, date = row
                report_date = date.split()[0]  # "YYYY-MM-DD" part

                # ✅ Apply filters
                if (not query or query in name.lower() or query in mobile) and \
                   (not filter_user or filter_user == username) and \
                   (not from_date or report_date >= from_date) and \
                   (not to_date or report_date <= to_date):
                    reports.append(row)

    except FileNotFoundError:
        pass

    return render_template(
        'allview.html',
        reports=reports,
        users=sorted(unique_users),
        dates=sorted(unique_dates),
        selected_user=filter_user,
        from_date=from_date,       # ✅ Pass back to template
        to_date=to_date,           # ✅ Pass back to template
        query=query,
        total_asha=len(set([r[0] for r in reports])),  # ASHA users in filtered reports
        total_reports=len(reports)                     # Filtered report count
    )

# ------------------------- export asha worker ------------------------- #
from flask import Flask, Response

@app.route('/export')
def export_users():
    output = io.StringIO()
    writer = csv.writer(output)

    # Read and write users.csv without the password column
    with open('users.csv', newline='') as f:
        reader = csv.reader(f)
        header = next(reader)
        
        # Find the index of the password column
        try:
            password_index = header.index('password')
        except ValueError:
            return "Password column not found", 400

        # Write new header without 'password'
        filtered_header = [col for i, col in enumerate(header) if i != password_index]
        writer.writerow(filtered_header)

        # Write filtered rows
        for row in reader:
            filtered_row = [col for i, col in enumerate(row) if i != password_index]
            writer.writerow(filtered_row)

    output.seek(0)

    return Response(
        output,
        mimetype='text/csv',
        headers={
            "Content-Disposition": "attachment; filename=asha_users.csv"
        }
    )

# ------------------------- export report ------------------------- #
from flask import Response
import csv

@app.route('/export_reports')
def export_reports():
    def generate():
        with open('reports.csv', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader)
            yield ','.join(header) + '\n'
            for row in reader:
                yield ','.join(row) + '\n'

    return Response(
        generate(),
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment;filename=all_patient_reports.csv"}
    )

# ------------------------- graph ------------------------- #
from collections import defaultdict
from flask import render_template, request

@app.route('/disease_graph', methods=['GET'])
def disease_graph():
    selected_user = request.args.get('user_id', '')
    selected_date = request.args.get('date', '')

    disease_counts = defaultdict(int)
    users = set()
    dates = set()

    # ✅ Always include all ASHA IDs from users.csv
    try:
        with open('users.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                users.add(row['username'])
    except FileNotFoundError:
        pass

    # ✅ Collect dates + disease counts from reports.csv
    try:
        with open(REPORT_FILE, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                username, name, age, mobile, disease, medicine, timestamp = row
                date_only = timestamp.split()[0]

                dates.add(date_only)

                if (not selected_user or selected_user == username) and \
                   (not selected_date or selected_date == date_only):
                    disease_counts[disease.lower()] += 1
    except FileNotFoundError:
        pass

    # ✅ Sort diseases by frequency
    sorted_diseases = sorted(disease_counts.items(), key=lambda x: x[1], reverse=True)
    labels = [d[0].title() for d in sorted_diseases]
    values = [d[1] for d in sorted_diseases]

    return render_template(
        'disease_graph.html',
        labels=labels,
        values=values,
        users=sorted(users),      # ✅ now includes ALL asha IDs from users.csv
        dates=sorted(dates),
        selected_user=selected_user,
        selected_date=selected_date
    )


# ------------------------- admin profile ------------------------- #
@app.route('/admin_profile')
def admin_profile():
    if 'admin' not in session:
        return redirect('/admin_login')  # ✅ Correct session key

    admin_username = session['admin']
    with open('admin.csv', 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['username'] == admin_username:
                return render_template(
                    'admin_profile.html',
                    admin_id=row['username'],
                    name=row['name'],
                    mobile=row['mobile'],
                    location=row['location'],
                    photo=row.get('photo', 'default_user.png')
                )
    return "Admin not found", 404


# ------------------------- mobile ------------------------- #
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)