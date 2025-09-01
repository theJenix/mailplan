from datetime import datetime

def before_today():
    # before:2023/5/1
    date_format = "%d-%b-%Y" # DD-Mon-YYYY e.g., 3-Mar-2014
    before_date = datetime.strftime(datetime.now(), date_format)

    print( "BEFORE " + before_date)
    return "BEFORE " + before_date