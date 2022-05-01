from datetime import date, datetime
import re
import pdfplumber
from dateutil import parser
import os
import pandas as pd


def get_ola_details(text, file_name):
    ola_date_regex = r'([0-2][0-9]|(3)[0-1]) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec), (\d{4})'
    ola_time_regex = r'([0-9]|0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])\s*([AaPp][Mm])'
    ola_amount_regex = r'₹\d+'

    # Extract date details
    day, _, month, year = re.findall(ola_date_regex, text)[0]
    datestr = ' '.join([day, month, year])
    date = parser.parse(datestr)

    # Extract time details
    _time = re.findall(ola_time_regex, text)
    start_time, end_time = _time[0], _time[1]
    start_time = start_time[0] + ":" + start_time[1] + " " + start_time[2]
    end_time = end_time[0] + ":" + end_time[1] + " " + end_time[2]

    # Extract amount details
    amount = re.findall(ola_amount_regex, text)[0]
    amount = amount.replace('₹', '')
    amount = int(amount)
    return {
        'provider': 'ola',
        'date': date,
        'start_time': start_time,
        'end_time': end_time,
        'amount': amount,
        'file_name': file_name
    }


def get_uber_details(text, file_name):
    uber_date_regex = r'(January|February|March|April|May|June|July|August|September|October|November|December) ([0-2][0-9]|(3)[0-1]), (\d{4})'
    uber_time_regex = r'([0-9]|0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])\s*([AaPp][Mm])'
    uber_amount_regex = r'₹\d+'

    # Extract date details
    month, day, _, year = re.findall(uber_date_regex, text)[0]
    datestr = ' '.join([day, month, year])
    date = parser.parse(datestr)

    # Extract time details
    _time = re.findall(uber_time_regex, text)
    start_time, end_time = _time[0], _time[1]
    start_time = start_time[0] + ":" + start_time[1] + " " + start_time[2]
    end_time = end_time[0] + ":" + end_time[1] + " " + end_time[2]

    # Extract amount details
    amount = re.findall(uber_amount_regex, text)[0]
    amount = amount.replace('₹', '')
    amount = int(amount)
    return {
        'provider': 'uber',
        'date': date,
        'start_time': start_time,
        'end_time': end_time,
        'amount': amount,
        'file_name': file_name
    }


def get_details(file_path, file_name):
    with pdfplumber.open(file_path) as pdf:
        pdf_text = ""
        for i in range(len(pdf.pages)):
            pdf_text = pdf_text + '\n' + pdf.pages[i].extract_text()
        if 'Ola Convenience'.lower() in pdf_text.lower():
            return get_ola_details(pdf_text, file_name)
        return get_uber_details(pdf_text, file_name)


if __name__ == '__main__':
    # List files in bills folder
    files = os.listdir('bills')
    lis = []
    for file in files:
        details = get_details('bills/' + file, file)
        lis.append(details)
    # Sort lis with date key
    lis = sorted(lis, key=lambda k: k['date'])
    # convert all date in lis to readable format
    for i in range(len(lis)):
        lis[i]['date'] = lis[i]['date'].strftime('%d %b %Y')
    # convert list to pandas dataframe
    df = pd.DataFrame(lis)
    # add row with total amount
    df = df.append({'provider': 'Total', 'date': '', 'start_time': '',
                   'end_time': '', 'amount': df['amount'].sum()}, ignore_index=True)
    df = df.append({'provider': 'Uber Total', 'date': '', 'start_time': '', 'end_time': '',
                   'amount': df['amount'].where(df['provider'] == 'uber', 0).sum()}, ignore_index=True)
    df = df.append({'provider': 'Ola Total', 'date': '', 'start_time': '', 'end_time': '',
                   'amount': df['amount'].where(df['provider'] == 'ola', 0).sum()}, ignore_index=True)

    print(df)

    bills = list(df['file_name'])
    import fitz
    result = fitz.open()

    for pdf in bills:
        if type(pdf) != str:
            continue
        with fitz.open('bills/' + pdf) as mfile:
            result.insert_pdf(mfile)
    result.save("combined_bills.pdf")

    # convert df to pdf
    import pandas as pd
    df.to_html('consolidated_report.html', classes='table table-stripped')
    df.to_markdown('consolidated_report.md')
    pdf_name = 'consolidated_report.pdf'
