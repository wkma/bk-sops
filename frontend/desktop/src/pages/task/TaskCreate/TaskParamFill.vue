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
    <div class="param-fill-wrapper">
        <div class="form-area">
            <div :class="['task-info', { 'functor-task-info': entrance === 'function' }]">
                <div class="task-info-title">
                    <span>{{ $t('任务信息') }}</span>
                </div>
                <div class="task-basic-info">
                    <div class="common-form-item">
                        <label class="required">{{ $t('任务名称') }}</label>
                        <div class="common-form-content" v-bkloading="{ isLoading: taskMessageLoading, opacity: 1, zIndex: 100 }">
                            <bk-input
                                v-model="taskName"
                                v-validate="taskNameRule"
                                class="step-form-content-size"
                                name="taskName">
                            </bk-input>
                            <span v-show="veeErrors.has('taskName')" class="common-error-tip error-msg">{{ veeErrors.first('taskName') }}</span>
                        </div>
                    </div>
                    <div
                        v-if="!isExecuteSchemeHide"
                        class="common-form-item">
                        <label class="required">{{$t('执行计划')}}</label>
                        <div class="common-form-content">
                            <div class="bk-button-group">
                                <bk-button
                                    :theme="!isStartNow ? 'default' : 'primary'"
                                    @click="onChangeStartNow(true)">
                                    {{ $t('立即执行') }}
                                </bk-button>
                                <bk-button
                                    :theme="!isStartNow ? 'primary' : 'default'"
                                    @click="onChangeStartNow(false)">
                                    {{ $t('周期执行') }}
                                </bk-button>
                            </div>
                        </div>
                    </div>
                    <div
                        v-if="isTaskTypeShow"
                        class="common-form-item">
                        <label class="required">{{ $t('流程类型') }}</label>
                        <div class="common-form-content">
                            <div class="bk-button-group">
                                <bk-button
                                    :theme="isSelectFunctionalType ? 'default' : 'primary'"
                                    @click="onSwitchTaskType(false)">
                                    {{ $t('默认任务流程') }}
                                </bk-button>
                                <bk-button
                                    :theme="isSelectFunctionalType ? 'primary' : 'default'"
                                    @click="onSwitchTaskType(true)">
                                    {{ $t('职能化任务流程') }}
                                </bk-button>
                            </div>
                        </div>
                    </div>
                    <div
                        v-if="!isStartNow"
                        class="common-form-item">
                        <label class="required">{{$t('周期表达式')}}</label>
                        <div class="common-form-content step-form-item-cron">
                            <LoopRuleSelect
                                ref="loopRuleSelect"
                                :manual-input-value="periodicCron">
                            </LoopRuleSelect>
                        </div>
                    </div>
                </div>
            </div>
            <div class="param-info">
                <div class="param-info-title">
                    <span>
                        {{ $t('参数信息') }}
                    </span>
                </div>
                <div>
                    <ParameterInfo
                        ref="ParameterInfo"
                        :referenced-variable="pipelineData.constants"
                        :un-referenced-variable="unreferenced"
                        :task-message-loading="taskMessageLoading"
                        @paramsLoadingChange="paramsLoadingChange">
                    </ParameterInfo>
                </div>
            </div>
        </div>
        <div class="action-wrapper">
            <bk-button
                class="preview-step-button"
                @click="onGotoSelectNode">
                {{ $t('上一步') }}
            </bk-button>
            <bk-button
                :class="['next-step-button', {
                    'btn-permission-disable': common ? !hasCommonTplCreateTaskPerm : !hasPermission(nextStepPerm, actions)
                }]"
                theme="primary"
                :loading="isSubmit"
                :disabled="paramsLoading || commonTplCreateTaskPermLoading || nextBtnDisable"
                v-cursor="{ active: common ? !hasCommonTplCreateTaskPerm : !hasPermission(nextStepPerm, actions) }"
                @click="onCreateTask">
                {{$t('下一步')}}
            </bk-button>
        </div>
    </div>
