### Fill in the following information before submitting
# Group id: 
# Members: 



from collections import deque

# PID is just an integer, but it is used to make it clear when a integer is expected to be a valid PID.
PID = int

# This class represents the PCB of processes.
# It is only here for your convinience and can be modified however you see fit.
class PCB:
    pid: PID

    def __init__(self, pid: PID, priority: int = float('inf')):
        self.pid = pid
        self.priority = priority
        self.should_exit = False


# This class represents the Kernel of the simulation.
# The simulator will create an instance of this object and use it to respond to syscalls and interrupts.
# DO NOT modify the name of this class or remove it.
class Kernel:
    scheduling_algorithm: str
    ready_queue: deque[PCB]
    waiting_queue: deque[PCB]
    running: PCB
    idle_pcb: PCB

    # Called before the simulation begins.
    # Use this method to initilize any variables you need throughout the simulation.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def __init__(self, scheduling_algorithm: str):
        self.scheduling_algorithm = scheduling_algorithm
        self.ready_queue: deque[PCB] = deque()
        self.waiting_queue = deque()
        self.idle_pcb = PCB(0)
        self.running = self.idle_pcb

    # This method is triggered every time a new process has arrived.
    # new_process is this process's PID.
    # priority is the priority of new_process.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def new_process_arrived(self, new_process: PID, priority: int) -> PID:
        self.ready_queue.append(PCB(new_process, priority))
        return self.choose_next_process()

    # This method is triggered every time the current process performs an exit syscall.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def syscall_exit(self) -> PID:
        self.running.should_exit = True
        return self.choose_next_process()

    # This method is triggered when the currently running process requests to change its priority.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def syscall_set_priority(self, new_priority: int) -> PID:
        self.running.priority = new_priority
        return self.choose_next_process()


    # This is where you can select the next process to run.
    # This method is not directly called by the simulator and is purely for your convinience.
    # Feel free to modify this method as you see fit.
    # It is not required to actually use this method but it is recommended.
    def choose_next_process(self):
        # First Come First Serve
        if self.scheduling_algorithm == "FCFS":
            # If there is no process running or if the current process has finished, replace it with the next process
            if (self.running == self.idle_pcb) or self.running.should_exit:
                self.running = self.ready_queue.popleft() if len(self.ready_queue) > 0 else self.idle_pcb
                return self.running.pid
            return self.running.pid

        # Priority
        elif self.scheduling_algorithm == "Priority":
            # If the current process has finished, stop it and remove from consideration
            if self.running.should_exit:
                self.running = self.idle_pcb

            # Find the process with the highest priority and min pid (for tie breaking)
            min_priority = float('inf')
            min_pid = float('inf')
            min_pcb = None
            for process in [i for i in self.ready_queue] + [self.running]: # Also consider the current running process
                if process.priority < min_priority:
                    min_priority = process.priority
                    min_pid = process.pid
                    min_pcb = process
                elif process.priority == min_priority and process.pid < min_pid:
                    min_priority = process.priority
                    min_pid = process.pid
                    min_pcb = process
            
            # If the current running process is the one with highest priority, do nothing
            if self.running.pid == min_pid:
                return self.running.pid
            
            # Add the current running process back to the ready queue
            self.ready_queue.append(self.running)
            
            # Set the new running process to the one with highest priority and remove it from the ready queue
            self.running = min_pcb
            self.ready_queue.remove(min_pcb)

            # Return the new running process
            return self.running.pid
