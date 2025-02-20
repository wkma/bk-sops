# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making 蓝鲸智云PaaS平台社区版 (BlueKing PaaS Community
Edition) available.
Copyright (C) 2017-2021 THL A29 Limited, a Tencent company. All rights reserved.
Licensed under the MIT License (the "License"); you may not use this file except in compliance with the License.
You may obtain a copy of the License at
http://opensource.org/licenses/MIT
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.
"""


from __future__ import unicode_literals

from django.db import migrations, connection

from data_migration.utils import dictfetchall, old_uer_table_exist
from data_migration.conf import settings
from pprint import pprint


def apply_alter(reverse=False):
    with connection.cursor() as cursor:
        pprint(settings.CONSTRAINT_MIGRATIONS)
        for mig in settings.CONSTRAINT_MIGRATIONS:
            table = mig['table']
            for c in mig['columns']:
                cursor.execute(
                    'select *'
                    'from information_schema.KEY_COLUMN_USAGE '
                    'where TABLE_NAME = %s and REFERENCED_TABLE_NAME = %s and COLUMN_NAME = %s and '
                    'REFERENCED_TABLE_SCHEMA = %s',
                    [table,
                     c['new_ref_table'] if reverse else c['origin_ref_table'],
                     c.get('new_name', c['origin_name']) if reverse else c['origin_name'],
                     cursor.db.settings_dict['NAME']])
                rows = dictfetchall(cursor)
                if rows:
                    constraint_name = rows[0]['CONSTRAINT_NAME']
                    ref_field = rows[0]['REFERENCED_COLUMN_NAME']
                    # drop constrain first
                    cursor.execute('ALTER TABLE `%s` DROP FOREIGN KEY `%s`; ' %
                                   (table,
                                    constraint_name))

                    if 'new_name' in c:
                        cursor.execute('SHOW COLUMNS FROM `%s` WHERE Field = \'%s\'' %
                                       (table,
                                        c['new_name'] if reverse else c['origin_name']))
                        c_type = dictfetchall(cursor)[0]['Type']
                        cursor.execute('ALTER TABLE `%s` CHANGE %s %s %s' % (
                            table,
                            c['new_name'] if reverse else c['origin_name'],
                            c['origin_name'] if reverse else c['new_name'],
                            c_type
                        ))

                    # add constrain
                    cursor.execute('ALTER TABLE `%s`  ADD CONSTRAINT `%s` '
                                   'FOREIGN KEY (`%s`) REFERENCES `%s` (`%s`);' %
                                   (table,
                                    constraint_name,
                                    c['origin_name'] if reverse else c.get('new_name', c['origin_name']),
                                    c['origin_ref_table'] if reverse else c['new_ref_table'],
                                    c.get('ref_field', ref_field)))


def reverse_func(apps, schema_editor):
    if not old_uer_table_exist():
        return

    apply_alter(reverse=True)


def forward_func(apps, schema_editor):
    if not old_uer_table_exist():
        return

    apply_alter(reverse=False)


class Migration(migrations.Migration):
    dependencies = [
        ('data_migration', '0001_user_migration'),
    ]

    operations = [
        migrations.RunPython(forward_func, reverse_func)
    ]