</template>
<script>
    import i18n from '@/config/i18n/index.js'
    // moment用于时区使用
    import moment from 'moment-timezone'
    import { mapState, mapActions, mapMutations } from 'vuex'
    import { errorHandler } from '@/utils/errorHandler.js'
    import { NAME_REG, PERIODIC_REG, STRING_LENGTH } from '@/constants/index.js'
    import tools from '@/utils/tools.js'
    import permission from '@/mixins/permission.js'
    import ParameterInfo from '@/pages/task/ParameterInfo.vue'
    import LoopRuleSelect from '@/components/common/Individualization/loopRuleSelect.vue'

    export default {
        name: 'TaskParamFill',
        components: {
            ParameterInfo,
            LoopRuleSelect
        },
        mixins: [permission],
        props: ['project_id', 'template_id', 'common', 'entrance', 'excludeNode'],
        data () {
            return {
                bkMessageInstance: null,
                isSubmit: false,
                isSelectFunctionalType: false,
                taskName: '',
                appmakerTaskName: '',
                pipelineData: {},
                unreferenced: {},
                taskNameRule: {
                    required: true,
                    max: STRING_LENGTH.TASK_NAME_MAX_LENGTH,
                    regex: NAME_REG
                },
                isStartNow: true,
                periodicCron: '*/5 * * * *',
                periodicRule: {
                    required: true,
                    regex: PERIODIC_REG
                },
                periodicCronImg: require('@/assets/images/' + i18n.t('task-zh') + '.png'),
                lastTaskName: '',
                node: {},
                templateData: {},
                taskParamEditLoading: true,
                taskMessageLoading: true,
                hasCommonTplCreateTaskPerm: false,
                commonTplCreateTaskPermLoading: false,
                paramsLoading: false,
                nextBtnDisable: false,
                disabledButton: true,
                tplActions: []
            }
        },
        computed: {
            ...mapState({
                'locations': state => state.template.location,
                'templateName': state => state.template.name,
                'viewMode': state => state.view_mode,
                'app_id': state => state.app_id,
                'permissionMeta': state => state.permissionMeta
            }),
            ...mapState('project', {
                'timeZone': state => state.timezone,
                'projectName': state => state.projectName
            }),
            ...mapState('appmaker', {
                'appmakerDetail': state => state.appmakerDetail
            }),
            isCommonProcess () {
                return Number(this.$route.query.common) === 1
            },
            isTaskTypeShow () {
                return this.entrance !== 'function' && this.isStartNow
            },
            isPeriodicSelectShow () {
                return this.entrance.indexOf('periodicTask') > -1
            },
            nextStepPerm () {
                if (this.viewMode === 'appmaker') {
                    return ['mini_app_create_task']
                } else {
                    if (this.isStartNow) {
                        return this.common ? ['common_flow_create_task'] : ['flow_create_task']
                    } else {
                        return this.common ? ['common_flow_create_periodic_task'] : ['flow_create_periodic_task']
                    }
                }
            },
            actions () {
                return this.viewMode === 'appmaker' ? this.appmakerDetail.auth_actions : this.tplActions
            },
            // 不显示【执行计划】的情况
            isExecuteSchemeHide () {
                return this.common || this.viewMode === 'appmaker' || (['periodicTask', 'taskflow', 'function'].indexOf(this.entrance) > -1)
            }
        },
        created () {
            if (this.entrance === 'periodicTask') {
                this.isStartNow = false
            }
            if (this.common) {
                this.queryCommonTplCreateTaskPerm()
            }
            this.loadData()
        },
        methods: {
            ...mapActions([
                'queryUserPermission'
            ]),
            ...mapActions('template/', [
                'loadTemplateData'
            ]),
            ...mapActions('appmaker/', [
                'loadAppmakerDetail'
            ]),
            ...mapActions('task/', [
                'getSchemeDetail',
                'loadPreviewNodeData',
                'createTask'
            ]),
            ...mapActions('periodic/', [
                'createPeriodic'
            ]),
            ...mapMutations('template/', [
                'setTemplateData'
            ]),
            async queryCommonTplCreateTaskPerm () {
                try {
                    this.commonTplCreateTaskPermLoading = true
                    const bkSops = this.permissionMeta.system.find(item => item.id === 'bk_sops')
                    const data = {
                        action: 'common_flow_create_task',
                        resources: [
                            {
                                system: bkSops.id,
                                type: 'project',
                                id: this.project_id,
                                attributes: {}
                            },
                            {
                                system: bkSops.id,
                                type: 'common_flow',
                                id: this.template_id,
                                attributes: {}
                            }
                        ]
                    }
                    const res = await this.queryUserPermission(data)
                    this.hasCommonTplCreateTaskPerm = res.data.is_allow
                } catch (err) {
                    errorHandler(err, this)
                } finally {
                    this.commonTplCreateTaskPermLoading = false
                }
            },
            async loadData () {
                this.taskMessageLoading = true
                try {
                    const data = {
                        templateId: this.template_id,
                        common: this.common
                    }
                    const templateSource = this.common ? 'common' : 'business'
                    const templateData = await this.loadTemplateData(data)
                    if (templateData.result === false) {
                        errorHandler(templateData, this)
                        this.nextBtnDisable = true
                        return
                    }

                    this.tplActions = templateData.auth_actions
                    this.setTemplateData(templateData)

                    let schemeId = ''
                    const excludeNodeIdList = []
                    if (this.viewMode === 'appmaker') {
                        await this.loadAppmakerDetail(this.app_id).then(res => {
                            schemeId = res.template_scheme_id
                            this.appmakerTaskName = res.name
                        })
                        if (schemeId) {
                            const schemeDetail = await this.getSchemeDetail({ id: schemeId, isCommon: this.isCommonProcess })
                            const allNodeId = JSON.parse(schemeDetail.data)
                            this.locations.filter(item => {
                                if (allNodeId.indexOf(item.id) === -1 && item.optional) {
                                    excludeNodeIdList.push(item.id)
                                }
                            })
                        }
                    }
                    const excludeTaskNodesId = this.excludeNode.length ? this.excludeNode : excludeNodeIdList
                    const params = {
                        templateId: this.template_id,
                        excludeTaskNodesId,
                        common: this.common,
                        project_id: this.project_id,
                        template_source: templateSource,
                        version: templateData.version
                    }
                    const previewData = await this.loadPreviewNodeData(params)
                    if (previewData.result === false) {
                        errorHandler(previewData, this)
                        this.nextBtnDisable = true
                        return
                    }
                    this.pipelineData = previewData.data.pipeline_tree
                    this.unreferenced = previewData.data.constants_not_referred
                    this.taskName = this.getDefaultTaskName()
                } catch (e) {
                    if (e.status === 404) {
                        this.$router.push({ name: 'notFoundPage' })
                    }
                    errorHandler(e, this)
                } finally {
                    this.taskMessageLoading = false
                }
            },
            getDefaultTaskName () {
                let nowTime = ''
                if (this.common) {
                    // 无时区的公共流程使用本地的时间
                    nowTime = moment().format('YYYYMMDDHHmmss')
                } else {
                    nowTime = moment.tz(this.timeZone).format('YYYYMMDDHHmmss')
                }
                if (this.viewMode === 'appmaker') {
                    return this.appmakerTaskName + '_' + nowTime
                }
                return this.templateName + '_' + nowTime
            },
            onSwitchTaskType (isFunctional) {
                this.isSelectFunctionalType = isFunctional
                this.$emit('toggleFunctionalStep', isFunctional)
            },
            onGotoSelectNode () {
                const url = {
                    name: 'taskCreate',
                    params: { project_id: this.project_id, step: 'selectnode' },
                    query: { 'template_id': this.template_id, common: this.common || undefined, entrance: this.entrance || undefined }
                }
                if (this.entrance !== 'function') {
                    this.$emit('setFunctionalStep', false)
                } else {
                    url.name = 'functionTemplateStep'
                }
                if (this.viewMode === 'appmaker') {
                    url.name = 'appmakerTaskCreate'
                    url.params.app_id = this.app_id
                }
                this.$router.push(url)
            },
            onCreateTask () {
                let hasNextPermission = false
                if (this.common) {
                    if (this.commonTplCreateTaskPermLoading) {
                        return
                    }
                    hasNextPermission = this.hasCommonTplCreateTaskPerm
                } else {
                    hasNextPermission = this.hasPermission(this.nextStepPerm, this.actions)
                }
                if (!hasNextPermission) {
                    let resourceData = {}
                    if (this.viewMode === 'appmaker') {
                        resourceData = {
                            mini_app: [{
                                id: this.app_id,
                                name: this.appmakerDetail.name
                            }],
                            project: [{
                                id: this.project_id,
                                name: this.projectName
                            }]
                        }
                    } else {
                        if (this.common) {
                            resourceData = {
                                common_flow: [{
                                    id: this.template_id,
                                    name: this.templateName
                                }],
                                project: [{
                                    id: this.project_id,
                                    name: this.projectName
                                }]
                            }
                        } else {
                            resourceData = {
                                flow: [{
                                    id: this.template_id,
                                    name: this.templateName
                                }],
                                project: [{
                                    id: this.project_id,
                                    name: this.projectName
                                }]
                            }
                        }
                    }
                    this.applyForPermission(this.nextStepPerm, this.actions, resourceData)
                    return
                }

                const loopRule = !this.isStartNow ? this.$refs.loopRuleSelect.validationExpression() : { check: true, rule: '' }
                if (!loopRule.check || this.isSubmit) {
                    return false
                }
                // 页面中是否有 TaskParamEdit 组件
                const paramEditComp = this.$refs.ParameterInfo.getTaskParamEdit()
                this.$validator.validateAll().then(async (result) => {
                    let formValid = true
                    const pipelineData = tools.deepClone(this.pipelineData)
                    // 取最新参数
                    if (paramEditComp) {
                        const formData = await paramEditComp.getVariableData()
                        pipelineData.constants = formData
                        formValid = paramEditComp.validate()
                    }

                    if (!result) {
                        const $basicInfo = document.querySelector('.task-basic-info')
                        $basicInfo.scrollIntoView()
                        return
                    }

                    if (!formValid) {
                        const $renderform = document.querySelector('.render-form')
                        const $tipsEl = Array.from($renderform.querySelectorAll('.common-error-tip'))
                        let $tipInView = null
                        $tipsEl.some(item => {
                            console.log(item.style.display)
                            if (item.style.display !== 'none') {
                                $tipInView = item
                                return true
                            }
                        })
                        if ($tipInView) {
                            $tipInView.scrollIntoView()
                        }
                        return
                    }

                    this.isSubmit = true
                    let flowType
                    if (
                        (this.$route.name === 'functionTemplateStep'
                        && this.entrance === 'function')
                        || this.isSelectFunctionalType) {
                        // 职能化任务
                        flowType = 'common_func'
                    } else {
                        // 普通任务
                        flowType = 'common'
                    }
                    if (this.isStartNow) {
                        const data = {
                            'name': this.taskName,
                            'description': '',
                            'templateId': this.template_id,
                            'execData': JSON.stringify(pipelineData),
                            'flowType': flowType,
                            'common': this.common
                        }
                        try {
                            const taskData = await this.createTask(data)
                            let url = {}
                            if (this.viewMode === 'appmaker') {
                                const { template_id } = this.$route.query
                                if (this.isSelectFunctionalType) { // 轻应用创建职能化任务
                                    url = {
                                        name: 'appmakerTaskHome',
                                        params: { app_id: this.app_id, project_id: this.project_id },
                                        query: { template_id }
                                    }
                                } else {
                                    url = {
                                        name: 'appmakerTaskExecute',
                                        params: { app_id: this.app_id, project_id: this.project_id },
                                        query: { instance_id: taskData.instance_id, template_id }
                                    }
                                }
                            } else if (this.$route.name === 'functionTemplateStep' && this.entrance === 'function') { // 职能化创建任务
                                url = {
                                    name: 'functionTaskExecute',
                                    params: { project_id: this.project_id },
                                    query: { instance_id: taskData.instance_id, common: this.common }
                                }
                            } else if (this.isSelectFunctionalType) { // 手动选择职能化流程
                                url = {
                                    name: 'taskList',
                                    params: { project_id: this.project_id },
                                    query: { common: this.common }
                                }
                            } else {
                                url = {
                                    name: 'taskExecute',
                                    params: { project_id: this.project_id },
                                    query: { instance_id: taskData.instance_id, common: this.common } // 公共流程创建职能化任务
                                }
                            }
                            this.$router.push(url)
                        } catch (e) {
                            errorHandler(e, this)
                        } finally {
                            this.isSubmit = false
                        }
                    } else {
                        // 创建周期任务
                        const cronArray = loopRule.rule.split(' ')
                        const cron = {
                            'minute': cronArray[0],
                            'hour': cronArray[1],
                            'day_of_week': cronArray[2],
                            'day_of_month': cronArray[3],
                            'month_of_year': cronArray[4]
                        }
                        const data = {
                            'name': this.taskName,
                            'cron': cron,
                            'templateId': this.template_id,
                            'execData': JSON.stringify(pipelineData),
                            'templateSource': this.common ? 'common' : undefined
                        }
                        try {
                            await this.createPeriodic(data)
                            this.$bkMessage({
                                'message': i18n.t('创建周期任务成功'),
                                'theme': 'success'
                            })
                            this.$router.push({ name: 'periodicTemplate', params: { project_id: this.project_id } })
                        } catch (e) {
                            errorHandler(e, this)
                        } finally {
                            this.isSubmit = false
                        }
                    }
                })
            },
            onChangeStartNow (value) {
                if (value === this.isStartNow) {
                    return
                }
                this.isStartNow = value
                this.$emit('togglePeriodicStep', !value, this.isSelectFunctionalType)
                if (!value) {
                    this.lastTaskName = this.taskName
                    this.taskName = this.templateName
                } else {
                    this.taskName = this.lastTaskName
                }
            },
            paramsLoadingChange (val) {
                this.paramsLoading = val
            }
        }
    }
