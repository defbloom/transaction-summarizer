import pandas as pd

# Function to calculate income, expenses, and net totals from data

def calculate_statistics(data):

  data = data.copy()

  # Ensures date values are correct, and if not marked as NaT.
  data['Date'] = pd.to_datetime(data['Date'], errors='coerce')  # Convert to datetime
  data['Month'] = data['Date'].dt.to_period('M')

  # Separate transactions into income, expenses, and zero amounts
  income = data.loc[data['Amount'] > 0]
  expenses = data.loc[data['Amount'] < 0]
  zero_amounts = data.loc[data['Amount'] == 0]

  # Calculate the total income and expenses of each month separately
  monthly_income = income.groupby('Month')['Amount'].sum()
  monthly_expenses = expenses.groupby('Month')['Amount'].sum()

  # Ensure all months are represented
  all_months = monthly_income.index.union(monthly_expenses.index).union(zero_amounts['Month'].unique())
  monthly_income = monthly_income.reindex(all_months, fill_value=0)
  monthly_expenses = monthly_expenses.reindex(all_months, fill_value=0)
  monthly_net = monthly_income + monthly_expenses

  # Calculate totals of the overall period from the csv data.
  total_income = round(monthly_income.sum(), 2)
  total_expenses = round(monthly_expenses.sum(), 2)
  net_total = round(total_income + total_expenses, 2)

  # Calculate percentage of income saved/spent for each month
  percentage_net = []
  for month in all_months:
    income = monthly_income[month]
    expenses = monthly_expenses[month]

    # Calculate the percentage using the formula
    if income != 0 or expenses != 0:  # Avoid division by zero
        if income == 0 or expenses == 0:
          percentage = (income or expenses) * 100
          income if income != 0 else expenses
        else:
          net_difference = income + expenses
          if net_difference > 0:
            percentage = (net_difference / abs(expenses)) * 100
          else:
            percentage = (net_difference / income) * 100
    else:
      percentage = 0

    percentage_net.append(round(percentage, 2) if isinstance(percentage, (int, float)) else percentage)

  active_years = max(data[data['Amount'] != 0]['Date'].dt.year.nunique(), 1)
  active_months = max(data[data['Amount'] != 0]['Month'].nunique(), 1)
  active_weeks = max(data[data['Amount'] != 0]['Date'].dt.isocalendar().week.nunique(), 1)
  active_days = max(data[data['Amount'] != 0]['Date'].dt.dayofyear.nunique(), 1)

  # Calculate averages
  averages = {
      "Yearly Income": round(total_income / active_years, 2) if active_years > 0 else 0,
      "Yearly Expenses": round(total_expenses / active_years, 2) if active_years > 0 else 0,
      "Monthly Income": round(total_income / active_months, 2) if active_months > 0 else 0,
      "Monthly Expenses": round(total_expenses / active_months, 2) if active_months > 0 else 0,
      "Weekly Income": round(total_income / active_weeks, 2) if active_weeks > 0 else 0,
      "Weekly Expenses": round(total_expenses / active_weeks, 2) if active_weeks > 0 else 0,
      "Daily Income": round(total_income / active_days, 2) if active_days > 0 else 0,
      "Daily Expenses": round(total_expenses / active_days, 2) if active_days > 0 else 0,
  }

  #Return the calculated values
  return monthly_income, monthly_expenses, monthly_net, total_income, total_expenses, net_total, averages, percentage_net
