import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import sqlite3
import bcrypt

# --- 1. PAGE CONFIG & DATABASE ---
st.set_page_config(page_title="Finance Hub", page_icon="💰", layout="wide")

def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    conn.commit()
    conn.close()

init_db()

# --- 2. SESSION STATE INITIALIZATION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'transactions' not in st.session_state:
    st.session_state.transactions = pd.DataFrame(columns=["Date", "Type", "Category", "Amount", "Description"])

# --- 3. AUTHENTICATION FUNCTIONS ---
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed)

def sign_up(user, pw):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users VALUES (?, ?)", (user, hash_password(pw)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def login_user(user, pw):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username=?", (user,))
    result = c.fetchone()
    conn.close()
    if result and check_password(pw, result[0]):
        return True
    return False

# --- 4. NAVIGATION LOGIC ---
if not st.session_state.logged_in:
    # --- LOGIN / REGISTER PAGE ---
    st.title("💰 Personal Finance Tracker")
    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                if login_user(u, p):
                    st.session_state.logged_in = True
                    st.session_state.username = u
                    st.rerun()
                else:
                    st.error("Invalid Username or Password")

    with tab2:
        with st.form("register"):
            new_u = st.text_input("Choose Username")
            new_p = st.text_input("Choose Password", type="password")
            if st.form_submit_button("Register"):
                if sign_up(new_u, new_p):
                    st.success("Account created! Please login.")
                else:
                    st.error("Username already taken.")

else:
    # --- THE DASHBOARD (Only shows if logged_in is True) ---
    
    ## --- SIDEBAR ---
    st.sidebar.title(f"Welcome, {st.session_state.username}!")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    st.sidebar.subheader("🎯 Financial Goals")
    monthly_income = st.sidebar.number_input("Monthly Income (Rs)", min_value=0.0, value=500.0)
    savings_target = st.sidebar.number_input("Monthly Savings Target (Rs)", min_value=0.0, value=150.0)

    st.sidebar.subheader("➕ Add Transaction")
    with st.sidebar.form("transaction_form", clear_on_submit=True):
        date = st.date_input("Date", datetime.now())
        t_type = st.selectbox("Type", ["Expense", "Savings"])
        category = st.selectbox("Category", ["Food", "Transport", "Entertainment", "Utilities", "Shopping", "Healthcare", "Bank", "Other"])
        amount = st.number_input("Amount (Rs)", min_value=0.0, step=5.0)
        description = st.text_input("Description (optional)")
        submit = st.form_submit_button("Add Transaction")

        if submit:
            new_row = {"Date": date, "Type": t_type, "Category": category, "Amount": amount, "Description": description}
            st.session_state.transactions = pd.concat([st.session_state.transactions, pd.DataFrame([new_row])], ignore_index=True)
            st.sidebar.success("Transaction added!")

    ## --- MAIN DASHBOARD ---
    st.title("💰 Personal Finance Dashboard")

    # Calculations
    total_expenses = st.session_state.transactions[st.session_state.transactions["Type"] == "Expense"]["Amount"].sum()
    total_savings = st.session_state.transactions[st.session_state.transactions["Type"] == "Savings"]["Amount"].sum()
    remaining_balance = monthly_income - total_expenses

    # Top Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Monthly Income", f"Rs{monthly_income:,.2f}")
    col2.metric("Total Expenses", f"Rs{total_expenses:,.2f}")
    col3.metric("Total Savings", f"Rs{total_savings:,.2f}")
    col4.metric("Remaining Balance", f"Rs{remaining_balance:,.2f}")

    st.divider()

    # Visuals
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔥 Savings Progress")
        fig_progress = px.bar(x=["Savings"], y=[total_savings], range_y=[0, max(savings_target, total_savings) + 50], color_discrete_sequence=['#00CC96'])
        fig_progress.add_hline(y=savings_target, line_dash="dash", line_color="red")
        st.plotly_chart(fig_progress, use_container_width=True)

    with c2:
        st.subheader("📊 Expense Breakdown")
        expense_df = st.session_state.transactions[st.session_state.transactions["Type"] == "Expense"]
        if not expense_df.empty:
            fig_pie = px.pie(expense_df, values='Amount', names='Category', hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No expenses yet.")

    st.subheader("📝 Transaction History")
    st.dataframe(st.session_state.transactions, use_container_width=True)