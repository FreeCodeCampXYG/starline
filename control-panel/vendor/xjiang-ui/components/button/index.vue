<script setup lang="ts">

export type SwitchProps = {
  text?: string;
  type?: string;
  disabled?: boolean;
};

const emits = defineEmits(["click"]);
const props = withDefaults(defineProps<SwitchProps>(), { type: "default" });

const onClick = () => {
  if (props.disabled) return;
  emits("click");
};
</script>

<template>
  <div
    class="xj-button"
    :class="`${ type }`"
    @click="onClick"
  >
    {{text}}
  </div>
</template>

<style lang="scss">
@mixin hi-all-transition {
  transition: all 0.3s ease;
}

.xj-button {
  @apply text-center text-[1.2rem];
  height: 50px;
  line-height: 50px;
  border-radius: 25px;
  background-color: rgba(0,0,0,.1);
  &.primary {
    background-color: var(--active-color);
    color: #fff;
  }
}
</style>
