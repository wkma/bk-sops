<template>
    <div class="variable-edit">
        <div class="variable-edit-content">
            <section class="form-section">
                <h3>{{ $t('基础信息') }}</h3>
                <!-- 名称 -->
                <div class="form-item clearfix">
                    <label class="required">{{ $t('名称') }}</label>
                    <div class="form-content">
                        <bk-input
                            name="variableName"
                            v-model="theEditingData.name"
                            v-validate="variableNameRule"
                            :readonly="isSystemVar">
                        </bk-input>
                        <span v-show="veeErrors.has('variableName')" class="common-error-tip error-msg">{{ veeErrors.first('variableName') }}</span>
                    </div>
                </div>
                <!-- key -->
                <div class="form-item clearfix">
                    <label class="required">KEY</label>
                    <div class="form-content">
                        <bk-input
                            name="variableKey"
                            v-model="theEditingData.key"
                            v-validate="variableKeyRule"
                            :readonly="isSystemVar"
                            :disabled="isHookedVar">
                        </bk-input>
                        <span v-show="veeErrors.has('variableKey')" class="common-error-tip error-msg">{{ veeErrors.first('variableKey') }}</span>
                    </div>
                </div>
                <!-- 类型 -->
                <div class="form-item variable-type clearfix" v-if="!isSystemVar">
                    <label>{{ $t('类型') }}</label>
                    <div class="form-content">
                        <bk-select
                            v-model="currentValType"
                            :disabled="isHookedVar"
                            :clearable="false"
                            @change="onValTypeChange">
                            <template v-if="isHookedVar">
                                <bk-option
                                    v-for="(option, optionIndex) in varTypeList"
                                    :key="optionIndex"
                                    :id="option.code"
                                    :name="option.name">
                                </bk-option>
                            </template>
                            <template v-else>
                                <bk-option-group
                                    v-for="(group, groupIndex) in varTypeList"
                                    :key="groupIndex"
                                    :name="group.name">
                                    <bk-option
                                        v-for="(option, optionIndex) in group.children"
                                        :key="optionIndex"
                                        :id="option.code"
                                        :name="option.name">
                                    </bk-option>
                                </bk-option-group>
                            </template>
                        </bk-select>
                        <div class="phase-tag" v-if="varPhase">{{ varPhase }}</div>
                    </div>
                    <div class="variable-type-desc" v-if="variableDesc">{{ variableDesc }}</div>
                </div>
                <!-- 验证规则 -->
                <div v-show="theEditingData.custom_type === 'input'" class="form-item clearfix">
                    <label class="form-label">{{ $t('正则校验') }}</label>
                    <div class="form-content">
                        <bk-input
                            name="valueValidation"
                            v-model="theEditingData.validation"
                            v-validate="validationRule"
                            @blur="onBlurValidation">
                        </bk-input>
                        <span v-show="veeErrors.has('valueValidation')" class="common-error-tip error-msg">{{veeErrors.first('valueValidation')}}</span>
                    </div>
                </div>
                <!-- 显示/隐藏 -->
                <div class="form-item clearfix" v-if="!isSystemVar">
                    <label>{{ $t('显示')}}</label>
                    <div class="form-content">
                        <bk-select
                            v-model="theEditingData.show_type"
                            :disabled="theEditingData.source_type === 'component_outputs'"
                            :clearable="false"
                            @change="onToggleShowType">
                            <bk-option
                                v-for="(option, index) in showTypeList"
                                :key="index"
                                :id="option.id"
                                :name="option.name">
                            </bk-option>
                        </bk-select>
                    </div>
                </div>
                <!-- 模板预渲染 -->
                <div class="form-item clearfix" v-if="!isSystemVar">
                    <label class="form-label">{{ $t('模板预渲染')}}</label>
                    <div class="form-content">
                        <bk-select
                            :value="String(theEditingData.pre_render_mako)"
                            :clearable="false"
                            @selected="onSelectPreRenderMako">
                            <bk-option
                                v-for="(option, index) in preRenderList"
                                :key="index"
                                :id="option.id"
                                :name="option.name">
                            </bk-option>
                        </bk-select>
                    </div>
                </div>
                <!-- 描述 -->
                <div class="form-item clearfix">
                    <label class="form-label">{{ $t('说明') }}</label>
                    <div class="form-content">
                        <bk-input
                            type="textarea"
                            v-model="theEditingData.desc"
                            :placeholder="isSystemVar ? ' ' : $t('请输入')"
                            :readonly="isSystemVar">
                        </bk-input>
                    </div>
                </div>
            </section>
            <section v-if="theEditingData.source_type !== 'component_outputs' && !isSystemVar" class="form-section">
                <h3>{{ theEditingData.is_meta ? $t('配置') : $t('默认值') }}</h3>
                <!-- 默认值 -->
                <div class="form-item value-form clearfix">
                    <div class="form-content" v-bkloading="{ isLoading: atomConfigLoading, opacity: 1, zIndex: 100 }">
                        <template v-if="!atomConfigLoading && renderConfig.length">
                            <RenderForm
                                ref="renderForm"
                                :scheme="renderConfig"
                                :form-option="renderOption"
                                v-model="renderData">
                            </RenderForm>
                        </template>
                    </div>
                </div>
            </section>
        </div>
        <div class="btn-wrap">
            <template v-if="!isSystemVar">
                <bk-button theme="primary" :disabled="atomConfigLoading || varTypeListLoading" @click="onSaveVariable">{{ $t('保存') }}</bk-button>
                <bk-button @click="$emit('closeEditingPanel')">{{ $t('取消') }}</bk-button>
            </template>
            <bk-button v-else theme="primary" @click="$emit('closeEditingPanel')">{{ $t('返回') }}</bk-button>
        </div>
        <bk-dialog
            width="400"
            ext-cls="common-dialog"
            :theme="'primary'"
            :mask-close="false"
            :show-footer="false"
            :value="isSaveConfirmDialogShow"
            @cancel="isSaveConfirmDialogShow = false">
            <div class="variable-confirm-dialog-content">
                <div class="leave-tips">{{ $t('保存已修改的变量信息吗？') }}</div>
                <div class="action-wrapper">
                    <bk-button theme="primary" :disabled="atomConfigLoading" @click="onConfirmClick">{{ $t('保存') }}</bk-button>
                    <bk-button theme="default" @click="$emit('closeEditingPanel')">{{ $t('不保存') }}</bk-button>
                </div>
            </div>
        </bk-dialog>
    </div>
