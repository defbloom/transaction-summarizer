import pandas as pd  # Imports the pandas library to be able to manipulate and analyze data from data sheet.
import requests  # Helps download user link, check if there are errors in the request, and get its content.
import io  # Used to convert csv data into an object to be read and processed by other functions.

# Function to validate the provided Google Sheets CSV link

def validate_sample_data(file_or_url):

    print("Loaded validation.py")
    print("Available symbols:", dir())

    try:
        if isinstance(file_or_url, str):
            response = requests.get(file_or_url)
            response.raise_for_status()
            csv_content = response.content.decode('utf-8')
            print(f"CSV Content: {csv_content[:1000]}")  # Print first 1000 characters for testing
            data = pd.read_csv(io.StringIO(csv_content))
        else:
            file_or_url.seek(0)
            data = pd.read_csv(file_or_url)

        # Remove leading/trailing whitespace from column names
        data = data.copy()
        data.columns = data.columns.str.strip()

        valid_columns = {}
        for col in ['Date', 'Amount', 'Description']:
            matches = [c for c in data.columns if c.strip().lower() == col.lower()]
            if matches:
                valid_columns[col] = matches[0]  # Take the first match

        if 'Date' not in valid_columns or 'Amount' not in valid_columns:
            return False, None, []

        # Keep only the relevant columns for validation
        data = data[valid_columns.values()]
        data.columns = ['Date', 'Amount']

        # Change rows with invalid dates to datetime format
        data['Date'] = pd.to_datetime(data['Date'], errors='coerce')  # Convert to datetime
        # Strip commas from the Amount column
        data['Amount'] = data['Amount'].astype(str).str.replace(',', '', regex=True)
        # Convert the Amount column to numeric, coercing errors to NaN
        data['Amount'] = pd.to_numeric(data['Amount'], errors='coerce')

        invalid_rows = data[(data['Date'].isna()) | (data['Amount'].isna())]
        skipped_rows = invalid_rows.astype(object).to_dict('records')  # Convert skipped rows to a list of dicts for display
        print(f"Skipped rows: {skipped_rows}")  # For debugging

        data = data.dropna(subset=['Date', 'Amount'])

        return True, data, skipped_rows
    except Exception as e:
        print(f"Validation error: {e}")  # For debugging
        return False, None, []
