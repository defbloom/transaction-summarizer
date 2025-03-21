# Transaction Summarizer App

## Description
Transaction Summarizer App is a web application that processes financial data and generates summary reports in CSV and PDF format. The app is built using Flask and deployed on Render. Anyone can use it - including freelancers and small business owners looking for a way to quickly get insights from their income and expenses.

Built with Flask, Pandas, and Matplotlib, the app allows users to upload CSV files of their financial transactions and calculates/displays detailed financial statistics, including income, expenses, and net totals. The app also generates interactive charts and exports PDF reports with visual summaries.A

There are instructions for generating a csv file from ones's transactions. This csv method is more assuring than directly linking one's account to an external app. The app also automatically detects and handles CSV format errors by skipping problematic rows while keeping the rest of the data intact.

## Live Demo
Try the app here: [Live on Render][link]

## Features
- Upload  CSV files of financial transactions (amt, date)
- Automatically handles format errors
- Calculates and displays financial statistics
- Generates Summary Charts
- Exports reports in PDF and CSV/XLX format

## Technologies Used
- **Backend**: Flask, Pandas (Data Processing)
- **Frontend**: HTML, CSS (Bootstrap), JavaScript
- **Visualization**: Matplotlib (Data Visualization)
- **Deployment**: Render