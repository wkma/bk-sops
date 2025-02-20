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

import re
import logging

from django import forms
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from tastypie import fields
from tastypie.authorization import ReadOnlyAuthorization
from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie.exceptions import BadRequest, NotFound
from tastypie.validation import FormValidation

from iam.contrib.tastypie.authorization import ReadOnlyCompleteListIAMAuthorization
from iam.contrib.tastypie.authorization import IAMUpdateAuthorizationMixin

from pipeline.component_framework.constants import LEGACY_PLUGINS_VERSION
from pipeline.component_framework.library import ComponentLibrary
from pipeline.component_framework.models import ComponentModel
from pipeline.variable_framework.models import VariableModel
from pipeline_web.label.models import LabelGroup, Label
from pipeline_web.plugin_management.utils import DeprecatedPlugin
from pipeline.exceptions import ComponentNotExistException

from gcloud.core.models import Business, Project, ProjectCounter, ProjectBasedComponent
from gcloud.commons.tastypie import GCloudModelResource
from gcloud.iam_auth import IAMMeta, get_iam_client
from gcloud.iam_auth.utils import get_user_projects
from gcloud.iam_auth.resource_helpers import SimpleResourceHelper
from gcloud.iam_auth.authorization_helpers import ProjectIAMAuthorizationHelper

logger = logging.getLogger("root")
iam = get_iam_client()
group_en_pattern = re.compile(r"(?:\()(.*)(?:\))")


class BusinessResource(GCloudModelResource):
    class Meta(GCloudModelResource.CommonMeta):
        queryset = Business.objects.exclude(status="disabled").exclude(
            life_cycle__in=[Business.LIFE_CYCLE_CLOSE_DOWN, _("停运")]
        )
        authorization = ReadOnlyAuthorization()
        resource_name = "business"
        detail_uri_name = "cc_id"
        filtering = {
            "cc_id": ALL,
            "cc_name": ALL,
            "cc_owner": ALL,
            "cc_company": ALL,
        }


class ProjectForm(forms.Form):
    name = forms.CharField(max_length=256)
    desc = forms.CharField(max_length=512, required=False)


class ProjectAuthorization(IAMUpdateAuthorizationMixin, ReadOnlyCompleteListIAMAuthorization):
    pass


class ProjectResource(GCloudModelResource):
    create_at = fields.DateTimeField(attribute="create_at", readonly=True)
    from_cmdb = fields.BooleanField(attribute="from_cmdb", readonly=True)
    bk_biz_id = fields.IntegerField(attribute="bk_biz_id", readonly=True)

    ALLOW_UPDATE_FIELD = ["desc", "is_disable"]

    class Meta(GCloudModelResource.CommonMeta):
        queryset = Project.objects.all().order_by("-id")
        validation = FormValidation(form_class=ProjectForm)
        resource_name = "project"
        filtering = {
            "id": ALL,
            "name": ALL,
            "creator": ALL,
            "from_cmdb": ALL,
            "bk_biz_id": ALL,
            "is_disable": ALL,
        }
        q_fields = ["id", "name", "desc", "creator"]
        # iam config
        authorization = ProjectAuthorization(
            iam=iam,
            helper=ProjectIAMAuthorizationHelper(
                system=IAMMeta.SYSTEM_ID,
                create_action=None,
                read_action=IAMMeta.PROJECT_VIEW_ACTION,
                update_action=IAMMeta.PROJECT_EDIT_ACTION,
                delete_action=None,
            ),
        )
        iam_resource_helper = SimpleResourceHelper(
            type=IAMMeta.PROJECT_RESOURCE,
            id_field="id",
            creator_field=None,
            name_field="name",
            iam=iam,
            system=IAMMeta.SYSTEM_ID,
            actions=[
                IAMMeta.PROJECT_VIEW_ACTION,
                IAMMeta.PROJECT_EDIT_ACTION,
                IAMMeta.FLOW_CREATE_ACTION,
                IAMMeta.PROJECT_FAST_CREATE_TASK_ACTION,
            ],
        )

    def obj_create(self, bundle, **kwargs):
        bundle.data["creator"] = bundle.request.user.username
        return super(ProjectResource, self).obj_create(bundle, **kwargs)

    def obj_update(self, bundle, skip_errors=False, **kwargs):
        update_data = {}
        for field in self.ALLOW_UPDATE_FIELD:
            update_data[field] = bundle.data.get(field, getattr(bundle.obj, field))

        bundle.data = update_data

        return super(ProjectResource, self).obj_update(bundle, skip_errors, **kwargs)

    def obj_delete(self, bundle, **kwargs):
        raise BadRequest("can not delete project")


