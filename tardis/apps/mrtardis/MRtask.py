from task import Task


class MRtask(Task):
    schema = "http://localhost/task/mrtardis"
    type = "msg"

    @staticmethod
    def getTaskList():
        return super(MRtask).getTaskList(type=MRtask.type)
