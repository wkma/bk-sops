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
    <div class="task-container">
        <skeleton :loading="firstLoading" loader="taskList">
            <div class="list-wrapper">
                <advance-search-form
                    id="taskList"
                    :open="isSearchFormOpen"
                    :search-config="{ placeholder: $t('请输入任务名称') }"
                    :search-form="searchForm"
                    @onSearchInput="onSearchInput"
                    @submit="onSearchFormSubmit">
                    <template v-slot:operation>
                        <bk-button
                            theme="primary"
                            style="min-width: 120px;"
                            @click="onCreateTask">
                            {{$t('新建')}}
                        </bk-button>
                    </template>
                </advance-search-form>
                <div class="task-table-content">
                    <bk-table
                        :data="taskList"
                        :pagination="pagination"
                        :size="setting.size"
                        v-bkloading="{ isLoading: !firstLoading && listLoading, opacity: 1, zIndex: 100 }"
                        @page-change="onPageChange"
                        @page-limit-change="onPageLimitChange">
                        <bk-table-column
                            v-for="item in setting.selectedFields"
                            :key="item.id"
                            :label="item.label"
                            :prop="item.id"
                            :width="item.width"
                            :min-width="item.min_width">
                            <template slot-scope="props">
                                <!--任务名称-->
                                <div v-if="item.id === 'name'">
                                    <a
                                        v-if="!hasPermission(['task_view'], props.row.auth_actions)"
                                        v-cursor
                                        class="text-permission-disable"
                                        :title="props.row.name"
                                        @click="onTaskPermissonCheck(['task_view'], props.row)">
                                        {{props.row.name}}
                                    </a>
                                    <router-link
                                        v-else
                                        class="template-operate-btn"
                                        :title="props.row.name"
                                        :to="{
                                            name: 'taskExecute',
                                            params: { project_id: project_id },
                                            query: { instance_id: props.row.id }
                                        }">
                                        {{props.row.name}}
                                    </router-link>
                                </div>
                                <!--创建方式-->
                                <div v-else-if="item.id === 'create_method'">
                                    {{ transformCreateMethod(props.row.create_method) }}
                                </div>
                                <!--状态-->
                                <div v-else-if="item.id === 'task_status'" class="task-status">
                                    <span :class="executeStatus[props.$index] && executeStatus[props.$index].cls"></span>
                                    <span v-if="executeStatus[props.$index]" class="task-status-text">{{executeStatus[props.$index].text}}</span>
                                </div>
                                <!-- 其他 -->
                                <template v-else>
                                    <span :title="props.row[item.id] || '--'">{{ props.row[item.id] || '--' }}</span>
                                </template>
                            </template>
                        </bk-table-column>
                        <bk-table-column :label="$t('操作')" width="190">
                            <template slot-scope="props">
                                <div class="task-operation">
                                    <!-- 事后鉴权，后续对接新版权限中心 -->
                                    <a v-if="props.row.template_deleted" class="task-operation-btn disabled">{{$t('再创建')}}</a>
                                    <a
                                        v-else-if="!hasCreateTaskPerm(props.row)"
                                        v-cursor
                                        class="text-permission-disable task-operation-btn"
                                        @click="onTaskPermissonCheck([props.row.template_source === 'project' ? 'flow_create_task' : 'common_flow_create_task'], props.row)">
                                        {{$t('再创建')}}
                                    </a>
                                    <router-link
                                        v-else
                                        class="task-operation-btn"
                                        :to="getCreateTaskUrl(props.row)">
                                        {{$t('再创建')}}
                                    </router-link>
                                    <a
                                        v-cursor="{ active: !hasPermission(['task_clone'], props.row.auth_actions) }"
                                        :class="['task-operation-btn', {
                                            'text-permission-disable': !hasPermission(['task_clone'], props.row.auth_actions)
                                        }]"
                                        href="javascript:void(0);"
                                        @click="onCloneTaskClick(props.row, $event)">
                                        {{ $t('克隆') }}
                                    </a>
                                    <a
                                        v-cursor="{ active: !hasPermission(['task_delete'], props.row.auth_actions) }"
                                        :class="['task-operation-btn', {
                                            'text-permission-disable': !hasPermission(['task_delete'], props.row.auth_actions)
                                        }]"
                                        href="javascript:void(0);"
                                        @click="onDeleteTask(props.row, $event)">
                                        {{ $t('删除') }}
                                    </a>
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
            :entrance="'taskflow'"
            :project_id="project_id"
            :is-new-task-dialog-show="isNewTaskDialogShow"
            :business-info-loading="businessInfoLoading"
            :task-category="taskCategory"
            @onCreateTaskCancel="onCreateTaskCancel">
        </TaskCreateDialog>
        <TaskCloneDialog
            :is-task-clone-dialog-show="isTaskCloneDialogShow"
            :task-name="theCloneTaskName"
            :pending="pending.clone"
            @confirm="onCloneConfirm"
            @cancel="onCloneCancel">
        </TaskCloneDialog>
        <bk-dialog
            width="400"
            ext-cls="common-dialog"
            :theme="'primary'"
            :mask-close="false"
            :header-position="'left'"
            :title="$t('删除')"
            :value="isDeleteDialogShow"
            @confirm="onDeleteConfirm"
            @cancel="onDeleteCancel">
            <div class="dialog-content" v-bkloading="{ isLoading: pending.delete, opacity: 1, zIndex: 100 }">
                {{$t('确认删除') + '"' + theDeleteTaskName + '"?'}}
            </div>
        </bk-dialog>
    </div>
