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
    <div class="tag-select">
        <div v-if="formMode">
            <el-select
                v-model="seletedValue"
                v-loading="loading"
                filterable
                :clearable="clearable"
                popper-class="tag-component-popper"
                :allow-create="allowCreate"
                :disabled="!editable || disabled"
                :remote="remote"
                :multiple-limit="multiple_limit"
                :multiple="multiple"
                :no-data-text="empty_text"
                :filter-method="filterMethod"
                :placeholder="placeholder"
                @visible-change="onVisibleChange">
                <template v-if="showRightBtn" slot="prefix">
                    <i class="right-btn" :class="rightBtnIcon" @click="onRightBtnClick"></i>
                </template>
                <template v-if="!hasGroup">
                    <el-option
                        v-for="item in options"
                        :key="item.value"
                        :label="item.text"
                        :value="item.value">
                        <span class="option-item">{{ item.text }}</span>
                    </el-option>
                </template>
                <template v-else>
                    <el-option-group
                        v-for="group in options"
                        :key="group.value"
                        :label="group.text">
                        <el-option
                            v-for="item in group.options"
                            :key="item.value"
                            :label="item.text"
                            :value="item.value">
                            <span class="option-item">{{ item.text }}</span>
                        </el-option>
                    </el-option-group>
                </template>
            </el-select>
            <span v-show="!validateInfo.valid" class="common-error-tip error-info">{{validateInfo.message}}</span>
        </div>
        <span v-else class="rf-view-value">{{viewValue}}</span>
    </div>
</template>
<script>
    import '@/utils/i18n.js'
    import { getFormMixins } from '../formMixins.js'

    export const attrs = {
        value: {
            type: [String, Array, Boolean, Number],
            required: false,
            default: '',
            desc: gettext('下拉框的选中值，可输入 String、Boolean、Number 类型的值，若为多选请输入包含上述类型的数组格式数据')
        },
        items: {
            type: Array,
            required: false,
            default () {
                return []
            },
            desc: "array like [{text: '', value: ''}, {text: '', value: ''}]"
        },
        multiple: {
            type: Boolean,
            required: false,
            default: false,
            desc: 'set multiple selected items'
        },
        multiple_limit: {
            type: Number,
            required: false,
            default: 0,
            desc: 'limit of selected items when multiple is true'
        },
        clearable: {
            type: Boolean,
            required: false,
            default: true,
            desc: 'show the icon for clearing input value'
        },
        allowCreate: {
            type: Boolean,
            required: false,
            default: false,
            desc: 'create value in input field'
        },
        remote: {
            type: Boolean,
            required: false,
            default: false,
            desc: 'use remote data or not'
        },
        remote_url: {
            type: [String, Function],
            required: false,
            default: '',
            desc: 'remote url when remote is true'
        },
        remote_data_init: {
            type: Function,
            required: false,
            default: function (data) {
                return data
            },
            desc: 'how to process data after getting remote data'
        },
        hasGroup: {
            type: Boolean,
            required: false,
            default: false,
            desc: 'whether the options in group'
        },
        disabled: {
            type: Boolean,
            required: false,
            default: false,
            desc: 'selector is disabled'
        },
        placeholder: {
            type: String,
            required: false,
            default: '',
            desc: 'placeholder'
        },
        showRightBtn: {
            type: Boolean,
            required: false,
            default: false,
            desc: 'whether to display the button on the right of the selection box'
        },
        rightBtnIcon: {
            type: String,
            required: false,
            default: 'bk-icon icon-chain',
            desc: 'button icon to the right of the selection box'
        },
        rightBtnCb: {
            type: Function,
            required: false,
            default: null,
            desc: 'Button to the right of the selection box to click on the event callback function'
        },
        empty_text: {
            type: String,
            required: false,
            default: gettext('无数据'),
            desc: 'tips when data is empty'
        }
    }
    export default {
        name: 'TagSelect',
        mixins: [getFormMixins(attrs)],
        data () {
            return {
                options: this.$attrs.items ? this.$attrs.items.slice(0) : [],
                loading: false,
                loading_text: gettext('加载中')
            }
        },
        computed: {
            seletedValue: {
                get () {
                    return this.value
                },
                set (val) {
                    if (!this.hook) {
                        this.updateForm(val)
                    }
                }
            },
            viewValue () {
                if (Array.isArray(this.seletedValue)) { // 多选
                    if (!this.seletedValue.length) {
                        return '--'
                    }
                    if (this.items.length) {
                        return this.seletedValue.map(val => {
                            return this.filterLabel(val)
                        }).join(',')
                    } else {
                        return this.value.join(',')
                    }
                } else { // 单选
                    if (this.seletedValue === 'undefined') {
                        return '--'
                    }
                    if (this.items.length) {
                        return this.filterLabel(this.seletedValue)
                    } else {
                        return this.value
                    }
                }
            }
        },
        watch: {
            items (val) {
                this.options = val.slice(0)
            }
        },
        mounted () {
            this.remoteMethod()
        },
        methods: {
            filterLabel (val) {
                let label = val
                this.items.some(item => {
                    if (item.value === val) {
                        label = item.text
                        return true
                    }
                })
                return label
            },
            // 自定义搜索，支持以','符号分隔的多条数据搜索
            filterMethod (val) {
                if (!val) {
                    this.options = this.items.slice(0)
                    return
                }

                const inputVal = val.split(',')
                this.options = this.items.filter(option => inputVal.some(i => option.text.toLowerCase().includes(i.toLowerCase())))
            },
            set_loading (loading) {
                this.loading = loading
            },
            remoteMethod () {
                const self = this
                const remote_url = typeof this.remote_url === 'function' ? this.remote_url() : this.remote_url
                if (!remote_url) return

                // 请求远程数据
                this.loading = true
                $.ajax({
                    url: remote_url,
                    method: 'GET',
                    success: function (res) {
                        const data = self.remote_data_init(res) || []

                        self.items = data
                        self.loading = false
                    },
                    error: function (resp) {
                        self.placeholder = gettext('请求数据失败')
                        self.loading = false
                    }
                })
            },
            onRightBtnClick () {
                typeof this.rightBtnCb === 'function' && this.rightBtnCb()
            },
            onVisibleChange (val) {
                if (!val) { // 下拉框隐藏后，还原搜索过滤掉的选项
                    this.options = this.items.slice(0)
                }
            }
        }
    }
</script>
<style lang="scss" scoped>
    .el-select {
        position: relative;
        width: 100%;
        /deep/ .el-input__inner {
            padding-left: 10px;
            padding-right: 60px;
            height: 32px;
            line-height: 32px;
            font-size: 12px;
        }
        /deep/.el-input__prefix {
            left: auto;
            right: 34px;
        }
        /deep/.el-tag.el-tag--info.el-tag--small.el-tag--light { // 解决已选多选项选项过长不换行问题
            height: auto;
            .el-select__tags-text {
                white-space: normal;
                word-break: break-all;
                height: auto;
            }
        }
        .right-btn {
            display: flex;
            align-items: center;
            height: 100%;
            color: #63656e;
            cursor: pointer;
            &:hover {
                color: #3a84ff;
            }
        }
    }
</style>
<style lang="scss">
    .tag-component-popper {
        .el-select-dropdown {
            max-width: 500px;
            .el-select-dropdown__item { // 解决选项过长问题
                white-space: normal;
                word-break: break-all;
                height: auto;
            }
        }
    }
</style>
