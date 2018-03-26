# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2018-03-26 15:21
from __future__ import unicode_literals, print_function

from django.db import migrations, connection


DUPES_QUERY = '''
SELECT
  `dupes`.`user_id`,
  `dupes`.`experiment_id`,
  COUNT(*) AS dupe_count
FROM (

  SELECT
    `experiments_experimentdisablement`.`id`,
    `experiments_experimentdisablement`.`user_id`,
    `experiments_experimentdisablement`.`experiment_id`,
    CONCAT(`experiments_experimentdisablement`.`user_id`,
           CONCAT('-', `experiments_experimentdisablement`.`experiment_id`)
    ) AS `user_exp`
  FROM `experiments_experimentdisablement`
) AS dupes
GROUP BY `dupes`.`user_exp`
HAVING `dupe_count` > 1
ORDER BY `id` DESC
'''


def dedupe(apps, schema_editor):
    ExperimentDisablement = apps.get_model('experiments', 'ExperimentDisablement')
    if not ExperimentDisablement.objects.all().exists():
        return

    qs = ExperimentDisablement.objects.all().order_by('-id')

    def clear_dupes():
        with connection.cursor() as cursor:
            cursor.execute(DUPES_QUERY)
            rows = cursor.fetchall()
        cleared_pairs = 0
        for user_id, experiment_id, dupe_count in rows:
            dupe_qs = qs.filter(user_id=user_id, experiment_id=experiment_id)
            last_id = dupe_qs.first().id
            dupe_qs.filter(id__lt=last_id).delete()
            cleared_pairs += 1
        return cleared_pairs

    for cleared in iter(clear_dupes, 0):
        print(' {}...'.format(cleared), end='')


class Migration(migrations.Migration):

    dependencies = [
        ('experiments', '0005_experiment_disablement_model'),
    ]

    operations = [
        migrations.RunPython(dedupe, reverse_code=migrations.RunPython.noop),
        migrations.AlterUniqueTogether(
            name='experimentdisablement',
            unique_together=set([('user', 'experiment')]),
        ),
    ]
