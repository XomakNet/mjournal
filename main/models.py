from datetime import datetime

from django.db.models import Manager
from django.db import models


class MaintenanceLinkManager(Manager):
    def pending_links(self, limit=None, parent_object=None, future_days=0):
        params = []
        limit_substitution = ""
        objects_substitution = ""
        raw_query = "SELECT links.*, objects.*, types.*, " \
                    "MAX(maintenance_date) AS last_date, " \
                    "datetime(MAX(maintenance_date),'+'||links.periodicity||' days') AS due_date " \
                    "FROM {link_table} AS links " \
                    "LEFT JOIN {event_table} AS events ON " \
                    "links.maintenance_object_id = events.maintenance_object_id AND " \
                    "links.maintenance_type_id = events.maintenance_type_id " \
                    "INNER JOIN {objects_table} AS objects ON links.maintenance_object_id=objects.id " \
                    "INNER JOIN {types_table} AS types ON links.maintenance_type_id=types.id " \
                    "WHERE links.periodicity IS NOT NULL " \
                    "{objects_substitution}" \
                    "GROUP BY links.maintenance_object_id, links.maintenance_type_id " \
                    "HAVING due_date < datetime(CURRENT_TIMESTAMP,'+{future_days} days') OR due_date IS NULL " \
                    "ORDER BY due_date ASC{limit_substitution}"

        if parent_object is not None:
            children_ids = [obj.id for obj in parent_object.get_children()]
            children_ids.append(parent_object.id)
            for child_id in children_ids:
                objects_substitution += ',' if len(objects_substitution) > 0 else ''
                objects_substitution += '%s'
                params.append(child_id)
            objects_substitution = " AND links.maintenance_object_id IN ({})".format(objects_substitution) if len(
                objects_substitution) > 0 else ''

        if limit is not None:
            limit_substitution = " LIMIT 0, %s"
            params.append(limit)

        raw_query = raw_query.format(link_table=MaintenanceLink._meta.db_table,
                                     event_table=MaintenanceEvent._meta.db_table,
                                     objects_table=MaintenanceObject._meta.db_table,
                                     types_table=MaintenanceObject._meta.db_table,
                                     objects_substitution=objects_substitution,
                                     limit_substitution=limit_substitution,
                                     future_days=int(future_days)
                                     )
        query = self.raw(raw_query, params)
        result = []
        for link in query:
            if link.due_date is not None:
                link.due_date = datetime.strptime(link.due_date, "%Y-%m-%d %H:%M:%S")
            if link.last_date is not None:
                link.last_date = datetime.strptime(link.last_date, "%Y-%m-%d %H:%M:%S")
            result.append(link)
        return result


class MaintenanceEventManager(Manager):
    def events_for(self, required_object):
        required_objects_ids = [obj.id for obj in required_object.get_children()]
        required_objects_ids.append(required_object.id)
        return self.filter(maintenance_object__in=required_objects_ids).order_by(
            '-maintenance_date')


class MaintenanceObject(models.Model):
    """
    Object, which can be maintained (e.g. computer, server)
    """

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    parent = models.ForeignKey("self", blank=True, null=True)

    def __str__(self):
        return self.title

    def get_children(self):
        parent_id = self.id
        raw_query = 'WITH RECURSIVE r AS (SELECT * ' \
                    'FROM {table_name} AS found_items ' \
                    'WHERE id = %s ' \
                    'UNION ' \
                    'SELECT new_items.* ' \
                    'FROM {table_name}  AS new_items ' \
                    '   JOIN r ON new_items.parent_id = r.id) ' \
                    'SELECT * ' \
                    'FROM r'.format(table_name=MaintenanceObject._meta.db_table)
        result = list(MaintenanceObject.objects.raw(raw_query, [parent_id]))
        result.reverse()
        result.pop()
        return result

    def get_parents(self):
        raw_query = 'WITH RECURSIVE r AS (SELECT * ' \
                    'FROM {table_name} AS found_items ' \
                    'WHERE id = %s ' \
                    'UNION ' \
                    'SELECT new_items.* ' \
                    'FROM {table_name}  AS new_items ' \
                    '   JOIN r ON new_items.id = r.parent_id) ' \
                    'SELECT * ' \
                    'FROM r'.format(table_name=MaintenanceObject._meta.db_table)

        result = list(MaintenanceObject.objects.raw(raw_query, [self.id]))
        result.reverse()
        result.pop()
        return result


class MaintenanceType(models.Model):
    """
    Type of maintenance (e.g. cleaning, battery replacement)
    """

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    parent = models.ForeignKey("self", blank=True, null=True)

    def __str__(self):
        return self.title


class MaintenanceEvent(models.Model):
    """
    Maintenance event (e.g. cleaning of computer at 17:11 on 16.01.2017)
    """

    maintenance_object = models.ForeignKey(MaintenanceObject)
    maintenance_type = models.ForeignKey(MaintenanceType)
    maintenance_date = models.DateTimeField()
    comment = models.TextField(blank=True)

    objects = MaintenanceEventManager()

    def __str__(self):
        return "{} at {}".format(self.maintenance_type, self.maintenance_date)


class MaintenanceLink(models.Model):
    """
    Logical connection between maintenance object and type (e.g. computer can be cleaned)
    """

    maintenance_object = models.ForeignKey(MaintenanceObject, related_name="links")
    maintenance_type = models.ForeignKey(MaintenanceType, related_name="links")
    periodicity = models.IntegerField(blank=True, null=True)

    class Meta:
        unique_together = ("maintenance_object", "maintenance_type")

    objects = MaintenanceLinkManager()

    def __str__(self):
        return "{} is applicable to {}".format(self.maintenance_type, self.maintenance_object)
