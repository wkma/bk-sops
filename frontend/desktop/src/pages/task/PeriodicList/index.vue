/**
* Tencent is pleased to support the open source community by making 蓝鲸智云PaaS平台社区版 (BlueKing PaaS Community
* Edition) available.
* Copyright (C) 2017-2021 THL A29 Limited, a Tencent company. All rights reserved.
* Licensed under the MIT License (the "License"); you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
* http://opensource.org/licenses/MIT
* Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
* an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
* specific language governing permissions and limitations under the License.
*/
<template>
    <div class="periodic-container">
        <skeleton :loading="firstLoading" loader="taskList">
            <div class="list-wrapper">
                <advance-search-form
                    id="periodicList"
                    :open="isSearchFormOpen"
                    :search-config="{ placeholder: $t('请输入任务名称'), value: requestData.taskName }"
                    :search-form="searchForm"
                    @onSearchInput="onSearchInput"
                    @submit="onSearchFormSubmit">
                    <template v-if="!adminView" v-slot:operation>
                        <bk-button
                            ref="childComponent"
                            theme="primary"
                            size="normal"
                            style="min-width: 120px;"
                            @click="onCreatePeriodTask">
                            {{$t('新建')}}
                        </bk-button>
                    </template>
                </advance-search-form>
                <div class="periodic-table-content">
                    <bk-table
                        :data="periodicList"
                        :pagination="pagination"
                        :size="setting.size"
                        @page-change="onPageChange"
                        @page-limit-change="handlePageLimitChange"
                        v-bkloading="{ isLoading: !firstLoading && listLoading, opacity: 1, zIndex: 100 }">
                        <template v-for="item in setting.selectedFields">
                            <bk-table-column
                                v-if="item.isShow ? adminView : true"
                                :key="item.id"
                                :label="item.label"
                                :prop="item.id"
                                :width="item.width"
                                :min-width="item.min_width">
                                <template slot-scope="{ row }">
                                    <!--流程模板-->
                                    <div v-if="item.id === 'process_template'">
                                        <a
                                            v-if="!hasPermission(['periodic_task_view'], row.auth_actions)"
                                            v-cursor
                                            class="text-permission-disable"
                                            @click="onPeriodicPermissonCheck(['periodic_task_view'], row, $event)">
                                            {{row.task_template_name}}
                                        </a>
                                        <router-link
                                            v-else
                                            class="periodic-name"
                                            :title="row.task_template_name"
                                            :to="templateNameUrl(row)">
                                            {{row.task_template_name}}
                                        </router-link>
                                    </div>
                                    <!--项目-->
                                    <div v-else-if="item.id === 'project'">
                                        <span :title="row.project.name">{{ row.project.name }}</span>
                                    </div>
                                    <!--周期规则-->
                                    <div v-else-if="item.id === 'cron'">
                                        <div :title="splitPeriodicCron(row.cron)">{{ splitPeriodicCron(row.cron) }}</div>
                                    </div>
                                    <!--状态-->
                                    <div v-else-if="item.id === 'periodic_status'" class="periodic-status">
                                        <span :class="row.enabled ? 'bk-icon icon-check-circle-shape' : 'common-icon-dark-circle-pause'"></span>
                                        {{row.enabled ? $t('启动') : $t('暂停')}}
                                    </div>
                                    <!-- 其他 -->
                                    <template v-else>
                                        <span :title="row[item.id] || '--'">{{ row[item.id] || '--' }}</span>
                                    </template>
                                </template>
                            </bk-table-column>
                        </template>
                        <bk-table-column :label="$t('操作')" width="240">
                            <template slot-scope="props">
                                <div class="periodic-operation">
                                    <template v-if="!adminView">
                                        <a
                                            v-cursor="{ active: !hasPermission(['periodic_task_edit'], props.row.auth_actions) }"
                                            href="javascript:void(0);"
                                            :class="['periodic-pause-btn', {
                                                'periodic-start-btn': !props.row.enabled,
                                                'text-permission-disable': !hasPermission(['periodic_task_edit'], props.row.auth_actions)
                                            }]"
                                            @click="onSetEnable(props.row, $event)">
                                            {{!props.row.enabled ? $t('启动') : $t('暂停')}}
                                        </a>
                                        <a
                                            v-cursor="{ active: !hasPermission(['periodic_task_edit'], props.row.auth_actions) }"
                                            href="javascript:void(0);"
                                            :class="['periodic-bk-btn', {
                                                'periodic-bk-disable': props.row.enabled,
                                                'text-permission-disable': !hasPermission(['periodic_task_edit'], props.row.auth_actions)
                                            }]"
                                            :title="props.row.enabled ? $t('请暂停任务后再执行编辑操作') : ''"
                                            @click="onModifyCronPeriodic(props.row, $event)">
                                            {{ $t('编辑') }}
                                        </a>
                                    </template>
                                    <a
                                        v-else
                                        href="javascript:void(0);"
                                        @click="onRecordView(props.row, $event)">
                                        {{ $t('启动记录') }}
                                    </a>
                                    <router-link
                                        :to="{
                                            name: 'taskList',
                                            params: { project_id: props.row.project.id },
                                            query: { template_id: props.row.template_id, create_method: 'periodic', create_info: props.row.task.id, template_source: props.row.template_source }
                                        }">
                                        {{ $t('执行历史') }}
                                    </router-link>
                                    <bk-popover
                                        theme="light"
                                        placement="bottom-start"
                                        ext-cls="common-dropdown-btn-popver"
                                        :z-index="2000"
                                        :distance="0"
                                        :arrow="false"
                                        :tippy-options="{ boundary: 'window', duration: [0, 0] }">
                                        <i class="bk-icon icon-more drop-icon-ellipsis"></i>
                                        <ul slot="content">
                                            <li class="opt-btn">
                                                <a
                                                    v-cursor="{ active: !hasPermission(['periodic_task_edit'], props.row.auth_actions) }"
                                                    href="javascript:void(0);"
                                                    :class="{
                                                        'disable': props.row.id === collectingId || collectListLoading,
                                                        'text-permission-disable': !hasPermission(['periodic_task_edit'], props.row.auth_actions)
                                                    }"
                                                    @click="onCollectTask(props.row, $event)">
                                                    {{ isCollected(props.row.id) ? $t('取消收藏') : $t('收藏') }}
                                                </a>
                                            </li>
                                            <li class="opt-btn">
                                                <a
                                                    v-cursor="{ active: !hasPermission(['periodic_task_delete'], props.row.auth_actions) }"
                                                    href="javascript:void(0);"
                                                    :class="{
                                                        'text-permission-disable': !hasPermission(['periodic_task_delete'], props.row.auth_actions)
                                                    }"
                                                    @click="onDeletePeriodic(props.row, $event)">
                                                    {{ $t('删除') }}
                                                </a>
                                            </li>
                                        </ul>
                                    </bk-popover>
                                </div>
                            </template>
                        </bk-table-column>
                        <bk-table-column type="setting">
                            <bk-table-setting-content
                                :fields="setting.fieldList"
                                :selected="setting.selectedFields"
                                :size="setting.size"
                                @setting-change="handleSettingChange">
                            </bk-table-setting-content>
                        </bk-table-column>
                        <div class="empty-data" slot="empty"><NoData :message="$t('无数据')" /></div>
                    </bk-table>
                </div>
            </div>
        </skeleton>
        <TaskCreateDialog
            :entrance="'periodicTask'"
            :project_id="project_id"
            :is-new-task-dialog-show="isNewTaskDialogShow"
            :business-info-loading="businessInfoLoading"
            :task-category="taskCategory"
            :dialog-title="$t('新建周期任务')"
            @onCreateTaskCancel="onCreateTaskCancel">
        </TaskCreateDialog>
        <ModifyPeriodicDialog
            :loading="modifyDialogLoading"
            :constants="constants"
            :cron="selectedCron"
            :task-id="selectedPeriodicId"
            :is-modify-dialog-show="isModifyDialogShow"
            @onModifyPeriodicConfirm="onModifyPeriodicConfirm"
            @onModifyPeriodicCancel="onModifyPeriodicCancel">
        </ModifyPeriodicDialog>
        <BootRecordDialog
            :show="isBootRecordDialogShow"
            :id="selectedPeriodicId"
            @onClose="isBootRecordDialogShow = false">
        </BootRecordDialog>
        <DeletePeriodicDialog
            :is-delete-dialog-show="isDeleteDialogShow"
            :template-name="selectedTemplateName"
            :deleting="deleting"
            @onDeletePeriodicConfirm="onDeletePeriodicConfirm"
            @onDeletePeriodicCancel="onDeletePeriodicCancel">
        </DeletePeriodicDialog>
    </div>
