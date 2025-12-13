# Tutorial Portal

## This a Project similiar Udemy Online Education Platform

### it has teacher, student, admin, course, lesson, quiz and used ai for search in home page to gether information from this portal about course, teacher, students

## Database Part

---

# Download and Install PostGreSQL Database 15 and python 3.12.5 version

### Download and intall python 3.12.5 version its run perfect with this

### Download `PostgreSQL 15` version

### Install and browse using `pgAdmin` tools

### Set and Easy password for user `postgres` like `1234`

# Create database `tutorial_portal`

### Create user and password same: `tutorial_portal`

### Give super admin permission / priviliages to that user `tutorial_portal`

### From pg admin , software by postgresql under the database `tutorial_portal` restore and select the file `tutorials_portal_202505.backup`

### Adjust every table sequence, from `Sequences` above the table in schema

## Code Part

---

### Install dependencies, go to /code directory

### first upgrade `pip` if you see upgrade notice

### `python -m pip install --upgrade pip`

### `pip install -r requirement.txt`

### now in /code directory, run below command

### `flask --debug --app run.py run -p 5000`

### now browse in localhost:5000

### to run in domain or real ip

### `flask --app run.py run -p 80 -h your_ip_or_domain`

### rename `.env.txt` to `.env` , its enviroment variable required by project

### in app/static/uploads directory all files are uploaded

## OPEN AI Part

---

### `openrouter.ai` go here and get an api key

### put that key in `.env`, variable name is `OPENAI_API_KEY`
