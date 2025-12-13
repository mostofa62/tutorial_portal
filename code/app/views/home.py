from flask import Blueprint, render_template, redirect, url_for, request, flash,jsonify, current_app
from flask_login import login_user, login_required, current_user, logout_user
from app.models import User, db, Course,Category
from werkzeug.security import generate_password_hash, check_password_hash
from app.middleware import redirect_if_logged_in
import os
from flask_mail import Message
from app import mail

from flask import Blueprint, render_template
from app.middleware import redirect_if_logged_in

home_bp = Blueprint('home_bp', __name__)

@home_bp.route('/')
#@redirect_if_logged_in
def home():
    categories = Category.query.limit(20).all()
    app_name = os.getenv("APP_NAME", "App For All")
    return render_template('home.html', categories=categories,app_name=app_name)



@home_bp.route('/category-course/<int:category_id>')
#@redirect_if_logged_in
def category_course(category_id):
    category = Category.query.get_or_404(category_id)
    courses = Course.query.filter_by(category_id=category.id).limit(20).all()
    return render_template('category-course.html', category=category, courses=courses)

@home_bp.route('/login-all')
@redirect_if_logged_in
def login():
    return render_template('login-all.html')


@home_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')

        if not name or not email or not message:
            flash('Please fill out all required fields.', 'error')
            return redirect(url_for('home_bp.contact'))

        msg = Message(
            subject=f"[Contact Form] {subject}",
            sender=email,
            recipients=["admin@example.com"],  # Replace with admin's email
            body=f"From: {name} <{email}>\n\n{message}"
        )
        try:
            mail.send(msg)
            flash("Your message has been sent successfully!", "success")
        except Exception as e:
            flash("An error occurred while sending the email.", "error")
        return redirect(url_for('home_bp.contact'))

    return render_template('contact.html')