</template>
<script>
    import i18n from '@/config/i18n/index.js'
    import { mapActions, mapState } from 'vuex'
    import { errorHandler } from '@/utils/errorHandler.js'
    import toolsUtils from '@/utils/tools.js'
    import permission from '@/mixins/permission.js'
    import Skeleton from '@/components/skeleton/index.vue'
    import NoData from '@/components/common/base/NoData.vue'
    import TaskCreateDialog from '../../task/TaskList/TaskCreateDialog.vue'
    import ModifyPeriodicDialog from './ModifyPeriodicDialog.vue'
    import BootRecordDialog from './BootRecordDialog.vue'
    import DeletePeriodicDialog from './DeletePeriodicDialog.vue'
    import AdvanceSearchForm from '@/components/common/advanceSearchForm/index.vue'
    const SEARCH_FORM = [
        {
            type: 'input',
            key: 'creator',
            label: i18n.t('创建人'),
            placeholder: i18n.t('请输入创建人'),
            value: ''
        },
        {
            type: 'select',
            label: i18n.t('状态'),
            key: 'enabled',
            loading: false,
            placeholder: i18n.t('请选择状态'),
            list: [
                { 'value': 'true', 'name': i18n.t('启动') },
                { 'value': 'false', 'name': i18n.t('暂停') }
            ],
            value: ''
        }
    ]
    const TABLE_FIELDS = [
        {
            id: 'id',
            label: i18n.t('ID'),
            width: 80
        }, {
            id: 'name',
            label: i18n.t('任务名称'),
            disabled: true,
            min_width: 200
        }, {
            id: 'process_template',
            label: i18n.t('流程模板'),
            min_width: 200
        }, {
            id: 'project',
            label: i18n.t('项目'),
            isShow: true,
            width: 140
        }, {
            id: 'cron',
            label: i18n.t('周期规则'),
            width: 150
        }, {
            id: 'last_run_at',
            label: i18n.t('上次运行时间'),
            width: 200
        }, {
            id: 'creator',
            label: i18n.t('创建人'),
            width: 120
        }, {
            id: 'total_run_count',
            label: i18n.t('运行次数'),
            width: 100
        }, {
            id: 'periodic_status',
            label: i18n.t('状态'),
            width: 100
        }
    ]
    export default {
        name: 'PeriodicList',
        components: {
            Skeleton,
            AdvanceSearchForm,
            NoData,
            TaskCreateDialog,
            ModifyPeriodicDialog,
            BootRecordDialog,
            DeletePeriodicDialog
        },
        mixins: [permission],
        props: {
            project_id: {
                type: [String, Number]
            },
            admin: {
                type: Boolean,
                default: false
            }
        },
        data () {
            const { page = 1, limit = 15, creator = '', enabled = '', keyword = '' } = this.$route.query
            const searchForm = SEARCH_FORM.map(item => {
                if (this.$route.query[item.key]) {
                    if (Array.isArray(item.value)) {
                        item.value = this.$route.query[item.key].split(',')
                    } else {
                        item.value = this.$route.query[item.key]
                    }
                }
                return item
            })
            const isSearchFormOpen = SEARCH_FORM.some(item => this.$route.query[item.key])
            return {
                firstLoading: true,
                businessInfoLoading: true,
                isNewTaskDialogShow: false,
                listLoading: false,
                deleting: false,
                totalPage: 1,
                isDeleteDialogShow: false,
                isModifyDialogShow: false,
                isBootRecordDialogShow: false,
                selectedPeriodicId: undefined,
                periodicList: [],
                collectingId: '', // 正在被收藏/取消收藏的周期任务id
                collectListLoading: false,
                collectionList: [],
                selectedCron: undefined,
                constants: {},
                modifyDialogLoading: false,
                selectedTemplateName: undefined,
                periodEntrance: '',
                taskCategory: [],
                searchForm,
                isSearchFormOpen,
                requestData: {
                    creator,
                    enabled,
                    taskName: keyword
                },
                pagination: {
                    current: Number(page),
                    count: 0,
                    limit: Number(limit),
                    'limit-list': [15, 30, 50, 100]
                },
                tableFields: TABLE_FIELDS,
                setting: {
                    fieldList: TABLE_FIELDS,
                    selectedFields: TABLE_FIELDS.slice(0),
                    size: 'small'
                }
            }
        },
        computed: {
            ...mapState({
                hasAdminPerm: state => state.hasAdminPerm
            }),
            adminView () {
                return this.hasAdminPerm && this.admin
            }
        },
        async created () {
            this.getFields()
            this.getBizBaseInfo()
            this.getCollectList()
            this.onSearchInput = toolsUtils.debounce(this.searchInputhandler, 500)
            await this.getPeriodicList()
            this.firstLoading = false
        },
        methods: {
            ...mapActions([
                'addToCollectList',
                'deleteCollect',
                'loadCollectList'
            ]),
            ...mapActions('periodic/', [
                'loadPeriodicList',
                'setPeriodicEnable',
                'getPeriodic',
                'deletePeriodic'
            ]),
            ...mapActions('template/', [
                'loadProjectBaseInfo'
            ]),
            async getPeriodicList () {
                this.listLoading = true
                try {
                    const { creator, enabled, taskName } = this.requestData
                    const data = {
                        limit: this.pagination.limit,
                        offset: (this.pagination.current - 1) * this.pagination.limit,
                        task__celery_task__enabled: enabled || undefined,
                        task__creator__contains: creator || undefined,
                        task__name__icontains: taskName || undefined
                    }

                    if (!this.admin) {
                        data.project__id = this.project_id
                    }

                    const periodicListData = await this.loadPeriodicList(data)
                    const list = periodicListData.objects
                    this.periodicList = list
                    this.pagination.count = periodicListData.meta.total_count
                    const totalPage = Math.ceil(this.pagination.count / this.pagination.limit)
                    if (!totalPage) {
                        this.totalPage = 1
                    } else {
                        this.totalPage = totalPage
                    }
                } catch (e) {
                    errorHandler(e, this)
                } finally {
                    this.listLoading = false
                }
            },
            async getBizBaseInfo () {
                try {
                    const res = await this.loadProjectBaseInfo()
                    this.taskCategory = res.data.task_categories
                } catch (e) {
                    errorHandler(e, this)
                }
            },
            // 获取当前视图表格头显示字段
            getFields () {
                const settingFields = localStorage.getItem('PeriodicList')
                if (settingFields) {
                    const { fieldList, size } = JSON.parse(settingFields)
                    this.setting.size = size
                    this.setting.selectedFields = this.tableFields.slice(0).filter(m => fieldList.includes(m.id))
                }
            },
            async getCollectList () {
                try {
                    this.collectListLoading = true
                    const res = await this.loadCollectList()
                    this.collectionList = res.objects
                } catch (e) {
                    errorHandler(e, this)
                } finally {
                    this.collectListLoading = false
                }
            },
            searchInputhandler (data) {
                this.requestData.taskName = data
                this.pagination.current = 1
                this.getPeriodicList()
            },
            /**
             * 单个周期任务操作项点击时校验
             * @params {Array} required 需要的权限
             * @params {Object} periodic 模板数据对象
             */
            onPeriodicPermissonCheck (required, periodic) {
                const { id, name, task_template_name, template_id, project } = periodic
                const resourceData = {
                    periodic_task: [{ id, name }],
                    flow: [{
                        id: template_id,
                        name: task_template_name
                    }],
                    project: [{
                        id: project.id,
                        name: project.name
                    }]
                }
                this.applyForPermission(required, periodic.auth_actions, resourceData)
            },
            onDeletePeriodic (periodic) {
                if (!this.hasPermission(['periodic_task_delete'], periodic.auth_actions)) {
                    this.onPeriodicPermissonCheck(['periodic_task_delete'], periodic)
                    return
                }
                this.isDeleteDialogShow = true
                this.selectedDeleteTaskId = periodic.id
                this.selectedTemplateName = periodic.name
            },
            // 表格功能选项
            handleSettingChange ({ fields, size }) {
                this.setting.size = size
                this.setting.selectedFields = fields
                const fieldIds = fields.map(m => m.id)
                localStorage.setItem('PeriodicList', JSON.stringify({
                    fieldList: fieldIds,
                    size
                }))
            },
            onPageChange (page) {
                this.pagination.current = page
                this.updateUrl()
                this.getPeriodicList()
            },
            handlePageLimitChange (val) {
                this.pagination.limit = val
                this.pagination.current = 1
                this.updateUrl()
                this.getPeriodicList()
            },
            onSearchFormSubmit (data) {
                this.requestData = Object.assign({}, this.requestData, data)
                this.pagination.current = 1
                this.updateUrl()
                this.getPeriodicList()
            },
            updateUrl () {
                const { current, limit } = this.pagination
                const { creator, enabled, taskName } = this.requestData
                const filterObj = {
                    limit,
                    creator,
                    enabled,
                    page: current,
                    keyword: taskName
                }
                const query = {}
                Object.keys(filterObj).forEach(key => {
                    const val = filterObj[key]
                    if (val || val === 0 || val === false) {
                        query[key] = val
                    }
                })
                if (this.admin) {
                    this.$router.push({ name: 'adminPeriodic', query })
                } else {
                    this.$router.push({ name: 'periodicTemplate', params: { project_id: this.project_id }, query })
                }
            },
            async onSetEnable (item) {
                if (!this.hasPermission(['periodic_task_edit'], item.auth_actions)) {
                    this.onPeriodicPermissonCheck(['periodic_task_edit'], item)
                    return
                }
                try {
                    const data = {
                        'taskId': item.id,
                        'enabled': !item.enabled
                    }
                    const periodicData = await this.setPeriodicEnable(data)
                    if (periodicData.result) {
                        const periodic = this.periodicList.find(periodic => periodic.id === item.id)
                        periodic.enabled = !periodic.enabled
                    }
                } catch (e) {
                    errorHandler(e, this)
                }
            },
            onModifyCronPeriodic (item) {
                const { enabled, id: taskId, cron } = item
                if (!this.hasPermission(['periodic_task_edit'], item.auth_actions)) {
                    this.onPeriodicPermissonCheck(['periodic_task_edit'], item)
                    return
                }
                if (enabled) {
                    return
                }
                const splitCron = this.splitPeriodicCron(cron)
                this.selectedCron = splitCron
                this.selectedPeriodicId = taskId
                this.getPeriodicConstant(taskId)
                this.isModifyDialogShow = true
            },
            onModifyPeriodicCancel () {
                this.isModifyDialogShow = false
            },
            onModifyPeriodicConfirm () {
                this.isModifyDialogShow = false
                this.getPeriodicList()
            },
            async getPeriodicConstant (taskId) {
                this.modifyDialogLoading = true
                const data = {
                    'taskId': taskId
                }
                const periodic = await this.getPeriodic(data)
                this.constants = periodic.form
                this.modifyDialogLoading = false
            },
            onDeletePeriodicConfirm () {
                this.deleteSelecedPeriodic()
            },
            async deleteSelecedPeriodic () {
                if (this.deleting) {
                    return
                }
                try {
                    this.deleting = true
                    await this.deletePeriodic(this.selectedDeleteTaskId)
                    this.$bkMessage({
                        'message': i18n.t('删除周期任务成功'),
                        'theme': 'success'
                    })
                    this.isDeleteDialogShow = false
                    // 最后一页最后一条删除后，往前翻一页
                    if (
                        this.pagination.current > 1
                        && this.totalPage === this.pagination.current
                        && this.pagination.count - (this.totalPage - 1) * this.pagination.limit === 1
                    ) {
                        this.pagination.current -= 1
                    }
                    this.getPeriodicList()
                } catch (e) {
                    errorHandler(e, this)
                } finally {
                    this.deleting = false
                }
            },
            onDeletePeriodicCancel () {
                this.isDeleteDialogShow = false
            },
            splitPeriodicCron (cron) {
                return cron.split('(')[0].trim()
            },
            onCreatePeriodTask () {
                this.isNewTaskDialogShow = true
            },
            onCreateTaskCancel () {
                this.isNewTaskDialogShow = false
            },
            onRecordView (task) {
                this.selectedPeriodicId = task.id
                this.isBootRecordDialogShow = true
            },
            templateNameUrl (template) {
                const { template_id: templateId, template_source: templateSource, project } = template
                const url = {
                    name: 'templatePanel',
                    params: { type: 'edit', project_id: project.id },
                    query: { template_id: templateId, common: templateSource === 'common' || undefined }
                }
                return url
            },
            // 添加/取消收藏模板
            async onCollectTask (task, event) {
                if (!this.hasPermission(['periodic_task_view'], task.auth_actions)) {
                    this.onPeriodicPermissonCheck(['periodic_task_view'], task, event)
                    return
                }
                if (typeof this.collectingId === 'number') {
                    return
                }

                try {
                    this.collectingId = task.id
                    if (!this.isCollected(task.id)) { // add
                        const res = await this.addToCollectList([{
                            extra_info: {
                                project_id: task.project.id,
                                template_id: task.template_id,
                                name: task.name,
                                id: task.id
                            },
                            category: 'periodic_task'
                        }])
                        if (res.objects.length) {
                            this.$bkMessage({ message: i18n.t('添加收藏成功！'), theme: 'success' })
                        }
                    } else { // cancel
                        const delId = this.collectionList.find(m => m.extra_info.id === task.id && m.category === 'periodic_task').id
                        await this.deleteCollect(delId)
                        this.$bkMessage({ message: i18n.t('取消收藏成功！'), theme: 'success' })
                    }
                    this.getCollectList()
                } catch (e) {
                    errorHandler(e, this)
                } finally {
                    this.collectingId = ''
                }
            },
            // 判断是否已在收藏列表
            isCollected (id) {
                return !!this.collectionList.find(m => m.extra_info.id === id && m.category === 'periodic_task')
            }
        }
    }
