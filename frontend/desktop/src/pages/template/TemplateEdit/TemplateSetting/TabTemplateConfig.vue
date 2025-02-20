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
    <bk-sideslider
        :title="$t('基础信息')"
        :is-show="true"
        :width="800"
        :quick-close="true"
        :before-close="beforeClose">
        <div class="config-wrapper" slot="content">
            <bk-form
                ref="configForm"
                class="form-area"
                :model="formData"
                :label-width="140"
                :rules="rules">
                <section class="form-section">
                    <h4>{{ $t('基础') }}</h4>
                    <bk-form-item property="name" :label="$t('流程名称')" :required="true">
                        <bk-input ref="nameInput" v-model.trim="formData.name" :placeholder="$t('请输入流程模板名称')"></bk-input>
                    </bk-form-item>
                    <bk-form-item v-if="!common" :label="$t('标签')">
                        <bk-select
                            v-model="formData.labels"
                            ext-popover-cls="label-select"
                            :display-tag="true"
                            :multiple="true">
                            <bk-option
                                v-for="(item, index) in templateLabels"
                                :key="index"
                                :id="item.id"
                                :name="item.name">
                                <div class="label-select-option">
                                    <span
                                        class="label-select-color"
                                        :style="{ background: item.color }">
                                    </span>
                                    <span>{{item.name}}</span>
                                    <i class="bk-option-icon bk-icon icon-check-1"></i>
                                </div>
                            </bk-option>
                            <div slot="extension" @click="onEditLabel" class="label-select-extension">
                                <i class="common-icon-edit"></i>
                                <span>{{ $t('编辑标签') }}</span>
                            </div>
                        </bk-select>
                    </bk-form-item>
                    <bk-form-item property="category" :label="$t('分类')">
                        <bk-select
                            v-model="formData.category"
                            class="category-select"
                            :clearable="false">
                            <bk-option
                                v-for="(item, index) in taskCategories"
                                :key="index"
                                :id="item.id"
                                :name="item.name">
                            </bk-option>
                        </bk-select>
                        <i
                            v-if="!common"
                            class="common-icon-info category-tips"
                            v-bk-tooltips="{
                                content: $t('模板分类即将下线，建议使用标签'),
                                placement: 'bottom',
                                theme: 'light',
                                showOnInit: true
                            }">
                        </i>
                    </bk-form-item>
                </section>
                <section class="form-section">
                    <h4>{{ $t('通知') }}</h4>
                    <bk-form-item :label="$t('通知方式')">
                        <bk-checkbox-group v-model="formData.notifyType" v-bkloading="{ isLoading: notifyTypeLoading, opacity: 1, zIndex: 100 }">
                            <template v-for="item in notifyTypeList">
                                <bk-checkbox
                                    v-if="item.is_active"
                                    :key="item.type"
                                    :value="item.type">
                                    <img class="notify-icon" :src="`data:image/png;base64,${item.icon}`" />
                                    <span style="word-break: break-all;">{{item.label}}</span>
                                </bk-checkbox>
                            </template>
                        </bk-checkbox-group>
                    </bk-form-item>
                    <bk-form-item :label="$t('通知分组')">
                        <bk-checkbox-group v-model="formData.receiverGroup" v-bkloading="{ isLoading: notifyGroupLoading, opacity: 1, zIndex: 100 }">
                            <bk-checkbox
                                v-for="item in notifyGroup"
                                :key="item.id"
                                :value="item.id">
                                {{item.name}}
                            </bk-checkbox>
                        </bk-checkbox-group>
                    </bk-form-item>
                </section>
                <section class="form-section">
                    <h4>{{ $t('其他') }}</h4>
                    <bk-form-item :label="$t('执行代理人')">
                        <member-select
                            :multiple="false"
                            :value="formData.executorProxy"
                            @change="formData.executorProxy = $event">
                        </member-select>
                    </bk-form-item>
                    <bk-form-item property="notifyType" :label="$t('备注')">
                        <bk-input type="textarea" v-model.trim="formData.description" :rows="5" :placeholder="$t('请输入流程模板备注信息')"></bk-input>
                    </bk-form-item>
                </section>
            </bk-form>
            <div class="btn-wrap">
                <bk-button class="save-btn" theme="primary" :disabled="notifyTypeLoading || notifyGroupLoading" @click="onSaveConfig">{{ $t('保存') }}</bk-button>
                <bk-button theme="default" @click="closeTab">{{ $t('取消') }}</bk-button>
            </div>
            <bk-dialog
                width="400"
                ext-cls="common-dialog"
                :theme="'primary'"
                :mask-close="false"
                :show-footer="false"
                :value="isSaveConfirmDialogShow"
                @cancel="isSaveConfirmDialogShow = false">
                <div class="template-config-dialog-content">
                    <div class="leave-tips">{{ $t('保存已修改的配置信息吗？') }}</div>
                    <div class="action-wrapper">
                        <bk-button theme="primary" :disabled="notifyTypeLoading || notifyGroupLoading" @click="onConfirmClick">{{ $t('保存') }}</bk-button>
                        <bk-button theme="default" @click="closeTab">{{ $t('不保存') }}</bk-button>
                    </div>
                </div>
            </bk-dialog>
        </div>
    </bk-sideslider>