@home_bp.route('/all-courses')
def all_courses():
    page = request.args.get('page', 1, type=int)
    per_page = 10

    courses = Course.query.order_by(Course.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('all-courses.html', courses=courses)


from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate


import re

def extract_sql_query(text):
    # Remove triple backticks and markdown syntax
    code_block = re.search(r"```(?:sql)?(.*?)```", text, re.DOTALL)
    if code_block:
        return code_block.group(1).strip()
    
    # If no backticks, try to extract based on SQL keywords
    lines = text.strip().splitlines()
    sql_lines = [line for line in lines if any(kw in line.upper() for kw in ['SELECT', 'FROM', 'WHERE', 'JOIN', 'GROUP BY', 'ORDER BY', 'LIMIT'])]
    return " ".join(sql_lines).strip() if sql_lines else text.strip()


llm = ChatOpenAI(
    #model="mistralai/mistral-7b-instruct",
    model="gpt-4o-mini",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    default_headers={
        "HTTP-Referer": "http://localhost",
        "X-Title": "AI-SQL-Generator"
    }
)

# Your database schema description
schema_description = """
Database Schema:

- Table: users(id, name, email, password, role, bio, profile_picture, country)
  • role can be 'admin', 'teacher', or 'student'
  • Each user has a unique name and email
  • Teachers create courses; students can enroll in and order courses

- Table: categories(id, name)
  • Represents course categories like 'Math', 'Programming', etc.

- Table: courses(id, title, description, teacher_id, price, language, level, category_id, thumbnail, created_at, updated_at)
  • teacher_id is a foreign key referencing users(id)
  • category_id is a foreign key referencing categories(id)
  • Courses are taught by users with role='teacher'
  • A course belongs to one category and has many lessons

- Table: enrollments(id, student_id, course_id, enrolled_at)
  • student_id is a foreign key referencing users(id)
  • course_id is a foreign key referencing courses(id)
  • A student can only enroll in the same course once
  • Used to track course popularity and student participation

- Table: orders(id, student_id, course_id, amount, payment_status, created_at)
  • student_id is a foreign key referencing users(id)
  • course_id is a foreign key referencing courses(id)
  • payment_status can include values like 'completed', 'pending'
  • Represents financial transactions for course access

- Table: lessons(id, title, content, course_id, ...)
  • course_id is a foreign key referencing courses(id)
  • Each course can have multiple lessons
  • Lessons include instructional content tied to a course
"""



# Prompt template
prompt_template = ChatPromptTemplate.from_template(
    "Given the following PostgreSQL database schema:\n\n{schema}\n\n"
    "First, correct any grammatical mistakes in the user's question if needed.\n"
    "Then, use the corrected question to generate a valid SQL query.\n\n"

    "⚠️ IMPORTANT:\n"
    "- DO NOT use any table named 'student' or 'teacher'. They do NOT exist.\n"
    "- Use the 'users' table and filter by users.role = 'student' or users.role = 'teacher' where appropriate.\n"

    "👉 If the question involves **course details**, the query must SELECT:\n"
    "- courses.id, courses.title, courses.description, courses.price, courses.thumbnail,\n"
    "- the teacher's name (via JOIN with users table where users.role='teacher'),\n"
    "- the category name (via JOIN with categories table)\n\n"

    "👉 If the question involves **enrollment or student counts**,(e.g. 'how many students are enrolled in course X'), they query must include:\n"
    "- COUNT(enrollments.id) AS enrolled_count\n"
    "- Group the query by enrollments.id and JOIN with users and categories accordingly\n"
    "- Always JOIN users ON users.id = enrollments.student_id AND users.role = 'student'\n\n"

    "👉 If the question involves **orders or sales**, include:\n"
    "- orders.id, orders.amount, orders.payment_status, orders.created_at,\n"
    "- the student's name (users.name), and the course title (courses.title)\n"
    "- JOIN users ON users.id = orders.student_id AND users.role = 'student'\n\n"

    "👉 If the question involves **students enrolled in courses** (e.g. 'which students are enrolled in course X'),\n"
    "  the query must SELECT:\n"
    "- users.name AS student_name, users.country AS student_country,\n"
    "- courses.title AS course_title\n"
    "- JOIN enrollments ON enrollments.student_id = users.id AND users.role = 'student'\n"
    "- JOIN courses ON courses.id = enrollments.course_id\n\n"

    "👉 If the question asks about **best selling courses**, **most sold**, or **highest revenue**, write a query that:\n"
    "- Aggregates total sales per course using SUM(orders.amount) AS total_sales\n"
    "- Counts total orders per course using COUNT(orders.id) AS total_orders\n"
    "- Selects course details along with total_sales and total_orders\n"
    "- Orders the results by total_sales DESC or total_orders DESC\n"
    "- Optionally, limits the result to top 1 course\n\n"

    "👉 If the question asks about **top purchasing students** (e.g., 'which student purchased most courses', 'students with highest spending'), write a query that:\n"
    "- Aggregates total purchases per student using COUNT(orders.id) AS total_courses_purchased and/or SUM(orders.amount) AS total_spent\n"
    "- Selects users.name AS student_name, users.country AS student_country\n"
    "- Filters users with role='student'\n"
    "- Orders the results by total_courses_purchased DESC or total_spent DESC\n"
    "- Optionally, limits the results to top 1 or top N students\n\n"


    "👉 If the question involves **aggregates like totals, maximum, minimum, average, or count**, generate a query that:\n"
    "- Uses aggregate functions such as COUNT(), MAX(), MIN(), SUM(), AVG()\n"
    "- Applies the aggregate on appropriate fields and tables based on the user's question context\n"
    "- Includes necessary JOINs if the aggregation depends on related tables (e.g., count of orders per course)\n"
    "- Groups results using GROUP BY if aggregating per entity (e.g., per course, per student)\n"

    "👉 Use ILIKE for fuzzy matching if the question is vague.\n"
    "👉 Only return the SQL query, no explanations or natural language."
    "User's question: '{question}'"
)





# Unsafe query validator
unsafe_keywords = ["DROP", "TRUNCATE", "ALTER", "DELETE", "UPDATE", ";--"]

def validate_query(sql):
    return not any(keyword in sql.upper() for keyword in unsafe_keywords)


def enhance_results_with_thumbnail(parsed_sql: str, rows: list[dict]) -> list[dict]:
    """
    Enhances rows with course thumbnail URL if applicable.
    """
    # Check if SQL involves course thumbnails
    if re.search(r"courses\.thumbnail|thumbnail", parsed_sql, re.IGNORECASE):
        for row in rows:
            thumbnail = row.get("thumbnail")
            if thumbnail:
                thumbnail_path = os.path.join(current_app.static_folder, f'uploads/course_thumb/{thumbnail}')
                if os.path.exists(thumbnail_path):
                    row["thumbnail"] = url_for('static', filename=f'uploads/course_thumb/{thumbnail}')
                else:
                    row["thumbnail"] = None
    return rows
    

@home_bp.route('/ask', methods=["POST"])
def ask_question():
    data = request.get_json()
    user_question = data.get("question", "")

    if not user_question:
        return jsonify({"error": "Missing 'question' in request body reply from AI"}), 200

    try:
        # 1. Generate SQL
        messages = prompt_template.format_messages(
            schema=schema_description,
            question=user_question
        )
        response = llm.invoke(messages)
        #print('response',response)
        raw_generated_sql = response.content.strip()
        parsed_sql = extract_sql_query(raw_generated_sql)

        print('parsed_sql', parsed_sql)

        if not validate_query(parsed_sql):
            return jsonify({
                "error": "Sorry, we can't reply to your conversation due to unsafe query generation.",
                "sql": parsed_sql
            }), 200

        # 2. Run the SQL
        result = db.session.execute(db.text(parsed_sql))
        rows = [dict(row._mapping) for row in result]
        rows = enhance_results_with_thumbnail(parsed_sql, rows)


        print(rows)

        return jsonify({
            "generated_sql_raw": raw_generated_sql,
            "generated_sql_clean": parsed_sql,
            "results": rows
        })

    except Exception as e:
        #return jsonify({"error": str(e)}), 200
        print(e)
        return jsonify({"error": "We are enable to provide any result now by AI"}), 200
