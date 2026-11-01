<script setup lang="ts">
import { ref, watchEffect } from "vue";

export type SwitchProps = {
  active?: boolean;
  disabled?: boolean;
};

const emits = defineEmits(["click"]);

const props = withDefaults(defineProps<SwitchProps>(), { active: false });
const value = ref(false);

const onClick = () => {
  if (props.disabled) return;
  value.value = !value.value;
  emits("click", value.value);
};

watchEffect(() => {
  value.value = props.active;
});
</script>

<template>
  <div class="switch" :class="{
    active: value,
  }" @click="onClick">
    <div class="switch-block"></div>
  </div>
</template>

<style lang="scss">
@mixin hi-all-transition {
  transition: all 0.3s ease;
}

.switch {
  width: 36px;
  height: 20px;
  border-radius: 20px;
  position: relative;
  display: flex;
  align-items: center;
  background-color: rgba(0, 0, 0, .1);
  @include hi-all-transition;

  .switch-block {
    width: 16px;
    height: 16px;
    background-color: #fff;
    border-radius: 50%;
    @include hi-all-transition;
    transform: translateX(2px);
  }

  &.active {
    background-color: var(--active-color);

    .switch-block {
      transform: translateX(18px);
    }
  }
}
</style>
