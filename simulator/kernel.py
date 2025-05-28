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
    
    def __repr__(self):
        return f"PCB(pid={self.pid}, priority={self.priority}, should_exit={self.should_exit})"


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
    def __init__(self, scheduling_algorithm: str, logger):
        self.scheduling_algorithm = scheduling_algorithm
        self.ready_queue: deque[PCB] = deque()
        self.waiting_queue = deque()
        self.idle_pcb = PCB(0)
        self.running = self.idle_pcb
        self.logger = logger
        self.time = 0
        self.last_time_checked = -1000

        # For multilevel only
        self.foreground_queue = deque()
        self.background_queue = deque()
        self.current_level = None
        self.last_level_changed = -1000

    # This method is triggered every time a new process has arrived.
    # new_process is this process's PID.
    # priority is the priority of new_process.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def new_process_arrived(self, new_process: PID, priority: int, process_type: str) -> PID:
        if self.scheduling_algorithm == "Multilevel":
            if process_type == "Foreground":
                self.foreground_queue.append(PCB(new_process, priority))
            else:
                self.background_queue.append(PCB(new_process, priority))
        else:
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
        match self.scheduling_algorithm:
            case "FCFS":
                return self.first_come_first_serve()
            case "Priority":
                return self.priority()
            case "RR":
                x = self.round_robin()
                return x
            case "Multilevel":
                x = self.multilevel()
                self.logger.log(x)
                return x
            case _:
                raise NotImplementedError(f"Invalid scheduling algorithm: {self.scheduling_algorithm}")
    
    def first_come_first_serve(self):
        # If there is no process running or if the current process has finished, replace it with the next process
        if (self.running == self.idle_pcb) or self.running.should_exit:
            self.running = self.ready_queue.popleft() if len(self.ready_queue) > 0 else self.idle_pcb
            return self.running.pid
        return self.running.pid
    
    def priority(self):
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
    
    def round_robin(self):
        # Don't do anything if the quantum hasn't passed yet
        if self.time - self.last_time_checked < 40:
            if self.running.should_exit or self.running == self.idle_pcb:
                self.running = self.ready_queue.popleft() if len(self.ready_queue) > 0 else self.idle_pcb
                self.last_time_checked = self.time - self.time % 10
            return self.running.pid
        
        self.last_time_checked = self.time

        # Case: If current process is running and it hasn't finished add it back to the ready queue
        if not self.running == self.idle_pcb and not self.running.should_exit:
            self.ready_queue.append(self.running)
        
        # Get next process from ready queue
        self.running = self.ready_queue.popleft() if len(self.ready_queue) > 0 else self.idle_pcb
        return self.running.pid
    
    def multilevel(self):
        self.logger.log(f"Current level: {self.current_level}")
        self.logger.log(f"Foreground queue: {self.foreground_queue}")
        self.logger.log(f"Background queue: {self.background_queue}")
        # If nothing has ran yet
        if self.current_level is None:
            if len(self.foreground_queue) > 0:
                self.current_level = "Foreground"
                self.running = self.foreground_queue.popleft()
                self.logger.log(f"Current level: {self.current_level}")
            elif len(self.background_queue) > 0:
                self.current_level = "Background"
                self.running = self.background_queue.popleft()
                self.logger.log(f"Current level: {self.current_level}")
            else:
                self.current_level = None
                self.logger.log(f"Current level: {self.current_level}")
                return self.running.pid
            

        self.logger.log(f"Time: {self.time}, Last level changed: {self.last_level_changed}, Time - Last level changed: {self.time - self.last_level_changed}")
        current_queue = self.foreground_queue if self.current_level == "Foreground" else self.background_queue
        if (self.time - self.last_level_changed >= (200 if not self.running.should_exit else 190)) or (len(current_queue) == 0 and self.running.should_exit) or (self.running == self.idle_pcb):
            if self.current_level == "Foreground" and len(self.background_queue) > 0:
                self.current_level = "Background"
                if not self.running.should_exit:
                    self.foreground_queue.append(self.running)
                self.logger.log("Moving to background")
                self.running = self.idle_pcb
            elif self.current_level == "Background" and len(self.foreground_queue) > 0:
                self.current_level = "Foreground"
                if not self.running.should_exit:
                    self.background_queue.appendleft(self.running)
                self.logger.log("Moving to foreground")
                self.running = self.idle_pcb

            self.last_level_changed = self.time


        if self.current_level == "Foreground":
            ############## ROUND ROBIN ##############
            # Don't do anything if the quantum hasn't passed yet
            if self.time - self.last_time_checked < 40:
                if self.running.should_exit or self.running == self.idle_pcb:
                    self.running = self.foreground_queue.popleft() if len(self.foreground_queue) > 0 else self.idle_pcb
                    self.last_time_checked = self.time - self.time % 10
                return self.running.pid
            
            self.last_time_checked = self.time

            # Case: If current process is running and it hasn't finished add it back to the ready queue
            if not self.running == self.idle_pcb and not self.running.should_exit:
                self.foreground_queue.append(self.running)
            
            # Get next process from ready queue
            self.running = self.foreground_queue.popleft() if len(self.foreground_queue) > 0 else self.idle_pcb
            return self.running.pid
            ############## ROUND ROBIN ##############
        
        elif self.current_level == "Background":
            ############## FCFS ##############
            if self.running.should_exit or self.running == self.idle_pcb:
                self.running = self.background_queue.popleft() if len(self.background_queue) > 0 else self.idle_pcb
                return self.running.pid
            ############## FCFS ##############
        
        else:
            raise Exception("Invalid level")
        
    

                

        return self.running.pid

    # This method is triggered when the currently running process requests to initialize a new semaphore.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def syscall_init_semaphore(self, semaphore_id: int, initial_value: int):
        return
    
    # This method is triggered when the currently running process calls p() on an existing semaphore.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def syscall_semaphore_p(self, semaphore_id: int) -> PID:
        return self.running.pid

    # This method is triggered when the currently running process calls v() on an existing semaphore.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def syscall_semaphore_v(self, semaphore_id: int) -> PID:
        return self.running.pid

    # This method is triggered when the currently running process requests to initialize a new mutex.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def syscall_init_mutex(self, mutex_id: int):
        return

    # This method is triggered when the currently running process calls lock() on an existing mutex.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def syscall_mutex_lock(self, mutex_id: int) -> PID:
        return self.running.pid


    # This method is triggered when the currently running process calls unlock() on an existing mutex.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def syscall_mutex_unlock(self, mutex_id: int) -> PID:
        return self.running.pid

    # This function represents the hardware timer interrupt.
    # It is triggered every 10 microseconds and is the only way a kernel can track passing time.
    # Do not use real time to track how much time has passed as time is simulated.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def timer_interrupt(self) -> PID:
        self.time += 10
        self.choose_next_process()
        return self.running.pid