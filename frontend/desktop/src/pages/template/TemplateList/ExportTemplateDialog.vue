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
    <bk-dialog
        width="850"
        :ext-cls="'common-dialog'"
        :title="$t('导出流程')"
        :mask-close="false"
        :value="isExportDialogShow"
        :header-position="'left'"
        :auto-close="false"
        @confirm="onConfirm"
        @cancel="onCancel">
        <div class="export-container" v-bkloading="{ isLoading: businessInfoLoading, opacity: 1, zIndex: 100 }">
            <div class="template-wrapper">
                <div class="search-wrapper">
                    <div class="business-selector">
                        <bk-select
                            v-model="filterCondition.classifyId"
                            class="bk-select-inline"
                            :clearable="false"
                            :disabled="exportPending"
                            @change="onSelectClassify">
                            <bk-option
                                v-for="(item, index) in taskCategories"
                                :key="index"
                                :id="item.value"
                                :name="item.name">
                            </bk-option>
                        </bk-select>
                    </div>
                    <div class="template-search">
                        <bk-input
                            class="search-input"
                            v-model.trim="filterCondition.keywords"
                            :clearable="true"
                            :placeholder="$t('请输入流程名称')"
                            :right-icon="'icon-search'"
                            @input="onSearchInput">
                        </bk-input>
                    </div>
                </div>
                <div class="template-list" v-bkloading="{ isLoading: exportPending, opacity: 1, zIndex: 100 }">
                    <ul class="grouped-list">
                        <template v-for="group in templateInPanel">
                            <li
                                v-if="group.children.length"
                                :key="group.id"
                                class="template-group">
                                <h5 class="group-name">
                                    {{group.name}}
                                    (<span class="list-count">{{group.children.length}}</span>)
                                </h5>
                                <ul class="group-wrap">
                                    <base-card
                                        v-for="(template, i) in group.children"
                                        :key="i"
                                        :data="template"
                                        :selected="getTplIndexInSelected(template) > -1"
                                        :is-apply-permission="!hasPermission(reqPerm, template.auth_actions)"
                                        @onCardClick="onSelectTemplate(template)">
                                    </base-card>
                                </ul>
                            </li>
                        </template>
                        <NoData v-if="!templateInPanel.length" class="empty-template"></NoData>
                    </ul>
                </div>
            </div>
            <div class="selected-wrapper">
                <div class="selected-area-title">
                    {{$t('已选择')}}
                    <span class="select-count">{{selectedTemplates.length}}</span>
                    {{$t('项')}}
                </div>
                <ul class="selected-list">
                    <base-card
                        v-for="(template, i) in selectedTemplates"
                        :key="i"
                        :data="template"
                        :selected="true"
                        :show-delete="true"
                        @onDeleteCard="deleteTemplate(template)">
                    </base-card>
                </ul>
            </div>
            <bk-checkbox class="template-checkbox" @change="onSelectAllClick" :value="isTplInPanelAllSelected">{{ $t('全选') }}</bk-checkbox>
            <div class="task-footer" v-if="selectError">
                <span class="error-info">{{$t('请选择流程模版')}}</span>
            </div>
        </div>
    </bk-dialog>
