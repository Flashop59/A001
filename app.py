import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime

# Google Sheets authentication
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# Open the Google Sheets document
spreadsheet = client.open("OrbitInventory")

# Access specific sheets
items_sheet = spreadsheet.worksheet("Items Database")
transactions_sheet = spreadsheet.worksheet("Inventory Transactions")
stock_sheet = spreadsheet.worksheet("Stock")

# Function to add a transaction
def add_transaction(transaction_data):
    # Format the date fields
    if isinstance(transaction_data[1], datetime.date):
        transaction_data[1] = transaction_data[1].strftime('%Y-%m-%d')
    if isinstance(transaction_data[10], datetime.date):
        transaction_data[10] = transaction_data[10].strftime('%Y-%m-%d')

    # Append the transaction data to the Google Sheet
    transactions_sheet.append_row(transaction_data)

    # Update stock based on the transaction type
    update_stock(transaction_data[2], transaction_data[3], transaction_data[4])

# Function to update stock
def update_stock(item_id, quantity, transaction_type):
    # Find the row for the item in the Stock sheet
    try:
        stock_row = stock_sheet.find(item_id).row
    except gspread.exceptions.CellNotFound:
        st.error(f"Item ID {item_id} not found in stock. Please add the item first.")
        return

    # Get the current stock quantity
    current_stock = int(stock_sheet.cell(stock_row, 3).value)

    # Update the stock based on the transaction type
    if transaction_type == "Received":
        new_stock = current_stock + quantity
    elif transaction_type == "Sent":
        new_stock = current_stock - quantity
    else:
        st.error("Invalid transaction type.")
        return

    # Update the stock sheet
    stock_sheet.update_cell(stock_row, 3, new_stock)
    st.success(f"Stock for Item ID {item_id} updated. New stock: {new_stock}")

# Function to add a new item to the Items Database
def add_item(item_name):
    item_id = str(len(items_sheet.col_values(1)) + 1)  # Generate a new Item ID
    items_sheet.append_row([item_id, item_name])
    stock_sheet.append_row([item_id, item_name, 0])  # Initialize stock as 0
    st.success(f"Item '{item_name}' added to the Items Database with ID {item_id}.")

# Function to display the current inventory
def view_inventory():
    stock_data = stock_sheet.get_all_records()
    if stock_data:
        st.write("### Current Inventory")
        st.table(stock_data)
    else:
        st.warning("No inventory data available.")

# Streamlit app layout
def main():
    st.title("Orbit Inventory Management")

    # Tabs for different functionalities
    tabs = ["Add Transaction", "View Inventory", "Add Item"]
    selected_tab = st.sidebar.selectbox("Select a tab", tabs)

    if selected_tab == "Add Transaction":
        # Dropdown to select an item from the Items Database
        items = items_sheet.col_values(2)  # Assuming Item Name is in the second column
        item_name = st.selectbox("Select Item", items)

        # Input fields for transaction details
        transaction_date = st.date_input("Transaction Date", datetime.date.today())
        quantity = st.number_input("Quantity", min_value=0)
        transaction_type = st.selectbox("Transaction Type", ["Received", "Sent"])
        unit = st.text_input("Unit")
        manufacturer = st.text_input("Manufacturer")
        supplier = st.text_input("Supplier")
        supplier_contact = st.text_input("Supplier Contact")
        invoice_no = st.text_input("Invoice No.")
        invoice_date = st.date_input("Invoice Date", datetime.date.today())
        price = st.number_input("Price", min_value=0.0)
        remarks = st.text_area("Remarks")

        # Button to submit the form
        if st.button("Submit"):
            # Generate a Transaction ID
            transaction_id = str(len(transactions_sheet.col_values(1)) + 1)

            # Find the Item ID from the Items Database
            item_id_cell = items_sheet.find(item_name)
            item_id = items_sheet.cell(item_id_cell.row, 1).value

            # Prepare the transaction data
            transaction_data = [
                transaction_id,
                transaction_date,
                item_id,
                quantity,
                transaction_type,
                unit,
                manufacturer,
                supplier,
                supplier_contact,
                invoice_no,
                invoice_date,
                price,
                remarks
            ]

            # Add transaction to the sheet and update stock
            add_transaction(transaction_data)

    elif selected_tab == "View Inventory":
        view_inventory()

    elif selected_tab == "Add Item":
        new_item_name = st.text_input("Enter new item name")
        if st.button("Add Item"):
            add_item(new_item_name)

if __name__ == "__main__":
    main()
