import re                                                                                         
import urllib2                                                                                      
import subprocess                                                                                   
import time
import smtplib                                                                                      
import sqlite3 as sql                                                                               
from email.MIMEMultipart import MIMEMultipart                                                       
from email.MIMEText import MIMEText          

web_file = 'alphavantage_data.txt'
mail_dic = {}
zero_val = "{:.4f}".format(float(0))
conn = sql.connect('db_stock.db', check_same_thread=False)

def db_create():
    global conn
    try:                                                                                            
        exec_str = """CREATE TABLE stock_db (comp_name TEXT PRIMARY KEY, val TEXT, min_val TEXT, max_val TEXT, email_id TEXT, min_email_status TEXT, max_email_status TEXT)"""
        conn.execute(exec_str)                                                                       
        msg = "Stock DB Table successfully created"                                                             
    except Exception as e:                                                                          
        msg = "DB create failed. Error = " + str(e)                                                 
    finally:                                                                                        
        print msg        


def db_delete(comp):
    print comp
    global conn
    ret_val = 0
    try:                                                                                            
        cur = conn.cursor()                                                                          
        cur.execute('''DELETE from stock_db WHERE comp_name = ? ''', (comp,))
        conn.commit                                                                                  
        msg = "DB Deletion successful for " + comp
    except Exception as e:                                                                          
        msg = "Deletion failed for "+ comp + ". Error = " + str(e)
        ret_val = 1
    finally:                                                                                        
        print msg  
        cur.close()
        return ret_val


def db_add(new_comp, new_comp_val, min_val, max_val, email_id, min_email_status, max_email_status):
    global conn
    try:                                                                                            
        cur = conn.cursor()                                                                          
        ret_val = cur.execute("INSERT INTO stock_db (comp_name, val, min_val, max_val, email_id, min_email_status, max_email_status) VALUES (?,?,?,?,?,?,?)",(new_comp, new_comp_val, min_val, max_val, email_id, min_email_status, max_email_status))
        conn.commit()
        msg = "Record successfully added for " + new_comp
    except Exception as e:                                                                          
        conn.rollback()                                                                              
        msg = "DB insert failed for " + new_comp  + ". Error = " + str(e)                                                 
    finally:                                                                                        
        print msg                                                                                   
        cur.close()


def db_update(new_comp, new_comp_val, min_val, max_val, email_id, min_email_status, max_email_status):
    global conn
    try:                                                                                            
        cur = conn.cursor()                                                                          
        cur.execute('''UPDATE stock_db set val=?,min_val=?,max_val=?,email_id=?,min_email_status=?,max_email_status=? WHERE comp_name = ? ''', (new_comp_val, min_val, max_val, email_id, min_email_status, max_email_status, new_comp))
        conn.commit                                                                                  
        msg = "DB Updation successful for " + new_comp
    except Exception as e:                                                                          
        msg = "Updation failed. Error = " + str(e)                                                  
    finally:                                                                                        
        print msg                                                                                   
        cur.close()


def db_print():
    global conn
    print ("\nData file contents")
    print ("===================================================")
    conn.row_factory = sql.Row                                                                       
    cur = conn.cursor()                                                                              
    cur.execute("select * from stock_db")                                                           
    rows = cur.fetchall();                                                                          
    for row in rows:
        print row
    print ("===================================================")
    cur.close()


#Get the company info and write it to "data" file
def get_company_info_from_website(company):
    my_url = "https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=NSE:" + company + "&interval=1min&apikey=<alphavantage-key>"
    #Write the company info to "data" file
    dn_file = urllib2.urlopen(my_url)
    with open(web_file, 'wb') as output:
        output.write(dn_file.read())


def extract_info_from_web_file(line):
    match = re.search('(\"1. open\"\:\s\")(\w+.*)(\",)', line)
    return match


def search_invalid_response_from_data_file(line):
    match = re.search('Invalid', line)
    return match


def check_company_dic(data_dic, new_comp):
    if new_comp in data_dic:
        return True
    return False        


def get_company_dic_from_db():
    global conn
    data_dic = {}
    conn.row_factory = sql.Row                                                                       
    cur = conn.cursor()                                                                              
    cur.execute("select * from stock_db")                                                           
    rows = cur.fetchall();                                                                          
    for row in rows:                                                                                
        company = row["comp_name"]
        actual_val = row["val"]
        min_val = row["min_val"]
        max_val = row["max_val"]
        email_id = row["email_id"]
        min_mail_status = row["min_email_status"]
        max_mail_status = row["max_email_status"]
        data_dic[company] = actual_val
    cur.close()
    return data_dic


def send_mail(company, cur_val, min_val, max_val, email_id, is_lesser):
    print ("Sending mail to " + email_id + " about company " + company)
    
    if(True == is_lesser):
        comp_str = " has decreased below " + str(min_val) 
    else:
        comp_str = " has increased above " + str(max_val)
    subj_msg = "STOCK VALUE OF " + company + " CHANGED !!!"                                             
    body_msg = "Hi User,\n\nThis mail is from Stock-Notify Website.\n\nThe stock value of Company "     
    body_msg += company + comp_str +". Current value is " + str(cur_val)   
    body_msg += ".\n\nHappy to assist you always.\n\nThanks,\nStock-Notify-App team"         
    fromaddr = "<email-id>"
    toaddr = email_id
    msg = MIMEMultipart()                                                                               
    msg['From'] = fromaddr                                                                              
    msg['To'] = toaddr                                                                                  
    msg['Subject'] = subj_msg                                                                           
    msg.attach(MIMEText(body_msg, 'plain'))                                                             
    server = smtplib.SMTP('smtp.gmail.com', 587)                                                        
    server.starttls()                                                                                   
    server.login(fromaddr, "<password>")
    text = msg.as_string()                                                                              
    server.sendmail(fromaddr, toaddr, text)                                                             
    server.quit()                                 


