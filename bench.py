#! /usr/bin/env python2

def main(options, task_name):
    import imp
    import logging
    import multiprocessing

    logger = multiprocessing.log_to_stderr()
    if options.debug:
        logging_level = logging.DEBUG
    elif options.verbose:
        logging_level = logging.INFO
    else:
        logging_level = logging.WARNING
    logger.setLevel(logging_level)
    logger.debug("Options:\n" + repr(options))
    logger.debug("Args:\n" + repr(args))

    task_module = imp.load_module(task_name, *imp.find_module(task_name,
                                    [options.task_path]))
    task_master = task_module.TaskMaster(logger, options)
    task_master.run()


if __name__ == '__main__':
    import optparse
    import sys

    # TODO: more convinient/automatic way to pass clusterpoint connection data
    usage = "usage: %prog [options] task_module_name"
    parser = optparse.OptionParser(usage=usage)
    group = optparse.OptionGroup(parser, "Connection options")
    group.add_option("-u", "--url", action="append", type="string",
                        default=None,
                        help="target storage url, can be mutiple")
    group.add_option("-n", "--name", action="store", type="string",
                        default='test_storage',
                        help="target storage name [default 'test_storage']")
    group.add_option("--user", action="store", type="string",
                        default="root",
                        help="username [default 'root']")
    group.add_option("--password", action="store", type="string",
                        default="password",
                        help="password [default 'password']")
    parser.add_option_group(group)

    group = optparse.OptionGroup(parser, "Benchmark test options")
    group.add_option("--task_path", action="store", type="string",
                        default='.',
                        help="path to task module [default '.']")
    group.add_option("-p", "--proc_count", action="store",type="int",
                        default=1,
                        help="number of paralel tasks to run [default 1]")
    parser.add_option_group(group)

    parser.add_option("-v", "--verbose", action="store_true",
                        default=False,
                        help="make lots of noise [default false]")
    parser.add_option("--debug", action="store_true",
                        default=False,
                        help="make even more noise [default false]")

    (options, args) = parser.parse_args()

    if options.url is None:
        print("No storage url given!")
        sys.exit(1)

    sys.exit(main(options, *args))
