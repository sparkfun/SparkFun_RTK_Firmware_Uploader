import time
import queue
from threading import Thread
from .au_action import AxAction, AxJob
from contextlib import redirect_stdout, redirect_stderr

#--------------------------------------------------------------------------------------
# AUxIOWedge
#
# Used to redirect/capture output chars from the print() function and redirect to our
# console. Allows the use of command line routines in this GUI app


from io import TextIOWrapper, BytesIO


class AUxIOWedge(TextIOWrapper):
    def __init__(self, output_funct, suppress=False, newline="\n"):
        super(AUxIOWedge, self).__init__(BytesIO(),
                                        encoding="utf-8",
                                        errors="surrogatepass",
                                        newline=newline)

        self._output_func = output_funct
        self._suppress = suppress

    def write(self, buffer):

        # Just send buffer to our output console
        if not self._suppress:
            self._output_func(buffer)

        return len(buffer)
#--------------------------------------------------------------------------------------
# Worker thread to manage background jobs passed in via a queue

# define a worker class/thread

class AUxWorker(object):

    TYPE_MESSAGE    = 1
    TYPE_FINISHED   = 2

    def __init__(self, cb_function):

        object.__init__(self)

        # create a standard python queue = the queue is used to communicate
        # work to the background thread in a safe manner.  "Jobs" to do
        # are passed to the background thread via this queue
        self._queue = queue.Queue()

        self._cb_function = cb_function

        self._shutdown = False;

        # stash of registered actions
        self._actions = {}

        # throw the work/job into a thread
        self._thread = Thread(target = self.process_loop, args=(self._queue,))
        self._thread.start()

    # Make sure the thread stops running in Destructor. And add shutdown user method
    def __del__(self):

        self._shutdown = True

    def shutdown(self):

        self._shutdown = True

    #------------------------------------------------------
    # Add a execution type/object (an AxAction) to our available
    # job type list

    def add_action(self, *argv) -> None:

        for action in argv:
            if not isinstance(action, AxAction):
                print("Parameter is not of type AxAction" + str(type(action)))
                continue 
            self._actions[action.action_id] = action


    #------------------------------------------------------
    # Add a job for execution by the background thread.
    #
    def add_job(self, theJob:AxJob)->None:

        # just enqueue the job

        self._queue.put(theJob)

    #------------------------------------------------------    
    # call back function for output from the bootloader - called from our IO wedge class.
    #
    def message(self, message):

        # relay/post message to the GUI's console

        self._cb_function(self.TYPE_MESSAGE, message)
    #------------------------------------------------------
    # Job dispatcher. Job should be an AxJob object instance.
    # 
    # retval  0 = OKAY

    def dispatch_job(self, job):

        # make sure we have a job
        if not isinstance(job, AxJob):
            self.message("ERROR - invalid job dispatched\n")
            return 1

        # is the target action in our available actions dictionary?
        if job.action_id not in self._actions:
            self.message("Unknown job type. Aborting\n")
            return 1

        # write out the job
        # send a line break across the console - start of a new activity
        self.message('\n' + ('_'*70) + "\n")

        # Job details
        self.message(self._actions[job.action_id].name + "\n\n")
        for key in sorted(job.keys()):
            self.message(key.capitalize() + ":\t" + str(job[key]) + '\n')

        self.message('\n')

        # capture stdio and stderr outputs
        with redirect_stdout(AUxIOWedge(self.message)):
            with redirect_stderr(AUxIOWedge(self.message, suppress=True)):

                # catch any exit() calls the underlying system might make
                try:
                    # run the action
                    return self._actions[job.action_id].run_job(job)
                except SystemExit as  error:
                    # some scripts call exit(), even if not an error
                    self.message("Complete.")

        return 1

    #------------------------------------------------------
    # The thread processing loop

    def process_loop(self, inputQueue):

        # Wait on jobs .. forever... Exit when shutdown is true

        self._shutdown = False

        # run
        while not self._shutdown:

            if inputQueue.empty():
                time.sleep(1)  # no job, sleep a bit
            else:
                job = inputQueue.get()

                status = self.dispatch_job(job)

                # job is finished - let UX know
                self._cb_function(self.TYPE_FINISHED, status)
