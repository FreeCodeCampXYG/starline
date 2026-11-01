<!-- eslint-disable vue/multi-word-component-names -->
<script setup lang="ts">
import { onMounted, ref } from "vue";

export interface CenterConfirmDialogProps {
  title: string;
  message: string;
  cancelText?: string;
  confirmText?: string;
  canDismiss?: boolean;
  onClose?: () => void;
  onUnmountContainer?: () => void;
  onCancel?: () => boolean | void;
  onConfirm?: () => boolean | void;
}

const props = withDefaults(defineProps<CenterConfirmDialogProps>(), {
  cancelText: "",
  confirmText: "",
  canDismiss: true,
  onClose: () => {},
  onUnmountContainer: () => {},
  onCancel: () => true,
  onConfirm: () => true,
});

const emit = defineEmits<{ close: []; destroy: [] }>();

const visible = ref(false);

const close = () => {
  if (props.canDismiss) {
    visible.value = false;
  }
};

const run = (fn?: () => boolean | void) => {
  const ret = fn?.();
  if (ret !== false) {
    visible.value = false;
  }
};

function onTransitionAfterLeave() {
  emit("destroy");
  props.onUnmountContainer?.();
}

defineExpose({ visible, close });

onMounted(() => {
  visible.value = true;
});
</script>

<template>
  <Transition @before-leave="emit('close')" @after-leave="onTransitionAfterLeave">
    <div v-show="visible" class="ccd-overlay" role="presentation" @click="close">
      <div
        class="ccd-dialog"
        role="dialog"
        aria-modal="true"
        :aria-label="title"
        @click.stop="">
        <header class="ccd-header">
          <span class="ccd-icon" aria-hidden="true">
            <svg viewBox="0 0 22 22" width="22" height="22" xmlns="http://www.w3.org/2000/svg">
              <path
                fill="#F43F31"
                d="M11,22C4.9248672,22,0,17.075134,0,11C0,4.9248672,4.9248672,0,11,0C17.075134,0,22,4.9248672,22,11C22,17.075134,17.075134,22,11,22ZM10.212125,12.969C10.344125,13.36225,10.60675,13.624875,11,13.624875C11.39325,13.624875,11.655875,13.363626,11.787875,12.969L12.313126,5.7502503C12.311611,5.0256586,11.724591,4.4386382,11,4.4371252C10.212125,4.4371252,9.6868753,5.0930004,9.6868753,5.8808751L10.212125,12.969ZM11,14.938C10.212125,14.938,9.6868753,15.46325,9.6868753,16.249752C9.6868753,17.037626,10.212125,17.562876,11,17.562876C11.787875,17.562876,12.313126,17.037626,12.313126,16.249752C12.313126,15.463252,11.787875,14.938,11,14.938Z" />
            </svg>
          </span>
          <span class="ccd-title">{{ title }}</span>
        </header>
        <p class="ccd-message">{{ message }}</p>
        <footer class="ccd-footer">
          <button type="button" class="ccd-btn ccd-btn-cancel" @click="run(props.onCancel)">
            {{ cancelText }}
          </button>
          <button type="button" class="ccd-btn ccd-btn-confirm" @click="run(props.onConfirm)">
            {{ confirmText }}
          </button>
        </footer>
      </div>
    </div>
  </Transition>
</template>

<style lang="scss" scoped>
/* tokens from MasterGo: paint_2:1901 overlay black; paint_2:0529 #FFFFFF; paint_2:1240 #F7F8FC; paint_2:1957 #F43F31 警告颜色; paint_2:0770 #212121; paint_2:0681 #999999 */

.ccd-overlay {
  @apply fixed inset-0 z-[999999] flex items-center justify-center px-4;
  background: rgba(0, 0, 0, 0.4);
}

.ccd-dialog {
  /* width ~311 @375 from design; scales down on narrow screens */
  @apply w-full max-w-[min(19.4375rem,calc(100vw-2rem))] overflow-hidden rounded-[1.25rem] bg-white px-4 pb-4 pt-6;
  box-sizing: border-box;
}

.ccd-header {
  @apply mb-2 flex items-center justify-center gap-2 text-center;
}

.ccd-icon {
  @apply flex-shrink-0 leading-none;
}

.ccd-title {
  @apply text-base font-semibold leading-[1.375rem];
  color: #212121; /* token 主文字颜色 */
}

.ccd-message {
  @apply mb-6 text-center text-base leading-6;
  color: #999999;
  white-space: pre-line;
}

.ccd-footer {
  @apply flex w-full gap-[0.9375rem];
}

.ccd-btn {
  @apply min-h-11 flex-1 cursor-pointer rounded-lg border-0 text-base font-normal leading-[1.5625rem];
  box-sizing: border-box;
}

.ccd-btn-cancel {
  background: #f7f8fc; /* token 卡片背景色 */
  color: #212121; /* token 主色 */
}

.ccd-btn-confirm {
  background: #f43f31; /* token 警告颜色 */
  color: #f7f8fc; /* token 卡片背景色 on primary */
}
</style>