class UserProjectResource(GCloudModelResource):
    class Meta(GCloudModelResource.CommonMeta):
        queryset = Project.objects.all().order_by("-id")
        resource_name = "user_project"
        filtering = {"is_disable": ALL}
        q_fields = ["id", "name", "desc", "creator"]
        authorization = ProjectAuthorization(
            iam=iam,
            helper=ProjectIAMAuthorizationHelper(
                system=IAMMeta.SYSTEM_ID,
                create_action=None,
                read_action=IAMMeta.PROJECT_VIEW_ACTION,
                update_action=IAMMeta.PROJECT_EDIT_ACTION,
                delete_action=None,
            ),
        )
        iam_resource_helper = SimpleResourceHelper(
            type=IAMMeta.PROJECT_RESOURCE,
            id_field="id",
            creator_field=None,
            name_field="name",
            iam=iam,
            system=IAMMeta.SYSTEM_ID,
            actions=[
                IAMMeta.PROJECT_VIEW_ACTION,
                IAMMeta.PROJECT_EDIT_ACTION,
                IAMMeta.FLOW_CREATE_ACTION,
                IAMMeta.PROJECT_FAST_CREATE_TASK_ACTION,
            ],
        )

    def obj_get(self, bundle, **kwargs):
        raise BadRequest("invalid operation")

    def get_object_list(self, request):
        projects = get_user_projects(request.user.username)
        return projects


class ComponentModelResource(GCloudModelResource):
    class Meta(GCloudModelResource.CommonMeta):
        queryset = ComponentModel.objects.filter(status=True).order_by("name")
        resource_name = "component"
        excludes = ["status", "id"]
        detail_uri_name = "code"
        authorization = ReadOnlyAuthorization()

    def build_filters(self, filters=None, ignore_bad_filters=False):
        orm_filters = super(ComponentModelResource, self).build_filters(
            filters=filters, ignore_bad_filters=ignore_bad_filters
        )
        if filters and "version" in filters:
            orm_filters["version"] = filters.get("version") or LEGACY_PLUGINS_VERSION

        if filters and "project_id" in filters:
            project_id = filters.pop("project_id")
            # 处理list接口和detail接口获取到project_id形式不同的情况
            project_id = project_id[0] if type(project_id) is list else project_id
            exclude_component_codes = ProjectBasedComponent.objects.get_components_of_other_projects(project_id)
        else:
            exclude_component_codes = ProjectBasedComponent.objects.get_components()
        query_set = ~Q(code__in=exclude_component_codes)
        orm_filters.update({"custom_query_set": query_set})
        return orm_filters

    def apply_filters(self, request, applicable_filters):
        if "custom_query_set" in applicable_filters:
            custom_query_set = applicable_filters.pop("custom_query_set")
        else:
            custom_query_set = None
        semi_filtered = super(ComponentModelResource, self).apply_filters(request, applicable_filters)
        return semi_filtered.filter(custom_query_set) if custom_query_set else semi_filtered

    def get_detail(self, request, **kwargs):
        kwargs["version"] = request.GET.get("version", None)
        kwargs["project_id"] = request.GET.get("project_id", None)
        return super(ComponentModelResource, self).get_detail(request, **kwargs)

    def alter_list_data_to_serialize(self, request, data):

        component_phase_dict = DeprecatedPlugin.objects.get_components_phase_dict()
        altered_objects = []

        for bundle in data["objects"]:
            try:
                component = ComponentLibrary.get_component_class(bundle.data["code"], bundle.data["version"])
            except ComponentNotExistException:
                # 内存中没有读取到这个插件，故忽略掉后续的步骤避免影响整个接口的返回
                continue
            bundle.data["output"] = component.outputs_format()
            bundle.data["form"] = component.form
            bundle.data["output_form"] = component.output_form
            bundle.data["desc"] = component.desc
            bundle.data["form_is_embedded"] = component.form_is_embedded()
            # 国际化
            name = bundle.data["name"].split("-")
            bundle.data["group_name"] = _(name[0])
            bundle.data["group_icon"] = component.group_icon
            bundle.data["name"] = _(name[1])
            bundle.data["phase"] = component_phase_dict.get(bundle.data["code"], {}).get(
                bundle.data["version"], DeprecatedPlugin.PLUGIN_PHASE_AVAILABLE
            )
            group_name_en = group_en_pattern.findall(name[0] or "")
            bundle.data["sort_key_group_en"] = group_name_en[0] if group_name_en else "#"
            altered_objects.append(bundle)

        data["objects"] = altered_objects
        return data

    def alter_detail_data_to_serialize(self, request, data):
        data = super(ComponentModelResource, self).alter_detail_data_to_serialize(request, data)
        bundle = data
        try:
            component = ComponentLibrary.get_component_class(bundle.data["code"], bundle.data["version"])
        except ComponentNotExistException:
            raise NotFound("Can not found {}({})".format(bundle.data["code"], bundle.data["version"]))
        bundle.data["output"] = component.outputs_format()
        bundle.data["form"] = component.form
        bundle.data["output_form"] = component.output_form
        bundle.data["desc"] = component.desc
        bundle.data["form_is_embedded"] = component.form_is_embedded()
        # 国际化
        name = bundle.data["name"].split("-")
        bundle.data["group_name"] = _(name[0])
        bundle.data["group_icon"] = component.group_icon
        bundle.data["name"] = _(name[1])
        # 被前端插件继承js的地址
        bundle.data["base"] = component.base

        return data