def read_and_fill_info_from_db():
    global conn
    stock_data = []                                                                               
    conn.row_factory = sql.Row                                                                       
    cur = conn.cursor()                                                                              
    cur.execute("select * from stock_db")                                                           
    rows = cur.fetchall();
    print ("\nData file contents")
    print ("===================================================")
    for row in rows:
        print row
    print ("===================================================")
    for row in rows:     
        min_val = row["min_val"]
        max_val = row["max_val"]
        if(float(min_val) == float(zero_val)):
            min_val_str = "VALUE NOT PROVIDED"
        else:
            min_val_str = min_val
        if(float(max_val) == float(zero_val)):
            max_val_str = "VALUE NOT PROVIDED"
        else:
            max_val_str = max_val
        stock = {                                                                                 
            'name' : row["comp_name"],
            'actual_value' : row["val"],
            'min_value' : min_val_str,
            'max_value' : max_val_str,
            'email_id' : row["email_id"]
        }                                                                                           
        stock_data.append(stock)                                                                
    cur.close()
    return stock_data


def update_company_info_in_db(row):
    data_written = False
    with open(web_file) as fp_web:
        lines = fp_web.readlines()
    fp_web.close()
    for line in lines:
        match = extract_info_from_web_file(line)
        if match:
            company = row["comp_name"]
            min_val = row["min_val"]
            max_val = row["max_val"]
            email_id = row["email_id"]
            min_mail_status = row["min_email_status"]
            max_mail_status = row["max_email_status"]

            temp = (float)(match.group(2))
            new_comp_val = "{:.4f}".format(temp)
            print (company +" Current value " + str(new_comp_val))
            print (company +" Min value " + str(min_val))

            if(float(min_val) != float(zero_val)):
                if(float(new_comp_val) < float(min_val)):
                    print ("Found the Value to be lesser")
                    if("False" == min_mail_status):
                        print ("Trying to send mail to about company " + company + " to " + email_id)
                        send_mail(company, new_comp_val, min_val, max_val, email_id, True)
                    else:
                        print ("Not sending mail now. Mail already sent")
                    min_mail_status = "True"
            if(float(max_val) != float(zero_val)):
                if(float(new_comp_val) > float(max_val)):
                    print ("Found the Value to be higher")
                    if("False" == max_mail_status):
                        print ("Trying to send mail to about company " + company + " to " + email_id)
                        send_mail(company, new_comp_val, min_val, max_val, email_id, False)
                    else:
                        print ("Not sending mail now. Mail already sent")
                    max_mail_status = "True"                        
            db_update(company, new_comp_val, min_val, max_val, email_id, min_mail_status, max_mail_status)
            data_written = True
            break
    #if data retreival from website failed, rewrite old data of company back to output file            
    if(False == data_written):
        print ("\nSomething failed in retreving contents from Web file")
        with open(web_file) as fp_web:
            lines = fp_web.readlines()
            print (lines)


def thread_fun():
    global conn
    #Read DB
    conn.row_factory = sql.Row                                                                       
    cur = conn.cursor()                                                                              
    cur.execute("select * from stock_db")                                                           
    rows = cur.fetchall();                                                                          
    for row in rows:
        company = row["comp_name"]
        print ("\nGet the company info and write it to data file")
        get_company_info_from_website(company)
        update_company_info_in_db(row)
    db_print()
    cur.close()
    print ("\n!!!!!!!!!!NEXT LOOP!!!!!!!!!!!!!!!!!!!!!!!!")


def flask_fun(stock_name, min_value, max_value, mail_id):
    #Read the inputs
    new_comp = stock_name
    temp = (float)(min_value)
    min_val = "{:.4f}".format(temp)
    temp = (float)(max_value)
    max_val = "{:.4f}".format(temp)
    email_id = mail_id
    
    print ("\nCompany given = " + new_comp)
    print ("\nMin Value given = " + str(min_val))
    print ("\nMax Value given = " + str(max_val))
    print ("\nemail-id given = " + email_id)

    #Extract a dic of company-names
    data_dic = {}
    data_dic = get_company_dic_from_db()
    company_found = False
    no_of_retries = 0
    ret_value = 0

    while(no_of_retries < 3):
        print ("Getting company info of " + new_comp + " from website")
        get_company_info_from_website(new_comp)	
        #Read the data file
        with open(web_file) as fp:                                                                      
            lines = fp.readlines()
        for line in lines:
            match = extract_info_from_web_file(line)
            #if success, read the stock value
            if match:         
                company_found = True
                temp = (float)(match.group(2))
                new_comp_val = "{:.4f}".format(temp)
                print ("\nCompany current value " + str(new_comp_val))
                #Check if the company name provided by User already exists in DB
                if(check_company_dic(data_dic, new_comp) == False):
                    print ("\nNew Company provided")
                    db_add(new_comp, new_comp_val, min_val, max_val, email_id, "False", "False")
                else:
                    print ("\nCompany already exists. Replacing contents in data file")
                    db_update(new_comp, new_comp_val, min_val, max_val, email_id, "False", "False")
                ret_value = 0                    
                break
            else:
                match = search_invalid_response_from_data_file(line)
                if match:         
                    print ("\nCompany not found in Website. Return")
                    company_found = True
                    ret_value = 2
                    break
        if(True == company_found):
            break
        no_of_retries += 1            
        time.sleep(2)

    if(no_of_retries >= 3):        
        ret_value = 1

    return ret_value        
                                
