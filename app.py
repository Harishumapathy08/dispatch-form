import streamlit as st
import pandas as pd
import os
from datetime import datetime
from twilio.rest import Client

st.set_page_config(layout="wide")

DATA_FILE = 'dispatch_data.xlsx'  # Save/load Excel file in root folder
# Removed os.makedirs since no folder creation needed

columns = [
    "S.No", "INV DATE", "INV No", "CUSTOMER", "SALES PERSON", "SALE TYPE", "PRODUCT", "MODEL",
    "COLOUR", "QTY", "PLACE", "DESP DATE", "DESPATCH TIME", "TRANSPORT", "LR NUMBER",
    "VEHICLE NUMBER", "VEHICLE SIZE", "FREIGHT AMT", "PAYMENT TERMS", "PAYMENT STATUS",
    "REMARKS", "ACKN STATUS", "ACKN SENT DATE", "ACKN SENT BY", "Customer Number"
]

def load_data():
    if os.path.exists(DATA_FILE):
        dtypes = {
            "S.No": int,
            "INV No": int,
            "CUSTOMER": str,
            "SALES PERSON": str,
            "SALE TYPE": str,
            "PRODUCT": str,
            "MODEL": str,
            "COLOUR": str,
            "QTY": int,
            "PLACE": str,
            "TRANSPORT": str,
            "LR NUMBER": str,         # Changed to string (can have letters and numbers)
            "VEHICLE NUMBER": str,    # Changed to string
            "VEHICLE SIZE": float,
            "FREIGHT AMT": float,
            "PAYMENT TERMS": str,
            "PAYMENT STATUS": str,
            "REMARKS": str,
            "ACKN STATUS": str,
            "ACKN SENT BY": str,
            "Customer Number": str,
        }
        df = pd.read_excel(DATA_FILE, dtype=dtypes, parse_dates=["INV DATE", "DESP DATE", "ACKN SENT DATE"])
        return df
    else:
        return pd.DataFrame(columns=columns)

def save_data(df):
    df.to_excel(DATA_FILE, index=False)

def send_whatsapp_message(to_number, product, quantity, date):
    try:
        client = Client(st.secrets["twilio"]["account_sid"], st.secrets["twilio"]["auth_token"])
        message = client.messages.create(
            body=f"🚚 Hello, your dispatch is ready!\n\n📦 Product: {product}\n🔢 Quantity: {quantity}\n📅 Date: {date}\n✅ Thank you for your business!",
            from_=st.secrets["twilio"]["from_whatsapp"],
            to=f"whatsapp:{to_number}"
        )
        st.success("WhatsApp message sent successfully!")
    except Exception as e:
        st.error(f"Failed to send WhatsApp message: {e}")

st.title("🚚 Dispatch Entry System")

df = load_data()

# Summary
st.subheader("📊 Summary Dashboard")
col1, col2, col3 = st.columns(3)
col1.metric("Total Dispatches", len(df))
col2.metric("Total Quantity", df["QTY"].sum() if not df.empty else 0)
col3.metric("Total Freight", f"₹{df['FREIGHT AMT'].sum() if not df.empty else 0}")

# Form for new entry
with st.form("entry_form"):
    st.subheader("➕ New Dispatch Entry")
    c1, c2 = st.columns(2)
    inv_date = c1.date_input("INV DATE")
    inv_no = c2.number_input("INV No", min_value=0, step=1, format="%d")
    customer = c1.text_input("CUSTOMER")
    salesperson = c2.text_input("SALES PERSON")
    saletype = c1.selectbox("SALE TYPE", ["cash", "credit"])
    product = c2.text_input("PRODUCT")
    model = c1.text_input("MODEL")
    color = c2.text_input("COLOUR")
    qty = c1.number_input("QTY", min_value=0, step=1)
    place = c2.text_input("PLACE")
    desp_date = c1.date_input("DESP DATE")
    time = c2.time_input("DESPATCH TIME")
    transport = c1.text_input("TRANSPORT")
    lr = c2.text_input("LR NUMBER")              # Text input for LR NUMBER
    vehicle = c1.text_input("VEHICLE NUMBER")   # Text input for VEHICLE NUMBER
    size = c2.number_input("VEHICLE SIZE (feet)", min_value=0.0, step=0.01, format="%.2f")
    freight = c1.number_input("FREIGHT AMT", min_value=0.0, step=0.01, format="%.2f")
    payment_terms = c2.text_input("PAYMENT TERMS")
    payment_status = c1.selectbox("PAYMENT STATUS", ["paid", "pending"])
    remarks = c2.text_input("REMARKS")
    ack_status = c1.selectbox("ACKN STATUS", ["ok", "pending"])
    ack_date = c2.date_input("ACKN SENT DATE")
    ack_by = c1.text_input("ACKN SENT BY")
    customer_number = c2.text_input("Customer Number (with country code)")

    submitted = st.form_submit_button("Submit")
    if submitted:
        if not customer_number.startswith("+") or len(customer_number) < 10:
            st.error("Customer Number must start with '+' and include country code.")
        else:
            row = [
                len(df) + 1, inv_date, inv_no, customer, salesperson, saletype, product, model, color, qty,
                place, desp_date, time.strftime('%H:%M'), transport, lr, vehicle, size, freight,
                payment_terms, payment_status, remarks, ack_status, ack_date, ack_by, customer_number
            ]
            df.loc[len(df)] = row
            save_data(df)
            send_whatsapp_message(customer_number, product, qty, desp_date.strftime('%Y-%m-%d'))
            st.success("Entry added successfully!")

            df = load_data()

# Delete option
st.subheader("🗑️ Delete Dispatch Entry")
if not df.empty:
    delete_sno = st.selectbox("Select S.No to Delete", df["S.No"].tolist())
    if st.button("Delete Selected Entry"):
        df = df[df["S.No"] != delete_sno].reset_index(drop=True)
        df["S.No"] = range(1, len(df) + 1)
        save_data(df)
        st.success(f"Entry with S.No {delete_sno} deleted successfully!")
        st.experimental_rerun()
else:
    st.info("No records available to delete.")

# Show dispatch records table
st.subheader("📋 Dispatch Records")
st.dataframe(df)

# Download Excel
if not df.empty:
    with open(DATA_FILE, "rb") as f:
        st.download_button("⬇️ Download Excel", f, file_name="dispatch_data.xlsx")