</template>

<script>
    import { mapState, mapMutations, mapActions } from 'vuex'
    import MemberSelect from '@/components/common/Individualization/MemberSelect.vue'
    import { errorHandler } from '@/utils/errorHandler.js'
    import tools from '@/utils/tools.js'
    import { NAME_REG, STRING_LENGTH } from '@/constants/index.js'
    import i18n from '@/config/i18n/index.js'

    export default {
        name: 'TabTemplateConfig',
        components: {
            MemberSelect
        },
        props: {
            projectInfoLoading: Boolean,
            templateLabelLoading: Boolean,
            templateLabels: Array,
            isShow: Boolean,
            common: [String, Number]
        },
        data () {
            const {
                name, category, notify_type, notify_receivers, description,
                executor_proxy, template_labels
            } = this.$store.state.template
            return {
                formData: {
                    name,
                    category,
                    description,
                    executorProxy: executor_proxy ? [executor_proxy] : [],
                    receiverGroup: notify_receivers.receiver_group.slice(0),
                    notifyType: notify_type.slice(0),
                    labels: template_labels
                },
                notifyTypeList: [],
                projectNotifyGroup: [],
                isSaveConfirmDialogShow: false,
                notifyTypeLoading: false,
                notifyGroupLoading: false,
                rules: {
                    name: [
                        {
                            required: true,
                            message: i18n.t('必填项'),
                            trigger: 'blur'
                        },
                        {
                            max: STRING_LENGTH.TEMPLATE_NAME_MAX_LENGTH,
                            message: i18n.t('流程名称长度不能超过') + STRING_LENGTH.TEMPLATE_NAME_MAX_LENGTH + i18n.t('个字符'),
                            trigger: 'blur'
                        },
                        {
                            regex: NAME_REG,
                            message: i18n.t('流程名称不能包含') + '\'‘"”$&<>' + i18n.t('非法字符'),
                            trigger: 'blur'
                        }
                    ]
                }
            }
        },
        computed: {
            ...mapState({
                'projectBaseInfo': state => state.template.projectBaseInfo,
                'timeout': state => state.template.time_out
            }),
            notifyGroup () {
                let list = []
                if (this.projectBaseInfo.notify_group) {
                    const defaultList = list.concat(this.projectBaseInfo.notify_group.map(item => {
                        return {
                            id: item.value,
                            name: item.text
                        }
                    }))
                    list = defaultList.concat(this.projectNotifyGroup)
                }
                return list
            },
            taskCategories () {
                if (this.projectBaseInfo.task_categories) {
                    return this.projectBaseInfo.task_categories.map(item => {
                        return {
                            id: item.value,
                            name: item.name
                        }
                    })
                }
                return []
            }
        },
        created () {
            this.getNotifyTypeList()
            if (!this.common) {
                this.getProjectNotifyGroup()
            }
        },
        mounted () {
            this.$refs.nameInput.focus()
        },
        methods: {
            ...mapMutations('template/', [
                'setTplConfig'
            ]),
            ...mapActions([
                'getNotifyTypes',
                'getNotifyGroup'
            ]),
            async getNotifyTypeList () {
                try {
                    this.notifyTypeLoading = true
                    const res = await this.getNotifyTypes()
                    this.notifyTypeList = res.data
                } catch (error) {
                    errorHandler(error, this)
                } finally {
                    this.notifyTypeLoading = false
                }
            },
            onEditLabel () {
                const { href } = this.$router.resolve({ name: 'projectConfig', params: { id: this.$route.params.project_id } })
                window.open(href, '_blank')
            },
            async getProjectNotifyGroup () {
                try {
                    this.notifyGroupLoading = true
                    const res = await this.getNotifyGroup({ project_id: this.$route.params.project_id })
                    this.projectNotifyGroup = res.data
                } catch (error) {
                    errorHandler(error, this)
                } finally {
                    this.notifyGroupLoading = false
                }
            },
            getTemplateConfig () {
                const { name, category, description, executorProxy, receiverGroup, notifyType, labels } = this.formData
                return {
                    name,
                    category,
                    description,
                    template_labels: labels,
                    executor_proxy: executorProxy.length === 1 ? executorProxy[0] : '',
                    receiver_group: receiverGroup,
                    notify_type: notifyType
                }
            },
            onSaveConfig () {
                this.$refs.configForm.validate().then(result => {
                    if (!result) {
                        return
                    }

                    const data = this.getTemplateConfig()
                    this.setTplConfig(data)
                    this.closeTab()
                    this.$emit('templateDataChanged')
                })
            },
            onConfirmClick () {
                this.isSaveConfirmDialogShow = false
                this.onSaveConfig()
            },
            beforeClose () {
                const { name, category, description, template_labels, executor_proxy, notify_receivers, notify_type } = this.$store.state.template
                const originData = {
                    name,
                    category,
                    description,
                    template_labels,
                    executor_proxy,
                    receiver_group: notify_receivers.receiver_group,
                    notify_type
                }
                const editingData = this.getTemplateConfig()
                if (tools.isDataEqual(originData, editingData)) {
                    this.closeTab()
                    return true
                } else {
                    this.isSaveConfirmDialogShow = true
                    return false
                }
            },
            closeTab () {
                this.$emit('closeTab')
            }
        }
    }