</template>
<script>
    import i18n from '@/config/i18n/index.js'
    import toolsUtils from '@/utils/tools.js'
    import { mapState, mapActions } from 'vuex'
    import { errorHandler } from '@/utils/errorHandler.js'
    import NoData from '@/components/common/base/NoData.vue'
    import permission from '@/mixins/permission.js'
    import BaseCard from '@/components/common/base/BaseCard.vue'
    export default {
        name: 'ExportTemplateDialog',
        components: {
            NoData,
            BaseCard
        },
        mixins: [permission],
        props: {
            isExportDialogShow: Boolean,
            businessInfoLoading: Boolean,
            projectInfoLoading: Boolean,
            common: String,
            pending: Boolean,
            project_id: [Number, String]
        },
        data () {
            return {
                exportPending: false,
                isTplInPanelAllSelected: false,
                isCheckedDisabled: false,
                templateList: [],
                templateInPanel: [],
                searchList: [],
                selectedTemplates: [],
                selectError: false,
                templateEmpty: false,
                selectedTaskCategory: '',
                category: '',
                filterCondition: {
                    classifyId: 'all',
                    keywords: ''
                },
                dialogFooterData: [
                    {
                        type: 'primary',
                        loading: false,
                        btnText: i18n.t('确认'),
                        click: 'onConfirm'
                    }, {
                        btnText: i18n.t('取消'),
                        click: 'onCancel'
                    }
                ]
            }
        },
        computed: {
            ...mapState({
                'projectBaseInfo': state => state.template.projectBaseInfo
            }),
            taskCategories () {
                const list = toolsUtils.deepClone(this.projectBaseInfo.task_categories || [])
                list.unshift({ value: 'all', name: i18n.t('全部分类') })
                return list
            },
            reqPerm () {
                return this.common ? ['common_flow_view'] : ['flow_view']
            }
        },
        watch: {
            pending () {
                this.dialogFooterData[0].loading = this.pending
            }
        },
        created () {
            this.getData()
            this.onSearchInput = toolsUtils.debounce(this.searchInputhandler, 500)
        },
        methods: {
            ...mapActions('templateList/', [
                'loadTemplateList'
            ]),
            ...mapActions([
                'getCategorys'
            ]),
            async getData () {
                if (this.projectBaseInfo.task_categories && this.projectBaseInfo.task_categories.length === 0) {
                    await this.getCategorys()
                    this.getTemplateData()
                } else {
                    this.getTemplateData()
                }
            },
            async getTemplateData () {
                this.exportPending = true
                this.isCheckedDisabled = true
                try {
                    const data = {}
                    if (this.common) {
                        data.common = 1
                    } else {
                        data.project__id = this.project_id
                    }
                    const respData = await this.loadTemplateList(data)
                    const list = respData.objects
                    this.templateList = this.getGroupedList(list)
                    this.templateInPanel = this.templateList.slice(0)
                } catch (e) {
                    errorHandler(e, this)
                } finally {
                    this.exportPending = false
                    this.isCheckedDisabled = false
                }
            },
            getGroupedList (list) {
                const groups = []
                const atomGrouped = []
                this.taskCategories.forEach(item => {
                    groups.push(item.value)
                    atomGrouped.push({
                        name: item.name,
                        value: item.value,
                        children: []
                    })
                })
                list.forEach(item => {
                    const type = item.category
                    const index = groups.indexOf(type)
                    if (index > -1) {
                        atomGrouped[index].children.push(item)
                    }
                })
                const listGroup = atomGrouped.filter(item => item.children.length)
                return listGroup
            },
            getTemplateIcon (template) {
                return template.name.trim().substr(0, 1).toUpperCase()
            },
            getTplIndexInSelected (template) {
                return this.selectedTemplates.findIndex(item => item.id === template.id)
            },
            getTplIsAllSelected () {
                if (!this.templateInPanel.length) {
                    return false
                }
                return this.templateInPanel.every(group => {
                    return group.children.every(template => {
                        return this.selectedTemplates.findIndex(item => item.id === template.id) > -1
                    })
                })
            },
            onSelectClassify (value) {
                let groupedList = []
                this.filterCondition.classifyId = value

                if (value === 'all') {
                    groupedList = this.templateList.slice(0)
                } else {
                    groupedList = this.templateList.filter(group => group.value === value)
                }

                if (this.filterCondition.keywords !== '') {
                    this.searchInputhandler()
                } else {
                    this.templateInPanel = groupedList
                }

                this.isTplInPanelAllSelected = this.getTplIsAllSelected()
            },
            searchInputhandler () {
                let searchList = []

                if (this.filterCondition.classifyId !== 'all') {
                    searchList = this.templateList.filter(group => group.value === this.filterCondition.classifyId)
                } else {
                    searchList = this.templateList.slice(0)
                }
                this.templateInPanel = toolsUtils.deepClone(searchList).filter(group => {
                    group.children = group.children.filter(template => {
                        return template.name.includes(this.filterCondition.keywords)
                    })
                    return group.children.length
                })
            },
            onSelectTemplate (template) {
                if (this.hasPermission(this.reqPerm, template.auth_actions)) {
                    this.selectError = false
                    const tplIndex = this.getTplIndexInSelected(template)
                    if (tplIndex > -1) {
                        this.selectedTemplates.splice(tplIndex, 1)
                        this.isTplInPanelAllSelected = false
                    } else {
                        this.selectedTemplates.push(template)
                        this.isTplInPanelAllSelected = this.getTplIsAllSelected()
                    }
                } else {
                    let permissionData
                    if (this.common) {
                        permissionData = {
                            common_flow: [{
                                id: template.id,
                                name: template.name
                            }]
                        }
                    } else {
                        permissionData = {
                            flow: [{
                                id: template.id,
                                name: template.name
                            }],
                            project: [{
                                id: template.project.id,
                                name: template.project.name
                            }]
                        }
                    }
                    this.applyForPermission(this.reqPerm, template.auth_actions, permissionData)
                }
            },
            deleteTemplate (template) {
                const tplIndex = this.getTplIndexInSelected(template)
                this.selectedTemplates.splice(tplIndex, 1)
                this.isTplInPanelAllSelected = false
            },
            onSelectAllClick () {
                if (this.isCheckedDisabled) {
                    return
                }

                this.templateInPanel.forEach(group => {
                    group.children.forEach(template => {
                        if (this.hasPermission(this.reqPerm, template.auth_actions)) {
                            const tplIndex = this.getTplIndexInSelected(template)
                            if (this.isTplInPanelAllSelected) {
                                if (tplIndex > -1) {
                                    this.selectedTemplates.splice(tplIndex, 1)
                                }
                            } else {
                                if (tplIndex === -1) {
                                    this.selectedTemplates.push(template)
                                }
                            }
                        }
                    })
                })
                this.isTplInPanelAllSelected = !this.isTplInPanelAllSelected
            },
            onConfirm () {
                const idList = []
                if (this.selectedTemplates.length === 0) {
                    this.selectError = true
                    return false
                } else {
                    this.selectedTemplates.forEach(item => {
                        idList.push(item.id)
                    })
                    this.$emit('onExportConfirm', idList)
                    this.resetData()
                }
            },
            onCancel () {
                this.templateEmpty = false
                this.selectError = false
                this.resetData()
                this.$emit('onExportCancel')
            },
            resetData () {
                this.selectedTemplates = []
                this.filterCondition = {
                    classifyId: 'all',
                    keywords: ''
                }
                this.isTplInPanelAllSelected = false
                this.templateInPanel = this.templateList.slice(0)
            }
        }
    }