</template>
<script>
    import i18n from '@/config/i18n/index.js'
    import { mapState, mapMutations, mapActions } from 'vuex'
    import { errorHandler } from '@/utils/errorHandler.js'
    import toolsUtils from '@/utils/tools.js'
    import AdvanceSearchForm from '@/components/common/advanceSearchForm/index.vue'
    import TaskCreateDialog from './TaskCreateDialog.vue'
    import NoData from '@/components/common/base/NoData.vue'
    import moment from 'moment-timezone'
    import TaskCloneDialog from './TaskCloneDialog.vue'
    import Skeleton from '@/components/skeleton/index.vue'
    import permission from '@/mixins/permission.js'
    import task from '@/mixins/task.js'
    const SEARCH_FORM = [
        {
            type: 'dateRange',
            key: 'executeTime',
            placeholder: i18n.t('选择日期时间范围'),
            label: i18n.t('执行开始'),
            value: ['', '']
        },
        {
            type: 'select',
            label: i18n.t('创建方式'),
            key: 'createMethod',
            loading: true,
            placeholder: i18n.t('请选择创建方式'),
            list: [],
            value: ''
        },
        {
            type: 'input',
            key: 'creator',
            label: i18n.t('创建人'),
            placeholder: i18n.t('请输入创建人'),
            value: ''
        },
        {
            type: 'input',
            key: 'executor',
            label: i18n.t('执行人'),
            placeholder: i18n.t('请输入执行人'),
            value: ''
        },
        {
            type: 'select',
            label: i18n.t('状态'),
            key: 'statusSync',
            loading: false,
            placeholder: i18n.t('请选择状态'),
            list: [
                { 'value': 'nonExecution', 'name': i18n.t('未执行') },
                { 'value': 'running', 'name': i18n.t('未完成') },
                { 'value': 'revoked', 'name': i18n.t('撤销') },
                { 'value': 'finished', 'name': i18n.t('完成') }
            ],
            value: ''
        },
        {
            type: 'select',
            label: i18n.t('任务分类'),
            key: 'category',
            loading: true,
            placeholder: i18n.t('请选择分类'),
            list: [],
            value: ''
        }
    ]
    const TABLE_FIELDS = [
        {
            id: 'id',
            label: i18n.t('ID'),
            width: 100
        }, {
            id: 'name',
            label: i18n.t('任务名称'),
            disabled: true,
            min_width: 240
        }, {
            id: 'start_time',
            label: i18n.t('执行开始'),
            width: 200
        }, {
            id: 'finish_time',
            label: i18n.t('执行结束'),
            width: 200
        }, {
            id: 'create_time',
            label: i18n.t('创建时间'),
            width: 200
        }, {
            id: 'category_name',
            label: i18n.t('任务类型'),
            width: 100
        }, {
            id: 'creator_name',
            label: i18n.t('创建人'),
            width: 120
        }, {
            id: 'executor_name',
            label: i18n.t('执行人'),
            width: 120
        }, {
            id: 'create_method',
            label: i18n.t('创建方式'),
            width: 100
        }, {
            id: 'task_status',
            label: i18n.t('状态'),
            width: 120
        }
    ]
    export default {
        name: 'TaskList',
        components: {
            Skeleton,
            NoData,
            TaskCreateDialog,
            TaskCloneDialog,
            AdvanceSearchForm
        },
        mixins: [permission, task],
        props: {
            project_id: {
                type: [String, Number],
                default: ''
            }
        },
        data () {
            const {
                page = 1,
                limit = 15,
                template_source = '',
                create_info = '',
                category = '',
                executeTime = '',
                create_method = '',
                creator = '',
                executor = '',
                statusSync = '',
                keyword = ''
            } = this.$route.query
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
                listLoading: false,
                templateId: this.$route.query.template_id,
                taskCategory: [],
                searchStr: '',
                searchForm,
                isSearchFormOpen, // 高级搜索表单默认展开
                executeStatus: [], // 任务执行状态
                totalPage: 1,
                isDeleteDialogShow: false,
                shapeShow: false,
                theDeleteTaskId: undefined,
                theDeleteTaskName: '',
                isTaskCloneDialogShow: false,
                isNewTaskDialogShow: false,
                businessInfoLoading: true, // 模板分类信息 loading
                theCloneTaskName: '',
                theCloneTaskId: undefined,
                pending: {
                    delete: false,
                    clone: false
                },
                taskBasicInfoLoading: true,
                taskCreateMethodList: [],
                createMethod: create_method,
                createInfo: create_info,
                templateSource: template_source,
                requestData: {
                    executeTime: executeTime ? executeTime.split(',') : ['', ''],
                    category,
                    creator,
                    executor,
                    statusSync,
                    createMethod: create_method,
                    taskName: keyword
                },
                pagination: {
                    current: Number(page),
                    count: 0,
                    limit: Number(limit),
                    'limit-list': [15, 30, 50, 100]
                },
                tableFields: TABLE_FIELDS,
                defaultSelected: ['id', 'name', 'start_time', 'finish_time', 'executor_name', 'task_status'],
                setting: {
                    fieldList: TABLE_FIELDS,
                    selectedFields: TABLE_FIELDS.slice(0),
                    size: 'small'
                }
            }
        },
        computed: {
            ...mapState({
                taskList: state => state.taskList.taskListData
            }),
            ...mapState('project', {
                'authActions': state => state.authActions,
                'timeZone': state => state.timezone
            })
        },
        async created () {
            this.getFields()
            this.onSearchInput = toolsUtils.debounce(this.searchInputhandler, 500)
            await this.getData()
            this.firstLoading = false
        },
        methods: {
            ...mapActions('template/', [
                'loadProjectBaseInfo'
            ]),
            ...mapActions('task/', [
                'getInstanceStatus',
                'loadCreateMethod'
            ]),
            ...mapActions('taskList/', [
                'loadTaskList',
                'deleteTask',
                'cloneTask'
            ]),
            ...mapMutations('template/', [
                'setProjectBaseInfo'
            ]),
            ...mapMutations('taskList/', [
                'setTaskListData'
            ]),
            async getTaskList () {
                // 空字符串需要转换为undefined，undefined数据在axios请求发送过程中会被删除
                this.listLoading = true
                this.executeStatus = []
                try {
                    const { executeTime, category, createMethod, creator, executor, statusSync, taskName } = this.requestData
                    let pipeline_instance__is_started
                    let pipeline_instance__is_finished
                    let pipeline_instance__is_revoked
                    switch (statusSync) {
                        case 'nonExecution':
                            pipeline_instance__is_started = false
                            break
                        case 'running':
                            pipeline_instance__is_started = true
                            pipeline_instance__is_finished = false
                            pipeline_instance__is_revoked = false
                            break
                        case 'revoked':
                            pipeline_instance__is_revoked = true
                            break
                        case 'finished':
                            pipeline_instance__is_finished = true
                            break
                    }

                    const data = {
                        limit: this.pagination.limit,
                        offset: (this.pagination.current - 1) * this.pagination.limit,
                        category: category || undefined,
                        template_id: this.templateId || undefined,
                        pipeline_instance__creator__contains: creator || undefined,
                        pipeline_instance__executor__contains: executor || undefined,
                        pipeline_instance__name__icontains: taskName || undefined,
                        pipeline_instance__is_started,
                        pipeline_instance__is_finished,
                        pipeline_instance__is_revoked,
                        create_method: createMethod || undefined,
                        create_info: this.createInfo || undefined,
                        project__id: this.project_id,
                        template_source: this.templateSource || undefined
                    }

                    if (executeTime[0] && executeTime[1]) {
                        if (this.template_source === 'common') {
                            data['pipeline_template__start_time__gte'] = moment(executeTime[0]).format('YYYY-MM-DD')
                            data['pipeline_template__start_time__lte'] = moment(executeTime[1]).add('1', 'd').format('YYYY-MM-DD')
                        } else {
                            data['pipeline_instance__start_time__gte'] = moment.tz(executeTime[0], this.timeZone).format('YYYY-MM-DD')
                            data['pipeline_instance__start_time__lte'] = moment.tz(executeTime[1], this.timeZone).add('1', 'd').format('YYYY-MM-DD')
                        }
                    }
                    const taskListData = await this.loadTaskList(data)
                    const list = taskListData.objects
                    this.pagination.count = taskListData.meta.total_count
                    this.totalCount = taskListData.meta.total_count
                    const totalPage = Math.ceil(this.pagination.count / this.pagination.limit)
                    if (!totalPage) {
                        this.totalPage = 1
                    } else {
                        this.totalPage = totalPage
                    }
                    // mixins getExecuteStatus
                    this.getExecuteStatus('executeStatus', list)
                    this.setTaskListData(list)
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
                    this.setProjectBaseInfo(res.data)
                    this.taskBasicInfoLoading = false
                    const form = this.searchForm.find(item => item.key === 'category')
                    form.list = this.taskCategory
                    form.loading = false
                } catch (e) {
                    errorHandler(e, this)
                }
            },
            // 获取当前视图表格头显示字段
            getFields () {
                const settingFields = localStorage.getItem('TaskList')
                let selectedFields
                if (settingFields) {
                    const { fieldList, size } = JSON.parse(settingFields)
                    selectedFields = fieldList
                    this.setting.size = size
                } else {
                    selectedFields = this.defaultSelected
                }
                this.setting.selectedFields = this.tableFields.slice(0).filter(m => selectedFields.includes(m.id))
            },
            searchInputhandler (data) {
                this.requestData.taskName = data
                this.pagination.current = 1
                this.getTaskList()
            },
            hasCreateTaskPerm (task) {
                const authActions = [...task.auth_actions, ...this.authActions]
                const reqPerm = task.template_source === 'project' ? 'flow_create_task' : 'common_flow_create_task'
                return this.hasPermission([reqPerm], authActions)
            },
            getCreateTaskUrl (task) {
                const url = {
                    name: 'taskCreate',
                    query: { template_id: task.template_id },
                    params: { project_id: this.project_id, step: 'selectnode' }
                }
                if (task.template_source === 'common') {
                    url.query.common = 1
                }
                return url
            },
            /**
             * 单个任务操作项点击时校验
             * @params {Array} required 需要的权限
             * @params {Object} task 任务数据对象
             */
            onTaskPermissonCheck (required, task) {
                const resourceData = {
                    task: [{
                        id: task.id,
                        name: task.name
                    }],
                    project: [{
                        id: task.project.id,
                        name: task.project.name
                    }]
                }
                const flowKey = task.template_source === 'project' ? 'flow' : 'common_flow'
                resourceData[flowKey] = [{
                    id: task.template_id,
                    name: task.template_name
                }]
                this.applyForPermission(required, [...task.auth_actions, ...this.authActions], resourceData)
            },
            onDeleteTask (task) {
                if (!this.hasPermission(['task_delete'], task.auth_actions)) {
                    this.onTaskPermissonCheck(['task_delete'], task)
                    return
                }
                this.theDeleteTaskId = task.id
                this.theDeleteTaskName = task.name
                this.isDeleteDialogShow = true
            },
            async onDeleteConfirm () {
                if (this.pending.delete) return
                this.pending.delete = true
                try {
                    await this.deleteTask(this.theDeleteTaskId)
                    this.theDeleteTaskId = undefined
                    this.theDeleteTaskName = ''
                    // 最后一页最后一条删除后，往前翻一页
                    if (
                        this.pagination.current > 1
                        && this.totalPage === this.pagination.current
                        && this.pagination.count - (this.totalPage - 1) * this.pagination.limit === 1
                    ) {
                        this.pagination.current -= 1
                    }
                    await this.getTaskList()
                } catch (e) {
                    errorHandler(e, this)
                } finally {
                    this.isDeleteDialogShow = false
                    this.pending.delete = false
                }
            },
            onDeleteCancel () {
                this.theDeleteTaskId = undefined
                this.theDeleteTaskName = ''
                this.isDeleteDialogShow = false
            },
            onCloneTaskClick (task) {
                if (!this.hasPermission(['task_clone'], task.auth_actions)) {
                    this.onTaskPermissonCheck(['task_clone'], task)
                    return
                }
                this.isTaskCloneDialogShow = true
                this.theCloneTaskId = task.id
                this.theCloneTaskName = task.name
            },
            async onCloneConfirm (name) {
                if (this.pending.clone) return
                this.pending.clone = true
                const config = {
                    name,
                    task_id: this.theCloneTaskId
                }
                try {
                    const data = await this.cloneTask(config)
                    this.$router.push({
                        name: 'taskExecute',
                        params: { project_id: this.project_id },
                        query: { instance_id: data.data.new_instance_id }
                    })
                } catch (e) {
                    errorHandler(e, this)
                }
            },
            onCloneCancel () {
                this.isTaskCloneDialogShow = false
                this.theCloneTaskName = ''
            },
            onSelectedStatus (id) {
                this.isStarted = id !== 'nonExecution'
                this.isFinished = id === 'finished'
            },
            onClearStatus () {
                this.isStarted = undefined
                this.isFinished = undefined
            },
            // 表格功能选项
            handleSettingChange ({ fields, size }) {
                this.setting.size = size
                this.setting.selectedFields = fields
                const fieldIds = fields.map(m => m.id)
                localStorage.setItem('TaskList', JSON.stringify({
                    fieldList: fieldIds,
                    size
                }))
            },
            onPageChange (page) {
                this.pagination.current = page
                this.updateUrl()
                this.getTaskList()
            },
            onPageLimitChange (val) {
                this.pagination.limit = val
                this.pagination.current = 1
                this.updateUrl()
                this.getTaskList()
            },
            updateUrl () {
                const { current, limit } = this.pagination
                const { category, executeTime, createMethod, creator, executor, statusSync, taskName } = this.requestData
                const filterObj = {
                    limit,
                    category,
                    creator,
                    executor,
                    statusSync,
                    createMethod,
                    page: current,
                    executeTime: executeTime.every(item => item) ? executeTime.join(',') : '',
                    keyword: taskName
                }
                const query = {}
                Object.keys(filterObj).forEach(key => {
                    const val = filterObj[key]
                    if (val || val === 0 || val === false) {
                        query[key] = val
                    }
                })
                this.$router.push({ name: 'taskList', params: { project_id: this.project_id }, query })
            },
            async getCreateMethod () {
                try {
                    const createMethodData = await this.loadCreateMethod()
                    this.taskCreateMethodList = createMethodData.data.map(m => ({ value: m.value, name: m.name }))
                    const form = this.searchForm.find(item => item.key === 'createMethod')
                    form.list = this.taskCreateMethodList
                    form.loading = false
                } catch (e) {
                    errorHandler(e, this)
                }
            },
            async getData () {
                Promise.all([
                    this.getTaskList(),
                    this.getCreateMethod(),
                    this.getBizBaseInfo()
                ]).catch(e => {
                    errorHandler(e, this)
                })
            },
            transformCreateMethod (value) {
                if (this.taskCreateMethodList.length === 0) {
                    return ''
                }
                const taskCreateMethod = this.taskCreateMethodList.find((taskCreateMethod) => taskCreateMethod['value'] === value)
                return taskCreateMethod['name']
            },
            onCreateTask () {
                this.isNewTaskDialogShow = true
            },
            onCreateTaskCancel () {
                this.isNewTaskDialogShow = false
            },
            onSearchFormSubmit (data) {
                this.requestData = Object.assign({}, this.requestData, data)
                this.pagination.current = 1
                // 高级搜索手动点击时，清空 createInfo、templateId、templateSource 筛选条件
                this.createInfo = ''
                this.templateId = ''
                this.templateSource = ''
                this.updateUrl()
                this.getTaskList()
            }
        }
    }
