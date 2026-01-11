from threading import Thread
import threading
import time
# def wok_wok_wok():
#     while not event_obj.is_set():
#         time.sleep(5)
#         print('A Minorrrrrr')
        
#     print('Thread Exited here OHHHHH')

# t = Thread(target = wok_wok_wok)


# print('Mike check is it running?')
# event_obj = threading.Event()


# This runs in a separate Thread 
# t.start()
# time.sleep(8)
# event_obj.set()
# # t.stop()
# print('Main exited here uhhh')


def main_thread():
    print('[main-thread] WORK WORK WORK')
    time.sleep(12)
    print('[main-thread] Okay Work Done')
    event_.set()

def heartbeat(event_,interval):
    
    # while True:
    #     if event_.is_set():
    #         break
    #     time.sleep(2)
    #     print("[heart-beat] Bitch Don't Kill my Vibe")

    # print('[last heart-beat] Heart beat STOPPED')
    while not event_.is_set():
        print('[heart-beat] Still Alive 🫀')
        if event_.wait(interval):
            break
        
    print('[last heart-beat] Heart beat STOPPED')
event_ = threading.Event()
t1 = Thread(target=main_thread)
t2 = Thread(target=heartbeat, args= (event_,1))

t1.start()
t2.start()
t1.join()
print('[MAIN PROCESS] end')