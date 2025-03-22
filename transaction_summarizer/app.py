from flask import Flask, render_template, request, redirect, url_for, Response, send_file
from cleanup_data import cleanup_upload_folder
from transaction_summarizer.validation import is_valid_sample_gs
from calculations import calculate_statistics
import pandas as pd
import os
import json
import re
import threading
import io

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload directory exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

ERROR_MESSAGE = "An error occured while processing your file. Please ensure it meets the required format and requirements."

# Start the cleanup task in a background thread
threading.Thread(target=cleanup_upload_folder, args=(UPLOAD_FOLDER,), daemon=True).start()

# Data Upload and Validation Page
@app.route('/', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        csv_url = request.form.get('csv_url')
        if not csv_url:
            return render_template('error.html', error="No CSV URL provided. Please enter a valid URL.")

        try:
            # Validate the URL
            is_valid, data, skipped_rows = is_valid_sample_gs(csv_url)
            if not is_valid:
                return render_template('error.html', error=ERROR_MESSAGE)

            filename = sanitize_filename(os.path.basename(csv_url))
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            # Save validated data to CSV
            data.to_csv(file_path, index=False)

            return redirect(url_for('results', filename=filename, skipped=json.dumps(skipped_rows, default=str)))

        except Exception as e:
            print(f"Error during upload: {e}")  # For debugging
            return render_template('error.html', error=ERROR_MESSAGE)

    else:
        return render_template('data.html')

# Results/Visualization Page
@app.route('/results/<filename>')
def results(filename):

    sanitized_filename = sanitize_filename(filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], sanitized_filename)

    # Debugging: Check if the file exists
    if not os.path.exists(file_path):
        return render_template('error.html', error="Processed file not found. Please upload a new file.")

    try:
        # Load data
        data = pd.read_csv(file_path)

        # Parse the skipped rows string into a list of dictionaries
        skipped_rows = json.loads(request.args.get('skipped', default="[]"))

        # Pass the skipped_rows count separately
        skipped_count = len(skipped_rows)

        # Calculate totals
        (
            monthly_income, monthly_expenses, monthly_net,
            total_income, total_expenses, net_total,
            averages, percentage_net
        ) = calculate_statistics(data)

        monthly_rows = [
            [month.strftime('%Y-%m'), float(income), float(expenses), float(net), percentage]
            for month, income, expenses, net, percentage in zip(
                monthly_income.index, monthly_income.values,
                monthly_expenses.values, monthly_net.values,
                percentage_net
            )
        ]

        summary = {
            "columns": ["Month", "Income", "Expenses, Percentage Saved/Spent"],
            "monthly_rows": monthly_rows,
            "totals": [
                ["Total Income", total_income],
                ["Total Expenses", total_expenses],
                ["Net Total", net_total],
            ],
            "averages": [
                [key, value] for key, value in averages.items()  # Pass valid averages
            ],
            "skipped_rows": skipped_rows,    # Full skipped rows list
            "skipped_count": skipped_count,  # Count of skipped rows
        }

        return render_template('display.html', summary=summary, filename=filename)

    except Exception as e:
        print(f"Error during results processing: {e}")  # For debugging
        return render_template('error.html', error=ERROR_MESSAGE)

@app.route('/export_csv/<filename>', methods=['GET'])
def export_csv(filename):

    sanitized_filename = sanitize_filename(filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], sanitized_filename)

    # Debugging: Check if the file exists
    if not os.path.exists(file_path):
        return render_template('error.html', error="Processed file not found. Please upload a new file.")

    try:
        # Load data and calculate statistics
        data = pd.read_csv(file_path)
        (
            monthly_income, monthly_expenses, monthly_net,
            total_income, total_expenses, net_total,
            averages, percentage_net
        ) = calculate_statistics(data)

        # Prepare CSV content
        csv_data = [
            ["Metric", "Value"],
            ["Total Income", total_income],
            ["Total Expenses", total_expenses],
            ["Net Total", net_total],
            [],
            ["Monthly Statistics"],
            ["Month", "Income", "Expenses", "Net Total", "Net Savings %"]
        ]

        for month, income, expenses, net, percentage in zip(
                monthly_income.index, monthly_income.values,
                monthly_expenses.values, monthly_net.values,
                percentage_net):
            csv_data.append([month.strftime('%Y-%m'), income, expenses, net, percentage])

        csv_data.extend([
            [],
            ["Average Statistics"],
            ["Metric", "Value"]
        ])
        csv_data.extend([[key, value] for key, value in averages.items()])

        # Convert the data to CSV format
        output = "\n".join([",".join(map(str, row)) for row in csv_data])

        # Create a CSV response
        return Response(output, mimetype="text/csv",
                        headers={"Content-Disposition": f"attachment;filename=finance-statistics_{filename}.csv"})

    except Exception as e:
        print(f"Error during CSV export: {e}")  # For debugging
        return render_template('error.html', error="An error occurred during the CSV export process.")

