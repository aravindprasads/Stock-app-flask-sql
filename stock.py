from flask import Flask, render_template, request
import subprocess, threading, time, os, datetime                                                                                   
import stock_library as SL

app = Flask(__name__)                                                                               
app.config['DEBUG'] = True         
lock = threading.Lock()
thread_file = 'thread_spawned'

class Processer_thread(threading.Thread):
    #15 seconds is because QUANDL website supports only 5 calls per minute
    def __init__(self, name, interval=15):
        threading.Thread.__init__(self, name=name)
        self.interval = interval
        self.daemon = True
        self.start()

    def run(self):
        while True:
            global lock
            lock.acquire()
            print (str(datetime.datetime.now().strftime("%H:%M:%S")))
            print "Thread lock taken"
            SL.thread_fun()
            print (str(datetime.datetime.now().strftime("%H:%M:%S")))
            print "Thread lock released"
            lock.release()
            time.sleep(self.interval)

## Main page                                                                                        
@app.route('/', methods=['GET', 'POST'])                                                            
def index():         
    global lock
    lock.acquire()
    print (str(datetime.datetime.now().strftime("%H:%M:%S")))
    print "Main lock taken"
    file_path = "./" + thread_file
    if(False == os.path.isfile(file_path)):
        #Create Table in Stock DB
        SL.db_create()
        print ("Spawning new thread to read data file contents")
        thread_start = Processer_thread("READ_THREAD")
        bashCommand = "touch " + thread_file
        subprocess.check_output(['bash','-c', bashCommand])
    else:        
        print ("Not spawning new thread")
        
    ret_value = 0
    err_str = ""
    print "Entering main"
    if [request.method == 'POST']:
        user_stock_name = request.form.get('stock-name')
        if(user_stock_name):
            stock_name = user_stock_name.upper()
            min_value = request.form.get('min-value')                                                  
            max_value = request.form.get('max-value')                                                  
            mail_id = request.form.get('mail-id')    
            if(stock_name and mail_id):
                if(min_value and max_value):
                    ret_value = SL.flask_fun(stock_name, min_value, max_value, mail_id)
                    print "Got both min and max values"
                elif(min_value):
                    print "Got only min value"
                    ret_value = SL.flask_fun(stock_name, min_value, 0, mail_id)
                elif(max_value):
                    print "Got only max value"
                    ret_value = SL.flask_fun(stock_name, 0, max_value, mail_id)
                else:
                    print (str(datetime.datetime.now().strftime("%H:%M:%S")))
                    print "Main lock released"
                    lock.release()
                    return "<h1>Enter atleast Minimum or Maximum Stock value </h1>"
            else:
                if(stock_name):
                    err_str = "<h1>Enter atleast 3 details for the Stock - Name, Minimum/Maximum "
                    err_str += "value and Mail-ID</h1>"
                    print (str(datetime.datetime.now().strftime("%H:%M:%S")))
                    print "Main lock released"
                    lock.release()
                    return err_str
            if(1 == ret_value):
                err_str = "<h1>The Stock info is obtained from Alpha Vantage website. Currently," 
                err_str += "the website is not responding. Kindly try after some time</h1>"
                print (str(datetime.datetime.now().strftime("%H:%M:%S")))
                print "Main lock released"
                lock.release()
                return err_str
            elif(2 == ret_value):
                err_str =  "<h1>Company name "+ stock_name +" is not supported. Kindly try a "
                err_str += "different Company name</h1>"
                print (str(datetime.datetime.now().strftime("%H:%M:%S")))
                print "Main lock released"
                lock.release()
                return err_str

        user_stock_name_del = request.form.get('stock-name-del')
        if(user_stock_name_del):
            stock_name_del = user_stock_name_del.upper()
            print stock_name_del
            if(stock_name_del):
                if(0 != SL.db_delete(stock_name_del)):
                    err_str = "<h1>Failed to delete " + stock_name_del + "due to an internal error"
                    err_str = ". Please try after sometime."
                    return err_str

        stock_data = SL.read_and_fill_info_from_db()

    print (str(datetime.datetime.now().strftime("%H:%M:%S")))
    print "Main lock released"
    lock.release()
    return render_template('stock.html', stock_data=stock_data)                

if __name__ == '__main__':
    app.run()