</template>
<script>
    import i18n from '@/config/i18n/index.js'
    import { mapActions, mapState, mapMutations } from 'vuex'
    import { Validator } from 'vee-validate'
    import { NAME_REG, STRING_LENGTH } from '@/constants/index.js'
    import tools from '@/utils/tools.js'
    import { errorHandler } from '@/utils/errorHandler.js'
    import atomFilter from '@/utils/atomFilter.js'
    import formSchema from '@/utils/formSchema.js'
    import RenderForm from '@/components/common/RenderForm/RenderForm.vue'

    export default {
        name: 'VariableEdit',
        components: {
            RenderForm
        },
        props: {
            variableData: Object,
            common: [String, Number]
        },
        data () {
            const theEditingData = tools.deepClone(this.variableData)
            const isHookedVar = ['component_inputs', 'component_outputs'].includes(theEditingData.source_type)
            const currentValType = isHookedVar ? 'component' : theEditingData.custom_type

            return {
                theEditingData,
                isHookedVar, // 是否为勾选生成的变量
                currentValType,
                showTypeList: [
                    { id: 'show', name: i18n.t('显示') },
                    { id: 'hide', name: i18n.t('隐藏') }
                ],
                preRenderList: [ // 下拉框组件选项 id 不支持传布尔值
                    { id: 'true', name: i18n.t('是') },
                    { id: 'false', name: i18n.t('否') }
                ],
                metaTag: undefined, // 元变量tag名称
                renderData: {},
                renderConfig: [],
                renderOption: {
                    showHook: false,
                    showGroup: false,
                    showLabel: true,
                    showVarList: true,
                    validateSet: ['custom', 'regex']
                },
                varTypeListLoading: false,
                varTypeList: [], // 变量类型，input、textarea、datetime 等
                atomConfigLoading: false,
                atomTypeKey: '',
                isSaveConfirmDialogShow: false,
                // 变量名称校验规则
                variableNameRule: {
                    required: true,
                    max: STRING_LENGTH.VARIABLE_NAME_MAX_LENGTH,
                    regex: NAME_REG
                },
                // 正则校验规则
                validationRule: {
                    validReg: true
                }
            }
        },
        computed: {
            ...mapState({
                'atomFormConfig': state => state.atomForm.config,
                'constants': state => state.template.constants,
                'outputs': state => state.template.outputs
            }),
            ...mapState('project', {
                'project_id': state => state.project_id
            }),
            // 是否为系统内置变量
            isSystemVar () {
                return this.variableData.source_type === 'system'
            },
            /**
             * 变量配置项code
             */
            atomType () {
                const { custom_type, source_tag, source_type } = this.theEditingData

                if (source_type === 'component_inputs') {
                    return custom_type || source_tag.split('.')[0]
                } else {
                    return custom_type
                }
            },
            // 变量生命周期
            varPhase () {
                let phaseStr = ''
                const phaseMap = {
                    '1': i18n.t('即将下线'),
                    '2': i18n.t('已下线')
                }
                if (this.currentValType !== 'component' && this.varTypeList.length) {
                    this.varTypeList.some(group => {
                        return group.children.some(item => {
                            if (item.code === this.currentValType) {
                                phaseStr = phaseMap[item.phase]
                                return true
                            }
                        })
                    })
                }
                return phaseStr
            },
            // 变量 Key 校验规则
            variableKeyRule () {
                const rule = {
                    required: true,
                    regex: /(^\${[a-zA-Z_]\w*}$)|(^[a-zA-Z_]\w*$)/, // 合法变量key正则，eg:${fsdf_f32sd},fsdf_f32sd
                    keyLength: true,
                    keyRepeat: true
                }
                // 勾选的变量不做长度校验
                if (this.isHookedVar) {
                    delete rule.max
                }
                return rule
            },
            // 当前选中类型变量配置描述
            variableDesc () {
                let desc = ''
                if (this.isHookedVar) {
                    const item = this.varTypeList.find(i => i.code === this.currentValType)
                    if (item) {
                        desc = item.description
                    }
                } else {
                    this.varTypeList.some(group => {
                        const option = group.children.find(item => item.code === this.currentValType)
                        if (option) {
                            desc = option.description
                            return true
                        }
                    })
                }
                return desc
            }
        },
        created () {
            /**
             * 设置模板预渲染默认值（兼容以前存在的模板）
             * 预渲染功能发布后新建变量时，预渲染默认为false
             * 发布前用户不主动去修改变量，则不需要做处理
             */
            if (!this.variableData.key) {
                this.theEditingData.pre_render_mako = false
            }
            this.extendFormValidate()
        },
        async mounted () {
            const { is_meta, custom_type, source_tag } = this.theEditingData

            if (this.isHookedVar) {
                this.varTypeList = [{ code: 'component', name: i18n.t('组件') }]
            } else {
                await this.getVarTypeList()
                // 若当前编辑变量为元变量，则取meta_tag
                if (is_meta) {
                    const metaList = this.varTypeList.find(item => item.type === 'meta')
                    metaList.children.some(item => {
                        if (item.code === custom_type) {
                            this.metaTag = item.meta_tag
                            return true
                        }
                    })
                }
            }
            // 非输出参数勾选变量和系统内置变量(目前有自定义变量和输入参数勾选变量)需要加载标准插件配置项
            if (!['component_outputs', 'system'].includes(this.theEditingData.source_type)) {
                if (this.theEditingData.hasOwnProperty('value')) {
                    const sourceTag = is_meta ? this.metaTag : source_tag
                    const tagCode = sourceTag.split('.')[1]
                    this.renderData = {
                        [tagCode]: this.theEditingData.value
                    }
                }
                this.getAtomConfig()
            }
        },
        methods: {
            ...mapActions('template/', [
                'loadCustomVarCollection'
            ]),
            ...mapActions('atomForm/', [
                'loadAtomConfig'
            ]),
            ...mapMutations('template/', [
                'addVariable',
                'editVariable',
                'setOutputs'
            ]),
            // 获取变量类型
            async getVarTypeList () {
                this.varTypeListLoading = true
                try {
                    const customVarCollection = await this.loadCustomVarCollection()
                    const listData = [
                        {
                            name: i18n.t('普通变量'),
                            type: 'general',
                            children: []
                        },
                        {
                            name: i18n.t('动态变量'),
                            type: 'dynamic',
                            children: []
                        },
                        {
                            name: i18n.t('元变量'),
                            type: 'meta',
                            children: []
                        }
                    ]
                    customVarCollection.forEach(item => {
                        if (item.type === 'general') {
                            listData[0].children.push(item)
                        } else if (item.type === 'dynamic') {
                            listData[1].children.push(item)
                        } else {
                            listData[2].children.push(item)
                        }
                    })
                    this.varTypeList = listData
                } catch (e) {
                    errorHandler(e, this)
                } finally {
                    this.varTypeListLoading = false
                }
            },
            /**
             * 加载表单标准插件配置文件
             */
            async getAtomConfig () {
                const { source_tag, custom_type, version = 'legacy' } = this.theEditingData
                const tagStr = this.metaTag ? this.metaTag : source_tag

                // 兼容旧数据自定义变量勾选为输入参数 source_tag 为空
                const atom = tagStr.split('.')[0] || custom_type
                let classify = ''
                this.atomConfigLoading = true
                this.atomTypeKey = atom
                if (this.theEditingData.custom_type) {
                    classify = 'variable'
                } else {
                    classify = 'component'
                }
                if (atomFilter.isConfigExists(atom, version, this.atomFormConfig)) {
                    this.getRenderConfig()
                    this.$nextTick(() => {
                        this.atomConfigLoading = false
                    })
                    return
                }
                
                try {
                    await this.loadAtomConfig({
                        classify,
                        name: this.atomType,
                        project_id: this.common ? undefined : this.project_id,
                        version,
                        atom
                    })
                    this.getRenderConfig()
                } catch (e) {
                    errorHandler(e, this)
                } finally {
                    this.atomConfigLoading = false
                }
            },
            getRenderConfig () {
                const { source_tag, custom_type, version = 'legacy' } = this.theEditingData
                const tagStr = this.metaTag || source_tag
                let [atom, tag] = tagStr.split('.')
                // 兼容旧数据自定义变量勾选为输入参数 source_tag 为空
                if (custom_type) {
                    atom = atom || custom_type
                    tag = tag || custom_type
                }
                const atomConfig = this.atomFormConfig[atom][version]
                const config = tools.deepClone(atomFilter.formFilter(tag, atomConfig))
                if (custom_type === 'input' && this.theEditingData.validation !== '') {
                    config.attrs.validation.push({
                        type: 'regex',
                        args: this.getInputDefaultValueValidation(),
                        error_message: i18n.t('默认值不符合正则规则')
                    })
                }

                this.renderConfig = [config]
                if (!this.variableData.key) { // 新建变量
                    this.theEditingData.value = atomFilter.getFormItemDefaultValue(this.renderConfig)
                }
            },
            // 注册表单校验规则
            extendFormValidate () {
                this.validator = new Validator({})
                // 注册变量 key 是否重复校验规则
                this.validator.extend('keyRepeat', (value) => {
                    value = /^\$\{\w+\}$/.test(value) ? value : '${' + value + '}'
                    if (this.variableData.key === value) {
                        return true
                    }
                    if (value in this.constants) {
                        return false
                    }
                    return true
                })
                // 注册变量 key 长度规则
                this.validator.extend('keyLength', (value) => {
                    const reqLenth = /^\$\{\w+\}$/.test(value) ? (STRING_LENGTH.VARIABLE_KEY_MAX_LENGTH + 3) : STRING_LENGTH.VARIABLE_KEY_MAX_LENGTH
                    return value.length <= reqLenth
                })
                // 注册正则表达式校验规则
                this.validator.extend('validReg', (value) => {
                    try {
                        /* eslint-disable */
                        new RegExp(value)
                        /* eslint-enable */
                    } catch (e) {
                        console.error(e)
                        return false
                    }
                    return true
                })
                // 注册默认值校验规则
                this.validator.extend('customValueCheck', (value) => {
                    try {
                        const reg = new RegExp(this.theEditingData.validation)
                        if (!reg.test(value)) {
                            return false
                        }
                        return true
                    } catch (e) {
                        console.error(e)
                        return false
                    }
                })
            },
            getValidateSet () {
                const { show_type, custom_type } = this.theEditingData
                const validateSet = ['required', 'custom', 'regex']

                // 隐藏状态下，默认值为必填项
                // 输入框显示类型为隐藏时，按照正则规则校验，去掉必填项校验
                if (show_type === 'show' || (show_type === 'hide' && custom_type === 'input')) {
                    return validateSet.slice(1)
                } else {
                    return validateSet
                }
            },
            // input 表单默认校验规则
            getInputDefaultValueValidation () {
                let validation = this.theEditingData.validation
                if (this.theEditingData.show_type === 'show') {
                    validation = `(^$)|(${validation})`
                }
                return validation
            },
            // 变量类型切换
            onValTypeChange (val) {
                let data
                this.varTypeList.some(group => {
                    const option = group.children.find(item => item.code === val)
                    if (option) {
                        data = option
                        return true
                    }
                })
                this.renderData = {}
                // input 类型需要正则校验
                if (val === 'input') {
                    this.theEditingData.validation = '^.+$'
                } else {
                    this.theEditingData.validation = ''
                }
                this.theEditingData.custom_type = data.code
                this.theEditingData.source_tag = data.tag
                this.theEditingData.is_meta = data.type === 'meta'
                this.metaTag = data.meta_tag

                const validateSet = this.getValidateSet()
                this.$set(this.renderOption, 'validateSet', validateSet)
                this.getAtomConfig()
            },
            // 校验正则规则是否合法
            onBlurValidation () {
                const config = tools.deepClone(this.renderConfig[0])
                const regValidate = config.attrs.validation.find(item => item.type === 'regex')
                if (!this.veeErrors.has('valueValidation')) {
                    regValidate.args = this.getInputDefaultValueValidation()
                } else {
                    regValidate.args = ''
                }
                this.$set(this.renderConfig, 0, config)
                this.$nextTick(() => {
                    this.$refs.renderForm.validate()
                })
            },
            /**
             * 变量显示/隐藏切换
             */
            onToggleShowType (showType, data) {
                this.theEditingData.show_type = showType
                // 预渲染功能发布前的模板主动修改变量的【显示类型】，预渲染默认值为false
                const variableData = this.variableData
                if (!variableData.hasOwnProperty('pre_render_mako')) {
                    this.theEditingData.pre_render_mako = false
                }
                const validateSet = this.getValidateSet()
                this.$set(this.renderOption, 'validateSet', validateSet)

                if (this.theEditingData.custom_type === 'input' && this.theEditingData.validation !== '') {
                    const config = tools.deepClone(this.renderConfig[0])
                    const regValidate = config.attrs.validation.find(item => item.type === 'regex')
                    regValidate.args = this.getInputDefaultValueValidation()
                    this.$set(this.renderConfig, 0, config)
                    this.$nextTick(() => {
                        this.$refs.renderForm.validate()
                    })
                }
            },
            // 选择是否为模板预渲染
            onSelectPreRenderMako (val) {
                this.theEditingData.pre_render_mako = val === 'true'
            },
            handleMaskClick () {
                if (!this.variableData.key) {
                    this.isSaveConfirmDialogShow = true
                } else {
                    const tagCode = this.renderConfig[0].tag_code
                    const editingVariable = Object.assign({}, this.theEditingData, { value: this.renderData[tagCode] })
                    editingVariable.key = /^\$\{\w+\}$/.test(editingVariable.key) ? editingVariable.key : '${' + editingVariable.key + '}'
                    if (tools.isDataEqual(editingVariable, this.variableData)) {
                        this.$emit('closeEditingPanel')
                    } else {
                        this.isSaveConfirmDialogShow = true
                    }
                }
            },
            onConfirmClick () {
                this.isSaveConfirmDialogShow = false
                this.onSaveVariable()
            },
            // 保存变量数据
            onSaveVariable () {
                return this.$validator.validateAll().then(result => {
                    let formValid = true
            
                    // renderform表单校验
                    if (this.$refs.renderForm) {
                        formValid = this.$refs.renderForm.validate()
                    }

                    if (!result || !formValid) {
                        return false
                    }

                    const variable = this.theEditingData
                    if (this.renderConfig.length > 0) { // 变量有默认值表单需要填写时，取表单值
                        const tagCode = this.renderConfig[0].tag_code
                        let varValue = {}
    
                        // value为空且不渲染RenderForm组件的变量取表单默认值
                        if (this.renderData.hasOwnProperty(tagCode)) {
                            varValue = this.renderData
                        } else {
                            varValue = atomFilter.getFormItemDefaultValue(this.renderConfig)
                        }

                        // 变量key值格式统一
                        if (!/^\$\{\w+\}$/.test(variable.key)) {
                            variable.key = '${' + variable.key + '}'
                        }
    
                        this.theEditingData.value = varValue[tagCode]
                    }

                    this.theEditingData.name = this.theEditingData.name.trim()
                    if (!this.variableData.key) { // 新增变量
                        variable.version = 'legacy'
                        variable.form_schema = formSchema.getSchema(
                            variable.custom_type,
                            this.atomFormConfig[this.atomTypeKey][variable.version]
                        )
                        this.addVariable(tools.deepClone(variable))
                    } else { // 编辑变量
                        this.editVariable({ key: this.variableData.key, variable })
                        // 如果全局变量有被勾选为输出，修改变量 key 后需要更新 outputs 字段
                        if (this.variableData.key !== this.theEditingData.key && this.outputs.includes(this.variableData.key)) {
                            this.setOutputs({ changeType: 'edit', key: this.variableData.key, newKey: this.theEditingData.key })
                        }
                    }
                    this.$emit('onSaveEditing')
                    return true
                })
            }
        }
    }
