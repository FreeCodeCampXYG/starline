<script setup lang="ts">
import { onMounted, ref, toRefs } from "vue";

export interface ToastProps {
  text: string;
  duration?: number;
  onClose?: () => void;
}

defineEmits(["close", "destroy"]);

const props = withDefaults(defineProps<ToastProps>(), {
  duration: 2000,
  onClose: () => {},
});

const { text, duration } = toRefs(props);
const visible = ref(false);

const close = () => {
  visible.value = false;
};

defineExpose({
  visible,
  close,
});

onMounted(() => {
  visible.value = true;
  setTimeout(() => close(), duration.value);
});
</script>

<template>
  <Transition @before-leave="$emit('close')" @after-leave="$emit('destroy')">
    <div v-show="visible" class="toast" @click="close">
      <p>{{ text }}</p>
    </div>
  </Transition>
</template>

<style lang="scss" scoped>
.toast {
  @apply z-[1000] fixed bottom-[6.4rem] left-[1.6rem] right-[1.6rem] text-center;
  p {
    @apply text-[1.4rem] inline-block leading-[3.6rem] px-[1.6rem] rounded-[1.8rem] bg-[#4D4D4D] text-[#ffffff] shadow-[0_10px_50px_rgba(0,0,30,.3)] dark:text-[rgba(255,255,255,.86)] dark:shadow-[0_10px_50px_rgba(0,0,0,.8)];
  }
}
</style>
