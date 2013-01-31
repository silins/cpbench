import bases

##############################
# Worker Master class.
##############################
class WorkerMaster(bases.WorkerMaster):
    def __init__(self, logger, options):
        bases.WorkerMaster.__init__(self, logger, options)
        self.con_kwargs['document_root_xpath'] = 'page'

    def common_run(self):
        bases.WorkerMaster.common_run(self)

    def common_prep(self):
        bases.WorkerMaster.common_prep(self)

##############################
# Worker class.
##############################
class Worker(bases.Worker):
    def prep_load(self):
        bases.Worker.prep_load(self)

    def run_load(self):
        bases.Worker.run_load(self)