</script>
<style lang="scss" scoped>
@import "@/scss/config.scss";
@import "@/scss/mixins/scrollbar.scss";

.param-fill-wrapper {
    position: relative;
    height: calc(100vh - 100px);
    background: #fff;
}
.form-area {
    padding-top: 20px;
    height: calc(100% - 72px);
    overflow: auto;
    @include scrollbar;
}
.task-info,
.param-info {
    margin: 0 40px 20px 40px;
    .task-info-title,
    .param-info-title {
        font-size: 14px;
        line-height: 32px;
        font-weight: 600;
        color: #313238;
        border-bottom: 1px solid #cacedb;
        margin-bottom: 30px;
    }
    .common-form-item {
        label {
            color: #313238;
            font-weight: normal;
        }
    }
}
.param-info {
    margin: 0 20px 50px 20px;
}
.param-info-title {
    margin: 0 20px 0 20px;
}
.functor-task-info {
    padding-bottom: 0px;
}
.common-section-title {
    margin-bottom: 24px;
}
.bk-button-group {
    .bk-button {
        width: 250px;
        margin: 0px;
    }
    .bk-button.bk-primary {
        position: relative;
        z-index: 4;
        color: #3a84ff;
        background-color: #c7dcff;
        border-radius: 2px;
        border: 1px solid #3a84ff;
    }
    .bk-button:last-child {
        margin-left: -1px;
    }
}
.periodic-img-tooltip {
    position: absolute;
    right: 20px;
    top: 0;
    color: #c4c6cc;
    font-size: 14px;
    z-index: 4;
    &:hover {
        color: #f4aa1a;
    }
    /deep/ .bk-tooltip-arrow {
        display: none;
    }
}
.startnow-form-content,
.periodic-form-content {
    margin-top: 10px;
}
.radio-input {
    margin-right: 30px;
}
.step-form-content-size {
    max-width: 500px;
}
/deep/ .bk-tooltip-inner {
    max-width: 600px;
    border: 1px solid #c4c6cc;
    background-color: #000;
}
.step-form-content {
    /deep/ .bk-tooltip-arrow {
        position: absolute;
        bottom: 6px;
    }
    img {
        position: relative;
        bottom: -4px;
        left: 13px;
        background-color: $whiteDefault;
        border: 1px solid #dddddd;
    }
}
.step-form-item-cron {
    position: relative;
    input {
        vertical-align: top;
    }
}
.action-wrapper {
    height: 72px;
    line-height: 72px;
    border-top: 1px solid #cacedb;
    background-color: #ffffff;
    box-shadow: 0 -3px 4px 0 rgba(64,112,203,0.06);
    .preview-step-button {
        padding: 0px;
        margin-left: 40px;
        width: 90px;
        height: 32px;
        line-height: 32px;
        color: #313238;
    }
    .next-step-button {
        width: 140px;
    }
}
</style>
