from tardis.tardis_portal.models import DatasetParameterSet


class Task():
    schema = "http://localhost/task"

    def __init__(self, dataset=None):
        """
        instantiate new task or existing task
        :param dataset: optional parameter to instanciate task from
          metadata, will be tested for completeness and copied into
          new task if complete
        :type dataset: Dataset
        """
        if dataset:
            # read dataset metadata into Task instance
            self.taskdata = dataset.get_metadata(schema=Task.schema)
        else:
            # create new Task
            self.taskdata = dict()
        return True

    @staticmethod
    def getTaskList(experiment, type="all"):
        """
        Get list of all tasks or specify the type as string
        :param experiment: the experiment that is being searched for tasks
        :type experiment: Experiment
        :param type: the type of task to search for as defined
            in the schema name
        :type type: string
        yields DatasetParameterSet
        """
        schema = Task.schema
        if type != "all":
            schema += "/" + type
        DPSs = DatasetParameterSet.objects.filter(
            schema__namespace__startswith=schema)
        return DPSs
