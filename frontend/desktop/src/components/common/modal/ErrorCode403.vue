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
    <div class="content-wrapper">
        <h3 class="error-title">{{ $t('对不起，您没有当前应用的访问权限') }}</h3>
        <p>{{ $t('请尝试如下操作：') }}</p>
        <ul>
            <li>{{ $t('联系应用“管理员”为您添加应用访问白名单或者 IP 白名单') }}</li>
        </ul>
    </div>
</template>
<script>
    export default {
        name: 'ErrorCode403'
    }
</script>
<style lang="scss" scoped>
    ul {
        padding-left: 30px;
    }
    li {
        list-style: disc;
    }
</style>
