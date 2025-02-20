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

from rest_framework import serializers


class SchemesSerizlializer(serializers.Serializer):
    data = serializers.CharField()
    name = serializers.CharField(max_length=64)


class TemplateSchemeSerializer(SchemesSerizlializer):
    id = serializers.IntegerField(read_only=True)


class ParamsSerializer(serializers.Serializer):
    """
    查询及批量创建序列化使用
    """

    project_id = serializers.IntegerField()
    template_id = serializers.IntegerField()
    schemes = serializers.ListField(required=False)