class VariableModelResource(GCloudModelResource):
    name = fields.CharField(attribute="name", readonly=True, null=True)
    form = fields.CharField(attribute="form", readonly=True, null=True)
    type = fields.CharField(attribute="type", readonly=True, null=True)
    tag = fields.CharField(attribute="tag", readonly=True, null=True)
    meta_tag = fields.CharField(attribute="meta_tag", readonly=True, null=True)

    class Meta(GCloudModelResource.CommonMeta):
        queryset = VariableModel.objects.filter(status=True)
        resource_name = "variable"
        excludes = ["status", "id"]
        detail_uri_name = "code"
        authorization = ReadOnlyAuthorization()

    def alter_list_data_to_serialize(self, request, data):

        variable_phase_dict = DeprecatedPlugin.objects.get_variables_phase_dict()

        for bundle in data["objects"]:
            bundle.data["phase"] = variable_phase_dict.get(bundle.data["code"], {}).get(
                LEGACY_PLUGINS_VERSION, DeprecatedPlugin.PLUGIN_PHASE_AVAILABLE
            )

        return data


class CommonProjectResource(GCloudModelResource):
    project = fields.ForeignKey(ProjectResource, "project", full=True)

    class Meta(GCloudModelResource.CommonMeta):
        queryset = ProjectCounter.objects.all().order_by("-count")
        resource_name = "common_use_project"
        allowed_methods = ["get"]
        filtering = {
            "id": ALL,
            "username": ALL,
            "count": ALL,
        }
        q_fields = ["id", "username", "count"]

    @staticmethod
    def get_default_projects(empty_query, username):
        """初始化并返回用户有权限的项目"""

        projects = get_user_projects(username)
        if not projects:
            return ProjectCounter.objects.none()

        project_ids = projects.values_list("id", flat=True)

        # 初始化用户有权限的项目
        ProjectCounter.objects.bulk_create(
            [ProjectCounter(username=username, project_id=project_id) for project_id in project_ids]
        )

        return ProjectCounter.objects.filter(username=username, project_id__in=project_ids, project__is_disable=False)

    def get_object_list(self, request):

        query = super(GCloudModelResource, self).get_object_list(request)
        query = query.filter(username=request.user.username, project__is_disable=False)

        # 第一次访问或无被授权的项目
        if not query.exists():
            query = self.get_default_projects(query, request.user.username)

        return query


class LabelGroupModelResource(GCloudModelResource):
    code = fields.CharField(attribute="code", readonly=True)
    name = fields.CharField(attribute="name", readonly=True)

    class Meta(GCloudModelResource.CommonMeta):
        queryset = LabelGroup.objects.all()
        resource_name = "label_group"
        detail_uri_name = "id"
        authorization = ReadOnlyAuthorization()
        filtering = {"code": ALL}


class LabelModelResource(GCloudModelResource):
    group = fields.ForeignKey(LabelGroupModelResource, "group", full=True)
    code = fields.CharField(attribute="code", readonly=True)
    name = fields.CharField(attribute="name", readonly=True)

    class Meta(GCloudModelResource.CommonMeta):
        queryset = Label.objects.all()
        resource_name = "label"
        detail_uri_name = "id"
        authorization = ReadOnlyAuthorization()
        filtering = {"group": ALL_WITH_RELATIONS, "code": ALL}
