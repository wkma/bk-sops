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
    <div class="exception-box">
        <img :src="require('@/assets/images/building.png')" alt="404">
        <p>{{ $t('没找到页面！') }}</p>
    </div>
</template>

<script>
    export default {
    }
</script>
<style lang="scss">
    .exception-box {
        margin: 150px auto 0;
        width: 300px;
        text-align: center;
        img {
            width: 100%;
        }
    }
</style>
