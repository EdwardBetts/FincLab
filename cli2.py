import time, random, sys, collections
from multiprocessing import Process as Task, Queue
#from threading import Thread as Task
#from Queue import Queue

def download(status, filename):
    count = random.randint(5, 30)
    for i in range(count):
        status.put([filename, (i+1.0)/count])
        time.sleep(0.1)

def print_progress(progress):
    sys.stdout.write('\033[2J\033[H')  #clear screen
    for filename, percent in progress.items():
        bar = ('*' * int(percent * 20)).ljust(20)
        percent = int(percent * 100)
        sys.stdout.write("%s [%s] %s%%\n" % (filename, bar, percent))
    sys.stdout.flush()

def main():
    status = Queue()
    progress = collections.OrderedDict()
    workers = []
    for filename in ['test1.txt', 'test2.txt', 'test3.txt']:
        child = Task(target=download, args=(status, filename))
        child.start()
        workers.append(child)
        progress[filename] = 0.0
    while any(i.is_alive() for i in workers):
        time.sleep(0.1)
        while not status.empty():
            filename, percent = status.get()
            progress[filename] = percent
            print_progress(progress)
    print('all downloads complete')


if __name__ == '__main__':
    main()

