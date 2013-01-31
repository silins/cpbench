import multiprocessing
import Queue
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
# Worker Master class.
##############################
class WorkerMaster():
    def __init__(self, logger, options):
        self.logger = logger
        self.con_urls = options.url
        self.con_args = (options.name, options.user, options.password)
        self.proc_count = options.proc_count

        self.workers = []
        self.manager = multiprocessing.Manager()
        self.task_queue = self.manager.Queue()
        self.result_queue = self.manager.Queue()

        atexit.register(self.cleanup)

    def cleanup(self):
        for worker in self.workers:
            worker.terminate()

    def dump_queue(self, q):
        l = []
        q.put('STOP') # Sentinel
        for i in iter(q.get, 'STOP'):
            l.append(i)
        return l

    def run(self):
        self.common_prep()

        for i in range(self.proc_count):
            con_url = self.con_urls[i%len(self.con_urls)]
            con_kwargs = {'document_root_xpath': 'page'}
            worker = Worker(self.logger, self.task_queue, self.result_queue,
                            con_url, self.con_args, con_kwargs)
            worker.deamon = True
            self.workers.append(worker)

        self.logger.info('Load workers ...')
        for worker in self.workers:
            worker.start()

        for doc in self.documents:
            self.task_queue.put(doc)

        for i in range(self.proc_count):
            self.task_queue.put(None) # Poison!

        self.logger.info('Ordering workers to prep ...')
        for w in self.workers:
            w.prep_req.set()

        # TODO: get from tasks that prep is done
        self.logger.info('Ordering workers to run ...')
        start_time = time.time() #XXX
        for w in self.workers:
            w.run_req.set()
        self.task_queue.join()
        end_time = time.time() #XXX

        for worker in self.workers:
            worker.join(0.1)

        results = self.dump_queue(self.result_queue)
        self.cleanup()

        print('TIME:    ' + str(end_time-start_time)) # XXX
        print('OPS:     ' + str(len(results))) # XXX
        print('AVG LAT: ' + str(sum(results)/len(results)))
        print('MAX LAT: ' + str(max(results)))
        print('MIN LAT: ' + str(min(results)))

    def common_prep(self):
        con = pycps.Connection(self.con_urls[0], *self.con_args,
                                document_root_xpath = 'page')
        self.logger.info('Clearing storage ...')
        con.clear()
        self.logger.info('Loading document file ...')
        self.documents = load_pickle()


##############################
# Worker class.
##############################
class Worker(multiprocessing.Process):
    def __init__(self, logger, task_queue, result_queue, con_url, con_args,
                    con_kwargs):
        multiprocessing.Process.__init__(self)
        self.logger = logger
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.con_url = con_url
        self.con_args = con_args
        self.con_kwargs = con_kwargs

        self.prep_req = multiprocessing.Event()
        self.prep_req.clear()
        self.run_req = multiprocessing.Event()
        self.run_req.clear()
        self.stop_req = multiprocessing.Event()
        self.stop_req.clear()

    def run(self):
        self.prep_req.wait()
        self.prep_load()
        # TODO: Report prep_ok
        self.run_req.wait()
        self.run_load()
        # TODO: Report run_ok
        return

    def prep_load(self):
        self.connection = pycps.Connection(self.con_url, *self.con_args,
                                            **self.con_kwargs)
        self.logger.info('Connection madde to: ' + self.con_url)
        return

    def run_load(self):
        self.logger.info('Running load ...')

        # TODO: Report status peridocaly?
        while True:
            # TODO: conditon lai ieks queue samestos jobus ar ops/s throtletu
            task = self.task_queue.get()
            if task is None: # Poison!
                self.logger.info('Poisoned!')
                self.task_queue.task_done()
                break
            else:
                start_time = time.time()
                self.connection.insert(task, fully_formed=True)
                end_time = time.time()
                self.result_queue.put(end_time-start_time)
                self.task_queue.task_done()
        return
