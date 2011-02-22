from task import Task
from tardis.tardis_portal.models import DatasetParameter
from tardis.tardis_portal.models import Schema
from tardis.tardis_portal.models import ParameterName
from django.core.exceptions import ObjectDoesNotExist


class MRtask(Task):
    type = "mrtardis"

    @staticmethod
    def getTaskList(experiment, status="any"):
        """
        yields DatasetParameterSet
        """
        DPSs = Task.getTaskList(experiment, type=MRtask.type)
        #else:
        for dps in DPSs:
            if status == "any":
                yield dps
            else:
                try:
                    schema = Schema.objects.get(
                        namespace__endswith=MRtask.type)
                    parname = ParameterName.objects.get(name="TaskStatus",
                                                        schema=schema)
                    if status == DatasetParameter.objects.get(
                        parameterset=dps, name=parname).string_value:
                        yield dps
                except ObjectDoesNotExist:
                    pass
