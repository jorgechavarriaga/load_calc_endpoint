#!/usr/bin/env python3
import io
import os
import cgi
import json
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from pyloan import pyloan
import pandas as pd



class LoanCalcHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()


    def do_GET(self):
        if self.path == "/hello":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write("Hola mundo".encode("utf-8"))
        else:
            self.send_response(404)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write("Ruta no encontrada".encode("utf-8"))


    def do_POST(self):
        self.path == '/calculate_loan'
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        try:
            data = json.loads(post_data.decode('utf-8'))
            loan_amount = str(data.get('loan_amount'))
            annual_interest_rate = str(data.get('annual_interest_rate_range'))
            loan_period_years = str(data.get('loan_period_years_range'))
            loan_start_date = data.get('start_date')
            loan_amount_float = float(loan_amount.replace(',', '').replace('$', ''))
            annual_interest_rate_float = float(annual_interest_rate)
            loan_period_years_int = int(loan_period_years)
            start_date = datetime.strptime(loan_start_date, '%Y-%m-%d')
            new_start_date = start_date - timedelta(days=30)
            new_start_date_str = new_start_date.strftime('%Y-%m-%d')
            loan = pyloan.Loan(
                loan_amount=loan_amount_float,
                interest_rate=annual_interest_rate_float,
                loan_term=loan_period_years_int,
                start_date=new_start_date_str,
                first_payment_date=loan_start_date,
                payment_end_of_month=False,
                loan_type='annuity'
            )
            payment_schedule = loan.get_payment_schedule()
            df = pd.DataFrame.from_records(loan.get_payment_schedule(), columns=pyloan.Payment._fields)
            subset_df = df[['date', 'payment_amount', 'interest_amount', 'principal_amount', 'loan_balance_amount']]
            new_headers = {
                'date': 'Payment Date',
                'payment_amount': 'Payment Amount',
                'interest_amount': 'Interest Amount',
                'principal_amount': 'Principal Amount',
                'loan_balance_amount': 'Ending Balance'
            }
            subset_df_new_headers = subset_df.rename(columns=new_headers)
            data_list = subset_df_new_headers.astype(str).to_dict(orient='records')
            data = {
                "header": list(subset_df_new_headers.columns),
                "rows": data_list
            }
            json_data = json.dumps(data)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            self.wfile.write(json_data.encode('utf-8'))
        except json.JSONDecodeError as e:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response_data = {
                "error": "Error en el formato JSON de los datos",
                "details": str(e)
            }
            response_json = json.dumps(response_data)
            self.wfile.write(response_json.encode('utf-8'))


def run(server_class=HTTPServer, handler_class=LoanCalcHandler, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting server on port {port}...')
    httpd.serve_forever()


if __name__ == '__main__':
    run()