@app.route('/export_xlsx/<filename>', methods=['GET'])
def export_xlsx(filename):

    sanitized_filename = sanitize_filename(filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], sanitized_filename)

    # Check if the file exists
    if not os.path.exists(file_path):
        return render_template('error.html', error="Processed file not found. Please upload a new file.")

    try:
        # Load data
        data = pd.read_csv(file_path)

        # Calculate statistics
        (
            monthly_income, monthly_expenses, monthly_net,
            total_income, total_expenses, net_total,
            averages, percentage_net
        ) = calculate_statistics(data)

        # Create an Excel writer using an in-memory buffer
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Write cleaned data to "Cleaned Data" sheet
            data.to_excel(writer, index=False, sheet_name='Cleaned Data')

            # Write summary statistics to "Summary" sheet
            summary_data = {
                "Metric": ["Total Income", "Total Expenses", "Net Total"],
                "Value": [total_income, total_expenses, net_total],
            }
            pd.DataFrame(summary_data).to_excel(writer, index=False, sheet_name='Summary')

            # Write monthly statistics to "Monthly Statistics" sheet
            monthly_stats = {
                "Month": monthly_income.index.strftime('%Y-%m'),
                "Income": monthly_income.values,
                "Expenses": monthly_expenses.values,
                "Net Total": monthly_net.values,
                "Net Savings %": percentage_net,
            }
            pd.DataFrame(monthly_stats).to_excel(writer, index=False, sheet_name='Monthly Statistics')

            # Write averages to "Averages" sheet
            averages_df = pd.DataFrame(list(averages.items()), columns=["Metric", "Value"])
            averages_df.to_excel(writer, index=False, sheet_name='Averages')

        # Reset the buffer's position to the beginning
        output.seek(0)

        # Send the file as a response
        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                         download_name=f'finance-statistics_{filename}.xlsx', as_attachment=True)

    except Exception as e:
        print(f"Error during XLSX export: {e}")  # For debugging
        return render_template('error.html', error="An error occurred during the XLSX export process.<br>Please make sure you have Excel or another compatible spreadsheet editor.")

@app.route('/export_pdf/<filename>', methods=['GET', 'POST'])
def export_pdf(filename):

    sanitized_filename = sanitize_filename(filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], sanitized_filename)

    if not os.path.exists(file_path):
        return render_template('error.html', error="Processed file not found. Please upload a new file.")

    try:
        # Load data and calculate statistics
        data = pd.read_csv(file_path)
        (
            monthly_income, monthly_expenses, monthly_net,
            total_income, total_expenses, net_total,
            averages, percentage_net
        ) = calculate_statistics(data)


        from pdfcharts import generate_pie_chart, generate_bar_chart, generate_line_chart
        from io import BytesIO
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)

        elements = []
        styles = getSampleStyleSheet()

        # Add summary
        elements.append(Paragraph("Data Summary", styles['Heading1']))
        summary_data = [
            ["Metric", "Value"],
            ["Total Income", total_income],
            ["Total Expenses", total_expenses],
            ["Net Total", net_total],
        ]
        table = Table(summary_data)
        table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                   ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                   ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                   ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                   ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                   ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                   ('GRID', (0, 0), (-1, -1), 1, colors.black)]))
        elements.append(table)

        # Generate Pie Chart
        pie_chart_path = generate_pie_chart(total_income, total_expenses)
        elements.append(Image(pie_chart_path, width=400, height=300))

        # Add monthly table
        elements.append(Paragraph("Monthly Income and Expenses", styles['Heading2']))
        monthly_data = [
            ["Month", "Income", "Expenses", "Net Total", "Net Savings %"]
        ]
        for month, income, expenses, net, percentage in zip(
                monthly_income.index, monthly_income.values,
                monthly_expenses.values, monthly_net.values,
                percentage_net):
            monthly_data.append([month.strftime('%Y-%m'), income, expenses, net, f"{percentage:.2f}%"])

        monthly_table = Table(monthly_data)
        monthly_table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                           ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                           ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                           ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                           ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                           ('GRID', (0, 0), (-1, -1), 1, colors.black)]))

        elements.append(monthly_table)

        # Generate Bar Chart
        bar_chart_path = generate_bar_chart(monthly_income, monthly_expenses, monthly_net)
        elements.append(Image(bar_chart_path, width=400, height=300))

        # Generate Line Chart
        line_chart_path = generate_line_chart(monthly_income, monthly_expenses, monthly_net)
        elements.append(Image(line_chart_path, width=400, height=300))

        # Add averages
        elements.append(Paragraph("Averages", styles['Heading2']))
        averages_data = [["Metric", "Value"]] + [[key, value] for key, value in averages.items()]
        averages_table = Table(averages_data)
        averages_table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                            ('GRID', (0, 0), (-1, -1), 1, colors.black)]))
        elements.append(averages_table)

        # Generate and return the PDF
        doc.build(elements)
        buffer.seek(0)

        try:
            os.remove(pie_chart_path)
            os.remove(bar_chart_path)
            os.remove(line_chart_path)
        except Exception as cleanup_error:
            print(f"Error cleaning up chart files: {cleanup_error}")


        return send_file(buffer, as_attachment=True, download_name=f"{filename}_summary.pdf", mimetype="application/pdf")

    except Exception as e:
        print(f"Error during PDF export: {e}")
        return render_template('error.html', error="An error occurred during the PDF export process.")

def sanitize_filename(filename):
    return re.sub(r'[^\w.-]', '_', filename)

# Run the app
if __name__ == '__main__':
    app.run()
