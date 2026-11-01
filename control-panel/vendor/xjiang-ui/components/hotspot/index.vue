<script setup lang="ts">
import { toRefs } from "vue";
import { isNil } from "lodash-es";
// import { pxToRem } from "@/utils";

export interface HiHotspotProps {
  width?: number | null;
  height?: number | null;
  disabled?: boolean;
}

defineEmits(["click"]);

const props = withDefaults(defineProps<HiHotspotProps>(), {
  width: null,
  height: null,
  disabled: false,
});

const { width, height, disabled } = toRefs(props);
</script>

<template>
  <div
    class="relative"
    :class="{
      disabled: disabled,
    }"
    @click="() => $emit('click')"
  >
    <slot></slot>
    <div
      class="hi-hotspot"
      :style="{
        // width: isNil(width) ? '100%' : pxToRem(width),
        // height: isNil(height) ? '100%' : pxToRem(height),
        width: '100%',
        height: '100%',
      }"
    ></div>
  </div>
</template>

<style lang="scss" scoped>
.hi-hotspot {
  @apply absolute top-1/2 left-1/2;
  transform: translate(-50%, -50%);
}
</style>