</script>

<style lang="scss" scoped>
@import '@/scss/config.scss';
@import '@/scss/mixins/scrollbar.scss';
.config-wrapper {
    height: calc(100vh - 60px);
    background: none;
    border: none;
    .form-area {
        padding: 30px 30px 0;
        height: calc(100% - 49px);
        overflow-y: auto;
        @include scrollbar;
    }
    .form-section {
        margin-bottom: 30px;
        & > h4 {
            margin: 0 0 24px 0;
            padding-bottom: 10px;
            color: #313238;
            font-weight: bold;
            font-size: 14px;
            border-bottom: 1px solid #cacedb;
        }
    }
    .btn-wrap {
        padding: 8px 30px;
        border-top: 1px solid #cacedb;
        .bk-button {
            margin-right: 10px;
            padding: 0 25px;
        }
    }
    /deep/ .bk-label {
        font-size: 12px;
    }
    .bk-form-checkbox {
        margin-right: 20px;
        margin-bottom: 6px;
        min-width: 96px;
        /deep/ .bk-checkbox-text {
            color: $greyDefault;
            font-size: 12px;
        }
    }
    /deep/ .bk-checkbox-text {
        display: inline-flex;
        align-items: center;
        width: 100px;
    }
    .notify-icon {
        margin-right: 4px;
        width: 18px;
    }
    .user-selector {
        display: block;
    }
    .category-tips {
        position: absolute;
        right: -20px;
        top: 10px;
        font-size: 16px;
        color: #c4c6cc;
        cursor: pointer;
        &:hover {
            color: #f4aa1a;
        }
    }
}
/deep/ .template-config-dialog-content {
    padding: 40px 0;
    text-align: center;
    .leave-tips {
        font-size: 24px;
        margin-bottom: 20px;
    }
    .action-wrapper .bk-button {
        margin-right: 6px;
    }
}
</style>