</script>
<style lang="scss" scoped>
    .variable-edit {
        height: 100%;
    }
    .variable-edit-content {
        padding: 20px 20px 40px;
        height: calc(100% - 49px);
        overflow-y: auto;
    }
    .form-section {
        margin-bottom: 30px;
        & > h3 {
            margin: 0;
            padding-bottom: 10px;
            color: #313238;
            font-size: 14px;
            font-weight: bold;
            border-bottom: 1px solid #cacedb;
        }
    }
    .form-item {
        margin: 15px 0;
        &:first-child {
            margin-top: 0;
        }
        label {
            position: relative;
            float: left;
            width: 60px;
            margin-top: 8px;
            font-size: 12px;
            color: #666666;
            text-align: right;
            word-wrap: break-word;
            word-break: break-all;
            &.required:before {
                content: '*';
                position: absolute;
                top: 0px;
                right: -10px;
                color: #ff2602;
                font-family: "SimSun";
            }
        }
        &.value-form {
            .form-content {
                margin-left: 0;
            }
        }
    }
    .form-content {
        margin-left: 80px;
        min-height: 36px;
        /deep/ {
            .bk-select {
                background: #ffffff;
                &.is-disabled {
                    background-color: #fafbfd !important;
                    border-color: #dcdee5 !important;
                }
            }
            .el-input {
                .el-input__inner {
                    padding: 0 10px;
                    height: 36px;
                    line-height: 36px;
                }
            }
            .tag-form {
                margin-left: 0;
            }
        }
    }
    .error-msg {
        margin-top: 10px;
    }
    .variable-type {
        position: relative;
        .phase-tag {
            position: absolute;
            right: 30px;
            top: 4px;
            padding: 3px 6px;
            border-radius: 10px;
            border-bottom-left-radius: 0;
            font-size: 12px;
            color: #ffffff;
            background: #b8b8b8;
        }
        .variable-type-desc {
            margin-left: 80px;
            font-size: 12px;
            color: #666;
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
    /deep/ .variable-confirm-dialog-content {
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