</script>
<style lang='scss' scoped>
@import '@/scss/config.scss';
@import '@/scss/mixins/advancedSearch.scss';
@import '@/scss/task.scss';
@import '@/scss/mixins/scrollbar.scss';

@include advancedSearch;
.task-container {
    padding: 20px 24px;
    height: 100%;
    overflow: auto;
    @include scrollbar;
}
.dialog-content {
    padding: 30px;
    word-break: break-all;
}
.list-wrapper {
    min-height: calc(100vh - 300px);
    .advanced-search {
        margin: 20px 0px;
    }
}
.bk-select-inline {
    width: 260px;
    display: inline-block;
}
.bk-input-inline {
    display: inline-block;
    width: 260px;
}
.common-icon-dark-circle-pause {
    color: #ff9c01;
    font-size: 14px;
    vertical-align: middle;
}
.task-table-content {
    background: #ffffff;
    a.task-name {
        color: $blueDefault;
    }
    .task-status {
       @include ui-task-status;
    }
    .task-operation {
        .task-operation-btn {
            padding: 5px;
            color: #3a84ff;
            font-size: 12px;
            &.disabled {
                color: #cccccc;
                cursor: not-allowed;
            }
        }
    }
    .empty-data {
        padding: 120px 0;
    }
    .template-operate-btn {
        color: $blueDefault;
    }
}
</style>
