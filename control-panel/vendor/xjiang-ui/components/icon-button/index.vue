<script setup lang="ts">
import Icon from "../icon/index.vue";

export interface IconButtonProps {
  name: string;
  active?: boolean;
  size?: number;
  iconSize?: number;
  rounded?: number;
  buttonBg?: string;
  type?: number;  // 0 - svg; 1 - 图片
}

const props = withDefaults(defineProps<IconButtonProps>(), {
  size: 3.4
});
</script>

<template>
  <div 
    class="iconButton"
    :style="{ 
      width: `${size}rem`, height: `${size}rem`, 
      'border-radius': rounded ? `${ rounded }rem` : '50%', 
      background: buttonBg
    }"
    :class="{ 'active': active }"
    @click="$emit('click')"
  >
    <Icon 
      :name="name" 
      :width="`${ iconSize ?? (size / 2) }rem`" 
      :height="`${ iconSize ?? (size / 2) }rem`" 
      v-if="!type"
    />
    <img 
      v-else
      :src="name"
      :style="{
        width: `${ iconSize ?? (size / 2) }rem`,
        height: `${ iconSize ?? (size / 2) }rem`
      }"
    />
  </div>
</template>

<style lang="scss" scoped>
.iconButton {
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background-color: var(--icon-button-bg);
  svg {
    color:  var(--icon-color);
  }

  img {
    max-width: 100%;
  }
  &.active {
    background-color: var(--active-color);
    svg {
      color: #fff;
    }
    img {

    }
  }
}
</style>
