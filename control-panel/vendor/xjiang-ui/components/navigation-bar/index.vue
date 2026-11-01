<script setup lang="ts">
import Icon from "../icon/index.vue";
import { ref } from "vue";
import { useRouter } from "vue-router";
const router = useRouter();

const ICON_KEYS: any = {
  'back': "icon-back",
  'menu': "icon-setting1",
  'confirm': "icon-tick",
}

export type MenuOptions = {
  key?: string;
  badge?: boolean | null;
  onClick?: () => void;
};

export interface NavigationBarProps {
  title?: string;
  right?: MenuOptions[];
  left?: MenuOptions[];
  statusbarHeight?: number;
  backgroundColor?: string;
}

const props = defineProps<NavigationBarProps>();

const defaultLeft = [
  {
    key: "back",
    badge: false,
    onClick: () => router.back()
  }
]
const leftMenu = ref(props.left || defaultLeft);
</script>

<template>
  <div class="navigationBarOuter"
    :style="{ 'padding-top': `${(statusbarHeight || 24)}px`, background: backgroundColor || 'transparent' }">
    <div class="navigationBar">
      <div class="navigationBar_left" v-if="leftMenu && leftMenu.length">
        <template v-for="(item, index) in leftMenu" :key="item?.key || index">
          <div class="navigationBar_icon" :class="{ 'badge': !!item?.badge || false }"
            v-if="item?.key && ICON_KEYS.hasOwnProperty(item?.key)">
            <Icon :name="ICON_KEYS[item?.key]" @click="item?.onClick" />
          </div>
        </template>
      </div>
      <h1 v-if="title">{{ title }}</h1>
      <div class="navigationBar_left navigationBar_right" v-if="right && right.length">
        <template v-for="(item, index) in right" :key="item?.key || index">
          <div class="navigationBar_icon" :class="{ 'badge': !!item?.badge || false }"
            v-if="item?.key && ICON_KEYS.hasOwnProperty(item?.key)">
            <Icon :name="ICON_KEYS[item?.key]" @click="item?.onClick" />
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.navigationBarOuter {
  @apply relative z-[1000];
}

.navigationBar {
  @apply flex items-center;
  min-height: 56px;
  padding: 0 1.4rem;
  text-align: center;

  .navigationBar_icon {
    position: relative;
    width: 1.7rem;
    height: 1.7rem;

    &.badge::after {
      content: '';
      position: absolute;
      right: 0;
      top: 0;
      width: 5px;
      height: 5px;
      border-radius: 50%;
      background-color: rgb(216, 10, 10);
    }
  }

  .navigationBar_left {
    position: absolute;
    left: 17px;
    margin-top: 0px;
    max-width: 5rem;

    &.navigationBar_right {
      left: auto;
      right: 1.4rem;
    }

    i {}
  }

  h1 {
    display: block;
    flex: 1;
    font-weight: 500;
    font-size: 1.2rem;
  }
}
</style>