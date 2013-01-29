from multiprocessing import Process, Queue, Event
import time
import atexit
import pycps


##############################
# Helper functions.
##############################
def prepare_pickle(in_file='enwiki.xml', out_file='enwiki.pickle.gz',
                    comp_lvl=9):
    import cPickle
    import gzip
    import re

    if re.search('\.pickle\.gz$', out_file):
        pickle_file = gzip.open(out_file, 'wb', comp_lvl)
    elif re.search('\.pickle$', out_file):
        pickle_file = open(output_file, 'w')
    else:
        raise Error()
    lines = open(in_file, 'r').readlines()
    documents = []
    start_offset = None
    line_number = 0
    for line in lines:
        if start_offset is not None:
            if line.strip() == '</page>':
                documents.append(''.join(lines[start_offset:line_number+1]))
                start_offset = None
        else:
            if line.strip() == '<page>':
                start_offset = line_number
        line_number += 1
    cPickle.dump(documents, pickle_file, cPickle.HIGHEST_PROTOCOL)

def load_pickle(file_name='enwiki.pickle.gz'):
    import cPickle
    import gzip
    import re

    if re.search('\.pickle\.gz$', file_name):
        pickle_file = gzip.open(file_name, 'rb')
    elif re.search('\.pickle$', file_name):
        pickle_file = open(file_name, 'r')
    else:
        raise Error()
    return cPickle.load(pickle_file)


##############################
# Task master class.
##############################
class TaskMaster():
    def __init__(self, logger, options):
        self.logger = logger
        self.con_urls = options.url
        self.con_args = (options.name, options.user, options.password)
        self.proc_count = options.proc_count

        # XXX: for forced termination
        self.tasks = []
        self.doc_queue = None
        atexit.register(self.cleanup)

    def cleanup(self):
        for task in self.tasks:
            task.terminate()
        self.doc_queue.close()
        self.doc_queue.join_thread()

    def run(self):
        self.common_prep()

        #run_event = Event()
        #run_event.clear()

        self.doc_queue = Queue()
        for doc in self.documents:
            self.doc_queue.put(doc)

        for i in range(self.proc_count):
            con_url = self.con_urls[i%len(self.con_urls)]
            task = Task(self.logger, self.doc_queue, con_url, self.con_args)
            task.deamon = True
            self.tasks.append(task)

        for task in self.tasks:
            task.start()
        self.logger.info('All tasks launched!')

        start_time = time.time() #XXX
        for task in self.tasks:
            task.join()
        end_time = time.time() #XXX
        print('TIME: ' + str(end_time-start_time)) # XXX

    def common_prep(self):
        con = pycps.Connection(self.con_urls[0], *self.con_args,
                                document_root_xpath = 'page')
        con.clear()
        self.logger.info('Storage cleared')
        self.documents = load_pickle()
        self.logger.info('Documents file loaded')


##############################
# Task class.
##############################
class Task(Process):
    def __init__(self, logger, doc_queue, con_url, con_args):
        Process.__init__(self)
        self.logger = logger
        self.doc_queue = doc_queue
        self.con_url = con_url
        self.con_args = con_args

    def run(self):
        self.prep_load()
        self.run_load()

    def prep_load(self):
        self.connection = pycps.Connection(self.con_url, *self.con_args,
                                            document_root_xpath = 'page')
        self.logger.info('Connection madde to: ' + self.con_url)

    def run_load(self):
        self.logger.info('Running load ...')

        while True:
            try:
                doc = self.doc_queue.get()
                self.connection.insert(doc, fully_formed=True)
            except:
                break
