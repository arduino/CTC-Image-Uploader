import Queue, threading
import time

class ThreadWork:
	def __init__(self):
		self.queue=Queue.Queue()

	def addTask(self, task):
		#print task
		self.queue.put(task)

	def join(self):
		self.queue.join()



class MultiThreadWork(ThreadWork):
	def __init__(self, num_workers=3):
		ThreadWork.__init__(self)
		self.makeWorkers(num_workers)

	def setActualTask(self, func):
		self.actualTask=func

	def processing(self):
		return self.queue.qsize()>0


	def makeWorkers(self,num_workers):
		for i in range(num_workers):
			worker=threading.Thread(target=self.taskRunner,args=(i,self.queue))
			worker.setDaemon(True)
			worker.start()

	def taskRunner(self, index,queue):
		while True:
			task=queue.get()
			self.actualTask(index, task)
			queue.task_done()

class MultiTaskSingleThreadWork(ThreadWork):
	def __init__(self):
		ThreadWork.__init__(self)
		self.runnerTable={}

	def addTask(self, task_name, content):
		self.queue.put({"task_name":task_name,"content":content})

	def addActualTaskType(self, task_name, func):
		self.runnerTable[task_name]=func

	def process(self):
		while True:
			try:
				task=self.queue.get(False)
			except Queue.Empty:
				break
			self.runnerTable[task["task_name"]](task["content"])



if __name__=="__main__":
	tw=MultiThreadWork(3)
	tw2=MultiTaskSingleThreadWork()

	def acf(workerIndex, task):
		print "worker {} doing {}".format(workerIndex,task)
		tn="eat dinner" if task%2==0 else "mow lawn"
		tw2.addTask({"task_name":tn, "value":task})
		time.sleep(0.1)

	def runner1(task):
		print "eat dinner {}".format(task["value"])

	def runner2(task):
		print "mow lawn {}".format(task["value"])	


	tw.setActualTask(acf)

	tw2.addActualTaskType("eat dinner",runner1)
	tw2.addActualTaskType("mow lawn",runner2)

	for i in range(30):
		tw.addTask(i)

	while tw.processing():
		tw2.process()
	tw.join()
	tw2.process()
	