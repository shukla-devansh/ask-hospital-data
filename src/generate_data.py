# Creates data/hospital.db with fake (synthetic) hospital data.
# No real patient data is used anywhere in this project.

import os
import random
import sqlite3
from datetime import date, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "hospital.db")

NUM_PATIENTS = 500
NUM_ADMISSIONS = 2000

CITIES = ["Delhi", "Mumbai", "Bangalore", "Chennai", "Kolkata", "Hyderabad", "Pune", "Jaipur"]

# each department has its own diagnoses, a typical bill and a readmission chance
DEPARTMENTS = {
    "Cardiology": (["Heart Failure", "Arrhythmia", "Chest Pain", "Hypertension"], 90000, 0.20),
    "Orthopedics": (["Fracture", "Knee Replacement", "Back Pain"], 70000, 0.08),
    "Neurology": (["Stroke", "Migraine", "Epilepsy"], 80000, 0.15),
    "Pediatrics": (["Asthma", "Fever", "Bronchitis"], 20000, 0.06),
    "Oncology": (["Breast Cancer", "Lung Cancer", "Leukemia"], 150000, 0.25),
    "General Medicine": (["Diabetes", "Pneumonia", "Infection", "Dehydration"], 25000, 0.12),
    "Emergency": (["Trauma", "Poisoning", "Burns"], 40000, 0.10),
}

FIRST_NAMES = ["Amit", "Priya", "Rahul", "Sneha", "Vikram", "Anjali", "Rohan", "Kavya",
               "Arjun", "Neha", "Karan", "Pooja", "Sanjay", "Meera", "Aditya", "Riya"]
LAST_NAMES = ["Sharma", "Verma", "Gupta", "Iyer", "Reddy", "Patel", "Singh", "Nair", "Rao", "Das"]


def create_tables(conn):
    conn.executescript("""
        DROP TABLE IF EXISTS admissions;
        DROP TABLE IF EXISTS doctors;
        DROP TABLE IF EXISTS departments;
        DROP TABLE IF EXISTS patients;

        CREATE TABLE patients (
            id INTEGER PRIMARY KEY,
            age INTEGER,
            gender TEXT,
            city TEXT
        );

        CREATE TABLE departments (
            id INTEGER PRIMARY KEY,
            name TEXT
        );

        CREATE TABLE doctors (
            id INTEGER PRIMARY KEY,
            name TEXT,
            department_id INTEGER REFERENCES departments(id)
        );

        CREATE TABLE admissions (
            id INTEGER PRIMARY KEY,
            patient_id INTEGER REFERENCES patients(id),
            doctor_id INTEGER REFERENCES doctors(id),
            department_id INTEGER REFERENCES departments(id),
            admit_date TEXT,       -- format YYYY-MM-DD
            discharge_date TEXT,   -- format YYYY-MM-DD
            diagnosis TEXT,
            readmitted INTEGER,    -- 1 = patient came back within 30 days, 0 = no
            bill_amount REAL       -- in rupees
        );
    """)


def create_database(path=DB_PATH):
    random.seed(42)  # same data every time we run it

    conn = sqlite3.connect(path)
    create_tables(conn)

    for i in range(1, NUM_PATIENTS + 1):
        age = random.randint(1, 90)
        gender = random.choice(["Male", "Female"])
        city = random.choice(CITIES)
        conn.execute("INSERT INTO patients VALUES (?, ?, ?, ?)", (i, age, gender, city))

    # 3 doctors per department
    doctor_id = 1
    doctors_by_dept = {}
    for dept_id, dept_name in enumerate(DEPARTMENTS, start=1):
        conn.execute("INSERT INTO departments VALUES (?, ?)", (dept_id, dept_name))
        doctors_by_dept[dept_id] = []
        for _ in range(3):
            name = "Dr. " + random.choice(FIRST_NAMES) + " " + random.choice(LAST_NAMES)
            conn.execute("INSERT INTO doctors VALUES (?, ?, ?)", (doctor_id, name, dept_id))
            doctors_by_dept[dept_id].append(doctor_id)
            doctor_id += 1

    # admissions spread over the last 12 months
    today = date.today()
    dept_names = list(DEPARTMENTS)
    for i in range(1, NUM_ADMISSIONS + 1):
        dept_id = random.randint(1, len(dept_names))
        diagnoses, avg_bill, readmit_chance = DEPARTMENTS[dept_names[dept_id - 1]]

        admit = today - timedelta(days=random.randint(1, 365))
        stay = random.randint(1, 14)
        discharge = admit + timedelta(days=stay)
        if discharge > today:
            discharge = today

        bill = round(avg_bill * random.uniform(0.5, 1.5) + stay * 2000, 2)
        readmitted = 1 if random.random() < readmit_chance else 0

        conn.execute(
            "INSERT INTO admissions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (i, random.randint(1, NUM_PATIENTS), random.choice(doctors_by_dept[dept_id]), dept_id,
             admit.isoformat(), discharge.isoformat(), random.choice(diagnoses), readmitted, bill),
        )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_database()
    print("Created", os.path.abspath(DB_PATH))