</script>
<style lang='scss' scoped>
@import '@/scss/config.scss';
@import '@/scss/mixins/scrollbar.scss';

.periodic-container {
    padding: 20px 24px;
    height: 100%;
    overflow: auto;
    @include scrollbar;
}
.list-wrapper {
    min-height: calc(100vh - 300px);
    .advanced-search {
        margin: 0px;
    }
}
.query-button {
    padding: 10px;
    min-width: 450px;
    @media screen and (max-width: 1420px) {
        min-width: 390px;
    }
    text-align: center;
    .bk-button {
        height: 32px;
        line-height: 32px;
    }
    .query-cancel {
        margin-left: 5px;
    }
}
.periodic-table-content {
    margin-top: 25px;
    background: #ffffff;
    /deep/ .bk-table {
        td.is-last .cell {
            overflow: visible;
        }
    }
    .icon-check-circle-shape {
        color: #30d878;
    }
    a.periodic-name,
    .periodic-operation>a {
        color: $blueDefault;
        padding: 5px;
        &.periodic-bk-disable {
            color:#cccccc;
            cursor: not-allowed;
        }
    }
    .icon-check-circle-shape {
        color: $greenDefault;
    }
    .common-icon-dark-circle-pause {
        color: #ff9C01;
        border-radius: 20px;
        font-size: 12px;
    }
    .drop-icon-ellipsis {
        font-size: 18px;
        vertical-align: -3px;
        cursor: pointer;
        &:hover {
            color: #3a84ff;
            background: #dcdee5;
            border-radius: 50%;
        }
    }
    .empty-data {
        padding: 120px 0;
    }
}
</style>