</script>
<style lang="scss" scoped>
@import '@/scss/mixins/scrollbar.scss';
@import '@/scss/mixins/multiLineEllipsis.scss';
@import '@/scss/config.scss';
.export-container {
    position: relative;
    height: 340px;
    .search-wrapper {
        padding: 0 18px 0 20px;
    }
    .project-selector {
        position: absolute;
        top: 20px;
        width: 255px;
        height: 32px;
    }
    .business-selector {
        width: 260px;
        display: inline-block;
        vertical-align: top;
    }
    .template-search {
        width: 250px;
        display: inline-block;
        vertical-align: top;
    }
    .template-wrapper {
        float: left;
        padding: 20px 4px 20px 0;
        width: 557px;
        height: 100%;
        .template-list {
            padding: 0 14px 0 20px;
            height: 284px;
            overflow-y: auto;
            @include scrollbar;
        }
        .template-group {
            margin-bottom: 30px;
        }
        .search-list {
            padding-top: 40px;
        }
        .group-name {
            margin-bottom: 8px;
            font-size: 12px;
        }
    }
    .group-wrap {
        width: 100%;
        overflow: hidden;
        .card-item {
            float: left;
            width: calc(( 100% - 16px) / 2);
            margin-right: 0;
            border-radius: 2px;
            &:not(:nth-child(2n)) {
                margin-right: 16px;
            }
        }
    }
    .empty-template {
        padding-top: 104px;
    }
    .selected-wrapper {
        width: 292px;
        height: 100%;
        margin-left: 557px;
        padding-right: 4px;
        border-left:1px solid #dde4eb;
        .selected-area-title {
            padding: 28px 20px 22px;
            line-height: 1;
            font-size: 14px;
            font-weight: 600;
            color: #313238;
            .select-count {
                color: #3a84ff;
            }
        }
    }
    .selected-list {
        padding-top: 8px;
        height: 276px;
        overflow-y: auto;
        @include scrollbar;
        .card-item {
            width: 252px;
            margin: 0 0 10px 14px;
        }
    }
    .template-checkbox {
        position: absolute;
        left: 20px;
        bottom: -38px;
    }
    .task-footer {
        position: absolute;
        right: 290px;
        bottom: -40px;
        .error-info {
            margin-right: 20px;
            font-size: 12px;
            color: #ea3636;
        }
    }
}
</style>
